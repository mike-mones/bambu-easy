"""Pick which nozzle a 3MF should use, and check it against the live printer."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass

SUPPORTED_NOZZLES = ("0.2", "0.4", "0.6", "0.8")


@dataclass
class NozzleDecision:
    nozzle: str           # canonical "0.4mm"
    diameter: str         # bare "0.4"
    source: str
    mismatch: bool = False
    attached: str | None = None


def _normalize(value: str) -> str:
    """Accept '0.4', '0.4mm', '0.40', '0.40mm' → '0.4'."""
    v = str(value).strip().lower().replace("mm", "").strip()
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return v


def read_nozzle_from_3mf(path: str) -> str | None:
    """Return bare diameter string ('0.4') from a 3MF, or None."""
    try:
        with zipfile.ZipFile(path) as zf:
            if "Metadata/project_settings.config" not in zf.namelist():
                return None
            settings = json.loads(zf.read("Metadata/project_settings.config"))
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError):
        return None
    nd = settings.get("nozzle_diameter")
    if isinstance(nd, list) and nd:
        return _normalize(nd[0])
    if isinstance(nd, str) and nd:
        return _normalize(nd)
    return None


def pick_nozzle(
    source_3mf: str,
    attached_diameter: str | None,
    override: str | None = None,
) -> NozzleDecision:
    """Resolve a nozzle choice and (if printer online) flag mismatch.

    Args:
        source_3mf: path to the input 3MF.
        attached_diameter: live printer's nozzle (bare '0.4') or None if offline.
        override: user --nozzle flag (bare or with 'mm') or None.
    """
    if override:
        chosen = _normalize(override)
        source = "user override (--nozzle)"
    else:
        baked = read_nozzle_from_3mf(source_3mf)
        if baked:
            chosen = baked
            source = "baked in source 3MF"
        else:
            # TODO(v2): mesh-geometry inference. For v1, default + warn.
            chosen = "0.4"
            source = "default (no nozzle in source 3MF; geometry inference is TODO)"

    if chosen not in SUPPORTED_NOZZLES:
        raise ValueError(
            f"Unsupported nozzle {chosen!r}. Supported: {', '.join(SUPPORTED_NOZZLES)}mm."
        )

    mismatch = False
    if attached_diameter is not None:
        attached = _normalize(attached_diameter)
        mismatch = (attached != chosen)
        return NozzleDecision(
            nozzle=f"{chosen}mm",
            diameter=chosen,
            source=source,
            mismatch=mismatch,
            attached=attached,
        )
    return NozzleDecision(
        nozzle=f"{chosen}mm",
        diameter=chosen,
        source=source,
        mismatch=False,
        attached=None,
    )
