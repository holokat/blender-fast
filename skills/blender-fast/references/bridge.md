# Blender Lab bridge

The helper speaks the installed Blender Lab protocol: a UTF-8 JSON request terminated by a null byte, with `type: execute`, Python `code`, and `strict_json: true`. Code sets a JSON-serializable dictionary named `result`. The bridge returns a null-terminated JSON envelope. It executes the script in Blender's calling/main thread. Each request uses a new connection; this bridge closes the client after its response.

This is separate from the third-party ahujasid/blender-mcp protocol. Confirm which implementation is installed rather than assuming every Blender MCP server has the same wire format. The helper intentionally limits connections to loopback addresses. It does not install an add-on, register an MCP server in Codex or expose a network service.

## Commands

Resolve paths relative to the installed skill folder. Replace the snapshot path with the current task's work directory. These examples assume `python3` is an existing Python 3.10+ interpreter and the existing Blender Lab add-on is running on port 9876.

```sh
python3 scripts/blender_client.py status
python3 scripts/blender_client.py --timeout 90 execute --file work/scene_step.py
python3 scripts/polling_profile.py status
python3 scripts/polling_profile.py apply --snapshot work/blender-polling.json
python3 scripts/polling_profile.py restore --snapshot work/blender-polling.json
```

`apply` refuses to overwrite its snapshot. `restore` checks the snapshot's schema, add-on, port and installed numeric limits. Add `--persist` to apply or restore only when you want to save Blender preferences. The helper leaves the current idle delay unchanged and retains polling intervals that are already shorter than the tested profile. Use `--addon` if a verified Blender Lab installation uses another extension module name.

For in-process orchestration, import `execute` from `scripts/blender_client.py`. It returns `(result_dict, round_trip_ms)`. Use one call for a useful group of operations. The client bounds request and response size, applies an overall deadline and never retries a script automatically. A transport failure raises `ExecutionUncertain`; inspect the current state before attempting another mutation. A returned script error can also occur after earlier lines of that script have run.

The tested add-on reads socket input in 4 KiB chunks during timer polling. Large inline scripts may therefore require multiple ticks. When both processes are local, a short command can load an already-authored task-local builder with `runpy.run_path`. Check that the path is available to Blender. Do not use this to run an unreviewed downloaded script or to evade the client's execution restrictions.

## Supported settings

| Setting | Installed default in the test | Tested profile |
| --- | ---: | ---: |
| Active interval | 0.25 s | 0.05 s |
| Idle interval | 1.0 s | 0.25 s |
| Idle delay | 5.0 s | 5.0 s |

The UI's active preference default was 0.25 s, even though the server module's initial constant was 0.05 s. The registered preference overwrote that constant when the server started. This is why measuring the live settings matters.

Sources: [Blender Lab MCP](https://www.blender.org/lab/mcp-server/), the installed Blender Lab MCP add-on 1.0.0 source (`__init__.py`, `mcp_to_blender_server.py`), and [Blender's threading guidance](https://docs.blender.org/api/5.0/info_gotchas_threading.html).
