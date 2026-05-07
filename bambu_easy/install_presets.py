"""Install bambu-easy's vendored user presets into Bambu Studio.

Bambu Studio stores user presets in a per-user folder. The presets we
ship reference filament_settings_id values like
"Mike PLA Matte 230C @BBL P2S (0.4 nozzle)" — those names are baked
into FILAMENT_PRESET_IDS in print_profiles.py and MUST exist in the
user's BS install or BS will silently fall back to system presets that
have the wrong nozzle temperature (the May 1 2026 230°C bug).

This module finds the BS user-data folder, picks the active user
account subfolder, and copies our vendored presets into the
filament/ subdirectory.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

# Vendored presets ship inside the package.
_VENDORED_ROOT = Path(__file__).resolve().parent / "data" / "presets" / "filament"


@dataclass
class InstallResult:
    success: bool
    installed: list[str]
    skipped: list[str]
    target_dir: str | None
    message: str


def bs_user_data_root() -> Path | None:
    """Return the Bambu Studio per-OS user-data root, or None if unknown."""
    system = platform.system()
    if system == "Darwin":
        return Path(os.path.expanduser("~/Library/Application Support/BambuStudio"))
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "BambuStudio"
        return None
    if system == "Linux":
        return Path(os.path.expanduser("~/.config/BambuStudio"))
    return None


def find_active_user_dir(bs_root: Path) -> Path | None:
    """BS keeps per-account subfolders under user/<numeric_id>/.

    Pick the one whose preset_folder is named in BambuStudio.conf, falling
    back to the most-recently-modified account folder if conf is missing.
    """
    user_root = bs_root / "user"
    if not user_root.is_dir():
        return None

    # Try BambuStudio.conf hint first
    conf = bs_root / "BambuStudio.conf"
    if conf.is_file():
        try:
            text = conf.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("preset_folder"):
                    # Format: preset_folder = 2521976645
                    _, _, val = line.partition("=")
                    val = val.strip().strip('"')
                    if val:
                        candidate = user_root / val
                        if candidate.is_dir():
                            return candidate
        except OSError:
            pass

    # Fallback: most-recently-modified subdir
    subdirs = [p for p in user_root.iterdir() if p.is_dir()]
    if not subdirs:
        return None
    return max(subdirs, key=lambda p: p.stat().st_mtime)


def list_vendored_presets() -> list[Path]:
    if not _VENDORED_ROOT.is_dir():
        return []
    return sorted(_VENDORED_ROOT.glob("*.json"))


def install_presets(
    overwrite: bool = False,
    bs_root: Path | None = None,
) -> InstallResult:
    """Copy vendored user presets into the active BS user/<id>/filament/ folder."""
    root = bs_root or bs_user_data_root()
    if root is None:
        return InstallResult(
            success=False, installed=[], skipped=[], target_dir=None,
            message=f"Unsupported platform: {platform.system()}",
        )
    if not root.is_dir():
        return InstallResult(
            success=False, installed=[], skipped=[], target_dir=None,
            message=(
                f"Bambu Studio user-data folder not found at {root}. "
                "Open Bambu Studio at least once to create it."
            ),
        )

    user_dir = find_active_user_dir(root)
    if user_dir is None:
        return InstallResult(
            success=False, installed=[], skipped=[], target_dir=None,
            message=(
                f"No Bambu Studio user account found under {root / 'user'}. "
                "Sign in to Bambu Studio at least once."
            ),
        )

    target = user_dir / "filament"
    target.mkdir(parents=True, exist_ok=True)

    presets = list_vendored_presets()
    if not presets:
        return InstallResult(
            success=False, installed=[], skipped=[], target_dir=str(target),
            message=f"No vendored presets found in {_VENDORED_ROOT}",
        )

    installed: list[str] = []
    skipped: list[str] = []
    for src in presets:
        dst = target / src.name
        if dst.exists() and not overwrite:
            skipped.append(src.name)
            continue
        shutil.copy2(src, dst)
        installed.append(src.name)

    msg = f"Installed {len(installed)} preset(s) into {target}"
    if skipped:
        msg += f" ({len(skipped)} already existed; pass overwrite=True to replace)"
    return InstallResult(
        success=True,
        installed=installed,
        skipped=skipped,
        target_dir=str(target),
        message=msg,
    )


def verify_preset_names_match_engine() -> tuple[bool, list[str]]:
    """Sanity check: every USER-preset name (i.e., not a Bambu system preset)
    listed in FILAMENT_PRESET_IDS for nozzles we ship presets for must have
    a matching vendored .json file.

    Returns (ok, missing_names). Bambu-shipped system presets (anything not
    prefixed "Mike ") are skipped — BS provides them out of the box.
    """
    from ._engine.print_profiles import FILAMENT_PRESET_IDS

    vendored = {p.stem for p in list_vendored_presets()}
    shipped_nozzles = {"0.2mm", "0.4mm"}  # 0.6/0.8 user presets not yet created
    missing: list[str] = []
    for (nozzle, _material), preset_name in FILAMENT_PRESET_IDS.items():
        if nozzle not in shipped_nozzles:
            continue
        # Only user presets need to be installed. Bambu system presets
        # ("Bambu PLA Basic @BBL P2S" etc.) ship with Bambu Studio.
        if not preset_name.startswith("Mike "):
            continue
        if preset_name not in vendored:
            missing.append(preset_name)
    return len(missing) == 0, missing
