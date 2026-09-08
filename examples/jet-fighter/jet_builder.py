"""Blender implementation shared by both jet benchmark lanes."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'mmo-house'))
from house_builder import material


class JetBuilder:
    def __init__(self,spec_path,name):
        self.spec=json.loads(Path(spec_path).read_text());self.name=name
        if bpy.data.scenes.get(name):raise RuntimeError('Scene name is already owned')
        self.scene=bpy.data.scenes.new(name)
        self.collection=bpy.data.collections.new(name+' geometry');self.scene.collection.children.link(self.collection)
        self.materials={k:material(name+' '+k,v) for k,v in self.spec['palette'].items()}
        self.meshes={};self.objects=[];self.created=set();self.extras=[]
        for shape,mat in sorted({(i['mesh'],i['mat']) for i in self.spec['items']}):
            source=self.spec['meshes'][shape]
            mesh=bpy.data.meshes.new(name+' '+shape+' '+mat)
            mesh.from_pydata(source['vertices'],[],source['faces'])
            bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
            mesh.materials.append(self.materials[mat]);mesh.update()
            if any(x in shape for x in ('fuselage','nose','canopy','engine','inlet','exhaust','fastener')):
                for poly in mesh.polygons:poly.use_smooth=len(poly.vertices)==4
            self.meshes[shape,mat]=mesh

    def build(self,start,end):
        if start<0 or end>len(self.spec['items']) or start>end:raise ValueError('Invalid range')
        for i in range(start,end):
            if i in self.created:raise RuntimeError('Duplicate object')
            entry=self.spec['items'][i]
            obj=bpy.data.objects.new(f'{self.name} {i:03d} {entry["name"]}',self.meshes[entry['mesh'],entry['mat']])
            self.collection.objects.link(obj);obj.location=entry['pos'];obj.scale=entry['scale'];obj.rotation_euler=entry['rot']
            obj['benchmark_id']=i;self.objects.append(obj);self.created.add(i)
        return {'created':len(self.created)}

    def fingerprint(self):
        if len(self.created)!=len(self.spec['items']):raise RuntimeError('Incomplete geometry')
        self.scene.view_layers[0].update();digest=hashlib.sha256();vertices=faces=0
        for obj in self.objects:
            entry={'id':obj['benchmark_id'],'matrix':[[round(v,6) for v in row] for row in obj.matrix_world],
                'vertices':[[round(c,6) for c in v.co] for v in obj.data.vertices],
                'faces':[list(p.vertices) for p in obj.data.polygons],
                'material':obj.data.materials[0].name.removeprefix(self.name+' ')}
            digest.update(json.dumps(entry,sort_keys=True,separators=(',',':')).encode())
            vertices+=len(obj.data.vertices);faces+=len(obj.data.polygons)
        digest.update(json.dumps(self.spec['palette'],sort_keys=True).encode())
        return {'sha256':digest.hexdigest(),'objects':len(self.objects),'vertices':vertices,'faces':faces}

    def preview(self,path):
        self.scene.view_layers[0].update();out=[]
        for obj in self.objects:
            obj.data.calc_loop_triangles()
            out.append({'id':obj['benchmark_id'],'vertices':[[round(v,5) for v in obj.matrix_world@p.co] for p in obj.data.vertices],
                'triangles':[list(p.vertices) for p in obj.data.loop_triangles],
                'color':self.spec['palette'][self.spec['items'][obj['benchmark_id']]['mat']][0]})
        Path(path).write_text(json.dumps({'objects':out,'fingerprint':self.fingerprint()},separators=(',',':')))

    def stage(self):
        scene=self.scene
        world=bpy.data.worlds.new(self.name+' world');world.use_nodes=True;scene.world=world
        world.node_tree.nodes['Background'].inputs[0].default_value=(.52,.62,.72,1)
        world.node_tree.nodes['Background'].inputs[1].default_value=.42
        floor=bpy.data.meshes.new(self.name+' floor');floor.from_pydata([(-200,-200,-1.04),(200,-200,-1.04),(200,200,-1.04),(-200,200,-1.04)],[],[(0,1,2,3)])
        floor.materials.append(self.materials['floor']);obj=bpy.data.objects.new(floor.name,floor);self.collection.objects.link(obj);self.extras.append(floor)
        for label,pos,power,size,color in [('Key',(-6,-5,12),2600,8,(1,.88,.75)),('Fill',(8,-1,7),1800,7,(.65,.84,1)),('Rim',(1,9,11),3000,6,(1,1,1))]:
            data=bpy.data.lights.new(self.name+' '+label,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
            obj=bpy.data.objects.new(data.name,data);self.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(-Vector(pos)).to_track_quat('-Z','Y').to_euler();self.extras.append(data)
        camera=bpy.data.cameras.new(self.name+' camera');obj=bpy.data.objects.new(camera.name,camera);self.collection.objects.link(obj)
        obj.location=(12,-17,12);obj.rotation_euler=(Vector((0,-.5,.15))-obj.location).to_track_quat('-Z','Y').to_euler()
        camera.type='ORTHO';camera.ortho_scale=18.8;scene.camera=obj;self.extras.append(camera)
        scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.seed=7421;scene.cycles.use_animated_seed=False
        scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.01;scene.cycles.adaptive_min_samples=0
        scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
        scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
        scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
        for prop in scene.render.bl_rna.properties:
            if prop.identifier.startswith('use_stamp') and prop.type=='BOOLEAN':setattr(scene.render,prop.identifier,False)
        return {'scene':scene.name,'resolution':[1400,1000],'samples':64}

    def save(self,path,optimized=False):
        self.scene.cycles.device='GPU'
        self.scene.cycles.denoising_use_gpu=optimized;self.scene.render.use_persistent_data=optimized
        bpy.data.libraries.write(str(Path(path).resolve()),{self.scene},fake_user=True,compress=True)
        return {'saved':True}

    def cleanup(self):
        world=self.scene.world
        for obj in list(self.collection.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.scenes.remove(self.scene);bpy.data.collections.remove(self.collection)
        for data in list(self.meshes.values())+self.extras:
            if data.users==0:
                if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
                elif isinstance(data,bpy.types.Camera):bpy.data.cameras.remove(data)
                elif isinstance(data,bpy.types.Light):bpy.data.lights.remove(data)
        for mat in self.materials.values():
            if mat.users==0:bpy.data.materials.remove(mat)
        if world and world.users==0:bpy.data.worlds.remove(world)
