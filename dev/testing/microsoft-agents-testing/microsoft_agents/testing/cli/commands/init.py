# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Init CLI command — scaffold a test harness from a preset template."""

import shutil
from pathlib import Path
from importlib.resources import files as _pkg_files

import click

from microsoft_agents.testing.cli.core import pass_output, Output

# ---------------------------------------------------------------------------
# Preset discovery — runs once at import time
# ---------------------------------------------------------------------------
_PRESETS_ROOT = _pkg_files("microsoft_agents.testing") / "presets"


def _discover_presets() -> dict:
    try:
        return {
            entry.name: entry
            for entry in _PRESETS_ROOT.iterdir()
            if entry.is_dir()
        }
    except Exception:
        return {}


PRESETS: dict = _discover_presets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _copy_traversable(src, dest: Path) -> None:
    """Recursively copy a Traversable tree into an existing dest directory."""
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            _copy_traversable(item, target)
        else:
            target.write_bytes(item.read_bytes())


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------
@click.command(name="init")
@click.argument("preset", required=False, default=None)
@click.option("--force", is_flag=True, default=False, help="Overwrite any existing files from the preset.")
@pass_output
def init_group(out: Output, preset: str, force: bool) -> None:
    """Scaffold a test harness from a preset template.

    PRESET is the name of the harness template to use.
    Omit PRESET to list available presets.
    """
    if not preset:
        if not PRESETS:
            out.warning("No presets found.")
        else:
            out.info("Available presets:")
            for name in PRESETS:
                out.info(f"\t{name}")
        return

    if preset not in PRESETS:
        available = ", ".join(PRESETS) or "none"
        out.error(f"Unknown preset '{preset}'. Available: {available}")
        raise SystemExit(1)

    cwd = Path.cwd()
    preset_traversable = PRESETS[preset]

    conflicts = [
        cwd / item.name
        for item in preset_traversable.iterdir()
        if (cwd / item.name).exists()
    ]

    if conflicts and not force:
        names = ", ".join(p.name for p in conflicts)
        out.error(f"Already exists: {names}. Use --force to overwrite.")
        raise SystemExit(1)

    if force:
        for conflict in conflicts:
            if conflict.is_dir():
                shutil.rmtree(conflict)
            else:
                conflict.unlink()

    out.info(f"Initializing preset '{preset}' ...")
    _copy_traversable(preset_traversable, cwd)
    out.success(f"Done. Files written to {cwd}")
