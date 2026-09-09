"""Run in isolated Blender to check real ownership, patches, and deterministic geometry."""
import copy
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/blender-fast/scripts'))
from scene_recipe.compiler import apply, inventory, roots

unrelated = bpy.context.scene
untouched = sorted(unrelated.objects.keys())
recipe = {'version': 1, 'title': 'Compiler checks', 'seed': 42,
          'assemblies': [{'id': 'desk', 'type': 'map_table', 'at': [2, 3, 0]},
                         {'id': 'scope', 'type': 'telescope', 'at': [-2, 0, 0]}]}
scene, first = apply(recipe)
assert inventory(scene)['assemblies'] == 2
desk = roots(scene)['desk']
children = list(desk.children)
identities = [(o.as_pointer(), o.data.as_pointer()) for o in children]
positions = [o.matrix_world.translation.copy() for o in children]
revision = copy.deepcopy(recipe)
revision['assemblies'][0]['at'][0] += 4
_, result = apply(revision, scene)
assert result['rebuilt'] == [] and result['transformed'] == ['desk'], result
assert identities == [(o.as_pointer(), o.data.as_pointer()) for o in children]
assert all((o.matrix_world.translation - p - Vector((4, 0, 0))).length < .0001 for o, p in zip(children, positions))
invalid = copy.deepcopy(revision)
invalid['assemblies'][0]['type'] = 'unknown'
fingerprint = scene['recipe_sha256']
try:
    apply(invalid, scene)
    raise AssertionError('invalid recipe mutated scene')
except ValueError:
    assert scene['recipe_sha256'] == fingerprint
revision['materials'] = {'wood': {'color': [.8, .1, .05]}}
apply(revision, scene)
wood = next(m for m in bpy.data.materials if m.get('recipe_owner') == scene['recipe_owner'] and m.get('recipe_material') == 'wood')
assert abs(wood.diffuse_color[0] - .8) < 1e-6
revision.pop('materials')
apply(revision, scene)
assert abs(wood.diffuse_color[0] - .2) < 1e-6
revision['assemblies'][1]['type'] = 'reactor'
_, result = apply(revision, scene)
assert result['rebuilt'] == ['scope']
revision['assemblies'] = revision['assemblies'][:1]
_, result = apply(revision, scene)
assert result['removed'] == ['scope'] and inventory(scene)['assemblies'] == 1
assert sorted(unrelated.objects.keys()) == untouched
second, _ = apply(recipe)
third, _ = apply(recipe)
def geometry_positions(s):
    return sorted((o.get('assembly_id'), tuple(round(v, 5) for v in o.location), len(o.data.polygons))
                  for o in s.objects if o.type == 'MESH')
assert geometry_positions(second) == geometry_positions(third)
print('BLENDER_RECIPE_CHECKS ' + json.dumps({'passed': True, 'checks': ['ownership', 'identity-preserving transform',
      'invalid input atomicity', 'material reset', 'type replacement', 'removal', 'deterministic seed']}))
