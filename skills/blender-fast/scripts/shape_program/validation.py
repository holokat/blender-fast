"""Structural validation shared by the expander and teaching tools."""
import re
from .expressions import evaluate,vector

OPS={
 'box':('size',),'sphere':('size',),'cylinder':('radius','height','segments'),
 'cone':('radius','height','segments'),'ring':('radius','tube','segments'),
 'beam':('a','b','radius','segments'),'sweep':('path','radii','segments','caps'),
 'lathe':('profile','segments'),'surface':('vertices','faces'),
 'text':('text','size','depth'),
 'group':('children',),'repeat':('count','index','step','turn','children'),
 'call':('use','args','materials'),
}
COMMON=('op','name','at','rotation','scale','material')


def fields(obj,allowed,where):
    if not isinstance(obj,dict) or set(obj)-set(allowed):raise ValueError(f'{where}: unexpected fields or non-object')


def name(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}',value):raise ValueError('Expected a lowercase identifier')
    return value


def identifier_map(obj):
    if not isinstance(obj,dict):raise ValueError('Expected a named mapping')
    for key in obj:name(key)


def validate_structure(program):
    fields(program,('version','title','seed','palette','definitions','assemblies','camera','lighting'),'program')
    if type(program.get('version')) is not int or program['version']!=1:raise ValueError('version must be 1')
    if not isinstance(program.get('title'),str) or not 1<=len(program['title'])<=120:raise ValueError('Invalid title')
    if type(program.get('seed',0)) is not int:raise ValueError('seed must be an integer')
    palette=program.get('palette');identifier_map(palette)
    if not 1<=len(palette)<=64:raise ValueError('Expected 1 through 64 materials')
    for key,mat in palette.items():
        fields(mat,('color','roughness','metallic','emission','transmission'),key)
        if any(not 0<=v<=1 for v in vector(mat.get('color'),{})):raise ValueError('Material color must be linear RGB from 0 through 1')
        for prop in ('roughness','metallic','transmission','emission'):
            if prop in mat:
                v=evaluate(mat[prop],{})
                if not 0<=v<=(100 if prop=='emission' else 1):raise ValueError('Invalid material property')
    definitions=program.get('definitions');identifier_map(definitions)
    if len(definitions)>64:raise ValueError('Too many definitions')
    total=[0]
    def nodes(rows,depth=0):
        if not isinstance(rows,list) or depth>12:raise ValueError('Invalid node nesting')
        for row in rows:
            total[0]+=1
            if total[0]>4000:raise ValueError('Too many source nodes')
            if not isinstance(row,dict) or not isinstance(row.get('op'),str) or row.get('op') not in OPS:raise ValueError('Unknown shape operation')
            fields(row,COMMON+OPS[row['op']],'node')
            if row['op'] in ('group','repeat','call') and 'material' in row:raise ValueError('Set material on a primitive or use call materials bindings')
            if row.get('index')=='pi':raise ValueError('pi is a reserved numeric constant')
            if 'name' in row and (not isinstance(row['name'],str) or len(row['name'])>100):raise ValueError('Invalid node name')
            if row['op'] in ('repeat','group'):nodes(row.get('children'),depth+1)
            if row['op']=='call':
                if not isinstance(row.get('use'),str) or row.get('use') not in definitions:raise ValueError('Unknown definition')
                identifier_map(row.get('args',{}));identifier_map(row.get('materials',{}))
    for key,definition in definitions.items():
        fields(definition,('params','anchors','nodes'),key)
        identifier_map(definition.get('params',{}));identifier_map(definition.get('anchors',{}))
        if 'pi' in definition.get('params',{}):raise ValueError('pi is a reserved numeric constant')
        nodes(definition.get('nodes'))
    rows=program.get('assemblies')
    if not isinstance(rows,list) or not 1<=len(rows)<=100:raise ValueError('Expected 1 through 100 assemblies')
    seen=set()
    for row in rows:
        fields(row,('id','use','args','at','rotation','scale','materials','attach'),'assembly')
        key=name(row.get('id'))
        if key in seen:raise ValueError('Duplicate assembly id')
        seen.add(key)
        if not isinstance(row.get('use'),str) or row.get('use') not in definitions:raise ValueError('Unknown assembly definition')
        identifier_map(row.get('args',{}));identifier_map(row.get('materials',{}))
        if 'attach' in row:
            fields(row['attach'],('to',),'attachment')
            target=row['attach'].get('to')
            if not isinstance(target,str) or len(target.split('.'))!=2:raise ValueError('Attachment uses assembly.anchor')
    for category,allowed in [('camera',('at','target','ortho_scale')),('lighting',('key','fill','rim','world','exposure'))]:
        fields(program.get(category,{}),allowed,category)
    camera=program.get('camera',{})
    for key in ('at','target'):
        if key in camera:vector(camera[key],{})
    if not 1<=evaluate(camera.get('ortho_scale',47),{})<=1000:raise ValueError('Invalid camera scale')
    if camera.get('at') is not None and camera.get('at')==camera.get('target'):raise ValueError('Camera must have a viewing direction')
    for key,value in program.get('lighting',{}).items():
        if not (-10 if key=='exposure' else 0)<=evaluate(value,{})<=10:raise ValueError('Invalid lighting value')
