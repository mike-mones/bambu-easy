"""Orchestrator: read 3MF → resolve nozzle/filament → bake → validate → write."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from ._engine.bake_3mf_settings import bake_settings, read_settings
from ._engine.bs_validation import (
    DEFAULT_BS_CLI_PATH,
    ValidationError,
    assert_bs_settings_valid,
    validate_bs_cli,
)
from ._engine.print_profiles import compose_profile


@dataclass
class PrepareResult:
    output_path: str
    nozzle: str
    material: str
    tier: str
    static_ok: bool
    bs_ok: bool | None        # None if skipped
    bs_message: str | None    # None if skipped
    settings_count: int
    filament_settings_id: str
    nozzle_temperature: list | str
    warnings: list[str] = field(default_factory=list)


def _suppress_stdout(fn, *args, **kwargs):
    """Silence the legacy bake_settings prints; we provide our own UI."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*args, **kwargs)


def prepare_3mf(
    input_path: str,
    output_path: str,
    nozzle: str,
    material: str,
    tier: str,
    do_bs_validate: bool = True,
    bs_path: str | None = None,
) -> PrepareResult:
    """Compose a profile, bake it into the 3MF, validate, and return a result."""
    profile = compose_profile(nozzle=nozzle, material=material, tier=tier)
    # Static validation up-front (fail before writing)
    assert_bs_settings_valid(profile)

    _suppress_stdout(
        bake_settings,
        target_path=str(input_path),
        output_path=str(output_path),
        reference_path=None,
        overrides=profile,
    )

    # Re-read the merged settings from the output for validation + reporting
    with zipfile.ZipFile(str(output_path)) as zf:
        merged = read_settings(zf)
    assert_bs_settings_valid(merged)

    bs_ok: bool | None = None
    bs_msg: str | None = None
    if do_bs_validate:
        bs_ok, bs_msg = validate_bs_cli(
            str(output_path),
            bs_path=bs_path or DEFAULT_BS_CLI_PATH,
        )

    fid = merged.get("filament_settings_id", "")
    if isinstance(fid, list) and fid:
        fid = fid[0]

    return PrepareResult(
        output_path=str(output_path),
        nozzle=nozzle,
        material=material,
        tier=tier,
        static_ok=True,
        bs_ok=bs_ok,
        bs_message=bs_msg,
        settings_count=len(merged),
        filament_settings_id=fid,
        nozzle_temperature=merged.get("nozzle_temperature", "?"),
    )


def default_output(input_path: str) -> str:
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_ready{p.suffix}"))
