# Implement the combined workflow

Use this guide when applying the selected pipeline to a new Blender task. It is intended for any LLM agent with a Blender Python execution tool or a local Blender process. Codex can discover the packaged skill; other agents can read `SKILL.md` and this guide directly. Installing a skill does not install or register a Blender MCP server.

## Selected path

Use coherent batches with direct `bpy.data` operations and shared mesh/material data where appropriate. For the verified local Blender Lab bridge, use supported fast polling while preserving faster existing values. For Cycles on the tested M2 Max, select **Metal GPU only, MetalRT Auto, GPU OpenImageDenoise, and persistent data for repeated renders**. Keep the requested quality settings and inspect the resulting image.

This is the best combined path measured here, not a claim that every scene or computer has the same optimum. Both the house and jet used this path successfully. CPU plus GPU and forced MetalRT were slower in the house device comparison. On other hardware, identify the available backend and denoiser support, then measure the corresponding configuration.

## Execute the task

1. **Inspect the actual task state.** Identify the Blender version, bridge protocol, active scene, renderer, selected backend and enabled devices. Preserve the user's current file. For a new asset, create an owned scene or collection. Respect an explicit renderer choice; this Cycles recipe does not require changing an Eevee project.
2. **Configure the bridge once.** For Blender Lab, run `scripts/blender_client.py status` and, if needed, `scripts/polling_profile.py apply --snapshot work/polling-before.json`, resolving these paths from the skill folder. The helper validates the installed RNA limits and preserves the idle delay and any already-faster intervals. Use session settings for experiments; save preferences only when persistence is intended. Keep the rollback snapshot.
3. **Build in useful batches.** Load the task's trusted builder once, then send short stage or range commands. Start with up to 64 inexpensive objects per request and adapt to stage cost and responsiveness. Keep all `bpy` mutations on Blender's main thread. Reuse mesh and material data when it preserves the desired object behavior. Return created counts or IDs from each acknowledged stage.
4. **Verify before rendering.** Check expected objects, material assignments, transforms and task-specific geometry requirements. In a benchmark, compare the actual resulting geometry/material fingerprint across paths. A matching hash does not replace visual inspection.
5. **Apply the render profile to the intended scene.** Use the implementation below on the verified M2 Max setup. For another backend, inspect support and adapt deliberately. Preserve samples, adaptive sampling thresholds, resolution, camera, lights and geometry. The house and jet's 64 samples are benchmark settings, not a universal quality default.
6. **Keep related renders in one process.** Persistent data helps later renders only while reusable data remains in that Blender process. Keep one background process alive across an iteration group or frame sequence. A separate process for every frame discards that cache. Queue GPU jobs on this single-GPU Mac; additional Python threads and overlapping renders do not add GPU capacity.
7. **Inspect and save.** Review silhouette, materials, shadows, noise and fine details. Save the intended `.blend` with `scene.cycles.device` and the selected scene settings. Backend/device preferences belong to Blender preferences, not solely to the file; reselect and verify them in another process or machine. Disable filename metadata before publishing PNGs.
8. **Report observed work.** Separate setup, bridge construction, first render in process, warm renders, and the actual combined total. Include device, samples, resolution and scope. Measure speedups directly; never multiply construction and rendering ratios. For comparisons on one GPU, measure sequentially and label synchronized playback as a recorded replay.

## M2 Max render implementation

Run this in Blender's main thread after selecting the intended task scene. It changes Cycles device preferences for the session and render settings on that scene. It does not save preferences, change quality settings, start a render or save a file. The default enables retained data for repeated rendering; set `repeated=False` for a task that should not retain a render cache. Retained data consumes extra memory.

```python
import bpy


def configure_m2_max(scene, *, repeated=True):
    if scene.render.engine != 'CYCLES':
        raise RuntimeError('Apply this profile to an intended Cycles scene')
    prefs = bpy.context.preferences.addons['cycles'].preferences
    if not hasattr(prefs, 'metalrt') or not hasattr(scene.cycles, 'denoising_use_gpu'):
        raise RuntimeError('Inspect GPU ray-tracing and denoiser support in this Blender build')
    previous_backend = prefs.compute_device_type
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        gpu_devices = [device for device in prefs.devices if device.type == 'METAL']
        if not gpu_devices:
            raise RuntimeError('No Metal GPU detected; choose a supported backend')
    except Exception:
        prefs.compute_device_type = previous_backend
        raise
    for device in prefs.devices:
        device.use = device.type == 'METAL'
    prefs.metalrt = 'AUTO'
    scene.cycles.device = 'GPU'
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.denoising_use_gpu = True
    scene.render.use_persistent_data = repeated
    return {
        'backend': prefs.compute_device_type,
        'enabled_devices': [device.name for device in prefs.devices if device.use],
        'scene_device': scene.cycles.device,
        'metalrt': prefs.metalrt,
        'denoiser': scene.cycles.denoiser,
        'gpu_denoising_requested': scene.cycles.denoising_use_gpu,
        'persistent_data': scene.render.use_persistent_data,
    }
```

Call `configure_m2_max(scene)` with the task's scene and inspect the returned settings. A requested GPU denoiser flag alone does not prove hardware support or a performance gain. Validate with an actual render. The existing house and jet results establish that this configuration rendered successfully on the tested M2 Max with Blender 5.2.0 LTS. The function also checks available properties/devices and avoids silently switching to a CPU backend.

For a temporary experiment in the user's foreground Blender process, snapshot and restore all preferences and scene properties you change. The bridge polling helper handles polling rollback only. Prefer an isolated background process for render experiments; those session preferences disappear when the process ends.

## Evidence and working examples

- The [jet comparison](https://github.com/holokat/blender-fast/blob/main/docs/live-comparison.md) measured 76.40 s versus 9.71 s for one build and four renders, including setup, validation, saving and renderer startup. Construction was 57.61 s versus 0.22 s. Three warm repeat renders had medians of 3.96 s versus 1.79 s. Both geometry/material fingerprints matched. Each full path was run once; system load and thermal effects were not controlled.
- [The shared jet builder](https://github.com/holokat/blender-fast/blob/main/examples/jet-fighter/jet_builder.py) demonstrates owned scene data, range-based object creation, fingerprinting, staging, saving and cleanup.
- [The combined runner](https://github.com/holokat/blender-fast/blob/main/preview/runner.py) demonstrates batching through the existing bridge, separate stage clocks, sequential render jobs and polling restoration.
- [The render worker](https://github.com/holokat/blender-fast/blob/main/preview/render_worker.py) keeps first and repeated renders in one process and returns actual timings and settings.
- [Rendering guidance](rendering.md) explains memory costs, hardware differences and the separate house experiments. [Protocol guidance](bridge.md) covers transport and rollback.

An incomplete response is not evidence of an unapplied mutation. After a timeout or disconnect, inspect owned IDs and saved state before retrying or cleaning up. Resume only after the current state is understood. The local preview blocks another run when bridge completion is uncertain.
