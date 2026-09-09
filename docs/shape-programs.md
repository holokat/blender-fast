# Local shape language and teaching experiment

The new path replaces some repeated Python authoring with executable construction lessons. It can compose arches, branching structures, curved spans, revolved profiles, window arrays and other combinations into editable Blender scenes. An agent still chooses the composition and writes unfamiliar shapes.

The local implementation includes a bounded data language, an incremental Blender compiler, eight teaching lessons, a fitted 1,072-parameter lesson selector, a training-pair exporter, and a reusable preview page. It uses existing Python, NumPy and Blender installations. No cloud training, new model downloads or paid services were used.

![Tidal conservatory, rendered in Blender](tidal-conservatory.png)

## What was measured

The conservatory has 25 assemblies, 1,305 Blender objects, 41,972 mesh faces and 35 shared mesh datablocks. It uses eight lessons and six new JSON definitions. All geometry operations were implemented before scene composition; the later visual revision changed camera framing and added a clock support using the existing `beam` operation. No new asset-specific Python was needed for those objects.

Hardware: Apple M2 Max, 30-core GPU. Blender 5.2.0 LTS. Cycles used Metal GPU only, MetalRT Auto, GPU OpenImageDenoise, persistent data, adaptive sampling and the existing scene-recipe profiles. All renders ran sequentially.

Three measured trials each built a new isolated scene and all geometry again. A tree-height parameter and the program hash changed between trials. The same Blender process had already rendered a separate warmup scene through all three profiles. The final images were newly rendered, not retrieved from an image cache.

| Milestone from prepared program | Median cumulative time, three trials |
| --- | ---: |
| Validate and construct geometry | 0.315 s |
| Eevee 4 preview, 800 × 550 | 0.517 s |
| Cycles 8 preview, 1600 × 1100 | 2.255 s |
| All three profiles and editable save | 6.750 s |

The three complete totals were 6.775, 6.187 and 6.750 seconds. The median Cycles 64 render stage itself took 4.203 seconds. The table uses medians of cumulative measurements; do not sum independent medians to reconstruct a run.

The initial run in a separate process took 24.612 seconds from prepared program through all renders and save: 0.188 seconds to validate/build, 5.644 seconds for Eevee, 13.223 seconds for the first Cycles frame, and 5.507 seconds for Cycles 64. Renderer startup affects the first frame, so the higher sample count was faster in that sequence. A later camera correction and clock support mean the initial and warmed runs are not a strict fixed-scene cold/warm comparison.

These results **do not demonstrate ten-second prompt-to-finished-art generation**. The observed checkpoint through writing and composing the first valid layout was 128.290 seconds, excluding earlier planning and all compiler/lesson development. Later visual correction and review were additional work. This scene and the earlier beach town differ, so that interval does not establish a controlled authoring speedup over the beach generator.

`opt1` and `optNEW` retain their existing rendering settings. The new contribution is a more composable authoring layer and reuse across requests. This experiment does not establish a new equivalent-quality rendering speedup over those profiles.

Raw evidence: [three fresh warm trials](../benchmarks/shape-programs/benchmark.json), [initial cold run](../benchmarks/shape-programs/cold-run.json), [authoring checkpoint](../benchmarks/shape-programs/authoring.json), [Blender checks](../benchmarks/shape-programs/blender-checks.json), and [saved-scene reopen check](../benchmarks/shape-programs/reopen-check.json).

## What was taught

The eight original lessons adapt construction patterns already used in the dungeon and beach examples, with new sweep and surface representations where needed. Their JSON includes provenance, complete executable programs, and separate training/test captions. The geometry is procedural and all code, original artwork, lessons and selector weights are covered by the repository's MIT license.

A local softmax classifier was fitted using 40 agent-written descriptions. It has 133 vocabulary features and 1,072 fitted parameters. Training ran for 600 gradient steps in 0.015 seconds after imports. All 16 held-out descriptions were classified correctly. A simpler cosine-centroid baseline also achieved 16/16, so a benefit from the fitted classifier has not been established. The evaluation covers new wording for known lessons, not unseen object categories. Because the evaluation also selects the inference path, future tuning needs a new untouched evaluation set.

The selector retrieves likely construction lessons. The LLM composes and adapts them. It does not predict novel geometry, train Blender itself, or implement the larger proposed joint image-and-geometry model. The exporter produces 56 prompt/program pairs with provenance and split labels as a starting point for further local teaching. [Training evidence](../benchmarks/shape-programs/selector-training.json).

## Reproduce and extend

Read the [agent language and teaching guide](../skills/blender-fast/references/shape-programs.md) for the schema, supported operations, mutation scope and local teaching commands.

```sh
mkdir -p work/conservatory
python3 skills/blender-fast/scripts/shape_program/teaching.py compose \
  examples/shape-programs/tidal-conservatory.layout.json --output work/program.json
python3 skills/blender-fast/scripts/shape_program/cli.py work/program.json --validate
blender --background --python-exit-code 1 \
  --python skills/blender-fast/scripts/shape_program/cli.py -- \
  work/program.json --output work/conservatory
```

For fresh builds in an already warmed renderer:

```sh
blender --background --python-exit-code 1 \
  --python examples/benchmark_shape_program.py -- work/program.json work/shape-benchmark
```

The benchmark is scoped to the conservatory layout and changes its `front_tree` parameter. It creates three new scenes, reports each timing, saves the final trial and verifies that reopening the saved active scene permits a no-op compiler update. Blender startup and warmup are excluded from the three trial totals but warmup measurements remain in the evidence.

Validation commands:

```sh
python3 -m unittest discover -s tests -v
node tests/test_timeline.mjs
blender --background --python-exit-code 1 --python tests/shape_blender_checks.py
```

Blender checks cover all eight lesson meshes, isolation of an unrelated object, unchanged object/mesh identity, transform-only edits, attachment matrices with shear, invalid-input isolation, scoped rebuilding, and material-default restoration. Successful structural checks do not replace visual review.

## Reuse the preview server

The new page is `preview/recipe-viewer/shapes.html`. It uses the existing recipe viewer's styles and static server. Serve the output directory under `shape-output/` within the viewer's static root, or pass another same-origin directory with `?data=...`. Keep generated media out of Git. For example, after generating the scene and ensuring the destination does not already exist:

```sh
ln -s "$(pwd)/work/conservatory" preview/recipe-viewer/shape-output
```

On the running local recipe server, visit `http://127.0.0.1:8772/shapes.html`. The page reads `result.json`, shows progressive completed renders, switches between saved quality levels, and links to the source and editable save. It does not start a new render when switching saved quality. The archive and beach pages remain separate.

| Before | After |
| --- | --- |
| Existing archive/beach navigation | Added a shape-lessons destination on the same server |
| No viewer for generic shape-program output | Added a rendered-quality selector, source/save links, scoped stage timings and scene inventory |
| Shared viewer styles | Reused sentence case, tabular numbers, image outlines and 42-pixel controls; added larger spacing between timing and teaching sections |

The next useful benchmark is a set of previously unseen briefs, starting the clock at prompt receipt. Record coverage misses, newly authored definitions, corrections and user-rated visual quality. That will determine whether lesson reuse reduces the remaining authoring time, and whether a larger locally runnable model is justified.
