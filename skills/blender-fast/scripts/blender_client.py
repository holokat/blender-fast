"""Dependency-free client for the Blender Lab null-delimited TCP bridge."""
import argparse
import json
import math
import socket
import time
from pathlib import Path

MAX_REQUEST_BYTES = 10 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
DEFAULT_ADDON = 'bl_ext.lab_blender_org.mcp'


class BridgeError(RuntimeError):
    """A complete Blender error response, possibly after partial script execution."""


class ExecutionUncertain(BridgeError):
    """Request transmission started, but completion cannot be established. Never retry blindly."""


def execute(code, *, host='127.0.0.1', port=9876, timeout=60, max_response=MAX_RESPONSE_BYTES):
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('This helper is for a verified local Blender Lab bridge only')
    if not isinstance(code, str):
        raise TypeError('code must be text')
    if not math.isfinite(timeout) or timeout <= 0 or max_response < 1:
        raise ValueError('Use a positive finite timeout and response limit')
    payload = json.dumps({'type': 'execute', 'code': code, 'strict_json': True}).encode('utf-8') + b'\0'
    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError('Request exceeds the Blender Lab bridge 10 MiB limit')
    started = time.perf_counter()
    deadline = started + timeout
    # Connection failures happen before code is transmitted.
    with socket.create_connection((host, port), timeout=timeout) as connection:
        try:
            connection.sendall(payload)
            data = bytearray()
            while b'\0' not in data:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    raise TimeoutError('Overall request deadline exceeded')
                connection.settimeout(remaining)
                chunk = connection.recv(min(65536, max_response + 1 - len(data)))
                if not chunk:
                    raise ConnectionError('Connection ended before the response delimiter')
                data.extend(chunk)
                if len(data) > max_response:
                    raise ValueError('Response exceeds the configured limit')
            raw, extra = data.split(b'\0', 1)
            if extra:
                raise ValueError('Unexpected trailing protocol data')
            response = json.loads(raw)
            if not isinstance(response, dict) or response.get('status') not in ('ok', 'error'):
                raise ValueError('Unexpected bridge response')
            if response['status'] == 'ok' and not isinstance(response.get('result'), dict):
                raise ValueError('Bridge result must be a JSON object')
        except (OSError, ValueError) as exc:
            raise ExecutionUncertain('Blender may have executed the request. Inspect its state before retrying. ' + str(exc)) from exc
    if response['status'] == 'error':
        raise BridgeError(str(response.get('message', 'Blender execution failed')))
    return response['result'], (time.perf_counter() - started) * 1000


def status(*, addon=DEFAULT_ADDON, **connection):
    code = f'''import bpy
p = bpy.context.preferences.addons.get({addon!r})
result = {{'blender_version': bpy.app.version_string, 'background': bpy.app.background,
          'addon': {addon!r}, 'addon_enabled': p is not None, 'scene_objects': len(bpy.context.scene.objects)}}
if p:
 keys = ('timer_interval_active','timer_interval_idle','timer_interval_idle_delay')
 result['polling'] = {{k:getattr(p.preferences,k) for k in keys}}
 result['limits'] = {{k:[p.preferences.bl_rna.properties[k].hard_min,p.preferences.bl_rna.properties[k].hard_max] for k in keys}}
'''
    return execute(code, **connection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=9876)
    parser.add_argument('--timeout', type=float, default=60)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('status')
    run = sub.add_parser('execute')
    run.add_argument('--file', type=Path, required=True, help='Read a Python script and send its contents to Blender')
    args = parser.parse_args()
    options = dict(port=args.port, timeout=args.timeout)
    result, elapsed = status(**options) if args.action == 'status' else execute(args.file.read_text(encoding='utf-8'), **options)
    print(json.dumps({'result': result, 'round_trip_ms': elapsed}, indent=2))


if __name__ == '__main__':
    main()
