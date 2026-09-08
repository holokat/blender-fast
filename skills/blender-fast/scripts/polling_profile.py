"""Inspect, apply or restore supported Blender Lab polling preferences."""
import argparse
import json
import math
from pathlib import Path
from blender_client import DEFAULT_ADDON, execute, status

FAST = {'timer_interval_active': .05, 'timer_interval_idle': .25, 'timer_interval_idle_delay': 5.0}


def validate_values(values, limits):
    if set(values) != set(FAST):
        raise ValueError('Unexpected or missing polling keys')
    for key, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'Invalid numeric preference: {key}')
        if not limits[key][0] - 1e-6 <= value <= limits[key][1] + 1e-6:
            raise ValueError(f'{key} is outside the installed add-on limits')


def write_values(values, *, addon=DEFAULT_ADDON, persist=False, **connection):
    code = f'import bpy\np=bpy.context.preferences.addons[{addon!r}].preferences\n'
    code += '\n'.join(f'p.{key}={value!r}' for key,value in values.items())
    if persist:
        code += '\nassert "FINISHED" in bpy.ops.wm.save_userpref(), "Preferences were not saved"'
    code += '\nresult={"polling":{' + ','.join(f'{key!r}:p.{key}' for key in values) + '}}'
    result, _ = execute(code, **connection)
    if any(abs(result['polling'][key] - value) > 1e-6 for key, value in values.items()):
        raise RuntimeError('Preference readback did not match the requested values')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=9876)
    parser.add_argument('--addon', default=DEFAULT_ADDON)
    parser.add_argument('action', choices=['status', 'apply', 'restore'])
    parser.add_argument('--snapshot', type=Path, help='Required for apply/restore; apply refuses to overwrite this file')
    parser.add_argument('--persist', action='store_true', help='Save Blender preferences, including other pending preference edits')
    args = parser.parse_args()
    connection = dict(port=args.port)
    current, _ = status(addon=args.addon, **connection)
    if not current['addon_enabled']:
        parser.error('The expected Blender Lab add-on is not enabled')
    if args.action == 'status':
        print(json.dumps(current, indent=2));return
    if not args.snapshot:
        parser.error('--snapshot is required for apply/restore')
    if args.action == 'apply':
        # Preserve settings that are already faster than the tested profile.
        values = dict(FAST)
        for key in ('timer_interval_active', 'timer_interval_idle'):
            values[key] = min(values[key], current['polling'][key])
        values['timer_interval_idle_delay'] = current['polling']['timer_interval_idle_delay']
        validate_values(values, current['limits'])
        snapshot = {'schema_version':1, 'addon':args.addon, 'port':args.port,
                    'blender_version':current['blender_version'], 'polling':current['polling']}
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        with args.snapshot.open('x', encoding='utf-8') as stream:
            json.dump(snapshot, stream, indent=2);stream.write('\n')
    else:
        snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
        if snapshot.get('schema_version') != 1 or snapshot.get('addon') != args.addon or snapshot.get('port') != args.port:
            raise ValueError('Snapshot does not match the selected local add-on and port')
        values = snapshot['polling']
        validate_values(values, current['limits'])
    result = write_values(values, addon=args.addon, persist=args.persist, **connection)
    print(json.dumps({'action':args.action, 'persisted':args.persist, **result}, indent=2))


if __name__ == '__main__':
    main()
