# Rendering performance

Bridge latency, geometry construction and image rendering are separate timing stages. Batching Python commands does not by itself make Cycles trace rays faster.

## Selected profile

For the verified M2 Max workflow, use Metal GPU only, MetalRT Auto, GPU OpenImageDenoise and persistent data for repeated rendering. Combine this with the skill's batched direct-data edits and supported faster polling. Keep the requested sample limit, resolution, camera, lights and essential geometry unchanged. Inspect the selected backend, actual enabled devices, scene device and denoiser separately. For other hardware, detect support and benchmark an equivalent profile rather than copying Metal settings.

The combined jet experiment measured one build plus four renders at 76.40 s versus 9.71 s. Its warm render median improved from 3.96 s to 1.79 s; the much larger construction ratio applies only to bridge object creation. [Combined benchmark and live preview](https://github.com/holokat/blender-fast/blob/main/docs/live-comparison.md). Do not multiply construction and render speedups. A job's total improvement depends on its actual stage durations and number of renders.

For a live comparison on one GPU, measure lanes sequentially and keep live monitoring separate from synchronized replay. Drive preview geometry from acknowledged build events, expose images only after their render completes, and distinguish first-in-process renders from warm repeats. Avoid presenting a recorded replay as simultaneous execution.

## Preserve quality while avoiding repeated work

For Cycles, inspect both the selected compute backend and the scene's `cycles.device`. An installed GPU is not evidence that the scene uses it. Select an available backend appropriate to the machine, enable its actual devices, and confirm the completed render's device. The house initially saved CPU as its scene device even though its separate render script selected Metal; this is why the saved scene and the render invocation both matter.

Check the denoiser device separately. On supported hardware, OpenImageDenoise can run on the GPU. The measured M2 Max render used GPU path tracing but CPU denoising until `denoising_use_gpu` was enabled. Compare speed and the resulting image because hardware support and numerical output can differ.

For repeated renders and animations with reusable scene data, test `scene.render.use_persistent_data = True`. It retains render data for later frames or re-renders in the same Blender process. It consumes more memory, provides no retained cache after process exit, and does not eliminate work for scene data that changed. Report warm results separately from startup and first-render costs.

Reuse mesh and material data where the asset allows it. Use appropriate geometry detail and texture sizes, but check shadow-casting and reflected objects before culling anything outside the camera. Avoid reducing essential geometry merely to improve a benchmark.

## Quality and workflow tradeoffs

The [scene recipe profiles](scene-recipes.md) provide a progressive default: Eevee 4 at 800 × 550 for initial feedback, then Cycles 8 and Cycles 64 at 1600 × 1100 in the same process. These named profiles (`interactive`, `optNEW`, `opt1`) trade image quality for latency. They do not replace the user's required renderer, samples or resolution. Reuse the preview server and distinguish saved-image selection from a newly rendered revision. See [the measured workflow](https://github.com/holokat/blender-fast/blob/main/docs/fast-workflow.md).

Adaptive sampling stops work in pixels that have converged. Noise thresholds, minimum samples and maximum samples jointly affect the result. Denoising may make a lower sample limit acceptable; inspect fine details, contact shadows and any animation for flicker. Do not treat a lower sample count as a quality-preserving change without checking it.

Eevee can suit fast previews and stylized final images when its lighting and effects meet the brief. It is an engine choice with a different rendering approach. Keep the user's requested renderer and approve the actual visual result before treating it as a replacement.

For static lighting or mostly-static animations, consider baking lighting/material effects or reusing rendered layers when the scene permits it. These choices move computation into an earlier stage and can become invalid when lighting, cameras, geometry, reflections or shadows change. They were not benchmarked on the house.

## Threads, async and multiple GPUs

Cycles already parallelizes work on the selected GPU. Additional Python threads do not create more GPU resources, and Blender's Python API is not thread-safe. Queue independent work or prepare the next job in a separate process when that can overlap useful CPU work with rendering. This can improve throughput without accelerating the current frame; simultaneous renders on one GPU can also compete for compute and memory.

A multi-GPU strategy requires actual supported devices. The test process exposed one Metal GPU on the M2 Max. More GPU cores within that device are already used by the renderer; they are not separate GPUs to schedule manually. On systems with multiple supported GPUs, verify the renderer's device configuration and memory limits. For animation, independent frames can also be distributed across machines, with explicit cost and data-transfer authorization if external services are involved.

CPU plus GPU and MetalRT are hardware-dependent options. Benchmark them instead of assuming more enabled devices or a forced ray-tracing option is faster. Apple's M3 introduced hardware-accelerated ray tracing to Mac; the M2 Max predates that hardware. A MetalRT preference does not add missing hardware units.

## Measured render results

Three warm repeats per configuration, 64 sample limit, adaptive sampling at the existing threshold (approximately 0.01), GPU path tracing, OpenImageDenoise, identical geometry and a 1,400 × 1,400 output:

| Configuration | Median |
| --- | ---: |
| CPU denoising, persistent data off | 9.168 s |
| GPU denoising, persistent data off | 6.218 s |
| GPU denoising, persistent data on | 4.109 s |

Each configuration had an excluded warmup. The three profiles ran in the listed order, so order and hardware load may affect the comparison. The full-sample optimized image was inspected visually; no sample or resolution reduction was used. CPU and GPU denoising are not guaranteed to produce bit-identical pixels.

A separate alternating-order sample experiment measured 8.143 s at 64 samples and 6.331 s at 32, a 22% reduction. Those results used CPU denoising and no persistent data. Do not mix baselines from these different experiments when calculating a speedup. The 32-sample preview was visually close for this stylized still; it does not establish acceptable quality for arbitrary assets or animation.

## Additional Metal device experiment

With GPU denoising and persistent data enabled, the same 64-sample scene produced these medians from three warm renders per profile:

| Configuration | Median | Excluded warmup |
| --- | ---: | ---: |
| Metal GPU only, MetalRT Auto | 3.880 s | 5.286 s |
| CPU plus Metal GPU, MetalRT Auto | 7.111 s | 10.285 s |
| Metal GPU only, MetalRT On | 4.251 s | 101.700 s |

GPU-only Auto was fastest among these tested choices. Enabling the CPU did not help this workload, and forcing MetalRT was slower than Auto. The long MetalRT warmup matters for short sessions even though it is excluded from the warm-render median. These are results from one M2 Max and one scene, not a universal device recommendation. Profiles ran sequentially; shared system load and thermal effects were not controlled experimentally. See the raw `metal-comparison.json` in the repository benchmarks.

## Run a comparison

Run these helpers in a separate background Blender process. They do not save the `.blend` or user preferences, and do not apply a persistent rendering profile.

```sh
blender --background work/house/house.blend --python skills/blender-fast/scripts/render_compare.py -- --device METAL --samples 64 32 --output work/sample-comparison
blender --background work/house/house.blend --python skills/blender-fast/scripts/render_tuning.py -- --device METAL --output work/render-tuning
blender --background work/house/house.blend --python skills/blender-fast/scripts/metal_compare.py -- --output work/metal-comparison
```

The first two helpers accept an available device backend. `metal_compare.py` is specific to a Mac with a Metal device and compares GPU alone, CPU plus GPU, and forced MetalRT when exposed by the installed build. Inspect every emitted JSON result, including configuration errors. For animation, validate multiple representative frames, temporal stability, memory use and output correctness before adopting an optimization.

Sources: [GPU setup](https://docs.blender.org/manual/en/5.2/render/cycles/render_settings/index.html), [sampling and denoising](https://docs.blender.org/manual/en/4.2/render/cycles/render_settings/sampling.html), [persistent data](https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/performance.html), [Blender threading](https://docs.blender.org/api/5.0/info_gotchas_threading.html), [Apple's M3 GPU architecture](https://www.apple.com/newsroom/2023/10/apple-unveils-m3-m3-pro-and-m3-max-the-most-advanced-chips-for-a-personal-computer/).
