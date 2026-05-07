"""Detect whether a source 3MF was built for the Bambu Lab P2S.

MakerWorld files are uploaded by users with whatever printer they happen to
own. When that printer isn't a P2S, the 3MF carries A1/X1/P1-flavored
gcode templates, mechanical limits, and `print_compatible_printers`
constraints that Bambu Studio (correctly) refuses to slice on a P2S.

We tried Python-side aggressive normalization and crashed BS itself.
The right answer is: detect non-P2S sources up-front, and tell the user
to open the file in BS once, switch to P2S, and save. After that, all
subsequent runs work cleanly.
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass

from ._engine.bake_3mf_settings import read_settings


_P2S_TOKENS = ("P2S",)


@dataclass
class SourceCheck:
    is_p2s: bool
    detected_printer: str | None      # human-readable label, e.g. "Bambu Lab A1 mini"
    raw_printer_settings_id: str
    raw_compatible: list[str]


def _flatten(value) -> str:
    """Lists in BS configs are sometimes JSON-as-string. Normalize."""
    if isinstance(value, list):
        return value[0] if value else ""
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list) and parsed:
                    return parsed[0]
            except (ValueError, TypeError):
                pass
        return s
    return ""


def check_source_3mf(path: str) -> SourceCheck:
    """Inspect a 3MF and decide whether its embedded settings target the P2S."""
    try:
        with zipfile.ZipFile(path) as zf:
            settings = read_settings(zf)
    except (zipfile.BadZipFile, KeyError, FileNotFoundError):
        # Either not a 3MF or no project_settings.config — be permissive.
        # The downstream bake/validate pipeline will surface a clear error.
        return SourceCheck(
            is_p2s=True,
            detected_printer=None,
            raw_printer_settings_id="",
            raw_compatible=[],
        )

    raw_psi = _flatten(settings.get("printer_settings_id", ""))

    raw_compat = settings.get("print_compatible_printers", "")
    compat_list: list[str] = []
    if isinstance(raw_compat, list):
        compat_list = [str(x) for x in raw_compat]
    elif isinstance(raw_compat, str) and raw_compat.strip():
        s = raw_compat.strip()
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    compat_list = [str(x) for x in parsed]
            except (ValueError, TypeError):
                compat_list = [s]
        else:
            compat_list = [s]

    haystack = " ".join([raw_psi, *compat_list])
    is_p2s = any(tok in haystack for tok in _P2S_TOKENS)

    detected = None
    if not is_p2s:
        # Pick the most descriptive label we have.
        if raw_psi:
            detected = raw_psi
        elif compat_list:
            detected = compat_list[0]
        else:
            detected = "(unknown — no printer metadata)"

    return SourceCheck(
        is_p2s=is_p2s,
        detected_printer=detected,
        raw_printer_settings_id=raw_psi,
        raw_compatible=compat_list,
    )
