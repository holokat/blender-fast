# Blender fast agent instructions

For Blender modeling, automation or rendering work in this repository, read [the skill](skills/blender-fast/SKILL.md) and [the implementation guide](skills/blender-fast/references/agent-workflow.md). Use the combined workflow as the starting path while preserving the task's renderer, scene and quality requirements. The Metal GPU-only profile is the measured choice for the M2 Max; inspect support on another machine.

Keep geometry creation, bridge latency and rendering timings separate. Publish speed claims only with their scene, hardware, quality settings, timing scope and raw evidence. Do not multiply stage speedups or present recorded playback as simultaneous execution.

For new scenes, check `skills/blender-fast/references/shape-programs.md` for composable construction lessons and `skills/blender-fast/references/scene-recipes.md` for finished asset factories. Reuse generators when they fit the brief, preserve stable assembly IDs, and measure recipe authoring separately from library development. Extend unsupported shapes explicitly. The interactive Eevee profile trades quality for speed and does not establish a faster equivalent-quality Cycles final.

Reuse the existing protocol client and isolated examples. Never clear an unrelated scene, save global preferences incidentally, or retry an uncertain mutation automatically. Read the scoped rollback guidance in the skill.

For code changes, run the relevant existing tests. Protocol and preview Python checks use synthetic loopback servers: `python3 -m unittest discover -s tests -v`. Replay checks use `node tests/test_timeline.mjs`. Verify Blender-facing changes in an isolated task scene or background process. Documentation-only changes need accurate links, validated snippets where changed, and consistency with the raw results.

This file routes agents working in this repository. For global Codex routing, use the install and routing instructions in [README.md](README.md). Keep machine-specific paths and private configuration out of public commits.
