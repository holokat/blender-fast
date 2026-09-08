"""Local preview server with fixed benchmark actions and same-origin write checks."""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from socketserver import TCPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
from state import RunState
from runner import run_comparison

HERE=Path(__file__).resolve().parent


class LocalHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        # Loopback does not need reverse DNS, which can stall local startup.
        TCPServer.server_bind(self)
        self.server_name=self.server_address[0];self.server_port=self.server_address[1]


def safe_file(root,relative):
    target=(root/relative).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():return None
    return target


def make_handler(state,config):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,data,kind='application/json'):
            if not isinstance(data,bytes):data=json.dumps(data).encode()
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def valid_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{config.port}',f'localhost:{config.port}'}
        def do_GET(self):
            if not self.valid_host():return self.send(403,{'error':'Loopback host required'})
            path=unquote(urlsplit(self.path).path)
            if path=='/api/state':return self.send(200,state.snapshot())
            if path=='/api/config':return self.send(200,{'device':config.device,'objects':json.loads((config.asset/'validation.json').read_text())['objects']})
            if path=='/asset/preview.json':target=config.asset/'preview.json'
            elif path.startswith('/runs/'):
                target=safe_file(config.output,path.removeprefix('/runs/'))
                if target and target.suffix not in {'.png','.json','.blend'}:target=None
            else:target=safe_file(HERE/'web','index.html' if path=='/' else path.lstrip('/'))
            if target is None or not target.is_file():return self.send(404,{'error':'File not found'})
            mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.png':'image/png','.blend':'application/octet-stream'}.get(target.suffix,'application/octet-stream')
            self.send(200,target.read_bytes(),mime)
        def do_POST(self):
            if not self.valid_host():return self.send(403,{'error':'Loopback host required'})
            origin=self.headers.get('Origin')
            if origin!=f'http://{self.headers.get("Host")}':return self.send(403,{'error':'Same-origin requests required'})
            if self.headers.get('Content-Length','0')!='0':return self.send(400,{'error':'No request body accepted'})
            if self.path=='/api/run':
                run_id=time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns())[-6:]
                if not state.begin(run_id):return self.send(409,{'error':'A comparison is running or Blender state needs inspection'})
                threading.Thread(target=run_comparison,args=(state,config,run_id),daemon=True).start()
                return self.send(202,{'run_id':run_id})
            if self.path=='/api/stop':state.cancel.set();return self.send(202,{'stopping':True})
            self.send(404,{'error':'Unknown action'})
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blender',type=Path,required=True);p.add_argument('--asset',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,default=8765);p.add_argument('--bridge-port',type=int,default=9876);p.add_argument('--device',default='METAL',choices=['METAL','CUDA','OPTIX','HIP','ONEAPI'])
    args=p.parse_args()
    for key in ('blender','asset','output'):setattr(args,key,getattr(args,key).resolve())
    if not args.blender.is_file():p.error('Blender executable does not exist')
    for name in ('preview.json','validation.json','jet-spec.json'):
        if not (args.asset/name).is_file():p.error('Run build_jet.py first to create the preview asset')
    args.output.mkdir(parents=True,exist_ok=True);state=RunState()
    previous=sorted(args.output.glob('*/events.json'))
    if previous:
        previous_data=json.loads(previous[-1].read_text())
        if previous_data['status']!='running':state.data=previous_data
    server=LocalHTTPServer(('127.0.0.1',args.port),make_handler(state,args))
    print(f'Preview ready at http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:state.cancel.set()
    finally:server.server_close()


if __name__=='__main__':main()
