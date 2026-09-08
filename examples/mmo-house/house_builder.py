"""Blender-side house builder. Both benchmark paths call this same implementation."""
import bpy
import bmesh
import hashlib
import json
import math
from mathutils import Vector
from pathlib import Path


def linear(value):
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4


def rgba(color):
    return tuple(linear(int(color[i:i+2],16)/255) for i in (1,3,5))+(1,)


def material(name, values):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=rgba(values[0])
    bsdf.inputs['Roughness'].default_value=values[1]
    bsdf.inputs['Metallic'].default_value=values[2]
    if len(values)>3:
        bsdf.inputs['Emission Color'].default_value=rgba(values[0])
        bsdf.inputs['Emission Strength'].default_value=values[3]
    mat.diffuse_color=rgba(values[0])
    return mat


def primitive(kind,name):
    mesh=bpy.data.meshes.new(name)
    bm=bmesh.new()
    if kind in ('box','beam'):
        bmesh.ops.create_cube(bm,size=1)
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.045,segments=2,affect='EDGES')
        bm.to_mesh(mesh)
    elif kind=='ico':
        bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
        bm.to_mesh(mesh)
    elif kind in ('cylinder','cone'):
        bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=24,radius1=1,radius2=0 if kind=='cone' else 1,depth=1)
        bm.to_mesh(mesh)
    elif kind=='torus':
        n,m=32,8
        verts=[];faces=[]
        for i in range(n):
            a=i*math.tau/n
            for j in range(m):
                b=j*math.tau/m;r=1+.065*math.cos(b)
                verts.append((r*math.cos(a),r*math.sin(a),.065*math.sin(b)))
        for i in range(n):
            for j in range(m):faces.append((i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m))
        mesh.from_pydata(verts,[],faces)
    elif kind=='gable':
        verts=[(-.5,y,0) for y in (-.5,.5)]+[(.5,y,0) for y in (-.5,.5)]+[(0,y,1) for y in (-.5,.5)]
        mesh.from_pydata(verts,[],[(0,2,4),(1,5,3),(0,1,3,2),(2,3,5,4),(4,5,1,0)])
    elif kind=='arch':
        profile=[(-.5,0),(.5,0)]+[(.5*math.cos(i*math.pi/16),.5+.5*math.sin(i*math.pi/16)) for i in range(17)]
        n=len(profile)
        verts=[(x,y,z) for y in (-.5,.5) for x,z in profile]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh.from_pydata(verts,[],faces)
    else:raise ValueError(kind)
    bm.free();mesh.update()
    return mesh


class HouseBuilder:
    def __init__(self,spec_path,name='MMO house'):
        self.spec=json.loads(Path(spec_path).read_text())
        self.name=name
        if bpy.data.scenes.get(name):raise RuntimeError('Benchmark scene already exists')
        self.scene=bpy.data.scenes.new(name)
        self.collection=bpy.data.collections.new(name+' geometry')
        self.scene.collection.children.link(self.collection)
        self.materials={k:material(name+' '+k,v) for k,v in self.spec['palette'].items()}
        self.templates={};self.meshes=[];self.objects=[]
        for kind in sorted({i['kind'] for i in self.spec['items']}):
            template=primitive(kind,name+' template '+kind);self.templates[kind]=template;self.meshes.append(template)
        self.variants={}
        for kind,mat in sorted({(i['kind'],i['mat']) for i in self.spec['items']} | {('box','ground')}):
            mesh=self.templates[kind].copy();mesh.name=name+' '+kind+' '+mat
            mesh.materials.append(self.materials[mat]);self.meshes.append(mesh)
            self.variants[kind,mat]=mesh
        self.created=set()

    def build(self,start,end):
        if start < 0 or end > len(self.spec['items']):raise ValueError('Invalid range')
        for i in range(start,end):
            if i in self.created:raise RuntimeError(f'Duplicate object {i}')
            spec=self.spec['items'][i]
            obj=bpy.data.objects.new(f'{self.name} {i:04d} {spec["kind"]}',self.variants[spec['kind'],spec['mat']])
            self.collection.objects.link(obj)
            obj['benchmark_id']=i
            if spec['kind']=='beam':
                a,b=Vector(spec['a']),Vector(spec['b']);direction=b-a
                obj.location=(a+b)/2
                obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
                obj.scale=(spec['width'],spec['depth'],direction.length)
            else:
                obj.location=spec['pos'];obj.scale=spec['scale'];obj.rotation_euler=spec['rot']
            self.objects.append(obj);self.created.add(i)
        return {'created':len(self.created)}

    def fingerprint(self):
        if len(self.created)!=len(self.spec['items']):raise RuntimeError('Incomplete build')
        self.scene.view_layers[0].update()
        hasher=hashlib.sha256()
        vertices=faces=0
        lower=[float('inf')]*3;upper=[float('-inf')]*3
        for obj in self.objects:
            mesh=obj.data
            values={'id':obj['benchmark_id'],'matrix':[[round(v,6) for v in row] for row in obj.matrix_world],
              'vertices':[[round(c,6) for c in v.co] for v in mesh.vertices],
              'faces':[list(p.vertices) for p in mesh.polygons],
              'material':obj.data.materials[0].name.removeprefix(self.name+' ')}
            hasher.update(json.dumps(values,sort_keys=True,separators=(',',':')).encode())
            vertices+=len(mesh.vertices);faces+=len(mesh.polygons)
            for co in obj.bound_box:
                world=obj.matrix_world@Vector(co)
                for i in range(3):lower[i]=min(lower[i],world[i]);upper[i]=max(upper[i],world[i])
        for key,mat in sorted(self.materials.items()):
            bsdf=mat.node_tree.nodes.get('Principled BSDF')
            values={k:list(bsdf.inputs[k].default_value) if k in ('Base Color','Emission Color') else bsdf.inputs[k].default_value for k in ('Base Color','Metallic','Roughness','Emission Color','Emission Strength')}
            hasher.update(json.dumps([key,values],sort_keys=True).encode())
        return {'sha256':hasher.hexdigest(),'objects':len(self.objects),'vertices':vertices,'faces':faces,'bounds_min':lower,'bounds_max':upper}

    def stage(self):
        scene=self.scene
        floor=bpy.data.objects.new(self.name+' backdrop',self.variants['box','ground'])
        self.collection.objects.link(floor);floor.location=(0,0,-.51);floor.scale=(200,200,.1)
        self.objects.append(floor)
        def area(name,pos,energy,size,color,target=(0,0,2)):
            data=bpy.data.lights.new(self.name+' '+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
            obj=bpy.data.objects.new(data.name,data);self.collection.objects.link(obj);self.objects.append(obj)
            obj.location=pos;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
        area('key',(-5,-7,12),1800,7,(1,.83,.64))
        area('fill',(8,-1,8),1350,6,(.69,.82,1))
        area('rim',(-3,7,10),2200,5,(1,.80,.55))
        world=bpy.data.worlds.new(self.name+' world');world.use_nodes=True
        world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.49,.60,1)
        world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
        cam=bpy.data.cameras.new(self.name+' camera');obj=bpy.data.objects.new(cam.name,cam);self.collection.objects.link(obj);self.objects.append(obj)
        obj.location=(12,-17,12);target=Vector((.2,0,2.8));obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
        cam.type='ORTHO';cam.ortho_scale=17.8;cam.lens=50;scene.camera=obj
        scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.seed=7421
        scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
        scene.view_settings.view_transform='AgX'
        scene.render.film_transparent=False
        scene.render.use_stamp_filename=False
        if bpy.context.window:bpy.context.window.scene=scene
        return {'scene':scene.name,'camera':obj.name}

    def cleanup(self):
        for obj in list(self.collection.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.scenes.remove(self.scene)
        bpy.data.collections.remove(self.collection)
        for mesh in self.meshes:
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        for mat in self.materials.values():
            if mat.users==0:bpy.data.materials.remove(mat)
