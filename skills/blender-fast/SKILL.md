---
name: blender-fast
description: Build, edit, inspect, automate and render Blender scenes using batched Python operations, supported polling settings and visual verification. Use for Blender modeling, materials, animation, scene generation, MCP and bpy scripting work.
---

# Blender fast

Use this workflow for Blender work. Preserve the user's scene, chosen tools and visual requirements. Speed is useful when the result remains correct and reviewable.

## Establish the connection

Identify the installed Blender version, bridge implementation and active scene before changing anything. Prefer an existing compatible Blender MCP tool. The bundled helper is specifically for the Blender Lab null-delimited local TCP bridge, verified with add-on 1.0.0 and Blender 5.2.0 LTS. It is not a client for the separate ahujasid/blender-mcp protocol.

For this local Blender Lab bridge, use `scripts/blender_client.py status`. The helper requires Python 3.10+ and the standard library. Reuse an existing Python installation. If Blender is not reachable, check whether it is running and its existing add-on is enabled. Do not install a replacement bridge just to follow this skill.

Read [references/bridge.md](references/bridge.md) when using the direct helper, changing polling preferences, or diagnosing transport latency. For another bridge, use its actual tool schema and keep the batching principles below.

## Build coherent batches

Write reusable scene-building Python locally when the task warrants it, then execute meaningful groups of operations. Avoid one tool call per object, material slot, modifier or transform.

For inexpensive repeated primitives, 32–64 objects per batch is a useful starting point. This is a heuristic, not a mandatory size. Batch larger groups when they remain quick, and split costly mesh edits, booleans, simulations and renders into smaller stages so failures are diagnosable and the interface stays responsive.

Prefer direct `bpy.data`, mesh arrays, `bmesh` and shared mesh/material data when they fit. Use `bpy.ops` where its context or behavior is needed. Keep Blender API mutations on Blender's main thread. Do not parallelize `bpy` calls using Python worker threads.

For a local bridge, load a trusted local builder once and invoke it with short batch commands when both processes share the filesystem. For a remote tool, use its supported code or file transfer mechanism. Return concise results such as created IDs, changed-object counts, bounds and validation failures.

Use a dedicated scene or collection for a new asset. For edits, address the intended objects explicitly. Make scripts safe to resume through owned IDs, existence checks or recorded completed ranges. Never clear the user's whole scene as incidental setup. After a timeout or dropped response, inspect the scene before retrying; a command may already have run, even if no reply arrived.

## Reduce avoidable waiting

Inspect actual polling settings before tuning. The tested Blender Lab profile uses 0.05 seconds active polling and 0.25 seconds idle polling, with a 5-second delay before idle. Respect installed property limits and preserve settings already faster than this profile.

When tuning is appropriate and authorized, use `scripts/polling_profile.py apply --snapshot <task-work-directory>/blender-polling.json`. It records the prior values and changes the current session. Add `--persist` only when saving the user's preferences is wanted; saving also commits other pending Blender preference edits. Keep the snapshot for rollback. Do not reapply a profile on every call. More frequent polling can increase CPU wakeups; do not assert a battery or CPU benefit without measuring it.

## Verify geometry and the visual result

Run compact checks at the end of each meaningful stage: expected objects, valid material assignments, transforms, dimensions and any task-specific topology or animation requirements. Evaluate the dependency graph when reading derived transforms or geometry; avoid forcing a full update after every property assignment.

Render or inspect the viewport at meaningful milestones and before claiming visual completion. Examine silhouette, proportions, intersections, materials, lighting and framing. A matching hash or successful script does not establish visual quality. Preserve the requested detail rather than reducing it to make a benchmark look faster.

For render optimization, read [references/rendering.md](references/rendering.md). Inspect the actual GPU backend, the scene device and the denoiser device separately. Measure persistent-data caching for repeated renders, preserving sample count and resolution before trying quality tradeoffs.

Use preview render settings during iteration and restore or explicitly record final settings. Save the editable `.blend` plus the requested final exports. Before publishing previews, inspect image metadata: Blender can embed an absolute `.blend` path even when visible stamping is disabled. Disable filename metadata at render time when the path should not be shared. Keep temporary previews and logs in the task's work directory.

## Report timings honestly

Separate model/tool orchestration, bridge waiting, scene setup, geometry construction, validation, saving and rendering. For a performance comparison, hold the scene, builder and output checks constant. Record batch size, call count, Blender/add-on versions, machine and sample count.

The documented 973-object house test used 973 individual bridge requests versus 16 batches. Object creation took 246.07 seconds versus 0.93 seconds, approximately 266 times faster for that specific comparison. These numbers exclude AI reasoning, external MCP client/server overhead, setup, validation, staging, saving and rendering. Do not promise that multiplier for an already-batched workflow or an arbitrary Blender task.

Read [references/benchmark.md](references/benchmark.md) for the evidence and reproduction scope. The public source is [holokat/blender-fast](https://github.com/holokat/blender-fast).
