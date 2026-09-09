"""Validate outside Blender; build and progressively render inside Blender."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shape_program.expand import expand


def write_json(path,value):
    path=Path(path)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    temp.replace(path)


def render(scene,profile,path):
    import bpy
    from scene_recipe.staging import configure
    start=time.perf_counter()
    config=configure(scene,profile)
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True,scene=scene.name)
    return config | {'render_seconds':time.perf_counter()-start,'file':Path(path).name}


def run(program,output,profiles,save):
    import bpy
    from shape_program.compiler import apply,inventory
    output.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    scene,build=apply(program)
    result={'title':program['title'],'timing_scope':'Prepared program through build, profiles and optional save; excludes authoring and Blender startup',
            'build':build,'inventory':inventory(scene),'renders':[]}
    write_json(output/'program.json',program)
    write_json(output/'result.json',result)
    for profile in profiles:
        result['renders'].append(render(scene,profile,output/(profile+'.png')))
        result['renders'][-1]['elapsed_seconds']=time.perf_counter()-start
        write_json(output/'result.json',result)
        print('SHAPE_PROGRESS '+json.dumps(result['renders'][-1]),flush=True)
    if save:
        t=time.perf_counter()
        bpy.ops.wm.save_as_mainfile(filepath=str(output/'scene.blend'))
        result['save_seconds']=time.perf_counter()-t
    result['total_seconds']=time.perf_counter()-start
    write_json(output/'result.json',result)
    print('SHAPE_RESULT '+json.dumps(result),flush=True)
    return scene,result


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('program',type=Path)
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--profiles',nargs='+',choices=('interactive','eevee','optNEW','opt1'),default=['interactive','optNEW','opt1'])
    parser.add_argument('--no-save',action='store_true')
    parser.add_argument('--worker',action='store_true',help='After initial build, accept one JSON program per stdin line; Blender stays warm')
    args=parser.parse_args(argv)
    if args.program.stat().st_size>2_000_000:parser.error('Program exceeds 2 MB input limit')
    program=json.loads(args.program.read_text())
    graph=expand(program)
    if args.validate:
        print(json.dumps({'program_sha256':graph['program_sha256'],'budget':graph['budget'],'assemblies':len(graph['assemblies'])}))
        return
    if args.output is None:parser.error('--output is required for Blender execution')
    scene,result=run(program,args.output.resolve(),args.profiles,not args.no_save)
    if args.worker:
        from shape_program.compiler import apply,inventory
        for line in sys.stdin:
            try:
                start=time.perf_counter()
                if len(line)>2_000_000:raise ValueError('Request exceeds 2 MB')
                request=json.loads(line)
                profile=request.get('profile','interactive')
                if profile not in ('interactive','eevee','optNEW','opt1'):raise ValueError('Unknown profile')
                scene,build=apply(request['program'],scene)
                frame=render(scene,profile,args.output/'live.png')
                reply={'build':build,'render':frame,'inventory':inventory(scene),'total_seconds':time.perf_counter()-start}
                print('SHAPE_FRAME '+json.dumps(reply),flush=True)
            except Exception as error:
                print('SHAPE_FRAME '+json.dumps({'error':str(error)}),flush=True)


if __name__=='__main__':main()
