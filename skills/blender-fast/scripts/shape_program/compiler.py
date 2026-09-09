"""Compile validated programs into isolated, editable Blender assemblies."""
import json
import time
import uuid
import bpy
from mathutils import Matrix
from scene_recipe.factories.geometry import Geometry
from scene_recipe.staging import stage, update_stage, assign_changed
from .expand import expand
from .mesh_ops import create


def roots(scene):
    return {obj['assembly_id']:obj for obj in scene.objects if obj.get('shape_root') and obj.get('shape_owner')==scene.get('shape_owner')}


def remove_collection(collection):
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(collection)


def materials(scene, palette):
    owner = scene['shape_owner']
    existing = {m['shape_material']:m for m in bpy.data.materials if m.get('shape_owner')==owner and 'shape_material' in m}
    for key, props in palette.items():
        if key not in existing:
            mat = bpy.data.materials.new(key)
            mat.use_nodes = True
            mat['shape_owner'],mat['shape_material'] = owner,key
            existing[key] = mat
        mat = existing[key]
        shader = mat.node_tree.nodes.get('Principled BSDF')
        rgba = (*props['color'],1)
        assign_changed(mat,'diffuse_color',rgba)
        for socket,value in [('Base Color',rgba),('Roughness',props.get('roughness',.55)),
            ('Metallic',props.get('metallic',0)),('Transmission Weight',props.get('transmission',0)),
            ('Emission Color',rgba),('Emission Strength',props.get('emission',0))]:
            assign_changed(shader.inputs[socket],'default_value',value)
    return {k:existing[k] for k in palette}


def set_matrix(obj, value):
    matrix = Matrix(value)
    if any(abs(obj.matrix_parent_inverse[i][j]-matrix[i][j])>1e-6 for i in range(4) for j in range(4)):
        obj.matrix_parent_inverse = matrix
        return True
    return False


def apply(program, scene=None):
    started = time.perf_counter()
    graph = expand(program)  # All data validation and expansion precedes Blender mutation.
    validation_seconds = time.perf_counter()-started
    is_new = scene is None
    if is_new:
        scene = bpy.data.scenes.new(graph['title'])
        scene['shape_owner'] = uuid.uuid4().hex
        origin = bpy.data.objects.new('Program origin',None)
        origin['shape_origin'] = True
        scene.collection.objects.link(origin)
    elif not scene.get('shape_owner'):
        raise ValueError('Refusing to modify a scene not owned by the shape compiler')
    origin = next(o for o in scene.collection.objects if o.get('shape_origin'))
    owner = scene['shape_owner']
    g = Geometry(scene,materials(scene,graph['palette']))
    existing = roots(scene)
    collections = {c['assembly_id']:c for c in scene.collection.children if c.get('shape_owner')==owner}
    before_meshes, before_curves = set(bpy.data.meshes),set(bpy.data.curves)
    prepared, moved = {},[]
    try:
        for row in graph['assemblies']:
            old = existing.get(row['id'])
            if old is not None and old.get('shape_hash')==row['shape_hash']:
                continue
            collection = bpy.data.collections.new(row['id'])
            collection['shape_owner'], collection['assembly_id'] = owner,row['id']
            scene.collection.children.link(collection)
            g.collection = collection
            root = bpy.data.objects.new(row['id'],None)
            collection.objects.link(root)
            root.parent = origin
            root['shape_owner'],root['shape_root'],root['assembly_id'] = owner,True,row['id']
            root['shape_hash'],root['definition'] = row['shape_hash'],row['use']
            root['anchors_json'] = json.dumps(row['anchors'])
            set_matrix(root,row['matrix'])
            prepared[row['id']] = collection
            for index,part in enumerate(row['parts']):
                obj = create(g,part,root)
                obj['shape_owner'],obj['assembly_id'],obj['part_index'] = owner,row['id'],index
    except Exception:
        for collection in prepared.values():remove_collection(collection)
        if is_new:
            bpy.data.objects.remove(origin,do_unlink=True)
            bpy.data.scenes.remove(scene)
        raise
    finally:
        for data in set(bpy.data.meshes)-before_meshes:data['shape_owner']=owner
        for data in set(bpy.data.curves)-before_curves:data['shape_owner']=owner
        for pool in (bpy.data.meshes,bpy.data.curves):
            for data in list(pool):
                if data.get('shape_owner')==owner and data.users==0:pool.remove(data)
    requested = {r['id'] for r in graph['assemblies']}
    removed = [key for key in existing if key not in requested]
    for key in list(prepared)+removed:
        if key in collections:remove_collection(collections[key])
    for row in graph['assemblies']:
        if row['id'] not in prepared:
            root = existing[row['id']]
            if set_matrix(root,row['matrix']):moved.append(row['id'])
            if root.get('anchors_json')!=json.dumps(row['anchors']):root['anchors_json']=json.dumps(row['anchors'])
    for pool in (bpy.data.meshes,bpy.data.curves,bpy.data.materials):
        for data in list(pool):
            if data.get('shape_owner')==owner and data.users==0:pool.remove(data)
    if is_new:stage(scene,g,graph)
    else:update_stage(scene,graph)
    scene['shape_json'],scene['shape_sha256'] = json.dumps(program,sort_keys=True),graph['program_sha256']
    if bpy.context.window:bpy.context.window.scene=scene
    scene.view_layers[0].update()
    return scene,{'validation_seconds':validation_seconds,'apply_seconds':time.perf_counter()-started,
        'rebuilt':list(prepared),'transformed':moved,'removed':removed,'program_sha256':graph['program_sha256'],'budget':graph['budget']}


def inventory(scene):
    meshes=[o for o in scene.objects if o.type=='MESH']
    return {'assemblies':len(roots(scene)),'objects':len(scene.objects),'mesh_objects':len(meshes),
        'mesh_datablocks':len({o.data for o in meshes}),'faces':sum(len(o.data.polygons) for o in meshes),
        'program_sha256':scene['shape_sha256']}
