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


# Cooling / fan options that Bambu Studio stores PER-FILAMENT (Filament →
# Cooling tab) even though they read like process settings. They scale with the
# filament count, so they must keep the same array length as every other
# per-filament option or BS rejects the project.
_PER_FILAMENT_COOLING_KEYS = {
    "fan_max_speed",
    "fan_min_speed",
    "overhang_fan_speed",
    "overhang_fan_threshold",
    "close_fan_the_first_x_layers",
    "slow_down_for_layer_cooling",
    "slow_down_layer_time",
    "slow_down_min_speed",
    "fan_cooling_layer_time",
    "additional_cooling_fan_speed",
    "reduce_fan_stop_start_freq",
    "full_fan_speed_layer",
    "enable_overhang_bridge_fan",
}


def _is_per_filament_key(key: str) -> bool:
    """Whether a project_settings key holds one value per filament slot.

    BS validates that every per-filament option's array length matches the
    filament count. Anything that scales with the number of filaments lands
    here; true process scalars (wall speeds, layer height, infill) do not.
    """
    if key.startswith("filament"):
        return True
    if key.startswith("nozzle_temperature"):
        return True
    if "plate_temp" in key:  # hot/cool/eng/textured/supertack _plate_temp[_*]
        return True
    if key in _PER_FILAMENT_COOLING_KEYS:
        return True
    if key in ("chamber_temperatures", "required_nozzle_HRC",
               "default_filament_colour"):
        return True
    return False


def _read_source_lengths(source_path: str) -> dict[str, int]:
    """Map per-filament key -> array length in the (GUI-valid) source 3MF."""
    with zipfile.ZipFile(source_path, "r") as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    return {
        k: len(v)
        for k, v in cfg.items()
        if isinstance(v, list) and _is_per_filament_key(k)
    }


def _normalize_filament_array_lengths(
    zip_path: str,
    source_lengths: dict[str, int],
    color: str | None = None,
) -> int:
    """Re-align every per-filament array to the source's filament count.

    The bug this fixes (failure-log 2026-06-04): a MakerWorld source is a
    *self-consistent* N-filament project (e.g. N=2, one per AMS slot) that the
    BS GUI opens fine. When bambu-easy bakes a single-filament profile, the
    bake/compose step shrinks SOME per-filament arrays to length 1
    (`filament_settings_id`, `nozzle_temperature`, plate temps, fan speeds…)
    while leaving the rest at the source length. The result claims 1 filament
    in some keys and N in others — an inconsistency the headless BS slicer
    tolerates but the GUI rejects with **"Invalid configuration file"**.

    Reducing the project to a *true* single filament is not robust: ground
    truth from a valid single-filament 3MF shows the per-key single-filament
    lengths are idiosyncratic (e.g. `flush_volumes_vector` is length 8 for one
    filament), so there is no length = source_len / N formula. Instead we keep
    the source's filament count and **broadcast the baked value across every
    slot**, so the output stays structurally identical to the GUI-valid source
    (only the values change). For a single-color model the extra slot is
    harmless — both slots carry the same filament.

    `source_lengths` is the per-filament-key → length map from the SOURCE 3MF
    (see `_read_source_lengths`). Only keys whose current length differs from
    the source are touched, so the pass is idempotent and leaves correctly
    sized arrays (including bare-geometry single-filament sources) alone.

    Returns the number of arrays re-aligned (for diagnostics).
    """
    import os
    import shutil
    import tempfile

    fixed = 0
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".3mf")
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(zip_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "Metadata/project_settings.config":
                    settings = json.loads(data)
                    for key, target_len in source_lengths.items():
                        if target_len < 1 or key not in settings:
                            continue
                        cur = settings[key]
                        # Normalize current value to a non-empty list so we can
                        # broadcast its first (baked) entry across all slots.
                        if isinstance(cur, list):
                            if not cur:
                                continue
                            seed = cur[0]
                            cur_len = len(cur)
                        else:
                            seed = cur
                            cur_len = None
                        if cur_len == target_len:
                            continue
                        settings[key] = [seed] * target_len
                        fixed += 1
                    if color and "filament_colour" in settings:
                        n = len(settings["filament_colour"]) or 1
                        settings["filament_colour"] = [color] * n
                    data = json.dumps(settings, indent=4).encode("utf-8")
                zout.writestr(item, data)
        shutil.move(tmp_path, zip_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return fixed


# Plate geometry for the Bambu Lab P2S. The printable area is a 256×256 square
# with origin at the front-left corner (BS build-coordinate convention), so the
# plate centre is (128, 128).
_P2S_BED_MM = 256.0
_PLATE_CENTRE = _P2S_BED_MM / 2.0


def _parse_vertices(model_xml: str) -> list[tuple[float, float, float]]:
    import re
    return [
        (float(a), float(b), float(c))
        for a, b, c in re.findall(
            r'<vertex x="([-\d.eE]+)" y="([-\d.eE]+)" z="([-\d.eE]+)"',
            model_xml,
        )
    ]


def _xy_bounds(verts) -> tuple[float, float, float, float] | None:
    if not verts:
        return None
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    return min(xs), min(ys), max(xs), max(ys)


def _apply_affine_xy(bounds_xy, transform_nums):
    """Apply a 3MF affine (12-number 4×3 matrix) to an XY bbox.

    The 3MF core spec stores the transform as m00 m01 m02 m10 m11 m12 m20 m21
    m22 m30 m31 m32, mapping [x y z 1]·M, so:
        world_x = m00*lx + m10*ly + m20*lz + m30
        world_y = m01*lx + m11*ly + m21*lz + m31
    We ignore Z (lz term) for plate placement; rotation about Z is honoured.
    Returns the transformed XY bbox by mapping its 4 corners.
    """
    minx, miny, maxx, maxy = bounds_xy
    m = transform_nums
    m00, m10, m30 = m[0], m[3], m[9]
    m01, m11, m31 = m[1], m[4], m[10]
    corners = [(minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy)]
    wx = [m00 * lx + m10 * ly + m30 for lx, ly in corners]
    wy = [m01 * lx + m11 * ly + m31 for lx, ly in corners]
    return min(wx), min(wy), max(wx), max(wy)


def _ensure_on_plate(zip_path: str) -> tuple[int, str]:
    """Centre off-plate objects on the P2S plate by rewriting build transforms.

    Bare-geometry / web-tool 3MFs (and BS-CLI retargets of them) frequently
    place the object off the plate — the retarget re-centres the mesh's local
    coordinates to the origin but leaves a build-item translation that drops the
    part into negative Y. BS then refuses to slice with rc=-50 ("no object fully
    inside plate"). MakerWorld files never hit this because they ship a valid
    on-plate arrangement; bambu-easy has historically had no arrange step (see
    Reference/failure-log.md June 3, 2026).

    This computes the combined world XY bounding box of all build items and, if
    any part falls outside the [0, 256] plate, shifts every item by one delta so
    the group is centred at (128, 128). It is idempotent: a file already on the
    plate is left untouched. Z is never modified (the bottom-at-Z=0 placement
    from the source/bake is preserved).

    Returns (items_moved, message).
    """
    import os
    import re
    import shutil
    import tempfile

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        if "3D/3dmodel.model" not in names:
            return 0, "no 3dmodel.model"
        model = zf.read("3D/3dmodel.model").decode("utf-8", "ignore")

        # Build a map: objectid in the root model -> local XY bounds of its mesh.
        # Objects are either inline (<object id><mesh>) or a component pointing
        # at 3D/Objects/object_N.model. Component transforms are honoured.
        root_objs = {}
        for om in re.finditer(
            r'<object\s+id="(\d+)"[^>]*>(.*?)</object>', model, re.S
        ):
            oid, body = om.group(1), om.group(2)
            inline = _xy_bounds(_parse_vertices(body))
            if inline is not None:
                root_objs[oid] = inline
                continue
            comp = re.search(
                r'<component[^>]*\bp:path="([^"]+)"[^>]*\bobjectid="(\d+)"'
                r'(?:[^>]*\btransform="([^"]+)")?',
                body,
            ) or re.search(
                r'<component[^>]*\bobjectid="(\d+)"[^>]*\bp:path="([^"]+)"'
                r'(?:[^>]*\btransform="([^"]+)")?',
                body,
            )
            if not comp:
                continue
            # Normalise group order across the two regex shapes
            groups = comp.groups()
            if groups[0].startswith("/") or groups[0].endswith(".model"):
                path, sub_oid, ctrans = groups[0], groups[1], groups[2]
            else:
                sub_oid, path, ctrans = groups[0], groups[1], groups[2]
            member = path.lstrip("/")
            if member not in names:
                continue
            sub_xml = zf.read(member).decode("utf-8", "ignore")
            sub_obj = re.search(
                rf'<object\s+id="{sub_oid}"[^>]*>(.*?)</object>', sub_xml, re.S
            )
            if not sub_obj:
                continue
            bxy = _xy_bounds(_parse_vertices(sub_obj.group(1)))
            if bxy is None:
                continue
            if ctrans:
                bxy = _apply_affine_xy(bxy, [float(x) for x in ctrans.split()])
            root_objs[oid] = bxy

    # Walk build items, accumulate world XY bbox.
    items = list(
        re.finditer(r'(<item\b[^>]*\btransform=")([^"]+)("[^>]*/>)', model)
    )
    if not items:
        return 0, "no build items"

    world = None
    parsed = []
    for it in items:
        nums = [float(x) for x in it.group(2).split()]
        oid_m = re.search(r'objectid="(\d+)"', it.group(0))
        oid = oid_m.group(1) if oid_m else None
        local = root_objs.get(oid)
        parsed.append((it, nums, local))
        if local is None:
            continue
        wb = _apply_affine_xy(local, nums)
        if world is None:
            world = list(wb)
        else:
            world = [min(world[0], wb[0]), min(world[1], wb[1]),
                     max(world[2], wb[2]), max(world[3], wb[3])]

    if world is None:
        return 0, "could not resolve object bounds"

    minx, miny, maxx, maxy = world
    on_plate = (minx >= 0.0 and miny >= 0.0
                and maxx <= _P2S_BED_MM and maxy <= _P2S_BED_MM)
    if on_plate:
        return 0, "already on plate"

    dx = _PLATE_CENTRE - (minx + maxx) / 2.0
    dy = _PLATE_CENTRE - (miny + maxy) / 2.0

    new_model = model
    for it, nums, _ in parsed:
        nums[9] += dx
        nums[10] += dy
        new_t = " ".join(f"{n:g}" for n in nums)
        new_model = new_model.replace(
            it.group(0), it.group(1) + new_t + it.group(3), 1
        )

    fd, tmp = tempfile.mkstemp(suffix=".3mf")
    os.close(fd)
    try:
        with zipfile.ZipFile(zip_path) as zin, \
             zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "3D/3dmodel.model":
                    data = new_model.encode("utf-8")
                zout.writestr(item, data)
        shutil.move(tmp, zip_path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

    return len(parsed), f"centred (shifted {dx:+.1f}, {dy:+.1f}mm)"


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

    # Per-filament array consistency: source 3MFs are often multi-filament
    # (one slot per AMS bay) even when a model uses one color. The bake step
    # shrinks SOME per-filament arrays to length 1 and leaves the rest at the
    # source length, which BS's GUI rejects as "Invalid configuration file"
    # (the headless slicer tolerates it). Re-align every per-filament array to
    # the source's filament count so the output stays as self-consistent as the
    # GUI-valid source. See failure-log 2026-06-04.
    source_lengths = _read_source_lengths(str(input_path))
    _normalize_filament_array_lengths(
        str(output_path), source_lengths, color=filament_color
    )

    # Ensure the object sits on the plate. Bare-geometry / web-tool sources
    # (and BS-CLI retargets of them) can land off-plate, which BS rejects with
    # rc=-50. Idempotent — on-plate files are untouched. See failure-log Jun 3.
    moved, place_msg = _ensure_on_plate(str(output_path))

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

    warnings: list[str] = []
    if moved:
        warnings.append(f"Re-arranged object onto plate: {place_msg}")

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
        warnings=warnings,
    )


def default_output(input_path: str) -> str:
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_ready{p.suffix}"))
