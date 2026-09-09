"""Validate geometry across lanes and summarize measured timing boundaries."""
import argparse
import collections
import hashlib
import json
import statistics
from pathlib import Path

LABELS = {'flat-opt1': 'opt1 · Cycles 64', 'flat-optNEW': 'optNEW · Cycles 8',
          'recipe-optNEW': 'Recipe · Cycles 8', 'recipe-eevee': 'Recipe · Eevee full size',
          'recipe-interactive': 'Recipe · Eevee fast preview'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    groups = collections.defaultdict(list)
    first = collections.defaultdict(list)
    raw, reference, max_error = [], None, 0
    for path in sorted(args.directory.glob('*/results.json')):
        result = json.loads(path.read_text())
        assert result['before_flatten'] == result['after_flatten'], path
        lane = result['mode'] + '-' + result['profile']
        groups[lane].extend(result['runs'][1:])
        first[lane].append(result['runs'][0]['through_png_seconds'])
        geometry = json.loads(path.with_name('geometry-validation.json').read_text())
        if reference is None:
            reference = geometry
        assert geometry.keys() == reference.keys(), 'Different scene object identities'
        for name, actual in geometry.items():
            expected = reference[name]
            for field in ('type', 'vertices', 'faces', 'materials', 'energy'):
                assert actual[field] == expected[field], (name, field)
            error = max(abs(a - b) for a, b in zip(actual['matrix'], expected['matrix']))
            max_error = max(max_error, error)
        raw.append({'run': path.parent.name, **result})
    assert len(groups) == 5 and all(len(rows) == 10 for rows in groups.values()), 'Expected ten edits per lane'
    assert max_error < 1e-5, ('Transform mismatch', max_error)
    medians = {lane: statistics.median(row['through_png_seconds'] for row in rows) for lane, rows in groups.items()}
    lanes = []
    for lane, label in LABELS.items():
        rows = groups[lane]
        times = sorted(row['through_png_seconds'] for row in rows)
        lanes.append({'id': lane, 'label': label, 'count': len(rows), 'median_seconds': medians[lane],
                      'min_seconds': min(times), 'max_seconds': max(times),
                      'apply_seconds': statistics.median(row['apply_seconds'] for row in rows),
                      'render_seconds': statistics.median(row['render_seconds'] for row in rows),
                      'png_seconds': statistics.median(row['png_seconds'] for row in rows),
                      'first_in_process_seconds': first[lane],
                      'speedup_opt1': medians['flat-opt1'] / medians[lane],
                      'speedup_optNEW': medians['flat-optNEW'] / medians[lane]})
    root = Path(__file__).resolve().parents[2]
    sources = list((root / 'skills/blender-fast/scripts/scene_recipe').rglob('*.py')) + list(Path(__file__).parent.glob('*.py'))
    result = {'scope': 'Ten warm semantic revisions per lane across two persistent processes, five edits per process. Each image newly rendered. Median apply-through-PNG excludes authoring, startup, initial render, geometry equivalence checks and blend saving. Processes run sequentially in seeded shuffled order. OS/driver caches, thermal conditions and unrelated system activity were not controlled.',
              'geometry_validation': {'objects': len(reference), 'max_transform_abs_error': max_error,
                  'same_object_ids_types_face_vertex_counts_material_colors_light_energies': True,
                  'unchanged_initial_geometry_fingerprint': True},
              'lanes': lanes, 'runs': raw,
              'source_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'lanes': lanes, 'geometry_validation': result['geometry_validation']}, indent=2))


if __name__ == '__main__':
    main()
