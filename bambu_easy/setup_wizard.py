"""Interactive `bambu-easy --setup` wizard.

Walks a first-time user through:
  1. printer_config.json (IP + serial + LAN access code)
  2. Vendored user-preset install into Bambu Studio
  3. A doctor run to confirm everything works

Designed for people who have never touched a CLI configuration file.
Every prompt has a hint about where to find the value on the printer
or in Bambu Studio.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .install_presets import install_presets
from .printer import config_path


_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)
_SERIAL_RE = re.compile(r"^[A-Z0-9]{8,20}$", re.IGNORECASE)
_ACCESS_CODE_RE = re.compile(r"^[0-9a-fA-F]{8}$")


def _ask(prompt: str, default: str | None = None, validator=None, hint: str | None = None) -> str:
    """Prompt for input with optional default, hint, and validator."""
    if hint:
        print(f"   💡 {hint}")
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            val = input(f"   {prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n   Aborted.")
            raise SystemExit(130)
        if not val and default is not None:
            val = default
        if not val:
            print("   ⚠️  Required.")
            continue
        if validator and not validator(val):
            print("   ⚠️  That doesn't look right. Try again.")
            continue
        return val


def _ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        val = input(f"   {prompt}{suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n   Aborted.")
        raise SystemExit(130)
    if not val:
        return default
    return val.startswith("y")


def run_setup() -> int:
    print("bambu-easy setup")
    print("════════════════")
    print()
    print("This wizard will get you ready to print in about 2 minutes.")
    print("You'll need:")
    print("  • Your printer powered on, with LAN Only Mode enabled.")
    print("  • Bambu Studio installed (https://bambulab.com/en/download/studio).")
    print()

    # --- Step 1: printer_config.json ---
    print("───── 1/3 · Printer connection ─────")
    cfg_path = config_path()
    cfg_path = Path(cfg_path)

    existing: dict = {}
    if cfg_path.exists():
        try:
            existing = json.loads(cfg_path.read_text(encoding="utf-8"))
            print(f"   Existing config found: {cfg_path}")
            if not _ask_yes_no("Overwrite it?", default=False):
                print("   Keeping existing printer_config.json.")
                existing_was_kept = True
            else:
                existing_was_kept = False
        except (OSError, json.JSONDecodeError):
            existing_was_kept = False
    else:
        existing_was_kept = False

    if not existing_was_kept:
        print()
        print("   On the printer touchscreen, go to:")
        print("     Settings (gear) → WLAN → look for the IP address.")
        ip = _ask(
            "Printer IP address",
            default=existing.get("printer_ip"),
            validator=lambda v: _IPV4_RE.match(v) is not None,
            hint="Looks like 192.168.1.234",
        )

        print()
        print("   On the printer screen, go to:")
        print("     Settings (gear) → Device → Device Info → SN.")
        serial = _ask(
            "Printer serial number",
            default=existing.get("serial"),
            validator=lambda v: _SERIAL_RE.match(v) is not None,
            hint="A short alphanumeric string like 03919C470500378",
        )

        print()
        print("   On the printer screen, go to:")
        print("     Settings → General → LAN Only Mode → make sure it's ON.")
        print("     The 8-character Access Code appears below the toggle.")
        access = _ask(
            "LAN access code (8 characters)",
            default=existing.get("access_code"),
            validator=lambda v: _ACCESS_CODE_RE.match(v) is not None,
            hint="Exactly 8 characters (digits and/or a-f), e.g. 12345678 or da8ce55e",
        )

        cfg = {
            "printer_ip": ip,
            "serial": serial,
            "access_code": access,
        }
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        try:
            os.chmod(cfg_path, 0o600)
        except OSError:
            pass
        print(f"   ✅ Wrote {cfg_path}")
    print()

    # --- Step 2: Install user presets into Bambu Studio ---
    print("───── 2/3 · Filament presets ─────")
    print("   bambu-easy ships filament presets that pin the correct nozzle")
    print("   temperatures (e.g. PLA Matte at 230°C). These need to be copied")
    print("   into your Bambu Studio install once.")
    print()
    if _ask_yes_no("Install them now?", default=True):
        result = install_presets(overwrite=False)
        if not result.success:
            print(f"   ⚠️  {result.message}")
            print("   You can re-run this later with: bambu-easy --install-presets")
        else:
            for name in result.installed:
                print(f"   ✅ Installed: {name}")
            for name in result.skipped:
                print(f"   ⏭  Already there: {name}")
            print(f"   Target: {result.target_dir}")
            if result.installed:
                print()
                print("   ℹ️  IMPORTANT: Quit and re-open Bambu Studio so it picks up")
                print("      the new presets.")
    else:
        print("   Skipping. You can run this later: bambu-easy --install-presets")
    print()

    # --- Step 3: Doctor ---
    print("───── 3/3 · Health check ─────")
    if _ask_yes_no("Run `bambu-easy --doctor` now to verify everything?", default=True):
        from .cli import cmd_doctor
        rc = cmd_doctor()
        if rc != 0:
            print()
            print("   ⚠️  Doctor reported issues. Address them above and re-run:")
            print("       bambu-easy --doctor")
            return rc

    print()
    print("✅ Setup complete!")
    print()
    print("   Try it now:")
    print("     bambu-easy <some_makerworld_file.3mf>")
    return 0
