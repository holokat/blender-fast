"""Run with Blender --background --python-exit-code 1 --python this_file."""
import copy
import json
import sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/blender-fast/scripts'))
from shape_program.compiler import apply,roots,inventory
from shape_program.expand import expand
from shape_program.teaching import load_library,compose

sentinel=bpy.data.objects.new('Unrelated user object',None)
bpy.context.scene.collection.objects.link(sentinel)
lessons=load_library()
layout={'title':'Compiler verification','assemblies':[{'id':r['id'],'use':r['id'],'at':[i*16,0,0]} for i,r in enumerate(lessons)]}
program=compose(layout,lessons)
scene,first=apply(program)
assert len(roots(scene))==8
assert sentinel.name in bpy.data.objects
for obj in scene.objects:
    if obj.type=='MESH':assert not obj.data.validate(),obj.name
pointers={o.name:o.as_pointer() for o in scene.objects}
mesh_pointers={m.as_pointer() for m in bpy.data.meshes}
scene,noop=apply(program,scene)
assert not noop['rebuilt'] and not noop['transformed']
assert pointers=={o.name:o.as_pointer() for o in scene.objects}
assert mesh_pointers=={m.as_pointer() for m in bpy.data.meshes}

changed=copy.deepcopy(program)
changed['assemblies'][0].update(at=[1,2,3],rotation=[13,27,45],scale=[1.7,.8,1.2])
scene,moved=apply(changed,scene)
assert not moved['rebuilt'] and moved['transformed']==[changed['assemblies'][0]['id']]
assert pointers=={o.name:o.as_pointer() for o in scene.objects}

# An attached root inherits the parent's full affine matrix, including shear.
changed['assemblies'][0]={'id':'planter','use':'revolved_bowl','rotation':[0,0,28],'scale':[2,1,1]}
changed['assemblies'][1]={'id':'tree','use':'branch_crown','attach':{'to':'planter.soil'},'rotation':[15,0,40]}
scene,attached=apply(changed,scene)
graph=expand(changed);row=next(r for r in graph['assemblies'] if r['id']=='tree')
actual=roots(scene)['tree'].matrix_world
assert max(abs(actual[i][j]-row['matrix'][i][j]) for i in range(4) for j in range(4))<1e-5
# Mesh primitives have an intrinsic scale; check a surface whose intrinsic matrix is identity.
canopy=next(r for r in graph['assemblies'] if r['use']=='radial_ribs')
idx=next(i for i,p in enumerate(canopy['parts']) if p['op']=='surface')
obj=next(o for o in scene.objects if o.get('assembly_id')==canopy['id'] and o.get('part_index')==idx)
expected=Matrix(canopy['matrix'])@Matrix(canopy['parts'][idx]['matrix'])
assert max(abs(obj.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-5

before={o.as_pointer() for o in bpy.data.objects}
bad=copy.deepcopy(changed);bad['assemblies'].append({'id':'bad','use':'unknown'})
try:apply(bad,scene)
except ValueError:pass
else:raise AssertionError('Invalid program was accepted')
assert before=={o.as_pointer() for o in bpy.data.objects}

survivor=roots(scene)['tree'].as_pointer()
changed['assemblies'][0]['args']={'radius':1.7}
scene,rebuild=apply(changed,scene)
assert rebuild['rebuilt']==['planter']
assert roots(scene)['tree'].as_pointer()==survivor
assert sentinel.name in bpy.data.objects

# Material-only edits preserve geometry, including restoring omitted defaults.
mesh_pointers={o.data.as_pointer() for o in scene.objects if o.type=='MESH'}
changed['palette']['stone']['metallic']=.9
scene,mat_change=apply(changed,scene)
assert not mat_change['rebuilt']
assert mesh_pointers=={o.data.as_pointer() for o in scene.objects if o.type=='MESH'}
del changed['palette']['stone']['metallic']
scene,_=apply(changed,scene)
stone=next(m for m in bpy.data.materials if m.get('shape_owner')==scene['shape_owner'] and m.get('shape_material')=='stone')
assert stone.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value==0
result={'status':'passed','lessons_built':len(lessons),'initial':first,'no_op':noop,'transform':moved,'rebuild':rebuild,'inventory':inventory(scene),
 'checks':['isolated user scene','all lesson meshes valid','no-op object and mesh identity','transform-only identity','attachment affine preservation','invalid graph leaves scene untouched','only changed shape rebuilt','material defaults restored']}
if '--' in sys.argv:
    path=Path(sys.argv[sys.argv.index('--')+1]);path.write_text(json.dumps(result,indent=2)+'\n')
print('SHAPE_CHECKS '+json.dumps(result),flush=True)
