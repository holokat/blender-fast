"""Combine real bridge edits and isolated Cycles renders without GPU contention."""
import json
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'skills/blender-fast/scripts'))
from blender_client import execute,status,ExecutionUncertain
from polling_profile import FAST,validate_values,write_values


class Cancelled(RuntimeError):pass


def run_comparison(state,config,run_id):
    folder=config.output/run_id;folder.mkdir(parents=True,exist_ok=False)
    original=None;key=None;initialized=False;uncertain=False;final_status="error"
    connection={'port':config.bridge_port}
    count=len(json.loads((config.asset/'jet-spec.json').read_text())['items'])
    expected=json.loads((config.asset/'validation.json').read_text())
    records=[]
    def check():
        if state.cancel.is_set():raise Cancelled('Comparison stopped at a safe boundary.')
    try:
        original,_=status(**connection)
        if not original.get('addon_enabled'):raise RuntimeError('The existing Blender Lab add-on must be enabled')
        (folder/'polling-before.json').write_text(json.dumps(original,indent=2)+'\n')
        state.update(total_objects=count,reference_fingerprint=expected,blender_version=original['blender_version'])
        for lane,batch,values in [('baseline',1,{'timer_interval_active':.25,'timer_interval_idle':1.,'timer_interval_idle_delay':5.}),('optimized',64,FAST)]:
            check();key='jet_compare_'+uuid.uuid4().hex;started=time.perf_counter()
            def event(kind,**data):
                state.event(lane,kind,time.perf_counter()-started,**data)
            event('lane_start',phase='setup',batch_size=batch,created=0)
            values=dict(values)
            if lane=='optimized':
                for k in ('timer_interval_active','timer_interval_idle'):values[k]=min(values[k],original['polling'][k])
                values['timer_interval_idle_delay']=original['polling']['timer_interval_idle_delay']
            validate_values(values,original['limits']);write_values(values,**connection)
            setup=time.perf_counter()
            execute(f"import bpy,runpy\nm=runpy.run_path({str(ROOT/'examples/jet-fighter/jet_builder.py')!r})\nbpy.app.driver_namespace[{key!r}]=m['JetBuilder']({str(config.asset/'jet-spec.json')!r},{key!r})\nresult={{'ready':True}}",**connection)
            initialized=True;setup_seconds=time.perf_counter()-setup
            event('build_start',phase='build',setup_seconds=setup_seconds)
            build_start=time.perf_counter();calls=0;call_seconds=0
            for start in range(0,count,batch):
                check();end=min(start+batch,count)
                response,ms=execute(f"import bpy\nresult=bpy.app.driver_namespace[{key!r}].build({start},{end})",**connection)
                if response['created']!=end:raise RuntimeError('Created count differs from requested range')
                calls+=1;call_seconds+=ms/1000
                event('build_progress',phase='build',created=end,calls=calls,build_seconds=time.perf_counter()-build_start)
            build_seconds=time.perf_counter()-build_start
            event('build_done',phase='verify',build_seconds=build_seconds,calls=calls)
            fp,_=execute(f"import bpy\nresult=bpy.app.driver_namespace[{key!r}].fingerprint()",**connection)
            if fp!=expected:raise RuntimeError('Jet geometry/material fingerprint differs from the reference')
            event('verified',phase='save',fingerprint=fp)
            blend=folder/f'{lane}.blend'
            execute(f"import bpy\nb=bpy.app.driver_namespace[{key!r}]\nb.stage()\nresult=b.save({str(blend)!r},optimized={lane=='optimized'})",**connection)
            execute(f"import bpy\nbpy.app.driver_namespace.pop({key!r}).cleanup()\nresult={{'removed':True}}",**connection);initialized=False
            write_values(original['polling'],**connection)
            check();event('worker_start',phase='start_renderer')
            worker_start=time.perf_counter()
            report=render_lane(state,config,folder,lane,blend,event,check)
            total=time.perf_counter()-started
            record={'lane':lane,'batch_size':batch,'calls':calls,'polling':values,'setup_seconds':setup_seconds,
                'build_seconds':build_seconds,'bridge_round_trip_seconds':call_seconds,'fingerprint':fp,
                'render_process_seconds':time.perf_counter()-worker_start,'total_seconds':total,**report}
            records.append(record)
            event('lane_done',phase='done',total_seconds=total,render_report=report)
            state.update(results=records);state.save(folder/'events.json')
        final_status="complete"
        state.update(message='Both lanes finished. Restoring polling preferences.',fingerprints_match=True)
    except ExecutionUncertain as exc:
        uncertain=True
        state.update(requires_inspection=True,message=f'Bridge completion is uncertain. Inspect namespace {key} before cleanup or retry. {exc}')
    except Cancelled as exc:
        final_status='cancelled';state.update(message=str(exc))
    except Exception as exc:state.update(message=f'{type(exc).__name__}: {exc}')
    finally:
        if original and not uncertain:
            try:
                if initialized:
                    execute(f"import bpy\nbpy.app.driver_namespace.pop({key!r}).cleanup()\nresult={{'removed':True}}",**connection)
                write_values(original['polling'],**connection);state.update(polling_restored=True)
            except Exception as exc:
                final_status='error';state.update(requires_inspection=True,message=f'Unable to confirm cleanup or polling restore: {exc}')
        if final_status=='complete':
            state.update(message='Both runs completed. Geometry fingerprints match. Replay aligns each lane at its measured start.')
        state.update(status=final_status)
        state.save(folder/'events.json')
        report={'schema_version':1,'scope':'Live local bridge build plus isolated render process for each lane. Lanes run sequentially. Three warm repeats follow the first render in each process. Timers exclude model authoring and preview preflight. Total includes profile setup, validation, saving, process startup, rendering and instrumentation. Rendering holds geometry, camera, lights, 64 sample limit and 1400x1000 resolution fixed. No AI or external MCP server/client is timed.',
                'status':state.snapshot()['status'],'results':records,'fingerprints_match':len(records)==2 and records[0]['fingerprint']==records[1]['fingerprint'],
                'order':['baseline','optimized'],'system_load_controlled':False,'polling_restored':state.snapshot().get('polling_restored',False)}
        (folder/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')


def render_lane(state,config,folder,lane,blend,event,check):
    cmd=[str(config.blender),'--background',str(blend),'--python',str(ROOT/'preview/render_worker.py'),'--','--lane',lane,'--device',config.device,'--output',str(folder),'--repeats','3']
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    # Reader thread handles child stdout only. All bpy work remains in Blender's main thread.
    import queue
    lines=queue.Queue()
    def read():
        for line in process.stdout:lines.put(line)
        lines.put(None)
    thread=threading.Thread(target=read,daemon=True);thread.start();report=None
    try:
        with (folder/f'{lane}-render.log').open('w') as log:
            while True:
                check()
                try:line=lines.get(timeout=.2)
                except queue.Empty:continue
                if line is None:break
                log.write(line)
                if line.startswith('BLENDER_FAST_EVENT '):
                    row=json.loads(line.split(' ',1)[1]);kind=row.pop('kind')
                    if 'image' in row:row['image']=f'/runs/{folder.name}/{row["image"]}'
                    if kind=='worker_done':report=row['report']
                    event(kind,**row)
                else:
                    found=re.search(r'Sample\s+(\d+)\s*/\s*(\d+)',line)
                    if found:event('render_progress',sample=int(found[1]),sample_limit=int(found[2]))
                    elif '| Denoising' in line:event('denoising',render_status='Denoising')
        code=process.wait(timeout=15)
        if code or report is None:raise RuntimeError(f'{lane} render process failed (exit {code}); inspect its local render log')
        return report
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        process.stdout.close()
