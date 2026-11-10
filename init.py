#!/usr/bin/env python3
"""Set up your OBS logic block plugin from the template.

Run once after forking and cloning:

    python init.py

Steps performed:
  1. Prerequisite check  — Python ≥ 3.11, Docker daemon, Docker Compose
  2. Personalise         — rename all template placeholders in one pass
  3. Environment setup   — create .env from .env.example
  4. Next-step summary
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── Template placeholder strings ──────────────────────────────────────────────
# These exact strings are replaced across all target files in step 2.
T_CLASS = "LogicTemplate"        # Python class name
T_TYPE  = "logic_template"       # type_name + entry-point key
T_LABEL = "Logic Template"       # display label in the GUI palette
T_PKG   = "obs-plugin-template"  # pip package name

PLUGINS_DIR = ROOT / "plugins"

TARGET_FILES = [
    ROOT / "pyproject.toml",
    ROOT / "tests" / "test_plugin.py",
    ROOT / "README.md",
]



def _plugin_file() -> Path:
    """The block's module: plugins/obs_plugin_<type_name>.py (one file per repo)."""
    files = sorted(PLUGINS_DIR.glob("obs_plugin_*.py"))
    if not files:
        _fail("No plugins/obs_plugin_*.py found", "restore it from the template repository")
    return files[0]


# ── Formatting helpers ────────────────────────────────────────────────────────

def _ok(msg: str) -> None:
    print(f"  [✓] {msg}")


def _fail(msg: str, hint: str = "") -> None:
    print(f"  [✗] {msg}" + (f"\n      → {hint}" if hint else ""))
    sys.exit(1)


def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    return input(f"  {prompt}{hint}: ").strip() or default


def _section(title: str) -> None:
    print(f"\n{title}")
    print("─" * 60)


# ── Name derivation ───────────────────────────────────────────────────────────

def _to_class(s: str) -> str:
    """'my block name' → 'MyBlockName'"""
    return "".join(w.capitalize() for w in re.split(r"[\s_\-]+", s) if w)


def _to_snake(s: str) -> str:
    """'My Block Name' → 'my_block_name'"""
    s = re.sub(r"[\s\-]+", "_", s.strip())
    return re.sub(r"[^a-z0-9_]", "", s.lower())


def _to_kebab(s: str) -> str:
    return s.replace("_", "-")


# ── File patching ─────────────────────────────────────────────────────────────

def _patch(path: Path, subs: list[tuple[str, str]]) -> bool:
    text = path.read_text("utf-8")
    result = text
    for old, new in subs:
        result = result.replace(old, new)
    if result != text:
        path.write_text(result, "utf-8")
        return True
    return False


# ── Step 1: Prerequisites ─────────────────────────────────────────────────────

def step_checks() -> None:
    _section("Step 1 — Prerequisites")

    # Python version
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 11):
        _ok(f"Python {major}.{minor}")
    else:
        _fail(f"Python {major}.{minor} is too old", "install Python 3.11 or newer")

    # Docker CLI present
    if not shutil.which("docker"):
        _fail("docker not found", "install Docker Desktop: https://docs.docker.com/get-docker/")

    # Docker daemon reachable
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=10
        )
        if result.returncode != 0:
            _fail("Docker daemon not running", "start Docker Desktop and try again")
    except Exception:
        _fail("Docker daemon not running", "start Docker Desktop and try again")
    _ok("Docker daemon running")

    # Docker Compose (plugin form: docker compose)
    try:
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError
    except Exception:
        _fail("Docker Compose not available", "update Docker Desktop or install the Compose plugin")
    _ok("Docker Compose available")


# ── Step 2: Personalise ───────────────────────────────────────────────────────

def step_personalise() -> dict:
    _section("Step 2 — Personalise")

    # Already personalised?
    plugin_file = _plugin_file()
    sample = plugin_file.read_text("utf-8")
    if T_TYPE not in sample:
        _ok("Already personalised — skipping rename step")
        # Still need to return something for the summary; try to read current type_name.
        m = re.search(r'type_name\s*=\s*"([^"]+)"', sample)
        type_name = m.group(1) if m else "my_block"
        return {"type_name": type_name, "package_name": "obs-plugin-" + _to_kebab(type_name)}

    print("  Enter your block details. Press Enter to accept the suggestion in brackets.\n")

    label     = _ask("Block display name (shown in the GUI palette)", "My Block")
    type_name = _ask("Block type name (unique snake_case identifier)", _to_snake(label))

    if not re.match(r"^[a-z][a-z0-9_]*$", type_name):
        _fail(f"type name must be lowercase snake_case (got {type_name!r})")

    description = _ask("Short description  (leave blank to keep placeholder)", "")

    class_name   = _to_class(type_name)
    package_name = "obs-plugin-" + _to_kebab(type_name)

    print()
    print(f"    Class name : {class_name}")
    print(f"    type_name  : {type_name}")
    print(f"    Label      : {label}")
    print(f"    Package    : {package_name}")
    if description:
        print(f"    Description: {description}")
    print()

    if input("  Apply? [Y/n] ").strip().lower() in ("n", "no"):
        sys.exit("Aborted.")

    subs: list[tuple[str, str]] = [
        (T_CLASS, class_name),
        (T_TYPE,  type_name),
        (T_LABEL, label),
        (T_PKG,   package_name),
    ]
    if description:
        subs.append(("Replace this description with your block's purpose.", description))

    changed = [p.name for p in [plugin_file, *TARGET_FILES] if p.exists() and _patch(p, subs)]
    _ok(f"Updated: {', '.join(changed)}")

    # The file is named after the block, so several plugins can share one
    # OBS plugins directory without clashing.
    renamed = plugin_file.with_name(f"obs_plugin_{type_name}.py")
    if renamed != plugin_file:
        plugin_file.rename(renamed)
        _ok(f"Renamed: plugins/{plugin_file.name} → plugins/{renamed.name}")

    return {"type_name": type_name, "package_name": package_name}


# ── Step 3: Environment ───────────────────────────────────────────────────────

def step_env() -> None:
    _section("Step 3 — Environment")

    env_file    = ROOT / ".env"
    env_example = ROOT / ".env.example"

    if env_file.exists():
        _ok(".env already exists")
    else:
        shutil.copy(env_example, env_file)
        _ok("Created .env from .env.example")


# ── Step 4: Dev dependencies ─────────────────────────────────────────────────

def step_dev_deps() -> None:
    _section("Step 4 — Dev dependencies")

    req = ROOT / "requirements_dev.txt"
    answer = input("  Install dev dependencies for local test runs? [Y/n] ").strip().lower()
    if answer in ("n", "no"):
        _ok("Skipped — run manually: pip install -r requirements_dev.txt")
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _ok("Dev dependencies installed (pytest)")
    else:
        print(f"  [!] pip install failed:\n{result.stderr.strip()}")
        print("      Run manually: pip install -r requirements_dev.txt")


# ── Step 5: Summary ───────────────────────────────────────────────────────────

def step_summary(info: dict) -> None:
    type_name    = info["type_name"]
    package_name = info["package_name"]

    print()
    print("═" * 60)
    print("  Setup complete!")
    print("═" * 60)
    print()
    print("  Implement your block:")
    print(f"    Edit plugins/obs_plugin_{type_name}.py")
    print("    Edit tests/test_plugin.py  (update for your ports and logic)")
    print()
    print("  Start the dev stack:")
    print("    docker compose up -d")
    print()
    print("  Open the Admin UI:")
    print("    http://localhost:8080   (first visit: set the admin password)")
    print(f"    Logic editor → your '{type_name}' block is in the palette")
    print()
    print("  Hot-reload — edit the plugin file and save, then watch:")
    print("    docker compose logs -f obs")
    print()
    print("  Run unit tests (no Docker needed):")
    print("    pytest tests/ -v")
    print()
    print("  Distribute:")
    print("    pip install hatch && hatch build && hatch publish")
    print(f"    → pip install {package_name}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("═" * 60)
    print("  obs-logic-block — setup")
    print("═" * 60)

    step_checks()
    info = step_personalise()
    step_env()
    step_dev_deps()
    step_summary(info)


if __name__ == "__main__":
    main()
