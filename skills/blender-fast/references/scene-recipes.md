# Compact scene recipes

Use a recipe when the available procedural factories fit the requested scene. The LLM supplies composition, transforms, materials and lighting. Tested functions generate geometry. For unfamiliar shapes, extend a focused factory or use the existing batched Python path. Preserve the requested objects and art direction.

The library contains 23 architectural, furnishing and instrument types. It is not an arbitrary text-to-3D model. Seeds change supported procedural variation, not the category of object. Each assembly remains an editable collection, with mesh parts parented to a named root. Translation, yaw and scale edit that root; a type or seed change rebuilds the assembly.

## Recipe interface

Required root fields: `version: 1`, `title`, integer `seed`, and `assemblies`. Each assembly needs a unique lowercase `id`, supported `type`, and `at: [x,y,z]` in Blender coordinates. Optional `yaw` is degrees about Z, `scale` is a positive three-component vector, and `seed` overrides its deterministic seed.

Supported factories: `chamber`, `portal`, `staircase`, `forge`, `throne`, `ritual`, `waterwell`, `collapsed_passage`, `alchemy`, `library`, `armory`, `supplies`, `hoist`, `organ`, `cage`, `sarcophagus`, `treasure`, `map_table`, `ossuary`, `chandelier`, `orrery`, `reactor`, `telescope`.

The chamber foundation spans 33 × 25 units. The installed [celestial archive recipe](../assets/celestial-archive.json) supplies a tested arrangement of twenty distinct types. Factory modules are under `scripts/scene_recipe/factories`; inspect the relevant module when extending an asset. `schema.py` lists accepted material names and numeric bounds.

Optional `materials` maps names to `color: [r,g,b]`, `roughness`, `metallic` and/or `emission`. Colors use linear RGB from 0–1. Optional `camera` accepts `at`, `target` and `ortho_scale`. Optional `lighting` accepts `key`, `fill`, `rim` and `world` multipliers, plus exposure in stops. Omitted material/staging properties return to compiler defaults when reapplied.

Recipes contain data only. They cannot execute Python or load arbitrary asset paths. Unknown fields and factory names fail validation before scene mutations.

## Execute and revise

Resolve script paths from the installed skill. From the repository root, run the included example with:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python skills/blender-fast/scripts/recipe_cli.py -- \
  examples/scene-recipes/celestial-archive.json --output work/scene --profile optNEW
```

Outputs: `scene.blend`, `recipe.json`, `preview.png`, and `result.json`. Its timer starts inside the Python script and excludes Blender startup, agent authoring and visual review. Record those separately for prompt-to-done measurements.

In a persistent Blender process, with the skill's scripts directory on `sys.path`:

```python
from scene_recipe.compiler import apply
scene, result = apply(updated_recipe, owned_scene)
```

Pass the intended owned scene explicitly. Calling `apply(recipe)` without a scene creates a new isolated scene. Results list rebuilt, transformed and removed assemblies. The compiler does not clear unrelated scene contents. After uncertain bridge completion, inspect state before retrying.

Avoid assigning unchanged properties in extensions. Blender can mark data dirty even when an assignment looks identical. The compiler compares transforms, materials and staging before assignment, then updates the dependency graph once per transaction. Keep `bpy` mutation on Blender's main thread.

## Render choices

| Profile | Engine and quality | Use |
| --- | --- | --- |
| opt1 | Metal Cycles, GPU OIDN, persistent data, 64 samples, 1600 × 1100 | Existing baseline and higher-sample inspection |
| optNEW | Same Cycles configuration, 8 samples, 1600 × 1100 | Cycles preview |
| eevee | Eevee with ray tracing and fast GI, 16 samples, 1600 × 1100 | Full-size preview with different lighting |
| interactive | Eevee, 4 samples, 800 × 550 | Early feedback with less detail and more noise |

These are explicit experiment profiles. Cycles helpers currently select Metal and fail if no Metal GPU is available. Inspect and implement another backend on other hardware. Saving a `.blend` does not replace device-preference setup in another process. Respect the task's required final quality and resolution; the interactive image is not a quality-equivalent Cycles final.

For a first useful image, use the interactive profile when appropriate, inspect the lighting, and refine. For delivery, use the accepted renderer and quality. Keep the worker resident through an iteration group.

## Timing and live preview

Separate reusable library preparation, recipe authoring/corrections, compiler execution, rendering, image display, and saving. Count new-factory work and coverage failures. Executing prepared JSON quickly does not establish prompt-to-done latency. The old nine-minute dungeon preparation interval was not a pure text-generation measurement.

The repository's `examples/scene-recipes/run_benchmark.py` compares per-part batch revisions with recipe-root revisions and explicit render profiles. Its baseline keeps identity parents to represent nonuniform affine transforms without changing geometry. Geometry equivalence is checked before accepting timings.

The optional `preview/recipe_server.py` provides a loopback live image viewer with a persistent Blender process, pushed completion events and coalesced pending requests. It does not interrupt an in-flight GPU render or claim continuous real-time frame rates. Request-to-image time includes queueing and transport; renderer time does not. Library development is an upfront cost, and measurements from unrelated scenes do not establish a universal creation speedup.
