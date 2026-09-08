"""Thread-safe event history used by live monitoring and exact recorded replay."""
import copy
import json
import threading
import time
from pathlib import Path


class RunState:
    def __init__(self):
        self.lock=threading.RLock();self.cancel=threading.Event();self.revision=0
        self.data={'status':'ready','run_id':None,'lanes':{},'events':[],'message':'Ready to measure both pipelines.'}

    def begin(self,run_id):
        with self.lock:
            if self.data['status']=='running' or self.data.get('requires_inspection'):return False
            self.cancel.clear();self.revision+=1
            self.data={'status':'running','run_id':run_id,'lanes':{},'events':[],
                       'message':'Sequential measurement on one GPU. Live events, no overlapping renders.'}
            return True

    def update(self,**values):
        with self.lock:self.data.update(values);self.revision+=1

    def event(self,lane,kind,elapsed,**values):
        with self.lock:
            row={'lane':lane,'kind':kind,'t':elapsed,**values};self.data['events'].append(row)
            target=self.data['lanes'].setdefault(lane,{'created':0,'phase':'setup','elapsed':0})
            target.update(values);target['elapsed']=elapsed;target['last_kind']=kind
            if kind=='lane_start':target['started_epoch']=time.time()
            if kind=='lane_done':target['done']=True
            self.revision+=1
            return copy.deepcopy(row)

    def snapshot(self):
        with self.lock:return copy.deepcopy({**self.data,'revision':self.revision,'server_epoch':time.time()})

    def save(self,path):
        Path(path).write_text(json.dumps(self.snapshot(),indent=2)+'\n')
