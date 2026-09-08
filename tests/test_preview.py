"""Observable preview invariants without invoking Blender."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from types import SimpleNamespace
from http.server import ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'preview'))
from state import RunState
from server import safe_file,make_handler,LocalHTTPServer


class StateTests(unittest.TestCase):
    def test_second_run_cannot_replace_active_history(self):
        state=RunState();self.assertTrue(state.begin('first'));state.event('baseline','lane_start',0)
        self.assertFalse(state.begin('second'));self.assertEqual(state.snapshot()['run_id'],'first')

    def test_uncertain_completion_blocks_another_mutation(self):
        state=RunState();state.begin('first');state.update(status='error',requires_inspection=True)
        self.assertFalse(state.begin('second'))

    def test_snapshot_is_detached_and_records_observed_time(self):
        state=RunState();state.begin('test');state.event('optimized','build_progress',.127,created=64)
        snapshot=state.snapshot();snapshot['events'][0]['created']=999
        self.assertEqual(state.snapshot()['events'][0]['created'],64)
        self.assertEqual(state.snapshot()['lanes']['optimized']['elapsed'],.127)

    def test_finished_lane_can_be_replaced_by_new_run(self):
        state=RunState();state.begin('first');state.event('baseline','lane_done',4,total_seconds=4)
        state.update(status='complete');self.assertTrue(state.begin('second'));self.assertEqual(state.snapshot()['events'],[])


class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)
        (root/'validation.json').write_text('{"objects":1}')
        self.state=RunState();self.config=SimpleNamespace(port=0,asset=root,output=root)
        self.server=LocalHTTPServer(('127.0.0.1',0),make_handler(self.state,self.config))
        self.config.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.config.port}'
        self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def test_live_state_is_readable(self):
        with self.http.open(self.url+'/api/state',timeout=3) as response:self.assertEqual(json.load(response)['status'],'ready')
    def test_cross_origin_run_is_rejected_without_mutation(self):
        request=urllib.request.Request(self.url+'/api/run',data=b'',headers={'Origin':'https://unrelated.example'},method='POST')
        with self.assertRaises(urllib.error.HTTPError) as failure:self.http.open(request,timeout=3)
        self.assertEqual(failure.exception.code,403);self.assertEqual(self.state.snapshot()['status'],'ready')
    def test_same_origin_cannot_supply_arbitrary_arguments(self):
        request=urllib.request.Request(self.url+'/api/run',data=b'{"command":"anything"}',headers={'Origin':self.url},method='POST')
        with self.assertRaises(urllib.error.HTTPError) as failure:self.http.open(request,timeout=3)
        self.assertEqual(failure.exception.code,400);self.assertEqual(self.state.snapshot()['status'],'ready')
    def test_traversal_does_not_escape_root(self):
        self.assertIsNone(safe_file(self.config.asset,'../outside'))
        self.assertIsNone(safe_file(self.config.asset,'/etc/passwd'))
