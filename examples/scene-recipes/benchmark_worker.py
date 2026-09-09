"""One isolated persistent process per lane; compare identical semantic revisions."""
import argparse
import copy
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/blender-fast/scripts'))
from scene_recipe.compiler import apply, roots, apply_materials, digest
from scene_recipe.staging import configure, update_stage
from scene_recipe.schema import validate


def fingerprint(scene):
    """Representation-independent geometry/material digest, outside render timers."""
    h = hashlib.sha256()
    mesh_hashes = {}
    for obj in sorted((o for o in scene.objects if o.type in ('MESH', 'LIGHT')), key=lambda o: o.name):
        values = [obj.name, obj.type, [round(x, 4) for row in obj.matrix_world for x in row]]
        if obj.type == 'MESH':
            if obj.data.name not in mesh_hashes:
                mesh_hashes[obj.data.name] = digest({
                    'vertices': [list(v.co) for v in obj.data.vertices],
                    'faces': [list(p.vertices) for p in obj.data.polygons]})
            values.extend([len(obj.data.vertices), len(obj.data.polygons),
                           mesh_hashes[obj.data.name],
                           [list(m.diffuse_color) for m in obj.data.materials]])
        else:
            values.extend([obj.data.energy, list(obj.data.color)])
        h.update(json.dumps(values, sort_keys=True).encode())
    return h.hexdigest()


class FlatScene:
    """Baseline: direct batched transforms of individual objects, as in the old revision."""
    def __init__(self, scene):
        self.scene, self.groups = scene, {}
        for key, root in roots(scene).items():
            children = list(root.children)
            world = root.matrix_world.copy()
            self.groups[key] = children
            # Keep an identity parent so full affine transforms are representable.
            # Assigning a sheared matrix to matrix_world would decompose it and
            # alter geometry when the recipe uses nonuniform assembly scaling.
            root.matrix_world = Matrix.Identity(4)
            for obj in children:
                obj.matrix_parent_inverse = world
        self.materials = {m['recipe_material']: m for m in bpy.data.materials
                          if m.get('recipe_owner') == scene['recipe_owner']}
        self.previous = json.loads(scene['recipe_json'])
        bpy.context.view_layer.update()

    def apply(self, recipe):
        started = time.perf_counter()
        validate(recipe)
        old = {a['id']: a for a in self.previous['assemblies']}
        changed = []
        for entry in recipe['assemblies']:
            if entry == old[entry['id']]:
                continue
            matrix = Matrix.Translation(Vector(entry['at'])) @ Matrix.Rotation(math.radians(entry.get('yaw', 0)), 4, 'Z') @ Matrix.Diagonal((*entry.get('scale', [1, 1, 1]), 1))
            for obj in self.groups[entry['id']]:
                obj.matrix_parent_inverse = matrix
            changed.append(entry['id'])
        apply_materials(self.materials, recipe.get('materials', {}))
        update_stage(self.scene, recipe)
        bpy.context.view_layer.update()
        self.previous = recipe
        return {'apply_seconds': time.perf_counter() - started, 'transformed': changed, 'rebuilt': []}


def revision(base, index):
    result = copy.deepcopy(base)
    selected = {'orrery', 'reactor', 'telescope', 'desk', 'treasury', 'throne', 'alchemy', 'hoist', 'ritual'}
    for entry in result['assemblies']:
        if entry['id'] in selected:
            entry['yaw'] = entry.get('yaw', 0) + 9 * math.sin(index * .61)
            entry['at'][0] += .28 * math.sin(index * .73)
            entry['at'][1] += .22 * math.cos(index * .57)
    result['lighting']['key'] *= 1 + .12 * math.sin(index * .43)
    result['materials']['cloth']['color'] = [.085 + .03 * math.sin(index * .45), .025, .19]
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--profile', required=True, choices=('opt1', 'optNEW', 'eevee', 'interactive'))
    p.add_argument('--mode', choices=('flat', 'recipe'), default='recipe')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--edits', type=int, default=10)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    args.output.mkdir(parents=True, exist_ok=True)
    scene = next(s for s in bpy.data.scenes if s.get('recipe_owner'))
    bpy.context.window.scene = scene
    base = json.loads(scene['recipe_json'])
    before = fingerprint(scene)
    flat = FlatScene(scene) if args.mode == 'flat' else None
    after = fingerprint(scene)
    if before != after:
        raise AssertionError('Baseline representation changed the scene fingerprint')
    report = {'profile': args.profile, 'mode': args.mode, 'recipe_sha256': digest(base),
              'before_flatten': before, 'after_flatten': after, 'settings': configure(scene, args.profile),
              'scope': 'Apply already-authored revision, render and PNG in persistent process. No cached result images. Initial render reported separately. Authoring, startup and reading blend excluded.', 'runs': []}
    def flush():
        (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    def render(label, edit=None):
        started = time.perf_counter()
        row = {'label': label}
        if edit:
            row.update(flat.apply(edit) if flat else apply(edit, scene)[1])
        at = time.perf_counter()
        bpy.ops.render.render(write_still=False, scene=scene.name)
        row['render_seconds'] = time.perf_counter() - at
        row['through_render_seconds'] = time.perf_counter() - started
        at = time.perf_counter()
        bpy.data.images['Render Result'].save_render(str(args.output / f'{label}.png'), scene=scene)
        row['png_seconds'] = time.perf_counter() - at
        row['through_png_seconds'] = time.perf_counter() - started
        row['completed_unix'] = time.time()
        row['fingerprint'] = fingerprint(scene)
        report['runs'].append(row)
        flush()
        print('FRAME ' + json.dumps(row), flush=True)
    render('first')
    for index in range(args.edits):
        render(f'edit-{index:02}', revision(base, index + 1))
    at = time.perf_counter()
    bpy.data.libraries.write(str(args.output / 'revised.blend'), {scene}, fake_user=True, compress=True)
    report['save_scene_seconds'] = time.perf_counter() - at
    report['final_scene_inventory'] = {'objects': len(scene.objects), 'faces': sum(len(o.data.polygons) for o in scene.objects if o.type == 'MESH')}
    # Keep exact transforms for tolerance-based cross-lane validation. A rounded
    # digest alone can differ when equivalent float results straddle a rounding boundary.
    validation = {o.name: {'type': o.type, 'matrix': [float(v) for row in o.matrix_world for v in row],
                          'vertices': len(o.data.vertices) if o.type == 'MESH' else None,
                          'faces': len(o.data.polygons) if o.type == 'MESH' else None,
                          'materials': [list(m.diffuse_color) for m in o.data.materials] if o.type == 'MESH' else [],
                          'energy': o.data.energy if o.type == 'LIGHT' else None}
                  for o in scene.objects if o.type in ('MESH', 'LIGHT')}
    (args.output / 'geometry-validation.json').write_text(json.dumps(validation, separators=(',', ':')))
    flush()


if __name__ == '__main__':
    main()
