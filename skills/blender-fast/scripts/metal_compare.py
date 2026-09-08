"""Benchmark Metal GPU, CPU plus Metal GPU, and MetalRT at fixed render quality."""
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
    if not bpy.app.background:raise RuntimeError('Run in a separate background Blender process')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=64)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.samples<1:parser.error('Sample count must be positive')
    args.output.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    if scene.render.engine!='CYCLES':raise RuntimeError('Expected a Cycles scene')
    devices=configure_device('METAL');prefs=bpy.context.preferences.addons['cycles'].preferences
    scene.cycles.samples=args.samples;scene.cycles.use_denoising=True
    scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_use_gpu=True
    scene.render.use_persistent_data=True
    if hasattr(scene.cycles,'use_animated_seed'):scene.cycles.use_animated_seed=False
    report={'device':'METAL','devices':devices,'blender_version':bpy.app.version_string,'samples':args.samples,
      'scope':'Same scene and sample count, GPU denoising, persistent data. Three warm repeated renders per configuration; one excluded full-sample warmup per configuration. No Blender or user preference files saved.',
      'settings':{'resolution':[scene.render.resolution_x,scene.render.resolution_y],
        'resolution_percentage':scene.render.resolution_percentage,'adaptive_sampling':scene.cycles.use_adaptive_sampling,
        'noise_threshold':scene.cycles.adaptive_threshold,'min_samples':scene.cycles.adaptive_min_samples,'seed':scene.cycles.seed},'profiles':[]}
    variants=[('gpu-auto',False,'AUTO'),('cpu-plus-gpu',True,'AUTO')]
    if hasattr(prefs,'metalrt'):variants.append(('gpu-metalrt',False,'ON'))
    for name,cpu,metalrt in variants:
        if hasattr(prefs,'metalrt'):prefs.metalrt=metalrt
        for device in prefs.devices:device.use=device.type=='METAL' or (cpu and device.type=='CPU')
        row={'name':name,'metalrt':getattr(prefs,'metalrt',None),
          'enabled_devices':[d.name for d in prefs.devices if d.use],'seconds':[]}
        try:
            scene.render.image_settings.file_format='PNG';scene.render.filepath=str((args.output/(name+'.png')).resolve())
            started=time.perf_counter();bpy.ops.render.render();row['warmup_seconds']=time.perf_counter()-started
            for repeat in range(3):
                started=time.perf_counter();bpy.ops.render.render(write_still=True)
                row['seconds'].append(time.perf_counter()-started)
                print('METAL_RESULT '+json.dumps({'profile':name,'repeat':repeat+1,'seconds':row['seconds'][-1]}),flush=True)
            row['median_seconds']=statistics.median(row['seconds'])
        except RuntimeError as exc:
            row['error']=str(exc)
        report['profiles'].append(row)
        (args.output/'metal-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print('METAL_COMPLETE '+json.dumps(report),flush=True)


if __name__=='__main__':main()
