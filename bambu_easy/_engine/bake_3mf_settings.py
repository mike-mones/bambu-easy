# VENDORED FROM /Users/mikemones/Documents/3D Printing/Scripts/bake_3mf_settings.py at commit 6f7017de4c794e4343a5136e7a7cf116a14efaa5. Do not edit here — sync via tools/sync_engine.sh.

#!/usr/bin/env python3
"""
Utility: Bake print settings into a 3MF file.

Overlays custom print/filament settings onto an existing 3MF's
project_settings.config. Clears preset IDs so Bambu Studio uses
the custom values instead of loading built-in presets.

Usage:
    # Bake settings from a reference 3MF onto a target
    python bake_3mf_settings.py target.3mf --from reference.3mf -o output.3mf

    # Bake specific overrides via JSON
    python bake_3mf_settings.py target.3mf \\
        --set layer_height=0.16 wall_loops=6 sparse_infill_density=30% \\
        --set nozzle_temperature=230 \\
        -o output.3mf

    # Inspect current settings
    python bake_3mf_settings.py target.3mf --inspect
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile


MINIMAL_SLICE_INFO = '''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="slicer" value="BambuStudio"/>
    <header_item key="slicer_version" value="02.05.00.66"/>
  </header>
</config>'''

# Settings to show in --inspect mode
INSPECT_KEYS = [
    'layer_height', 'initial_layer_print_height', 'wall_loops',
    'sparse_infill_density', 'sparse_infill_pattern',
    'outer_wall_speed', 'inner_wall_speed', 'top_surface_speed',
    'nozzle_temperature', 'nozzle_temperature_initial_layer',
    'initial_layer_line_width', 'elefant_foot_compensation',
    'enable_prime_tower', 'curr_bed_type', 'nozzle_diameter',
    'print_settings_id', 'filament_settings_id', 'printer_settings_id',
]


def read_settings(zf: zipfile.ZipFile) -> dict:
    """Read project_settings.config as a dict."""
    if 'Metadata/project_settings.config' not in zf.namelist():
        return {}
    return json.loads(zf.read('Metadata/project_settings.config').decode('utf-8'))


def inspect_settings(path: str, show_all: bool = False):
    """Print key settings from a 3MF."""
    with zipfile.ZipFile(path, 'r') as zf:
        settings = read_settings(zf)
    if not settings:
        print("No project_settings.config found")
        return

    print(f"Settings in: {os.path.basename(path)}")
    keys = sorted(settings.keys()) if show_all else INSPECT_KEYS
    for k in keys:
        if k in settings:
            val = settings[k]
            # Truncate long values in non-all mode
            s = str(val)
            if not show_all and len(s) > 120:
                s = s[:120] + '...'
            print(f"  {k}: {s}")


def compare_settings(path_a: str, path_b: str):
    """Show settings differences between two 3MF files."""
    with zipfile.ZipFile(path_a, 'r') as zf:
        settings_a = read_settings(zf)
    with zipfile.ZipFile(path_b, 'r') as zf:
        settings_b = read_settings(zf)

    name_a = os.path.basename(path_a)
    name_b = os.path.basename(path_b)
    print(f"Comparing: {name_a} vs {name_b}")
    print()

    all_keys = sorted(set(settings_a.keys()) | set(settings_b.keys()))
    diffs = 0
    for k in all_keys:
        va = settings_a.get(k)
        vb = settings_b.get(k)
        if va != vb:
            diffs += 1
            sa = str(va)[:200] if va is not None else '<missing>'
            sb = str(vb)[:200] if vb is not None else '<missing>'
            print(f"  {k}:")
            print(f"    {name_a}: {sa}")
            print(f"    {name_b}: {sb}")

    if diffs == 0:
        print("  No differences found.")
    else:
        print(f"\n  {diffs} settings differ.")


def bake_settings(target_path: str, output_path: str,
                  reference_path: str | None = None,
                  overrides: dict | None = None):
    """Bake settings from a reference 3MF and/or explicit overrides."""
    # Safety: never write to the same file we're reading — causes corruption
    if os.path.abspath(output_path) == os.path.abspath(target_path):
        print("ERROR: output path cannot be the same as input. Use a different filename.", file=sys.stderr)
        sys.exit(1)
    with zipfile.ZipFile(target_path, 'r') as zf_target:
        target_settings = read_settings(zf_target)

        # Start with target settings as base
        merged = dict(target_settings)

        # Overlay reference settings if provided
        if reference_path:
            with zipfile.ZipFile(reference_path, 'r') as zf_ref:
                ref_settings = read_settings(zf_ref)
            merged.update(ref_settings)
            print(f"  Overlaid {len(ref_settings)} settings from {os.path.basename(reference_path)}")

        # Apply explicit overrides
        if overrides:
            merged.update(overrides)
            print(f"  Applied {len(overrides)} explicit overrides")

        # Clear print_settings_id so BS uses our custom process settings
        # instead of loading a built-in profile that overrides them — UNLESS
        # the caller explicitly provided a print_settings_id override (this
        # is the post-2026-05-08 path for retargeted MakerWorld 3MFs, where
        # an empty print_settings_id paired with a non-P2S
        # print_compatible_printers triggers BS rc=-17 "process preset not
        # compatible" at slice time). When the caller knows the right P2S
        # preset to use, trust them.
        if not (overrides and overrides.get("print_settings_id")):
            merged['print_settings_id'] = ''

        new_settings = json.dumps(merged, indent=4, ensure_ascii=False)

        # Write output — copy everything byte-for-byte except settings + slice_info
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for item in zf_target.infolist():
                if item.filename == 'Metadata/project_settings.config':
                    zf_out.writestr(item, new_settings.encode('utf-8'))
                elif item.filename == 'Metadata/slice_info.config':
                    zf_out.writestr(item, MINIMAL_SLICE_INFO)
                else:
                    zf_out.writestr(item, zf_target.read(item.filename))

    print(f"  Written: {output_path} ({os.path.getsize(output_path)} bytes)")

    # Verify key settings
    with zipfile.ZipFile(output_path, 'r') as zf:
        final = read_settings(zf)
    print("  Verification:")
    for k in ['layer_height', 'wall_loops', 'sparse_infill_density',
              'nozzle_temperature', 'print_settings_id']:
        print(f"    {k}: {final.get(k, '?')}")


def parse_overrides(pairs: list[str]) -> dict:
    """Parse key=value pairs into a dict.
    
    Values that look like JSON lists (e.g. '["260"]') are parsed as lists.
    Plain strings are kept as-is.
    """
    result = {}
    for pair in pairs:
        if '=' not in pair:
            print(f"Invalid override (no '='): {pair}", file=sys.stderr)
            sys.exit(1)
        k, v = pair.split('=', 1)
        v = v.strip()
        # Try to parse JSON list values (e.g. filament_type=["PETG-HF"])
        if v.startswith('['):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                pass  # keep as string if not valid JSON
        result[k.strip()] = v
    return result


def main():
    parser = argparse.ArgumentParser(description='Bake print settings into a 3MF')
    parser.add_argument('target', help='Target 3MF file')
    parser.add_argument('--from', dest='reference', help='Reference 3MF to copy settings from')
    parser.add_argument('--set', nargs='+', action='append', default=[],
                       help='Key=value overrides (can repeat)')
    parser.add_argument('-o', '--output', help='Output 3MF path')
    parser.add_argument('--inspect', action='store_true', help='Just show current settings')
    parser.add_argument('--inspect-all', action='store_true', help='Show ALL settings (not just key ones)')
    parser.add_argument('--compare', metavar='OTHER', help='Compare settings with another 3MF')

    args = parser.parse_args()

    if args.inspect or args.inspect_all:
        inspect_settings(args.target, show_all=args.inspect_all)
        return

    if args.compare:
        compare_settings(args.target, args.compare)
        return

    if not args.output:
        print("--output required when baking settings", file=sys.stderr)
        sys.exit(1)

    overrides = {}
    for group in args.set:
        overrides.update(parse_overrides(group))

    if not args.reference and not overrides:
        print("Specify --from and/or --set", file=sys.stderr)
        sys.exit(1)

    bake_settings(args.target, args.output, args.reference, overrides or None)


if __name__ == '__main__':
    main()
