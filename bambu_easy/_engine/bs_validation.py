# VENDORED FROM /Users/mikemones/Documents/3D Printing/Scripts/bs_validation.py at commit 4a8bb90ad5f901257066081baea1a40473d3cb68. Do not edit here — sync via tools/sync_engine.sh.

"""Bambu Studio settings validation — both static (enum + cross-rules) and
oracle (headless BS CLI slice).

This module is intentionally dependency-light: pure-stdlib only. It is
imported by:
  - `export_3mf.py` — to validate every 3MF as part of the export step,
    so a known-bad config can never be silently shipped.
  - `preflight.py` — to expose the same checks at the CLI level.
  - Any project generator that wants to do a confirmation slice.

Rules are derived from observed Bambu Studio behavior, primarily the
2026-05-01 squish-test iteration cascade documented in
`Reference/failure-log.md`. Each rule maps to a real toast/error BS
showed; do not relax a rule unless a future BS release demonstrably
accepts the value (verify with `validate_bs_cli`).

Public API:
  validate_bs_settings(settings)      -> list[str]   # static checks
  validate_bs_cli(path, ...)          -> (ok, msg)   # oracle
  ValidationError                                      # raised by helpers
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile


class ValidationError(Exception):
    """Raised when a 3MF or settings dict fails BS validation."""


# =============================================================================
# Canonical enum tables. Source: scan of system process JSONs in
# ~/Library/Application Support/BambuStudio/system/BBL/process + observed
# BS rejections in failure-log.md. Add to these tables when a new
# legitimate value is verified by `validate_bs_cli` to be accepted.
# =============================================================================

VALID_SPARSE_INFILL_PATTERNS = frozenset({
    "concentric", "zig-zag", "crosshatch", "rectilinear",
    "monotonicline", "grid", "triangles", "tri-hexagon", "stars",
    "cubic", "adaptivecubic", "octagramspiral", "hilbertcurve",
    "archimedeanchords", "honeycomb", "gyroid", "lightning",
    "supportcubic", "alignedrectilinear",
})

# Patterns that BS allows when sparse_infill_density >= 100% (solid fill).
# Observed: 'grid' and 'gyroid' are rejected at 100% with
# "<pattern> doesn't work at 100% density".
SOLID_COMPATIBLE_SPARSE_PATTERNS = frozenset({
    "zig-zag", "concentric", "rectilinear",
    "monotonicline", "alignedrectilinear",
})

VALID_SURFACE_PATTERNS = frozenset({
    "monotonic", "monotonicline", "concentric",
    "rectilinear", "alignedrectilinear",
    "hilbertcurve", "archimedeanchords", "octagramspiral",
})

VALID_IRONING_TYPES = frozenset({"no ironing", "top", "topmost", "all"})

VALID_SEAM_POSITIONS = frozenset({"aligned", "random", "nearest", "back"})

# Per-extruder keys that must be at least length 2 on the P2S (2 extruder
# variants: Direct Drive Standard / High Flow). Trimming these to length 1
# causes BS to throw std::out_of_range on config parse, which surfaces
# as "vector" (CLI) or "no geometry data" (GUI).
P2S_PER_EXTRUDER_KEYS = ("filament_extruder_variant",)

# Default Bambu Studio CLI path on macOS. Override via the bs_path arg.
DEFAULT_BS_CLI_PATH = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"


# =============================================================================
# Static validation
# =============================================================================

def validate_bs_settings(settings: dict) -> list[str]:
    """Static validation of BS-specific enum values and cross-rules.

    Catches the kind of error BS reports as a toast on file open
    ("Invalid value monotonic", "grid doesn't work at 100%% density", etc.)
    without needing to launch BS.

    Args:
        settings: a project_settings.config dict (parsed JSON).

    Returns:
        list of human-readable error strings (empty if clean).
    """
    errors: list[str] = []

    sip = settings.get("sparse_infill_pattern")
    if sip and sip not in VALID_SPARSE_INFILL_PATTERNS:
        errors.append(
            f"sparse_infill_pattern={sip!r} is not a valid BS value. "
            f"'monotonic' is rejected here (top/bottom surface only). "
            f"Valid options include 'grid', 'gyroid', 'zig-zag', 'crosshatch', "
            f"'concentric', etc."
        )

    # Cross-rule: 100% density requires a solid-compatible pattern.
    density_str = str(settings.get("sparse_infill_density", "")).rstrip("%")
    try:
        density_pct = float(density_str) if density_str else 0.0
    except ValueError:
        density_pct = 0.0
    if (density_pct >= 100.0 and sip
            and sip not in SOLID_COMPATIBLE_SPARSE_PATTERNS):
        errors.append(
            f"sparse_infill_pattern={sip!r} doesn't work at 100% density. "
            f"BS requires a solid-compatible pattern: "
            f"{sorted(SOLID_COMPATIBLE_SPARSE_PATTERNS)}."
        )

    for key in ("top_surface_pattern", "bottom_surface_pattern"):
        v = settings.get(key)
        if v and v not in VALID_SURFACE_PATTERNS:
            errors.append(
                f"{key}={v!r} is not a valid BS value. "
                f"Valid: {sorted(VALID_SURFACE_PATTERNS)}"
            )

    ironing = settings.get("ironing_type")
    if ironing and ironing not in VALID_IRONING_TYPES:
        errors.append(
            f"ironing_type={ironing!r} is not a valid BS value. "
            f"Valid: {sorted(VALID_IRONING_TYPES)}. "
            f"('TopSurface' is a known wrong value — BS silently maps it "
            f"to 'no ironing'.)"
        )

    seam = settings.get("seam_position")
    if seam and seam not in VALID_SEAM_POSITIONS:
        errors.append(
            f"seam_position={seam!r} is not a valid BS value. "
            f"Valid: {sorted(VALID_SEAM_POSITIONS)}"
        )

    # Per-extruder array length check (P2S has 2 extruder variants).
    for key in P2S_PER_EXTRUDER_KEYS:
        v = settings.get(key)
        if isinstance(v, list) and len(v) == 1:
            errors.append(
                f"{key} has length 1 — P2S encodes 2 extruder variants. "
                f"This will cause BS to reject the file with a 'vector' "
                f"parse error. Likely cause: an over-aggressive array trim "
                f"in export_3mf.py that collapsed per-extruder data."
            )

    return errors


def assert_bs_settings_valid(settings: dict) -> None:
    """Raise ValidationError if `settings` has any blocking BS errors.

    Convenience wrapper for callers that want exception-style failure
    (e.g., export_3mf.export_bambu_3mf, which should refuse to write a
    known-bad file).
    """
    errors = validate_bs_settings(settings)
    if errors:
        msg = "BS settings validation failed:\n  - " + "\n  - ".join(errors)
        raise ValidationError(msg)


# =============================================================================
# Oracle: invoke BS headlessly
# =============================================================================

def validate_bs_cli(input_path: str,
                    bs_path: str | None = None,
                    timeout_sec: int = 120) -> tuple[bool, str]:
    """Run Bambu Studio's headless slicer to confirm the 3MF actually loads
    and slices.

    This is the strongest form of validation — BS itself is the oracle.
    Slow (~10-30s per slice). If BS isn't installed, returns
    (True, "skipped") so callers can opt in without hard-requiring BS.

    Args:
        input_path: path to a .3mf file.
        bs_path: path to the Bambu Studio executable. Defaults to the
            standard macOS install location.
        timeout_sec: seconds to wait before giving up.

    Returns:
        (ok, message). `ok` is False if BS rejected the file or the
        invocation failed. `message` is a human-readable summary.
    """
    if bs_path is None:
        bs_path = DEFAULT_BS_CLI_PATH
    if not os.path.exists(bs_path):
        return True, f"Bambu Studio CLI not found at {bs_path} — skipped"

    if not os.path.exists(input_path):
        return False, f"File not found: {input_path}"

    out_dir = tempfile.mkdtemp(prefix="bs_validate_")
    try:
        proc = subprocess.run(
            [bs_path, "--slice", "0", "--outputdir", out_dir, input_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        result_json = os.path.join(out_dir, "result.json")
        if os.path.exists(result_json):
            with open(result_json) as f:
                data = json.load(f)
            rc = data.get("return_code")
            err = data.get("error_string", "")
            if rc == 0:
                return True, "BS sliced successfully (rc=0)"
            return False, f"BS rejected the 3MF: rc={rc}, error={err!r}"
        # No result.json -> BS didn't reach validation. Surface stderr/stdout.
        tail = "\n".join(proc.stderr.splitlines()[-5:]) or proc.stdout[-500:]
        return False, f"BS exited without result.json. Tail: {tail}"
    except subprocess.TimeoutExpired:
        return False, f"BS slice timed out after {timeout_sec}s"
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


# =============================================================================
# CLI entry: `python bs_validation.py <file.3mf>` for ad-hoc checks
# =============================================================================

def _main() -> int:
    import argparse
    import zipfile
    import sys

    parser = argparse.ArgumentParser(
        description="Validate a 3MF against BS enum/cross-rules and "
                    "(optionally) the headless BS CLI.",
    )
    parser.add_argument("input", help="Path to a .3mf file")
    parser.add_argument(
        "--bs-validate", action="store_true",
        help="Also run BS headless slice (slow, ~30s).",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: not found: {args.input}", file=sys.stderr)
        return 2

    with zipfile.ZipFile(args.input) as z:
        settings = json.loads(z.read("Metadata/project_settings.config"))

    errors = validate_bs_settings(settings)
    if errors:
        print(f"BS static validation FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("BS static validation: PASS")

    if args.bs_validate:
        print("Running BS headless slice (this takes ~10-30s)...")
        ok, msg = validate_bs_cli(args.input)
        prefix = "  ✓" if ok else "  ✗"
        print(f"{prefix} {msg}")
        if not ok:
            return 2

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(_main())
