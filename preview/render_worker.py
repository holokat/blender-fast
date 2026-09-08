"""Blender render worker. Emits observed phase boundaries, never simulated progress."""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'skills/blender-fast/scripts'))
from render_compare import configure_device


def emit(kind,**data):
    print('BLENDER_FAST_EVENT '+json.dumps({'kind':kind,**data}),flush=True)


def main():
    if not bpy.app.background:raise RuntimeError('Run in a separate background Blender process')
    p=argparse.ArgumentParser();p.add_argument('--lane',choices=['baseline','optimized'],required=True)
    p.add_argument('--device',default='METAL');p.add_argument('--output',type=Path,required=True);p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=True)
    scenes=[s for s in bpy.data.scenes if s.render.engine=='CYCLES' and s.camera]
    if len(scenes)!=1:raise RuntimeError('Expected one staged Cycles scene in this isolated file')
    scene=scenes[0]
    if bpy.context.window:bpy.context.window.scene=scene
    optimized=args.lane=='optimized';devices=configure_device(args.device)
    prefs=bpy.context.preferences.addons['cycles'].preferences
    if args.device=='METAL' and hasattr(prefs,'metalrt'):prefs.metalrt='AUTO'
    scene.cycles.denoising_use_gpu=optimized;scene.render.use_persistent_data=optimized
    scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
    settings={'device':args.device,'devices':devices,'samples':scene.cycles.samples,
        'resolution':[scene.render.resolution_x,scene.render.resolution_y],
        'gpu_denoising':optimized,'persistent_data':optimized,'metalrt':getattr(prefs,'metalrt',None),
        'noise_threshold':scene.cycles.adaptive_threshold,'seed':scene.cycles.seed,'blender_version':bpy.app.version_string}
    emit('device_ready',settings=settings)
    results=[]
    for repeat in range(args.repeats+1):
        phase='first_render' if repeat==0 else f'repeat_{repeat}'
        name=f'{args.lane}-{phase}.png';scene.render.filepath=str((args.output/name).resolve())
        emit('render_start',phase=phase,repeat=repeat)
        started=time.perf_counter();bpy.ops.render.render(write_still=True,scene=scene.name);elapsed=time.perf_counter()-started
        result={'phase':phase,'seconds':elapsed,'image':name};results.append(result);emit('render_done',**result)
    report={'settings':settings,'renders':results,'warm_median_seconds':statistics.median(r['seconds'] for r in results[1:]) if len(results)>1 else None}
    (args.output/f'{args.lane}-renders.json').write_text(json.dumps(report,indent=2)+'\n');emit('worker_done',report=report)


if __name__=='__main__':main()
