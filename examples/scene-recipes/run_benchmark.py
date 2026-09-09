"""Queue isolated GPU jobs; no concurrent lane rendering or fabricated live timings."""
import argparse
import json
import random
import subprocess
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--blender', required=True)
    p.add_argument('--scene', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--edits', type=int, default=10)
    p.add_argument('--repetitions', type=int, default=1)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    jobs = [(repeat, profile, mode) for repeat in range(args.repetitions) for profile, mode in
            [('opt1', 'flat'), ('optNEW', 'flat'), ('optNEW', 'recipe'), ('eevee', 'recipe'), ('interactive', 'recipe')]]
    random.Random(91026).shuffle(jobs)
    results = []
    for repeat, profile, mode in jobs:
        lane = args.output / f'r{repeat}-{mode}-{profile}'
        lane.mkdir(exist_ok=True)
        command = [args.blender, '--background', str(args.scene.resolve()), '--python-exit-code', '1',
                   '--python', str(Path(__file__).with_name('benchmark_worker.py')), '--',
                   '--profile', profile, '--mode', mode, '--output', str(lane), '--edits', str(args.edits)]
        print('START ' + lane.name, flush=True)
        started = time.perf_counter()
        with (lane / 'process.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        row = {'lane': lane.name, 'process_seconds': time.perf_counter() - started}
        results.append(row)
        (args.output / 'processes.json').write_text(json.dumps(results, indent=2) + '\n')
        print('COMPLETE ' + json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
