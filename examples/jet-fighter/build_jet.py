"""Build and save the original jet concept in a fresh background Blender process."""
import argparse
import json
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from jet_spec import make_spec
from jet_builder import JetBuilder

if __name__=='__main__':
    if not bpy.app.background:raise RuntimeError('Use a separate background Blender process')
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=True)
    if (args.output/'jet.blend').exists():raise RuntimeError('Use a new output directory')
    spec=args.output/'jet-spec.json';spec.write_text(json.dumps(make_spec(),separators=(',',':')))
    builder=JetBuilder(spec,'Jet fighter study');builder.build(0,len(builder.spec['items']))
    builder.preview(args.output/'preview.json');builder.stage();builder.save(args.output/'jet.blend',True)
    (args.output/'validation.json').write_text(json.dumps(builder.fingerprint(),indent=2)+'\n')
    print('JET_READY '+json.dumps(builder.fingerprint()),flush=True)
