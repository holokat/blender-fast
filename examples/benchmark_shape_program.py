"""Fresh scene builds in a warmed Blender process, plus scoped timing evidence."""
import copy
import json
import sys
import time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/blender-fast/scripts'))
from shape_program.compiler import apply,inventory
from shape_program.cli import render,write_json

args=sys.argv[sys.argv.index('--')+1:]
program_path,output=Path(args[0]),Path(args[1]);output.mkdir(parents=True,exist_ok=True)
program=json.loads(program_path.read_text())
started=time.perf_counter()
warm_scene,warm_build=apply(program)
warmup=[render(warm_scene,p,output/'warmup.png') for p in ('interactive','optNEW','opt1')]
results=[]
for index in range(3):
    current=copy.deepcopy(program)
    current['seed']=index+1
    # Change the newly constructed geometry so this is not a saved-scene/frame replay.
    target=next(r for r in current['assemblies'] if r['id']=='front_tree')
    target['args']['height']+=index*.12
    t=time.perf_counter()
    scene,build=apply(current)
    row={'trial':index+1,'scene_owner':scene['shape_owner'],'build':build,'inventory':inventory(scene),'renders':[]}
    for profile in ('interactive','optNEW','opt1'):
        result=render(scene,profile,output/(profile+'.png'))
        result['elapsed_seconds']=time.perf_counter()-t
        row['renders'].append(result)
    s=time.perf_counter();bpy.ops.wm.save_as_mainfile(filepath=str(output/'scene.blend'))
    row['save_seconds']=time.perf_counter()-s;row['total_seconds']=time.perf_counter()-t
    results.append(row)
    print('SHAPE_TRIAL '+json.dumps(row),flush=True)
report={'scope':'New isolated scene per trial, complete geometry created again, three progressive renders and save. Renderer warmed on a separate scene first. Excludes prompt interpretation, authoring, process startup and visual review.',
        'warmup_build':warm_build,'warmup_renders':warmup,'trials':results,'experiment_seconds':time.perf_counter()-started}
write_json(output/'benchmark.json',report)
write_json(output/'program.json',current)
write_json(output/'result.json',{'title':current['title'],'timing_scope':report['scope'],'build':results[-1]['build'],
    'inventory':results[-1]['inventory'],'renders':results[-1]['renders'],'save_seconds':results[-1]['save_seconds'],'total_seconds':results[-1]['total_seconds']})
# Reopen the editable save and confirm compiler identity is recovered without a rebuild.
bpy.ops.wm.open_mainfile(filepath=str(output/'scene.blend'))
loaded=bpy.context.scene
_,check=apply(json.loads(loaded['shape_json']),loaded)
assert not check['rebuilt'] and not check['transformed']
assert loaded['shape_sha256']==results[-1]['build']['program_sha256']
write_json(output/'reopen-check.json',{'status':'passed','no_op':check,'inventory':inventory(loaded)})
