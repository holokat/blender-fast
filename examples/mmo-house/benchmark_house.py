"""Measure an isolated house scene through the existing local Blender Lab bridge."""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'skills/blender-fast/scripts'))
from blender_client import execute,status,ExecutionUncertain,DEFAULT_ADDON
from polling_profile import write_values,validate_values,FAST


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['batch','full'],default='batch',help='Full includes the slow individual-call baselines')
    parser.add_argument('--port',type=int,default=9876)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise RuntimeError('Output exists; choose a new results file')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    connection=dict(port=args.port)
    original,_=status(**connection)
    if not original['addon_enabled']:raise RuntimeError('Expected Blender Lab add-on is not enabled')
    baseline={'timer_interval_active':.25,'timer_interval_idle':1.,'timer_interval_idle_delay':5.}
    for values in (FAST,baseline):validate_values(values,original['limits'])
    strategies=[('faster polling, batches of 64',FAST,64)]
    if args.mode=='full':strategies=[('original, individual calls',baseline,1),('faster polling, individual calls',FAST,1)]+strategies
    key='blender_fast_'+uuid.uuid4().hex
    report={'original_polling':original['polling'],'blender_version':original['blender_version'],
      'scope':'Local bridge construction only; setup reported separately. Validation, staging, model reasoning, MCP client and rendering excluded.','runs':[]}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    initialized=False;uncertain=False
    count=len(json.loads((HERE/'house-spec.json').read_text())['items'])
    try:
        for label,values,batch in strategies:
            write_values(values,**connection)
            start=time.perf_counter()
            execute(f"import bpy,runpy\nm=runpy.run_path({str(HERE/'house_builder.py')!r})\nbpy.app.driver_namespace[{key!r}]=m['HouseBuilder']({str(HERE/'house-spec.json')!r},name={key!r})\nresult={{'ready':True}}",**connection)
            initialized=True;setup=time.perf_counter()-start;start=time.perf_counter();calls=0
            for first in range(0,count,batch):
                execute(f"import bpy\nresult=bpy.app.driver_namespace[{key!r}].build({first},{min(first+batch,count)})",**connection);calls+=1
                if calls%100==0:print(label,min(first+batch,count),'/',count,flush=True)
            duration=time.perf_counter()-start
            fp,_=execute(f"import bpy\nresult=bpy.app.driver_namespace[{key!r}].fingerprint()",timeout=90,**connection)
            report['runs'].append({'strategy':label,'batch_size':batch,'calls':calls,'setup_seconds':setup,'build_seconds':duration,'fingerprint':fp})
            args.output.write_text(json.dumps(report,indent=2)+'\n')
            execute(f"import bpy\nbpy.app.driver_namespace.pop({key!r}).cleanup()\nresult={{'removed':True}}",**connection);initialized=False
        report['fingerprints_match']=len({r['fingerprint']['sha256'] for r in report['runs']})==1
        if not report['fingerprints_match']:raise RuntimeError('Fingerprints differ')
    except ExecutionUncertain:
        uncertain=True
        print(f'Execution uncertain. Inspect Blender namespace {key} and the saved original_polling before cleanup or retry.',file=sys.stderr)
        raise
    finally:
        if not uncertain:
            if initialized:
                execute(f"import bpy\nbpy.app.driver_namespace.pop({key!r}).cleanup()\nresult={{'removed':True}}",**connection)
            write_values(original['polling'],**connection)
            report['polling_restored']=True
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
