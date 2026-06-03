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

    # Single-color normalization: source 3MFs are often multi-filament even
    # when only one is used. Trim per-filament arrays to length 1 so the
    # AMS Send dialog isn't confused.
    _normalize_to_single_filament(str(output_path), color=filament_color)

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
