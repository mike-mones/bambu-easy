"""Auto-convert non-P2S source 3MFs to P2S using Bambu Studio's CLI.

When a MakerWorld download was uploaded for an A1/X1/P1/etc., its
embedded gcode templates and machine limits make BS reject it on the
P2S. The GUI handles this with a "switch to current printer" prompt;
the headless CLI handles it via `--load-settings` + `--export-3mf`,
which is exactly what we use here.

We aim conservative: load the P2S 0.4mm machine + a generic 0.20mm
process + a generic PLA filament. The bake step downstream rewrites
filament/process/nozzle to the user's actual choices, so these initial
loads only need to be enough to make BS happy at retarget time.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Default macOS BS preset locations. BS keeps system presets here on macOS;
# Linux/Windows paths differ but bambu-easy is Mac-tested for now.
_BS_SYSTEM_ROOT = Path(
    os.path.expanduser("~/Library/Application Support/BambuStudio/system/BBL")
)


@dataclass
class ConvertResult:
    success: bool
    converted_path: str | None
    message: str


def _find_preset(category: str, candidates: list[str]) -> str | None:
    """Look for the first preset filename that exists, in order of preference."""
    folder = _BS_SYSTEM_ROOT / category
    if not folder.is_dir():
        return None
    for name in candidates:
        p = folder / name
        if p.is_file():
            return str(p)
    return None


def convert_to_p2s(
    input_path: str,
    bs_path: str = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    timeout: float = 60.0,
) -> ConvertResult:
    """Run BS CLI to retarget a 3MF onto the P2S 0.4mm machine.

    Returns a ConvertResult. On success, `converted_path` is a fresh 3MF
    in a temp directory — the caller is responsible for moving/keeping
    it as needed.
    """
    if not os.path.exists(bs_path):
        return ConvertResult(
            success=False,
            converted_path=None,
            message=f"Bambu Studio not found at {bs_path}",
        )

    machine = _find_preset("machine", ["Bambu Lab P2S 0.4 nozzle.json"])
    process = _find_preset("process", [
        "0.20mm Standard @BBL P2S.json",
        "0.20mm Standard @BBL P2S 0.4 nozzle.json",
    ])
    filament = _find_preset("filament", [
        "Bambu PLA Matte @BBL P2S.json",
        "Bambu PLA Basic @BBL P2S.json",
        "Generic PLA @BBL P2S.json",
    ])
    if not (machine and process and filament):
        missing = [
            label for label, val in
            [("machine", machine), ("process", process), ("filament", filament)]
            if not val
        ]
        return ConvertResult(
            success=False,
            converted_path=None,
            message=(
                f"Couldn't find P2S system presets for: {', '.join(missing)}. "
                f"Looked in {_BS_SYSTEM_ROOT}. Has Bambu Studio been opened "
                "at least once on this machine?"
            ),
        )

    workdir = tempfile.mkdtemp(prefix="bambu_easy_convert_")
    out_name = "converted.3mf"
    out_path = os.path.join(workdir, out_name)

    cmd = [
        bs_path,
        "--load-settings", f"{machine};{process}",
        "--load-filaments", filament,
        "--outputdir", workdir,
        "--export-3mf", out_name,
        input_path,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(workdir, ignore_errors=True)
        return ConvertResult(
            success=False,
            converted_path=None,
            message=f"Bambu Studio CLI timed out after {timeout:.0f}s",
        )

    if not os.path.exists(out_path):
        # Capture last useful line of stderr/stdout for diagnostics
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
        shutil.rmtree(workdir, ignore_errors=True)
        return ConvertResult(
            success=False,
            converted_path=None,
            message=(
                f"BS CLI did not write output. rc={proc.returncode}. "
                f"Tail: {' | '.join(tail)}"
            ),
        )

    return ConvertResult(
        success=True,
        converted_path=out_path,
        message=f"Converted via BS CLI ({os.path.getsize(out_path) // 1024}KB)",
    )
