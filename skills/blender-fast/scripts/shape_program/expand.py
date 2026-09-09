"""Expand a program into validated geometry instructions before touching Blender."""
import copy
import hashlib
import json
import math
from .expressions import evaluate,vector
from .transforms import identity,multiply,pose,point
from .validation import validate_structure,name

MAX_PARTS=12000
MAX_VERTICES=1000000
MAX_VISITS=60000


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def expand(program):
    validate_structure(program)
    definitions=program['definitions'];palette=program['palette'];budget={'parts':0,'vertices':0,'visits':0}
    checked=set()
    def check_cycles(key,trail=()):
        if key in trail:raise ValueError('Recursive definition: '+key)
        if len(trail)>16:raise ValueError('Call nesting is too deep')
        if key in checked:return
        def visit(nodes):
            for node in nodes:
                if node['op']=='call':check_cycles(node['use'],trail+(key,))
                if 'children' in node:visit(node['children'])
        visit(definitions[key]['nodes'])
        checked.add(key)
    for key in definitions:check_cycles(key)

    def params(key,args,outer):
        defaults=definitions[key].get('params',{})
        if set(args)-set(defaults):raise ValueError('Unknown argument to '+key)
        env=dict(outer)
        supplied={k:evaluate(v,outer) for k,v in args.items()}
        for k,v in defaults.items():env[k]=supplied[k] if k in supplied else evaluate(v,env)
        return env

    def transform(node,env):
        at=vector(node.get('at',[0,0,0]),env);rotation=vector(node.get('rotation',[0,0,0]),env)
        scale=vector(node.get('scale',[1,1,1]),env)
        if any(v<=0 or v>100 for v in scale):raise ValueError('Scale must be positive and at most 100')
        return pose(at,rotation,scale)

    def bindings(extra,current):
        result=dict(current)
        for key,value in extra.items():result[key]=current.get(name(value),value)
        return result

    def number(node,key,env,default=None,lo=.0001,hi=1000):
        v=evaluate(node.get(key,default),env)
        if not lo<=v<=hi:raise ValueError('Out-of-range '+key)
        return v

    def primitive(node,env,matrix,material):
        op=node['op'];result={'op':op,'name':node.get('name',op),'matrix':matrix,'material':material}
        n=number(node,'segments',env,24,3,128) if op in ('cylinder','cone','ring','beam','sweep','lathe') else 0
        if n and int(n)!=n:raise ValueError('segments must be an integer')
        if n:result['segments']=int(n)
        verts=32
        if op in ('box','sphere'):
            result['size']=vector(node.get('size'),env)
            if any(v<=0 or v>1000 for v in result['size']):raise ValueError('Invalid primitive size')
            verts=162 if op=='sphere' else 24
        elif op in ('cylinder','cone'):
            for key in ('radius','height'):result[key]=number(node,key,env)
            verts=2*n
        elif op=='ring':
            for key in ('radius','tube'):result[key]=number(node,key,env)
            if result['tube']>=result['radius']:raise ValueError('Ring tube must be smaller than radius')
            verts=n*8
        elif op=='beam':
            for key in ('a','b'):result[key]=vector(node.get(key),env)
            if sum((a-b)**2 for a,b in zip(result['a'],result['b']))<1e-10:raise ValueError('Beam endpoints coincide')
            result['radius']=number(node,'radius',env);verts=2*n
        elif op=='sweep':
            path=node.get('path')
            if not isinstance(path,list) or not 2<=len(path)<=128:raise ValueError('Sweep requires 2 through 128 path points')
            result['path']=[vector(p,env) for p in path]
            for a,b in zip(result['path'],result['path'][1:]):
                if sum((x-y)**2 for x,y in zip(a,b))<1e-10:raise ValueError('Sweep has duplicate adjacent points')
            radii=node.get('radii')
            if not isinstance(radii,list):radii=[radii]*len(path)
            if len(radii)!=len(path):raise ValueError('Sweep radii must match path length')
            result['radii']=[evaluate(r,env) for r in radii]
            if any(not .0001<=r<=1000 for r in result['radii']):raise ValueError('Invalid sweep radius')
            result['caps']=node.get('caps',True)
            if not isinstance(result['caps'],bool):raise ValueError('caps must be boolean')
            verts=n*len(path)
        elif op=='lathe':
            profile=node.get('profile')
            if not isinstance(profile,list) or not 2<=len(profile)<=128:raise ValueError('Lathe requires 2 through 128 radius/height pairs')
            result['profile']=[vector(p,env,2) for p in profile]
            if any(not .0001<=p[0]<=1000 for p in result['profile']):raise ValueError('Invalid lathe radius')
            if any(a==b for a,b in zip(result['profile'],result['profile'][1:])):raise ValueError('Duplicate profile point')
            verts=n*len(profile)
        elif op=='surface':
            points=node.get('vertices');faces=node.get('faces')
            if not isinstance(points,list) or not 3<=len(points)<=4096 or not isinstance(faces,list) or not 1<=len(faces)<=4096:raise ValueError('Invalid surface size')
            result['vertices']=[vector(p,env) for p in points];result['faces']=faces
            for face in faces:
                if not isinstance(face,list) or not 3<=len(face)<=64 or any(type(i) is not int or not 0<=i<len(points) for i in face) or len(set(face))!=len(face):raise ValueError('Invalid surface indices')
            verts=len(points)
        elif op=='text':
            text=node.get('text')
            if not isinstance(text,str) or not 1<=len(text)<=80:raise ValueError('Invalid text')
            result.update(text=text,size=number(node,'size',env,.4),depth=number(node,'depth',env,.01,0,1));verts=len(text)*128
        else:raise ValueError('Unsupported primitive')
        budget['parts']+=1;budget['vertices']+=int(verts)
        if budget['parts']>MAX_PARTS or budget['vertices']>MAX_VERTICES:raise ValueError('Program exceeds geometry budget')
        return result

    def visit(nodes,env,parent,materials,trail=()):
        budget['visits']+=1
        if budget['visits']>MAX_VISITS:raise ValueError('Program exceeds expansion budget')
        output=[]
        if len(trail)>16:raise ValueError('Call nesting is too deep')
        for node in nodes:
            budget['visits']+=1
            if budget['visits']>MAX_VISITS:raise ValueError('Program exceeds expansion budget')
            matrix=multiply(parent,transform(node,env));op=node['op']
            if op=='group':output.extend(visit(node['children'],env,matrix,materials,trail))
            elif op=='repeat':
                count=number(node,'count',env,lo=0,hi=512)
                if int(count)!=count:raise ValueError('Repeat count must be an integer')
                index=name(node.get('index','i'));step=vector(node.get('step',[0,0,0]),env);turn=vector(node.get('turn',[0,0,0]),env)
                for i in range(int(count)):
                    repeated=multiply(matrix,pose([i*v for v in step],[i*v for v in turn]))
                    output.extend(visit(node['children'],dict(env,**{index:i}),repeated,materials,trail))
            elif op=='call':
                key=node['use'];local=params(key,node.get('args',{}),env)
                output.extend(visit(definitions[key]['nodes'],local,matrix,bindings(node.get('materials',{}),materials),trail+(key,)))
            else:
                mat=node.get('material',next(iter(palette)))
                if not isinstance(mat,str):raise ValueError('Material must be a name')
                mat=materials.get(mat,mat)
                if mat not in palette:raise ValueError('Unknown material: '+mat)
                output.append(primitive(node,env,matrix,mat))
        return output

    rows={r['id']:r for r in program['assemblies']};expanded={};visiting=set()
    def assembly(key):
        if key in expanded:return expanded[key]
        if key in visiting:raise ValueError('Cyclic attachment')
        if key not in rows:raise ValueError('Unknown attachment assembly')
        visiting.add(key);row=rows[key];env=params(row['use'],row.get('args',{}),{'seed':program.get('seed',0)})
        matrix=transform(row,env)
        if 'attach' in row:
            target,anchor=row['attach']['to'].split('.');parent=assembly(target)
            if anchor not in parent['anchors']:raise ValueError('Unknown attachment anchor')
            matrix=multiply(multiply(parent['matrix'],pose(parent['anchors'][anchor])),matrix)
        parts=visit(definitions[row['use']]['nodes'],env,identity(),bindings(row.get('materials',{}),{}),(row['use'],))
        if not parts:raise ValueError('Assembly is empty: '+key)
        anchors={k:vector(v,env) for k,v in definitions[row['use']].get('anchors',{}).items()}
        for p in parts:
            world=multiply(matrix,p['matrix'])
            if any(not math.isfinite(v) or abs(v)>1e6 for line in world for v in line):raise ValueError('Invalid accumulated transform')
        result={'id':key,'use':row['use'],'matrix':matrix,'anchors':anchors,'parts':parts,'shape_hash':digest(parts)}
        expanded[key]=result;visiting.remove(key);return result
    for key in rows:assembly(key)
    numeric_palette={k:{p:vector(v,{}) if p=='color' else evaluate(v,{}) for p,v in m.items()} for k,m in palette.items()}
    camera={k:vector(v,{}) if k in ('at','target') else evaluate(v,{}) for k,v in program.get('camera',{}).items()}
    if camera.get('at',[35,-46,40])==camera.get('target',[0,1,1.4]):raise ValueError('Camera must have a viewing direction')
    return {'title':program['title'],'palette':numeric_palette,'assemblies':list(expanded.values()),
            'camera':camera,'lighting':{k:evaluate(v,{}) for k,v in program.get('lighting',{}).items()},
            'program_sha256':digest(program),'budget':budget}
