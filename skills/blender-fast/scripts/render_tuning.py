"""Compare GPU denoising and persistent data at the same Cycles sample limit."""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_compare import configure_device


def main():
    if not bpy.app.background:raise RuntimeError('Run this benchmark in a separate background Blender process')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=64)
    parser.add_argument('--repetitions',type=int,default=3)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.samples<1 or args.repetitions<1:parser.error('Samples and repetitions must be positive')
    args.output.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    if scene.render.engine!='CYCLES':raise RuntimeError('This benchmark requires a Cycles scene')
    devices=configure_device(args.device)
    scene.cycles.samples=args.samples;scene.cycles.use_denoising=True
    scene.cycles.denoiser='OPENIMAGEDENOISE'
    if hasattr(scene.cycles,'use_animated_seed'):scene.cycles.use_animated_seed=False
    report={'blender_version':bpy.app.version_string,'device':args.device,'devices':devices,'samples':args.samples,
      'scope':'Warm repeat renders of an unchanged scene in one background process. Each profile gets an excluded warmup. Render call includes preparation, denoising and PNG write. Device/process startup excluded.',
      'settings':{'resolution':[scene.render.resolution_x,scene.render.resolution_y],
        'resolution_percentage':scene.render.resolution_percentage,'adaptive_sampling':scene.cycles.use_adaptive_sampling,
        'noise_threshold':scene.cycles.adaptive_threshold,'min_samples':scene.cycles.adaptive_min_samples,'seed':scene.cycles.seed},'profiles':[]}
    for name,gpu_denoise,persistent in [('cpu-denoise',False,False),('gpu-denoise',True,False),('gpu-denoise-cached',True,True)]:
        scene.cycles.denoising_use_gpu=gpu_denoise;scene.render.use_persistent_data=persistent
        scene.render.image_settings.file_format='PNG';scene.render.filepath=str((args.output/(name+'.png')).resolve())
        started=time.perf_counter();bpy.ops.render.render()
        row={'name':name,'gpu_denoising_requested':gpu_denoise,'persistent_data':persistent,'warmup_seconds':time.perf_counter()-started,'seconds':[]}
        for repeat in range(args.repetitions):
            started=time.perf_counter();bpy.ops.render.render(write_still=True)
            row['seconds'].append(time.perf_counter()-started)
            print('TUNING_RESULT '+json.dumps({'profile':name,'repeat':repeat+1,'seconds':row['seconds'][-1]}),flush=True)
        row['median_seconds']=statistics.median(row['seconds']);report['profiles'].append(row)
        (args.output/'render-tuning.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TUNING_COMPLETE '+json.dumps(report),flush=True)


if __name__=='__main__':main()
