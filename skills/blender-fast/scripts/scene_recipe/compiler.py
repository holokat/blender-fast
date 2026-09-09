"""Owned assemblies, deterministic geometry, and incremental recipe updates."""
import hashlib
import json
import math
import time
import uuid
import bpy
from mathutils import Vector
from .schema import validate
from .factories import architecture, workshops, relics, celestial
from .factories.geometry import Geometry, R
from .staging import stage, update_stage, assign_changed

BUILDERS = {name: getattr(module, name) for module, names in (
    (architecture, 'chamber portal staircase forge throne ritual waterwell collapsed_passage'),
    (workshops, 'alchemy library armory supplies hoist organ'),
    (relics, 'cage sarcophagus treasure map_table ossuary chandelier'),
    (celestial, 'orrery reactor telescope')) for name in names.split()}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class RecipeGeometry(Geometry):
    def group(self, name, at=(0, 0, 0)):
        # Factory offsets belong to the old example. Recipe transforms are explicit.
        super().group(self.entry['id'], (0, 0, 0))
        self.collection['recipe_owner'] = self.scene['recipe_owner']
        self.collection['assembly_id'] = self.entry['id']


def roots(scene):
    return {o['assembly_id']: o for o in scene.collection.objects if o.get('recipe_root')}


def transform(root, entry):
    changed = assign_changed(root, 'location', entry['at'])
    changed |= assign_changed(root, 'rotation_euler', (0, 0, math.radians(entry.get('yaw', 0))))
    changed |= assign_changed(root, 'scale', entry.get('scale', (1, 1, 1)))
    return changed


def shape_key(entry, recipe):
    seed = entry.get('seed', int(digest([recipe['seed'], entry['id']])[:8], 16))
    return {'type': entry['type'], 'seed': seed}


def remove_assembly(scene, root):
    owner, identifier = scene['recipe_owner'], root['assembly_id']
    collections = [c for c in scene.collection.children if c.get('recipe_owner') == owner and c.get('assembly_id') == identifier]
    for collection in collections:
        for obj in list(collection.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
        bpy.data.collections.remove(collection)
    bpy.data.objects.remove(root, do_unlink=True)


def build_assembly(g, entry, recipe):
    shape = shape_key(entry, recipe)
    R.seed(shape['seed'])
    g.entry = entry
    BUILDERS[entry['type']](g)
    collection = g.groups[-1]
    root = bpy.data.objects.new(entry['id'], None)
    g.scene.collection.objects.link(root)
    root['recipe_root'] = True
    root['assembly_id'] = entry['id']
    root['assembly_type'] = entry['type']
    root['shape_key'] = json.dumps(shape, sort_keys=True)
    for obj in collection.objects:
        obj.parent = root
        obj['assembly_id'] = entry['id']
    transform(root, entry)
    return root


def apply_materials(materials, overrides):
    for name, material in materials.items():
        node = material.node_tree.nodes.get('Principled BSDF')
        if 'recipe_defaults' not in material:
            material['recipe_defaults'] = json.dumps({
                'color': list(node.inputs['Base Color'].default_value[:3]),
                'roughness': node.inputs['Roughness'].default_value,
                'metallic': node.inputs['Metallic'].default_value,
                'emission': node.inputs['Emission Strength'].default_value})
        props = json.loads(material['recipe_defaults']) | overrides.get(name, {})
        rgba = (*props['color'], 1)
        assign_changed(material, 'diffuse_color', rgba)
        assign_changed(node.inputs['Base Color'], 'default_value', rgba)
        assign_changed(node.inputs['Roughness'], 'default_value', props['roughness'])
        assign_changed(node.inputs['Metallic'], 'default_value', props['metallic'])
        assign_changed(node.inputs['Emission Strength'], 'default_value', props['emission'])
        if props['emission']:
            assign_changed(node.inputs['Emission Color'], 'default_value', rgba)


def apply(recipe, scene=None):
    """Validate first. Create an isolated scene, or update only owned assemblies."""
    started = time.perf_counter()
    validate(recipe)
    is_new = scene is None
    if is_new:
        scene = bpy.data.scenes.new(recipe['title'])
        scene['recipe_owner'] = str(uuid.uuid4())
        if bpy.context.window:
            bpy.context.window.scene = scene
        g = RecipeGeometry(scene)
        for key, material in g.materials.items():
            material['recipe_material'] = key
            material['recipe_owner'] = scene['recipe_owner']
    else:
        if not scene.get('recipe_owner'):
            raise ValueError('Refusing to modify a scene not owned by the recipe compiler')
        g = RecipeGeometry(scene, {m['recipe_material']: m for m in bpy.data.materials
                                   if m.get('recipe_owner') == scene['recipe_owner']})
    existing = roots(scene)
    requested = {entry['id']: entry for entry in recipe['assemblies']}
    rebuilt, moved, removed = [], [], []
    for identifier, root in existing.items():
        if identifier not in requested:
            remove_assembly(scene, root)
            removed.append(identifier)
    for entry in recipe['assemblies']:
        root = existing.get(entry['id'])
        shape = json.dumps(shape_key(entry, recipe), sort_keys=True)
        if root is None or root['shape_key'] != shape:
            if root:
                remove_assembly(scene, root)
            build_assembly(g, entry, recipe)
            rebuilt.append(entry['id'])
        else:
            if transform(root, entry):
                moved.append(entry['id'])
    apply_materials(g.materials, recipe.get('materials', {}))
    if is_new:
        stage(scene, g, recipe)
    else:
        update_stage(scene, recipe)
    scene['recipe_json'] = json.dumps(recipe, sort_keys=True)
    scene['recipe_sha256'] = digest(recipe)
    # The viewport/dependency graph updates once at the transaction boundary.
    bpy.context.view_layer.update()
    return scene, {'apply_seconds': time.perf_counter() - started,
                   'rebuilt': rebuilt, 'transformed': moved, 'removed': removed,
                   'recipe_sha256': scene['recipe_sha256']}


def inventory(scene):
    meshes = [o for o in scene.objects if o.type == 'MESH']
    assemblies = roots(scene)
    return {'assemblies': len(assemblies),
            'distinct_types': len({o['assembly_type'] for o in assemblies.values()}),
            'mesh_objects': len(meshes), 'faces': sum(len(o.data.polygons) for o in meshes),
            'shared_meshes': len({o.data for o in meshes}),
            'lights': sum(o.type == 'LIGHT' for o in scene.objects),
            'recipe_sha256': scene['recipe_sha256']}
