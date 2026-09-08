# Benchmark evidence

Measured on 9 September 2026, Blender 5.2.0 LTS, Blender Lab MCP add-on 1.0.0, Apple M2 Max with a 30-core GPU. The house is an original fictional asset made for the test. It contains 973 model objects, 451 roof tiles and 29 materials.

| Strategy | Bridge requests | Setup | Object creation |
| --- | ---: | ---: | ---: |
| Original polling, individual calls | 973 | 0.301 s | 246.068 s |
| Faster polling, individual calls | 973 | 0.073 s | 57.847 s |
| Faster polling, batches of 64 | 16 | 0.060 s | 0.925 s |

Each large-scene strategy was measured once. Actual mesh coordinates, polygon indices, transforms, material assignments and the used Principled BSDF parameters produced the same SHA-256 fingerprint after all three builds:

```text
580930f5f666efead53377d994686e1ddddc4c46d45ac256fbc71abfbe6d6b52
```

There were 34,174 vertices and 36,967 polygons when counting each mesh instance. Camera, lights and backdrop were added after the benchmark. The final Cycles render used 64 samples with denoising at 1,400 × 1,400 and took 13.01 seconds, including device setup inside the rendering script. Only the final optimized house was rendered; this was not a pixel-difference comparison.

The construction timings exclude AI reasoning, external MCP client/server overhead, setup, validation, staging, saving and rendering. The intentionally chatty baseline emphasizes bridge waiting. A task already using large scripts will see a smaller batching gain. Harder geometry, simulations and render-heavy work may have a different bottleneck.

A smaller repeated test found active read latency medians of 252.23 ms and 52.51 ms, with 24 reads per profile in alternating blocks. Transform tests used three repetitions per profile and checked changed coordinates after both individual and batched assignments.

The repository contains raw measurements, the portable house generator and reproduction commands: [benchmark files](https://github.com/holokat/blender-fast/tree/main/benchmarks), [house example](https://github.com/holokat/blender-fast/tree/main/examples/mmo-house). Compare your own scene and separate the same timing stages before claiming a speedup.
