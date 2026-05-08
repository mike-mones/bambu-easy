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


def _normalize_to_single_filament(zip_path: str, color: str | None = None) -> int:
    """Trim per-filament arrays in project_settings.config to length 1.

    MakerWorld 3MFs frequently embed N filaments (one per AMS slot) even
    when a model uses just one. After bambu-easy bakes a single-filament
    profile on top, the per-filament arrays (`filament_colour`,
    `*_plate_temp*`, etc.) are still length N. BS will then offer to map
    every slot to an AMS spool in the Send dialog — confusing for the
    user and historically the trigger of the PSA card holder Mar 19
    failure (mismatched array lengths → second extruder defaulted to
    0°C). Normalizing here keeps the file unambiguously single-color.

    Optionally sets `filament_colour[0]` to a hex like '#B76E79' so the
    AMS dialog displays the correct color.

    Returns the number of arrays trimmed (for diagnostics).
    """
    import json
    import os
    import shutil
    import tempfile

    # The set of project_settings keys that BS treats as "per-filament":
    PER_FILAMENT_KEYS = {
        "filament_colour",
        "hot_plate_temp", "hot_plate_temp_initial_layer",
        "cool_plate_temp", "cool_plate_temp_initial_layer",
        "eng_plate_temp", "eng_plate_temp_initial_layer",
        "textured_plate_temp", "textured_plate_temp_initial_layer",
        "supertack_plate_temp", "supertack_plate_temp_initial_layer",
    }

    trimmed = 0
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".3mf")
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(zip_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "Metadata/project_settings.config":
                    settings = json.loads(data)
                    for k in PER_FILAMENT_KEYS:
                        v = settings.get(k)
                        if isinstance(v, list) and len(v) > 1:
                            settings[k] = v[:1]
                            trimmed += 1
                    if color:
                        settings["filament_colour"] = [color]
                    data = json.dumps(settings, indent=4).encode("utf-8")
                zout.writestr(item, data)
        shutil.move(tmp_path, zip_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return trimmed


def prepare_3mf(
    input_path: str,
    output_path: str,
    nozzle: str,
    material: str,
    tier: str,
    do_bs_validate: bool = True,
    bs_path: str | None = None,
    filament_color: str | None = None,
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

    # Single-color normalization: source 3MFs are often multi-filament even
    # when only one is used. Trim per-filament arrays to length 1 so the
    # AMS Send dialog isn't confused.
    _normalize_to_single_filament(str(output_path), color=filament_color)

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
