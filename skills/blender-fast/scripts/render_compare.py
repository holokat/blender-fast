"""Run inside Blender to compare sample limits with fixed scene and render settings."""
import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path
import bpy
import numpy as np


def configure_device(kind):
    scene=bpy.context.scene
    if kind=='CPU':
        scene.cycles.device='CPU';return ['CPU']
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type=kind
    prefs.get_devices()
    selected=[]
    for device in prefs.devices:
        device.use=device.type==kind
        if device.use:selected.append(device.name)
    if not selected:raise RuntimeError(f'No {kind} device available; choose an installed device explicitly')
    scene.cycles.device='GPU'
    return selected


def main():
    if not bpy.app.background:raise RuntimeError("Run this benchmark in a separate background Blender process")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', choices=['CPU','METAL','CUDA','OPTIX','HIP','ONEAPI'], required=True)
    parser.add_argument('--samples', type=int, nargs=2, default=[64,32])
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if min(args.samples)<1 or args.repetitions<1:parser.error('Samples and repetitions must be positive')
    if args.samples[0]==args.samples[1]:parser.error('Choose two distinct sample limits')
    args.output.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    if scene.render.engine!='CYCLES':raise RuntimeError('This benchmark expects an existing Cycles scene')
    device_start=time.perf_counter();devices=configure_device(args.device)
    report={'blender_version':bpy.app.version_string,'device':args.device,'devices':devices,
      'device_setup_seconds':time.perf_counter()-device_start,
      'scope':'Render calls in one Blender process after an excluded warmup; includes scene preparation, denoising and PNG writing. Process startup and device selection excluded.',
      'settings':{'resolution':[scene.render.resolution_x,scene.render.resolution_y],
        'resolution_percentage':scene.render.resolution_percentage,'denoising':scene.cycles.use_denoising,
        'adaptive_sampling':scene.cycles.use_adaptive_sampling,'noise_threshold':scene.cycles.adaptive_threshold,
        'min_samples':scene.cycles.adaptive_min_samples,'persistent_data':scene.render.use_persistent_data,
        'seed':scene.cycles.seed,'view_transform':scene.view_settings.view_transform},'runs':[]}
    if getattr(scene.cycles,'use_animated_seed',False):scene.cycles.use_animated_seed=False
    original={'samples':scene.cycles.samples,'filepath':scene.render.filepath}
    try:
        scene.cycles.samples=min(8,min(args.samples))
        started=time.perf_counter();bpy.ops.render.render()
        report['warmup_seconds']=time.perf_counter()-started
        for repeat in range(args.repetitions):
            order=args.samples if repeat%2==0 else list(reversed(args.samples))
            for samples in order:
                scene.cycles.samples=samples
                scene.render.image_settings.file_format='PNG'
                scene.render.filepath=str((args.output/f'samples-{samples}.png').resolve())
                started=time.perf_counter();bpy.ops.render.render(write_still=True)
                elapsed=time.perf_counter()-started
                report['runs'].append({'repeat':repeat+1,'samples':samples,'seconds':elapsed})
                print('RENDER_SAMPLE_RESULT '+json.dumps(report['runs'][-1]),flush=True)
        report['medians_seconds']={str(samples):statistics.median(row['seconds'] for row in report['runs'] if row['samples']==samples) for samples in args.samples}
        # Compare the saved PNGs without modifying them. Read normalized RGB values exactly as exposed by Blender's PNG loader.
        arrays=[]
        for samples in args.samples:
            image=bpy.data.images.load(str((args.output/f'samples-{samples}.png').resolve()),check_existing=False)
            pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
            arrays.append(pixels.reshape(-1,4)[:,:3])
            bpy.data.images.remove(image)
        delta=np.abs(arrays[0]-arrays[1])
        mse=float(np.mean(delta**2))
        report['image_comparison']={'space':'Normalized RGB values from Blender PNG loader, peak 1',
          'mean_absolute_error':float(np.mean(delta)),'p99_absolute_error':float(np.quantile(delta,.99)),
          'psnr_db_peak_1':10*math.log10(1/mse) if mse else None,
          'interpretation':'Difference from the higher-sample result, not a ground-truth quality score. Inspect both images visually.'}
        (args.output/'render-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RENDER_COMPARISON_COMPLETE '+json.dumps(report),flush=True)
    finally:
        scene.cycles.samples=original['samples'];scene.render.filepath=original['filepath']
    # No blend file or user preferences are saved.


if __name__=='__main__':main()
