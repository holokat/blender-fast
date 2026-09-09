"""Run with Blender --background --python recipe_cli.py -- recipe.json --output directory."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from scene_recipe.compiler import apply, inventory
from scene_recipe.staging import configure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipe', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', choices=('opt1', 'optNEW', 'eevee', 'interactive'), default='optNEW')
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    started = time.perf_counter()
    recipe = json.loads(args.recipe.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    scene, result = apply(recipe)
    result.update(inventory(scene))
    result['settings'] = configure(scene, args.profile)
    if not args.no_render:
        at = time.perf_counter()
        bpy.ops.render.render(write_still=False, scene=scene.name)
        result['render_seconds'] = time.perf_counter() - at
        at = time.perf_counter()
        bpy.data.images['Render Result'].save_render(str(args.output / 'preview.png'), scene=scene)
        result['png_seconds'] = time.perf_counter() - at
    at = time.perf_counter()
    bpy.context.window.scene = scene
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output / 'scene.blend'), compress=True)
    result['save_scene_seconds'] = time.perf_counter() - at
    result['script_seconds'] = time.perf_counter() - started
    result['completed_unix'] = time.time()
    result['scope'] = 'Recipe read through editable scene and optional PNG; excludes agent authoring and Blender startup.'
    (args.output / 'recipe.json').write_text(json.dumps(recipe, indent=2) + '\n')
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('RECIPE_RESULT ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
