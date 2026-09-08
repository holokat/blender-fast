"""Build the example inside a fresh background Blender process; optionally render it."""
import argparse
import json
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from house_builder import HouseBuilder
from house_spec import create_spec


def main():
    if not bpy.app.background:raise RuntimeError('Use a separate background Blender process')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--device',choices=['CPU','METAL','CUDA','OPTIX','HIP','ONEAPI'],default='CPU')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'house.blend').exists():raise RuntimeError('Output house.blend exists; choose a new output directory')
    spec_path=out/'house-spec.json';spec_path.write_text(json.dumps(create_spec())+'\n')
    builder=HouseBuilder(spec_path)
    builder.build(0,len(builder.spec['items']))
    fingerprint=builder.fingerprint();builder.stage()
    scene=builder.scene
    if bpy.context.window:bpy.context.window.scene=scene
    else:raise RuntimeError('No window context to select the example scene')
    helpers=HERE.parents[1]/'skills/blender-fast/scripts';sys.path.insert(0,str(helpers))
    from render_compare import configure_device
    devices=configure_device(args.device)
    scene.render.filepath=str(out/'house.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'house.blend'))
    if args.render:bpy.ops.render.render(write_still=True,scene=scene.name)
    (out/'validation.json').write_text(json.dumps(fingerprint,indent=2)+'\n')
    print('HOUSE_VALIDATION '+json.dumps({'fingerprint':fingerprint,'devices':devices}),flush=True)


if __name__=='__main__':main()
