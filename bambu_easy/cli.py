"""bambu-easy CLI."""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

from . import __version__
from ._engine.bs_validation import (
    DEFAULT_BS_CLI_PATH,
    ValidationError,
    validate_bs_cli,
)
from .filament_picker import (
    FilamentResolutionError,
    SUPPORTED_MATERIALS,
    pick_filament,
)
from .nozzle_picker import SUPPORTED_NOZZLES, pick_nozzle
from .prepare import default_output, prepare_3mf
from .printer import (
    PrinterConfigError,
    config_path,
    load_config,
    query as query_printer_status,
)
from .source_check import check_source_3mf
from .auto_convert import convert_to_p2s
from .install_presets import install_presets, verify_preset_names_match_engine
from .setup_wizard import run_setup

QUALITY_TIERS = ("fast", "standard", "quality", "premium")


def _info(msg: str) -> None:
    print(msg)


def _ok(msg: str) -> None:
    print(f"✅ {msg}")


def _warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def _fail(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)


def cmd_doctor() -> int:
    print("bambu-easy doctor")
    print("─────────────────")

    # 1. BS CLI
    if os.path.exists(DEFAULT_BS_CLI_PATH):
        _ok(f"Bambu Studio CLI found: {DEFAULT_BS_CLI_PATH}")
    else:
        _warn(f"Bambu Studio CLI NOT found at {DEFAULT_BS_CLI_PATH}")
        print("    Install Bambu Studio from https://bambulab.com/en/download/studio")
        print("    Without it, --bs-validate cannot run (you'll need --skip-bs-validate).")

    # 2. User presets installed in BS
    from .install_presets import (
        bs_user_data_root,
        find_active_user_dir,
        list_vendored_presets,
    )
    bs_root = bs_user_data_root()
    if bs_root and bs_root.is_dir():
        active = find_active_user_dir(bs_root)
        if active:
            target_filament = active / "filament"
            installed = {p.name for p in target_filament.glob("*.json")} if target_filament.is_dir() else set()
            shipped = {p.name for p in list_vendored_presets()}
            missing = shipped - installed
            if not missing:
                _ok(f"Filament user presets installed ({len(shipped)} files)")
            else:
                _warn(f"Filament user presets MISSING: {len(missing)} of {len(shipped)}")
                for name in sorted(missing):
                    print(f"      - {name}")
                print("    Run: bambu-easy --install-presets")
        else:
            _warn(f"No Bambu Studio user account under {bs_root / 'user'}")
            print("    Sign in to Bambu Studio at least once, then run:")
            print("      bambu-easy --install-presets")
    else:
        _warn("Bambu Studio user-data folder not found")
        print("    Open Bambu Studio at least once.")

    # 3. printer_config.json
    cfg_path = config_path()
    try:
        cfg = load_config()
        _ok(f"printer_config.json valid: {cfg_path}")
        print(f"    printer_ip:  {cfg['printer_ip']}")
        print(f"    serial:      {cfg.get('serial', '(missing)')}")
    except PrinterConfigError as exc:
        _fail(str(exc))
        print("    Run: bambu-easy --setup")
        return 1

    # 4. MQTT reachable
    print("Polling printer over MQTT (up to 8s)...")
    status = query_printer_status(cfg, timeout=8.0)
    if status is None:
        _warn("Printer did not respond. Common causes:")
        print("    • Printer is off or asleep.")
        print("    • Printer is on a different Wi-Fi network than this machine.")
        print(f"    • The IP address has changed (current config: {cfg.get('printer_ip')}).")
        print("    • The access code is wrong (re-check it in Bambu Studio or on the printer).")
        print("    • [Rare] Older firmware may need 'LAN Only Mode' enabled (Settings →")
        print("      General → LAN Only Mode). This disables cloud features (mobile app,")
        print("      remote start, remote camera) — only enable as a last resort.")
        print("    bambu-easy can still work — it will fall back to settings baked in the source 3MF.")
        return 0
    _ok(f"Printer online — nozzle {status.get('nozzle_diameter')}mm ({status.get('nozzle_type')})")
    spools = status.get("spools") or []
    loaded = [s for s in spools if s.get("type")]
    if loaded:
        print(f"    AMS: {len(loaded)} loaded slot(s)")
        for s in loaded:
            label = (s.get("sub_brand") or s.get("type") or "?")
            print(f"      {s['slot']}: {label}  ({s.get('remain', '?')}%)")
    return 0


def cmd_self_test(skip_bs_validate: bool, debug: bool) -> int:
    here = Path(__file__).resolve().parent
    fixture = here.parent / "tests" / "fixtures" / "squish_test.3mf"
    if not fixture.exists():
        _fail(f"Bundled test fixture missing: {fixture}")
        return 2
    out = fixture.with_name("squish_test_ready.3mf")
    print(f"Self-test: preparing {fixture}")
    try:
        result = prepare_3mf(
            input_path=str(fixture),
            output_path=str(out),
            nozzle="0.4mm",
            material="PLA Matte",
            tier="standard",
            do_bs_validate=not skip_bs_validate,
        )
    except ValidationError as exc:
        _fail(f"Settings validation failed: {exc}")
        return 2
    except Exception as exc:
        _fail(f"Internal error: {type(exc).__name__}: {exc}")
        if debug:
            traceback.print_exc()
        return 2
    _ok(f"Bake complete: {result.output_path} ({result.settings_count} settings)")
    print(f"   filament_settings_id = {result.filament_settings_id}")
    print(f"   nozzle_temperature   = {result.nozzle_temperature}")
    if result.bs_ok is None:
        _warn("BS validation skipped")
    elif result.bs_ok:
        _ok(f"BS validation: {result.bs_message}")
    else:
        _fail(f"BS validation failed: {result.bs_message}")
        return 2
    # Cleanup
    try:
        out.unlink()
    except OSError:
        pass
    _ok("Self-test passed")
    return 0


def _print_decisions(
    input_path: str,
    nozzle_dec,
    filament_dec,
    tier: str,
    status: dict | None,
) -> None:
    _info(f"🔍 Reading {input_path}")
    if status is not None:
        _ok(f"Live printer online — attached nozzle: {status.get('nozzle_diameter')}mm "
            f"({status.get('nozzle_type', '?')})")
        spools = status.get("spools") or []
        for s in spools:
            if s.get("type"):
                label = (s.get("sub_brand") or s.get("type") or "?")
                print(f"    AMS {s['slot']}: {label} ({s.get('remain', '?')}%)")
    else:
        _warn("Live printer offline (or unreachable) — proceeding with baked-in defaults")
    print("🎯 Decisions:")
    if nozzle_dec.attached is not None:
        match = "matches attached ✅" if not nozzle_dec.mismatch else "MISMATCH ❌"
        print(f"    Nozzle:   {nozzle_dec.nozzle}  ← {nozzle_dec.source} ({match})")
    else:
        print(f"    Nozzle:   {nozzle_dec.nozzle}  ← {nozzle_dec.source}")
    print(f"    Filament: {filament_dec.material}  ← {filament_dec.source}")
    print(f"    Quality:  {tier}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bambu-easy",
        description="Friendly CLI to prepare 3MF files for the Bambu Lab P2S.",
        epilog="Run `bambu-easy --doctor` to verify your install.",
    )
    parser.add_argument("input", nargs="?", help="Source 3MF (typically a MakerWorld download)")
    parser.add_argument("-o", "--output", help="Output path. Default: <input stem>_ready.3mf")
    parser.add_argument("-q", "--quality", choices=QUALITY_TIERS, default="standard")
    parser.add_argument("-f", "--filament", choices=SUPPORTED_MATERIALS, default=None,
                        help="Override auto-detected filament.")
    parser.add_argument("-n", "--nozzle", choices=SUPPORTED_NOZZLES, default=None,
                        help="Override auto-detected nozzle (mm).")
    parser.add_argument("--skip-bs-validate", action="store_true",
                        help="Skip the headless BS slice (faster, less safe).")
    parser.add_argument("--force", action="store_true",
                        help="Bypass nozzle-mismatch hard-stop.")
    parser.add_argument("--no-open", dest="auto_open", action="store_false",
                        help="Don't auto-open the result in Bambu Studio.")
    parser.set_defaults(auto_open=True)
    parser.add_argument("--doctor", action="store_true",
                        help="Check install: BS CLI + printer config + MQTT reachability.")
    parser.add_argument("--self-test", action="store_true",
                        help="Run end-to-end on bundled fixture.")
    parser.add_argument("--setup", action="store_true",
                        help="Interactive first-time setup wizard.")
    parser.add_argument("--install-presets", action="store_true",
                        help="Copy bambu-easy's filament presets into Bambu Studio.")
    parser.add_argument("--debug", action="store_true",
                        help="Show full Python traceback on unexpected errors.")
    parser.add_argument("--version", action="version", version=f"bambu-easy {__version__}")
    args = parser.parse_args(argv)

    if args.setup:
        return run_setup()
    if args.install_presets:
        result = install_presets(overwrite=False)
        if not result.success:
            _fail(result.message)
            return 2
        for name in result.installed:
            _ok(f"Installed: {name}")
        for name in result.skipped:
            print(f"⏭  Already there: {name}")
        print(f"Target: {result.target_dir}")
        if result.installed:
            print("ℹ️  Quit and re-open Bambu Studio so it picks up the new presets.")
        return 0
    if args.doctor:
        return cmd_doctor()
    if args.self_test:
        return cmd_self_test(skip_bs_validate=args.skip_bs_validate, debug=args.debug)

    if not args.input:
        parser.print_help()
        return 0

    input_path = args.input
    if not os.path.exists(input_path):
        _fail(f"Input file not found: {input_path}")
        return 2
    if not input_path.lower().endswith(".3mf"):
        _warn(f"Input does not end in .3mf: {input_path}")

    output_path = args.output or default_output(input_path)
    if os.path.abspath(output_path) == os.path.abspath(input_path):
        _fail("Output path must differ from input — refusing to overwrite the source.")
        return 2

    # 0. Source-printer check. If this 3MF was uploaded for a non-P2S printer
    # (common with MakerWorld downloads), retarget it via BS CLI before
    # continuing. BS does this internally when a user opens such a file in
    # the GUI; we automate the equivalent.
    source = check_source_3mf(input_path)
    if not source.is_p2s:
        _info(f"🔄 Source 3MF was built for {source.detected_printer}.")
        _info("   Retargeting to Bambu Lab P2S via Bambu Studio CLI...")
        conv = convert_to_p2s(input_path)
        if not conv.success:
            _fail(f"Auto-conversion failed: {conv.message}")
            print()
            print("   📋 Fallback (one-time, ~30 seconds):")
            print(f"     1. Open the file in Bambu Studio: {input_path}")
            print("     2. Click YES when asked to switch to your current printer.")
            print("     3. File → Save Project (⌘S / Ctrl+S).")
            print(f"     4. Re-run: bambu-easy {input_path}")
            return 2
        _ok(f"Retargeted ({conv.message})")
        # Replace input_path for the rest of the pipeline; the user's
        # output path is still derived from the ORIGINAL filename so they
        # don't end up with `converted_ready.3mf`.
        input_path = conv.converted_path or input_path

    # 1. Try to query printer (best effort)
    try:
        cfg = load_config()
    except PrinterConfigError as exc:
        _warn(f"printer_config.json: {exc}")
        cfg = None

    status = None
    if cfg is not None:
        status = query_printer_status(cfg, timeout=6.0)

    attached = status.get("nozzle_diameter") if status else None
    spools = status.get("spools") if status else None

    # 2. Resolve nozzle
    try:
        nozzle_dec = pick_nozzle(
            source_3mf=input_path,
            attached_diameter=attached,
            override=args.nozzle,
        )
    except ValueError as exc:
        _fail(str(exc))
        return 2

    # 3. Resolve filament
    try:
        filament_dec = pick_filament(
            source_3mf=input_path,
            spools=spools,
            override=args.filament,
        )
    except FilamentResolutionError as exc:
        _fail(str(exc))
        return 2

    _print_decisions(input_path, nozzle_dec, filament_dec, args.quality, status)

    # 4. Hard-stop on nozzle mismatch
    if nozzle_dec.mismatch and not args.force:
        print()
        _fail("Nozzle mismatch")
        print(f"   You requested:    {nozzle_dec.nozzle}")
        print(f"   Printer has:      {nozzle_dec.attached}mm")
        print("   What to do:")
        print(f"     Option 1: Swap to the {nozzle_dec.nozzle} nozzle on the printer, then re-run.")
        print(f"     Option 2: Re-run without -n to use the {nozzle_dec.attached}mm nozzle.")
        print("     Option 3: Re-run with --force to override (NOT recommended).")
        return 1
    if nozzle_dec.mismatch and args.force:
        _warn(f"Nozzle mismatch overridden by --force ({nozzle_dec.nozzle} vs attached {nozzle_dec.attached}mm)")

    # 5. Compose / bake / validate
    print(f"🔧 Composing profile ({nozzle_dec.nozzle} + {filament_dec.material} + {args.quality})")
    print("🔧 Baking settings into project_settings.config")
    try:
        result = prepare_3mf(
            input_path=input_path,
            output_path=output_path,
            nozzle=nozzle_dec.nozzle,
            material=filament_dec.material,
            tier=args.quality,
            do_bs_validate=not args.skip_bs_validate,
        )
    except ValidationError as exc:
        _fail(f"Settings validation failed:\n{exc}")
        return 2
    except FileNotFoundError as exc:
        _fail(f"File not found while baking: {exc}")
        return 2
    except Exception as exc:
        _fail(f"Internal error: {type(exc).__name__}: {exc}. Please report this.")
        if args.debug:
            traceback.print_exc()
        return 2

    print("🔬 Static validation... clean")
    if result.bs_ok is None:
        _warn("BS slice validation skipped (--skip-bs-validate)")
    elif result.bs_ok:
        print(f"🔬 BS slice validation... {result.bs_message}")
    else:
        _fail(f"BS slice validation FAILED: {result.bs_message}")
        print("   The output 3MF was written but Bambu Studio rejected it on slice.")
        print("   Re-run with --debug, or open the file in BS to see the toast error.")
        return 2

    print()
    _ok(f"Done! Output: {output_path}")
    if args.auto_open:
        opened, msg = _open_in_default_app(output_path)
        if opened:
            print(f"   🚀 Opening in Bambu Studio... ({msg})")
            print("   When BS finishes loading, just press Print.")
        else:
            _warn(f"Couldn't auto-open ({msg}). Open it manually in Bambu Studio and press Print.")
    else:
        print(f"   Open {output_path} in Bambu Studio and press Print.")
    return 0


def _open_in_default_app(path: str) -> tuple[bool, str]:
    """Open a file in the OS default handler (Bambu Studio for .3mf).

    Returns (success, message). Never raises — auto-open is a convenience,
    not a critical step. macOS uses `open`, Windows uses `os.startfile`,
    Linux uses `xdg-open`.
    """
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", path], check=True, timeout=10)
            return True, "macOS open"
        if system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
            return True, "Windows shell"
        if system == "Linux":
            if shutil.which("xdg-open") is None:
                return False, "xdg-open not installed"
            subprocess.run(["xdg-open", path], check=True, timeout=10)
            return True, "xdg-open"
        return False, f"unsupported platform: {system}"
    except subprocess.CalledProcessError as exc:
        return False, f"launcher exit {exc.returncode}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"{type(exc).__name__}: {exc}"


if __name__ == "__main__":
    raise SystemExit(main())
