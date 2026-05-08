"""Decide which MATERIALS key to use for the print."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass

SUPPORTED_MATERIALS = ("PLA Matte", "PLA Basic", "PLA Silk+", "PETG-HF")


class FilamentResolutionError(Exception):
    """Raised when no acceptable filament can be auto-determined."""


@dataclass
class FilamentDecision:
    material: str
    source: str
    slot: str | None = None  # e.g. "A1"
    color: str | None = None  # hex like '#B76E79' from AMS, or None


def _map_name_to_material(raw: str) -> str | None:
    """Map a Bambu filament name (sub_brand or settings_id) to a MATERIALS key."""
    if not raw:
        return None
    s = raw.lower()
    # Order matters: check more specific patterns first
    if "petg" in s and ("hf" in s or "-hf" in s.replace(" ", "")):
        return "PETG-HF"
    if "petg" in s:
        # Default PETG to PETG-HF (the only PETG we support); user can override
        return "PETG-HF"
    if "matte" in s:
        return "PLA Matte"
    if "silk" in s:
        return "PLA Silk+"
    if "pla" in s:
        return "PLA Basic"
    return None


def read_filament_from_3mf(path: str) -> str | None:
    """Return a Bambu-style filament_settings_id string from a 3MF, or None."""
    try:
        with zipfile.ZipFile(path) as zf:
            if "Metadata/project_settings.config" not in zf.namelist():
                return None
            settings = json.loads(zf.read("Metadata/project_settings.config"))
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError):
        return None
    fid = settings.get("filament_settings_id")
    if isinstance(fid, list) and fid:
        return str(fid[0])
    if isinstance(fid, str) and fid:
        return fid
    return None


def _spool_color_hex(spool: dict) -> str | None:
    """Return a '#RRGGBB' hex color from an AMS spool dict, or None.

    Bambu MQTT returns tray_color as 8-char RRGGBBAA (e.g. 'B76E79FF').
    BS project_settings.config wants '#RRGGBB' (no alpha).
    """
    raw = (spool.get("color") or "").strip().upper()
    if not raw:
        return None
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) >= 6 and all(c in "0123456789ABCDEF" for c in raw[:6]):
        return f"#{raw[:6]}"
    return None


def _spool_label(spool: dict) -> str:
    """Best-effort name string from a spool dict."""
    sub = spool.get("sub_brand") or ""
    typ = spool.get("type") or ""
    return f"{sub} {typ}".strip() or typ or sub


def pick_filament(
    source_3mf: str,
    spools: list[dict] | None,
    override: str | None = None,
    slot_hint: str | None = None,
) -> FilamentDecision:
    """Choose a filament. See README §Key design rules for priority."""
    if override:
        if override not in SUPPORTED_MATERIALS:
            raise FilamentResolutionError(
                f"Unsupported filament {override!r}. Supported: "
                f"{', '.join(SUPPORTED_MATERIALS)}."
            )
        # If the user override matches a loaded spool, harvest its color too.
        # This lets `--filament "PLA Silk+"` still get the correct AMS color.
        color = None
        slot = None
        if spools:
            for sp in spools:
                if sp.get("type") and _map_name_to_material(_spool_label(sp)) == override:
                    color = _spool_color_hex(sp)
                    slot = sp.get("slot")
                    break
        return FilamentDecision(
            material=override,
            source="user override (--filament)",
            slot=slot,
            color=color,
        )

    # AMS path
    if spools:
        # Prefer slot_hint
        if slot_hint:
            for sp in spools:
                if sp.get("slot") == slot_hint:
                    name = _spool_label(sp)
                    mat = _map_name_to_material(name)
                    if mat:
                        return FilamentDecision(
                            material=mat,
                            source=f"AMS {sp['slot']} ({name})",
                            slot=sp["slot"],
                            color=_spool_color_hex(sp),
                        )
        # Most-filled loaded spool that maps
        loaded = [s for s in spools if s.get("type") and _map_name_to_material(_spool_label(s))]
        if loaded:
            def remain(s):
                try:
                    return int(s.get("remain", -1))
                except (TypeError, ValueError):
                    return -1
            loaded.sort(key=remain, reverse=True)
            best = loaded[0]
            name = _spool_label(best)
            mat = _map_name_to_material(name)
            assert mat is not None
            return FilamentDecision(
                material=mat,
                source=f"AMS {best['slot']} most filled ({name})",
                slot=best["slot"],
                color=_spool_color_hex(best),
            )

    # Fallback to baked filament_settings_id
    baked = read_filament_from_3mf(source_3mf)
    if baked:
        mat = _map_name_to_material(baked)
        if mat:
            return FilamentDecision(
                material=mat,
                source=f"baked in source 3MF ({baked})",
            )

    raise FilamentResolutionError(
        "Could not determine filament.\n"
        "  - The printer is offline (no AMS data), AND\n"
        "  - The source 3MF does not contain a recognizable filament setting.\n"
        f"  Pass --filament with one of: {', '.join(SUPPORTED_MATERIALS)}."
    )
