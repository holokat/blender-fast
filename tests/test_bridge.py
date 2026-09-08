"""Protocol tests use an isolated synthetic TCP server, never a live Blender scene."""
import contextlib
import json
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/blender-fast/scripts'))
import blender_client as client
from polling_profile import validate_values, FAST


@contextlib.contextmanager
def server(reply):
    requests=[];errors=[]
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(2)
    def serve():
        try:
            with listener.accept()[0] as conn:
                conn.settimeout(2);data=bytearray()
                while b'\0' not in data:data.extend(conn.recv(4096))
                requests.append(json.loads(data.split(b'\0')[0]))
                reply(conn)
        except Exception as exc:errors.append(exc)
    thread=threading.Thread(target=serve);thread.start()
    try:yield listener.getsockname()[1],requests
    finally:
        thread.join(3);listener.close()
        if thread.is_alive():raise AssertionError('Test server did not stop')
        if errors:raise errors[0]


class ProtocolTests(unittest.TestCase):
    def test_fragmented_unicode_response(self):
        raw=json.dumps({'status':'ok','result':{'label':'house 🏡'}},ensure_ascii=False).encode()+b'\0'
        def reply(conn):
            for byte in raw:
                conn.sendall(bytes([byte]));time.sleep(.0001)
        with server(reply) as (port,requests):
            result,elapsed=client.execute('result={"ok":True}',port=port)
        self.assertEqual(result,{'label':'house 🏡'})
        self.assertGreater(elapsed,0)
        self.assertEqual(requests[0]['strict_json'],True)
        self.assertEqual(requests[0]['type'],'execute')

    def test_complete_script_error_is_reported(self):
        raw=json.dumps({'status':'error','message':'Object not found'}).encode()+b'\0'
        with server(lambda conn:conn.sendall(raw)) as (port,_):
            with self.assertRaises(client.BridgeError) as raised:client.execute('raise ValueError()',port=port)
        self.assertNotIsInstance(raised.exception,client.ExecutionUncertain)
        self.assertIn('Object not found',str(raised.exception))

    def test_disconnect_is_uncertain_and_not_retried(self):
        with server(lambda conn:None) as (port,requests):
            with self.assertRaises(client.ExecutionUncertain):client.execute('result={}',port=port)
        self.assertEqual(len(requests),1)

    def test_timeout_is_uncertain(self):
        with server(lambda conn:time.sleep(.15)) as (port,_):
            with self.assertRaises(client.ExecutionUncertain):client.execute('result={}',port=port,timeout=.05)

    def test_response_is_bounded(self):
        with server(lambda conn:conn.sendall(b'x'*100)) as (port,_):
            with self.assertRaises(client.ExecutionUncertain):client.execute('result={}',port=port,max_response=32)

    def test_malformed_response_is_uncertain(self):
        with server(lambda conn:conn.sendall(b'{broken}\0')) as (port,_):
            with self.assertRaises(client.ExecutionUncertain):client.execute('result={}',port=port)

    def test_non_dictionary_result_is_rejected(self):
        with server(lambda conn:conn.sendall(b'{"status":"ok","result":[]}\0')) as (port,_):
            with self.assertRaises(client.ExecutionUncertain):client.execute('result={}',port=port)

    def test_oversized_request_never_connects(self):
        with patch.object(client,'MAX_REQUEST_BYTES',20),patch.object(client.socket,'create_connection') as connect:
            with self.assertRaises(ValueError):client.execute('result={}')
            connect.assert_not_called()

    def test_remote_destination_never_connects(self):
        with patch.object(client.socket,'create_connection') as connect:
            with self.assertRaises(ValueError):client.execute('result={}',host='example.com')
            connect.assert_not_called()


class ProfileTests(unittest.TestCase):
    limits={'timer_interval_active':[.050000000745,5.0],'timer_interval_idle':[.1,10.0],'timer_interval_idle_delay':[1.,60.]}

    def test_accepts_blender_float_boundaries(self):validate_values(FAST,self.limits)

    def test_rejects_out_of_range_and_nonfinite_values(self):
        for value in (-1,float('nan'),float('inf'),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_values({**FAST,'timer_interval_active':value},self.limits)

    def test_rejects_unrelated_preferences(self):
        with self.assertRaises(ValueError):validate_values({**FAST,'unknown':1},self.limits)


if __name__=='__main__':unittest.main()
