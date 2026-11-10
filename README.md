# obs-logic-block-template

Template repository for building custom logic block plugins for [open bridge server](https://github.com/abeggled/openbridgeserver).

Fork this repo, run `python init.py`, edit `plugins/obs_plugin_logic_template.py` — your block appears in the OBS logic editor immediately, no restart needed.

---

## Quick start

**Prerequisites:** Python 3.11+, Docker Desktop (or Docker Engine + Compose plugin)

```bash
# 1. Fork this repo on GitHub, then clone your fork
git clone https://github.com/your-name/obs-plugin-my-block
cd obs-plugin-my-block

# 2. Run the setup script — does everything in one go
python init.py

# 3. Start the stack  (.env was already created by init.py)
docker compose up -d
```

OBS ships without any account. On the first visit to **http://localhost:8080** it shows a setup page: choose the administrator's name and password there — once, the account persists in the database across restarts and image upgrades. Then open the Logic editor → your block is listed in the node palette.

Prefer not to claim the instance over the network? Create the owner on the shell instead, before the first visit:

```bash
docker compose exec obs sh -c 'echo yourpassword | obs-admin auth first-owner admin --password-stdin'
```

---

## What `init.py` does

The script runs three steps automatically:

**Step 1 — Prerequisites:** checks that Python ≥ 3.11, the Docker daemon, and Docker Compose are all available. Fails fast with a clear hint if anything is missing.

**Step 2 — Personalise:** asks for your block name, renames all template placeholders across every file in one pass and names the plugin file after your block:

```
Step 2 — Personalise
────────────────────────────────────────────────────────────
  Block display name (shown in the GUI palette) [My Block]: Shadow Control
  Block type name (unique snake_case identifier) [shadow_control]:
  Short description  (leave blank to keep placeholder):

    Class name : ShadowControl
    type_name  : shadow_control
    Label      : Shadow Control
    Package    : obs-plugin-shadow-control

  Apply? [Y/n]

  [✓] Updated: obs_plugin_logic_template.py, pyproject.toml, test_plugin.py, README.md
  [✓] Renamed: plugins/obs_plugin_logic_template.py → plugins/obs_plugin_shadow_control.py
```

**Step 3 — Environment:** copies `.env.example` → `.env` so the dev stack has credentials on first run.

After `init.py` finishes, the repo is fully personalised — no more "LogicTemplate" anywhere.

---

## Hot-reload development loop

The `plugins/` directory is bind-mounted into the OBS container. Save a change and OBS reloads it automatically:

```
INFO  obs.logic.plugin_loader: Plugin reloaded: obs_plugin_shadow_control.py — types: ['shadow_control']
```

Mount the directory, never the single file: a single-file mount misses changes, and editors that save by writing a new file and renaming it (JetBrains "safe write", vim, `git checkout`) leave the container on the old file. `WATCHFILES_FORCE_POLLING` in `docker-compose.yml` makes the reload work on Docker Desktop (macOS/Windows) as well.

Watch the logs live:

```bash
docker compose logs -f obs
```

If the file has a syntax error, OBS logs a warning and waits for the next save — no crash, no restart:

```
WARNING obs.logic.plugin_loader: Plugin reload produced no types: obs_plugin_shadow_control.py
ERROR   obs.logic.plugin_loader: Plugin failed to load: obs_plugin_shadow_control.py
Traceback ...
```

Fix the error and save again.

---

## Project layout

```
obs-logic-block-template/
├── init.py                    # Run once after cloning — personalises the repo
├── plugins/
│   └── obs_plugin_logic_template.py  # Your logic block — the only file you edit daily
├── docker-compose.yml         # Dev stack: OBS + Mosquitto
├── mosquitto/
│   └── mosquitto.conf         # MQTT broker config (no changes needed)
├── pyproject.toml             # Packaging metadata for pip distribution
├── tests/
│   ├── conftest.py            # OBS API stubs (no OBS install needed to run tests)
│   └── test_plugin.py         # Unit tests for evaluate()
└── .github/
    └── workflows/
        └── test.yml           # CI: runs pytest on every push
```

---

## Implementing your block

`plugins/obs_plugin_logic_template.py` ships with a minimal working example (`(in1 + in2) × multiplier`). Replace it with your logic:

1. **`type_name`** — globally unique snake_case identifier across all plugins and built-in blocks.
2. **`node_type_def()`** — set `label`, `category`, `inputs`, `outputs`, and `config_schema`.
3. **`evaluate()`** — receives `inputs` and `config`, returns `(outputs, state)`.

### Port types

```python
NodeTypePort(id="trigger_in", label="Trigger", type="trigger")  # trigger signal
NodeTypePort(id="value_in",   label="Value")                    # value (default)
```

### Multiple blocks in one file

```python
@register_node_type
class BlockA(LogicNodePlugin):
    type_name = "block_a"
    ...

@register_node_type
class BlockB(LogicNodePlugin):
    type_name = "block_b"
    ...
```

### Several plugins side by side

OBS loads every `*.py` file in its plugins directory as a plugin of its own, so blocks from different repositories can share one OBS instance — reloading or deleting one file only touches the node types that file registered. Two rules keep them apart:

- **One file per plugin, named after the block** (`obs_plugin_<type_name>.py`, which `init.py` takes care of). A generic name such as `plugin.py` could not sit next to another plugin's file.
- **A globally unique `type_name`.** A plugin reusing a built-in block's name or one another plugin already registered is ignored, and OBS logs an error.

To try your block together with others in the dev stack, copy their plugin files into your `plugins/` directory. A directory plugin cannot import helper modules next to it (files starting with `_` are skipped and the directory is not on `sys.path`) — keep it in one file, or ship it as a pip package.

### Persistent state

The `state` dict survives graph executions and server restarts:

```python
@classmethod
def evaluate(cls, node_id, inputs, config, state):
    total = state.get("total", 0.0) + float(inputs.get("value") or 0)
    state["total"] = total
    return {"total": total}, state
```

Keep it JSON-serialisable (`str`, `int`, `float`, `bool`, `list`, `dict` only).

---

## Running unit tests

Tests call `evaluate()` directly — no Docker, no running OBS needed. `conftest.py` stubs the OBS plugin API so the plugin module imports cleanly in isolation.

```bash
pip install -r requirements_dev.txt   # installs pytest (done by init.py step 4)
pytest tests/ -v
```

Update `tests/test_plugin.py` after `init.py` and after changing ports or config fields.

---

## Distributing as a pip package

When your block is ready to share, build and publish it so others can install it with one command.

### Build and publish

```bash
pip install hatch
hatch build
hatch publish   # publishes to PyPI
```

### Install on a running OBS instance

```bash
# LXC / bare-metal
source /opt/obs/venv/bin/activate
pip install obs-plugin-template
systemctl restart obs

# Docker
docker exec obs pip install obs-plugin-template
docker compose restart obs
```

No `OBS_PLUGINS_DIR` configuration is needed for pip-installed entry-point plugins — OBS discovers them automatically via the `obs.logic_blocks` entry point group.

The wheel installs `plugins/obs_plugin_logic_template.py` as the top-level module `obs_plugin_logic_template` (see `pyproject.toml`) — the same unique name as in the plugins directory, so several plugins can be installed side by side without overwriting each other. Install a plugin either way, not both: the second copy of its type would be ignored.

---

## Plugin API reference

Full interface documentation, `NodeTypeDef` field reference, type coercion helpers, and advanced examples live in the OBS source repo:

[`docs/logic-plugin-api.md`](https://github.com/abeggled/openbridgeserver/blob/main/docs/logic-plugin-api.md)

---

## Licence

MIT
