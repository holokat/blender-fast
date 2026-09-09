# Shape programs and executable lessons

Use this path to compose unfamiliar scenes from reusable construction patterns without writing a new Python factory for every object. Prefer the existing scene recipes when their finished assets fit better. The shape language supports stylized procedural construction; it does not cover arbitrary sculpting, characters, simulations, or every Blender modifier.

## Agent workflow

1. Resolve `scripts/shape_program` and `assets/shape-lessons` relative to this skill. Run `teaching.py suggest "<brief>"` for construction hints, then inspect only the relevant lesson JSON files. The selector is small and limited to eight known lessons. Its scores are uncalibrated hints, and no match is a reason to author a new definition.
2. Author a short layout with `title` and `assemblies`. Reference lesson definitions by `use`; add unfamiliar shapes in `definitions` using the operations below. Set art direction through `palette`, `camera`, and `lighting`. Existing lessons are examples to adapt, not mandatory scene contents.
3. Run `teaching.py compose layout.json --output program.json`, then `cli.py program.json --validate`. Composition resolves called definitions and material overrides into a standalone program. Programs have no external asset dependencies.
4. Execute the prepared program in an existing compatible warm Blender process when possible. Use `shape_program.compiler.apply(program)` to create an isolated scene, or `apply(program, owned_scene)` for revisions. Keep the returned scene and stable assembly IDs. Keep `bpy` on the main thread.
5. For progressive feedback, use the existing `scene_recipe.staging.configure`: `interactive` (Eevee 4 at 800 × 550), then `optNEW` (Cycles 8 at 1600 × 1100), then `opt1` (Cycles 64 at the same resolution). These names are quality profiles, not different shape compilers. Respect the user's chosen renderer and final quality.
6. Review the actual images and framing. Save the editable scene and its source program. If a reusable construction method worked well, add an executable lesson with distinct training and evaluation captions, render it, and retrain the local selector. Record failures as well as successful examples.

From the repository root:

```sh
python3 skills/blender-fast/scripts/shape_program/teaching.py suggest \
  "A conservatory with curved bridges and radial glass roofs"
python3 skills/blender-fast/scripts/shape_program/teaching.py compose \
  examples/shape-programs/tidal-conservatory.layout.json --output work/program.json
python3 skills/blender-fast/scripts/shape_program/cli.py work/program.json --validate
blender --background --python-exit-code 1 \
  --python skills/blender-fast/scripts/shape_program/cli.py -- \
  work/program.json --output work/conservatory
```

Create `work/` first. The CLI renders the three profiles sequentially and saves `scene.blend`, `program.json`, `result.json`, and PNGs. `--profiles interactive` limits a run to the first preview. CLI validation, composition, export and selector inference use the standard library; retraining uses NumPy. The current rendering configuration requires Metal, as described in [scene-recipes.md](scene-recipes.md). It does not save global Blender preferences.

`--worker` keeps the same Blender process alive while its stdin pipe stays open. After `SHAPE_RESULT`, send one line of JSON with `program` and `profile`. Read the matching `SHAPE_FRAME` response, which references `live.png`; keep one request in flight. An interactive shell pipe that reaches EOF ends the worker. For richer integration, call `apply` and the rendering helpers in an existing worker instead of starting another server.

## Language version 1

A full program has `version: 1`, `title`, `palette`, `definitions`, and `assemblies`. Optional root fields are `seed`, `camera`, and `lighting`. Identifiers use lowercase letters, digits, and underscores, starting with a letter, up to 48 characters. Geometry uses Blender Z-up coordinates and rotation degrees in XYZ order. Colors are linear RGB, not sRGB hex values.

A definition has `params` (numeric defaults), `anchors` (named local points), and `nodes`. An assembly has a unique `id`, a definition `use`, numeric `args`, and optional `at`, `rotation`, `scale`, and `materials` bindings. `attach: {"to": "other_assembly.anchor"}` makes its transform relative to that anchor, including the parent's rotation and scale. Attachment cycles fail validation. Anchors are points with inherited orientation, not independently oriented sockets.

Common node fields: `op`, optional `name`, `at`, `rotation`, and positive `scale`. Set `material` on a primitive. A `call` can bind material names through `materials`. Group transforms apply to children.

| Operation | Fields and meaning |
| --- | --- |
| `box` | `size: [x,y,z]`, dimensions of a lightly beveled unit box |
| `sphere` | `size: [x,y,z]`, radii of a faceted sphere |
| `cylinder`, `cone` | `radius`, `height`, optional `segments`; centered on local Z, cone has a small tip cap |
| `ring` | `radius`, `tube`, optional `segments`; ring lies in XY |
| `beam` | `a`, `b`, `radius`, optional `segments` |
| `sweep` | `path` of 2–128 points, scalar or per-point `radii`, `segments`, optional `caps` |
| `lathe` | `profile` of 2–128 `[radius,z]` points, `segments`; capped revolved surface |
| `surface` | `vertices` and indexed polygon `faces`; author winding and topology deliberately |
| `text` | `text`, `size`, `depth`; centered Blender font curve in local XY |
| `group` | `children` under one transform |
| `repeat` | `count`, `children`, optional `index`, `step` and `turn` |
| `call` | `use`, optional `args` and `materials` |

A repeat transforms each child by index times `step` and `turn`. The index defaults to `i`; use different index names for nested repeats. Numeric expressions start with `=`, for example `"=radius*cos(i*pi/6)"`. Supported arithmetic: `+ - * / %`, unary signs, and `sin`, `cos`, `sqrt`, `abs`, `min`, `max`. `pi` is reserved. There is no Python evaluation, attribute access, code execution, asset loading, random function, or implicit AI operation. `seed` is only a numeric variable unless a definition uses it.

Parameter defaults are evaluated in declaration order. Call arguments are evaluated in the caller's environment; definitions receive that environment plus their parameters. Numeric values and intermediate arithmetic must be finite with magnitude at most one million. Primitive sizes have tighter bounds. See `validation.py` and `expand.py` for exact limits.

The expander limits source nodes, call depth, loop counts, traversal work, 12,000 parts, and one million estimated vertices. It validates structure and expands used definitions before touching Blender. An unused definition's numeric geometry is not evaluated until used. Surface index validity is checked; manifold topology, self-intersection and visual quality still need inspection. This is a bounded local construction format, not a security sandbox for running arbitrary Python.

## Revision and ownership behavior

Every new `apply(program)` creates a separate scene with owned assembly collections and named roots. The saved scene stores the source as `shape_json` and its hash as `shape_sha256`. `apply(program, scene)` rejects scenes without the compiler's ownership marker. It preserves unrelated objects, and never clears the user's scene as setup.

Unchanged geometry keeps object and mesh identity. Transform edits move only assembly roots. A changed definition or parameter rebuilds affected assemblies; removed IDs remove their owned collections. Material-only changes update shared materials without rebuilding geometry. Omitted properties reset to defaults. Full affine parent matrices preserve shear through nonuniform transforms and attachments.

Invalid expanded data causes no Blender mutation. Geometry replacements are staged before replacing existing collections. Runtime failures such as memory exhaustion are not a general transactional guarantee; inspect state after an uncertain result. Keep a saved scene for recovery.

## Teach locally

Each lesson file in `assets/shape-lessons` contains an `id`, `summary`, `provenance`, complete `program`, and `captions` with separate `train` and `test` lists. Add new lessons to a task-owned copy of the library, verify construction and render quality, then fit a selector and inspect the report before updating the installed library. Do not silently overwrite a user's library or label generated examples as human-approved.

```sh
python3 skills/blender-fast/scripts/shape_program/train_selector.py \
  --output work/selector.json --report work/selector-training.json
python3 skills/blender-fast/scripts/shape_program/teaching.py suggest \
  "A suspended lantern" --model work/selector.json
python3 skills/blender-fast/scripts/shape_program/teaching.py export \
  --output work/training-pairs.jsonl
```

Use `--library <task-library>` before the subcommand in `teaching.py`, or as a normal argument in `train_selector.py`, to teach a custom library. The trainer fits TF-IDF softmax weights with NumPy, compares a cosine-centroid baseline, and saves the better observed top-1 path, preferring softmax on a tie. This selection uses the small evaluation set and needs a new untouched test set for further tuning. A corpus hash rejects stale selectors. Training uses local CPU, no cloud account, model download or paid API.

The shipped selector has 1,072 parameters fitted on 40 agent-written captions. Both it and the baseline classified all 16 held-out captions correctly. That small within-category test does not establish broader generalization or a learned advantage over retrieval. The 56 exported prompt/program pairs retain split and provenance fields. Structural validation is recorded separately from visual approval. This is a lesson-selection model, not a model that generates novel 3D geometry from arbitrary text.

## Timing boundaries

Record prompt receipt, first valid authored program, geometry construction, renderer startup, preview, final rendering, saving, and visual review separately. Do not time only the shell write and call it LLM authoring: that misses the model's output generation. New lesson development is an upfront cost, and a new unsupported shape can still require minutes of work.

On the tested M2 Max, three fresh 1,305-object conservatory builds in a warmed process reached Eevee feedback in a median 0.517 s, Cycles 8 in 2.255 s, and all three profiles plus save in 6.750 s. Those are cumulative times from prepared-program execution. They exclude authoring, process startup and the preceding warmup. The initial separate cold run took 24.612 s. Its framing and one clock support were subsequently corrected, so this is not a controlled cold/warm speedup ratio. See the public [experiment report](https://github.com/holokat/blender-fast/blob/main/docs/shape-programs.md).
