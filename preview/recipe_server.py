"""Loopback recipe preview with push notifications and a latest-request queue."""
import argparse
import functools
import http.server
import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/blender-fast/scripts'))
from scene_recipe.schema import validate


class Controller:
    def __init__(self, blender, scene, cache):
        self.cache = cache
        self.condition = threading.Condition()
        self.pending = None
        self.state = {'status': 'ready', 'revision': 0}
        self.frames = {}
        self.process = subprocess.Popen([blender, '--background', str(scene), '--python-exit-code', '1',
            '--python', str(ROOT / 'skills/blender-fast/scripts/scene_recipe/live_worker.py'), '--', str(cache)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.run, daemon=True).start()

    def publish(self, result):
        with self.condition:
            self.state = result | {'revision': self.state['revision'] + 1}
            self.condition.notify_all()

    def submit(self, payload):
        with self.condition:
            if self.process.poll() is not None:
                raise ValueError('Blender worker exited; restart the preview server')
            job = payload | {'id': uuid.uuid4().hex, 'submitted_unix': time.time()}
            self.pending = job
            self.condition.notify_all()
            return job['id']

    def run(self):
        with (self.cache / 'worker.log').open('a') as log:
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.pending is not None)
                    job, self.pending = self.pending, None
                self.publish({'id': job['id'], 'status': 'rendering'})
                try:
                    self.process.stdin.write(json.dumps(job) + '\n')
                    self.process.stdin.flush()
                    for line in self.process.stdout:
                        log.write(line)
                        log.flush()
                        if not line.startswith('RECIPE_FRAME '):
                            continue
                        result = json.loads(line[len('RECIPE_FRAME '):])
                        result['request_through_worker_seconds'] = time.time() - job['submitted_unix']
                        if result.get('frame'):
                            self.frames[result['frame']] = result['id']
                        self.publish(result)
                        break
                    else:
                        raise RuntimeError('Blender worker exited')
                except Exception as error:
                    self.publish({'id': job['id'], 'status': 'error', 'message': str(error)})
                    return

    def close(self):
        self.process.terminate()
        self.process.wait(timeout=15)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blender', required=True)
    p.add_argument('--scene', type=Path, required=True)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--port', type=int, default=8772)
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    controller = Controller(args.blender, args.scene.resolve(), args.cache.resolve())
    frontend = ROOT / 'preview/recipe-viewer'

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def respond(self, value, status=200):
            self.send_bytes(json.dumps(value).encode(), 'application/json', status)

        def send_bytes(self, data, mime, status=200):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != '/api/render':
                return self.respond({'error': 'Not found'}, 404)
            if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{args.port}', f'http://localhost:{args.port}'):
                return self.respond({'error': 'Origin rejected'}, 403)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length < 65536:
                    raise ValueError('Invalid request size')
                request = json.loads(self.rfile.read(length))
                validate(request['recipe'])
                if request.get('profile') not in ('opt1', 'optNEW', 'eevee', 'interactive'):
                    raise ValueError('Unknown profile')
                if not isinstance(request.get('save', False), bool):
                    raise ValueError('save must be a boolean')
                job = controller.submit({'recipe': request['recipe'], 'profile': request['profile'], 'save': request.get('save', False)})
                self.respond({'id': job})
            except (ValueError, KeyError, TypeError) as error:
                self.respond({'error': str(error)}, 400)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == '/api/events':
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                revision = -1
                try:
                    while True:
                        with controller.condition:
                            controller.condition.wait_for(lambda: controller.state['revision'] != revision, timeout=15)
                            state = dict(controller.state)
                        revision = state['revision']
                        self.wfile.write(('data: ' + json.dumps(state) + '\n\n').encode())
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
            if url.path == '/api/status':
                return self.respond(controller.state)
            if url.path in ('/recipe.json', '/summary.json', '/reference.png', '/initial.png'):
                path = args.data / url.path[1:]
                if not path.is_file():
                    return self.respond({'error': 'Not available'}, 404)
                return self.send_bytes(path.read_bytes(), 'image/png' if path.suffix == '.png' else 'application/json')
            if url.path.startswith('/frames/'):
                name = url.path.split('/')[-1]
                wanted = parse_qs(url.query).get('id', [''])[0]
                if controller.frames.get(name) != wanted or name not in ('frame-0.png', 'frame-1.png', 'frame-2.png'):
                    return self.respond({'error': 'Superseded frame'}, 409)
                return self.send_bytes((args.cache / name).read_bytes(), 'image/png')
            if url.path == '/scene-live.blend' and (args.cache / 'scene-live.blend').exists():
                return self.send_bytes((args.cache / 'scene-live.blend').read_bytes(), 'application/octet-stream')
            return super().do_GET()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(Handler, directory=str(frontend)))
    print(f'Recipe preview http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    finally:
        controller.close()
        server.server_close()


if __name__ == '__main__':
    main()
