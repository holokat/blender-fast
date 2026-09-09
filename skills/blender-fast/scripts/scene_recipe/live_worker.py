"""Persistent Blender main-thread worker; commands arrive over stdin, not polling files."""
import json
import sys
import time
import traceback
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_recipe.compiler import apply
from scene_recipe.staging import configure


def main():
    destination = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
    scene = next(s for s in bpy.data.scenes if s.get('recipe_owner'))
    bpy.context.window.scene = scene
    current_profile = None
    frame_number = 0
    for line in sys.stdin:
        request = json.loads(line)
        try:
            started = time.perf_counter()
            scene, result = apply(request['recipe'], scene)
            profile = request['profile']
            if profile != current_profile:
                settings = configure(scene, profile)
                current_profile = profile
            result['settings'] = settings
            at = time.perf_counter()
            bpy.ops.render.render(write_still=False, scene=scene.name)
            result['render_seconds'] = time.perf_counter() - at
            name = f'frame-{frame_number % 3}.png'
            frame_number += 1
            temporary = destination / (name + '.tmp.png')
            bpy.data.images['Render Result'].save_render(str(temporary), scene=scene)
            temporary.replace(destination / name)
            result.update(id=request['id'], status='complete', frame=name,
                          worker_seconds=time.perf_counter() - started)
            if request.get('save'):
                at = time.perf_counter()
                bpy.context.window.scene = scene
                bpy.ops.wm.save_as_mainfile(filepath=str(destination / 'scene-live.blend'), compress=True)
                (destination / 'scene-live.json').write_text(json.dumps(request['recipe'], indent=2) + '\n')
                result['save_seconds'] = time.perf_counter() - at
                result['saved'] = True
            print('RECIPE_FRAME ' + json.dumps(result), flush=True)
        except Exception as error:
            traceback.print_exc()
            print('RECIPE_FRAME ' + json.dumps({'id': request['id'], 'status': 'error', 'message': str(error)}), flush=True)


if __name__ == '__main__':
    main()
