# VENDORED FROM /Users/mikemones/Documents/3D Printing/Scripts/print_profiles.py at commit 6f7017de4c794e4343a5136e7a7cf116a14efaa5. Do not edit here — sync via tools/sync_engine.sh.

"""Global print profiles for the Bambu Lab P2S.

Composable system: nozzle_base + material + quality_tier → complete settings dict.

Usage:
    from print_profiles import compose_profile, list_profiles

    # Get a complete settings dict for PETG-HF, quality tier, 0.2mm nozzle
    settings = compose_profile(nozzle="0.2mm", material="PETG-HF", tier="quality")

    # Use with export_3mf
    from export_3mf import export_bambu_3mf
    export_bambu_3mf(mesh, "output.3mf", settings_overrides=settings)

Confidence tags in comments:
    VERIFIED = confirmed by a successful print in print-journal.md
    SOURCED  = from external docs (Bambu, Ellis, Prusa, Simplify3D) but untested
    INFERRED = general knowledge reasoning
"""

# =============================================================================
# NOZZLE BASES — line widths and mechanical limits per nozzle diameter
# =============================================================================

NOZZLE_BASES = {
    "0.4mm": {
        "nozzle_diameter": ["0.4"],
        "printer_settings_id": "Bambu Lab P2S 0.4 nozzle",
        "line_width": "0.42",
        "outer_wall_line_width": "0.42",
        "inner_wall_line_width": "0.45",
        "top_surface_line_width": "0.42",
        "sparse_infill_line_width": "0.45",
        "internal_solid_infill_line_width": "0.42",
        "support_line_width": "0.42",
        "initial_layer_line_width": "0.50",
        "skin_infill_line_width": "0.45",
        "skeleton_infill_line_width": "0.45",
        "max_layer_height": ["0.32"],
        "min_layer_height": ["0.08"],
    },
    "0.2mm": {
        "nozzle_diameter": ["0.2"],
        "printer_settings_id": "Bambu Lab P2S 0.2 nozzle",
        "line_width": "0.22",
        "outer_wall_line_width": "0.22",         # VERIFIED — 0.2mm_premium preset
        "inner_wall_line_width": "0.23",
        "top_surface_line_width": "0.22",
        "sparse_infill_line_width": "0.23",
        "internal_solid_infill_line_width": "0.22",
        "support_line_width": "0.22",
        "initial_layer_line_width": "0.24",
        "skin_infill_line_width": "0.23",
        "skeleton_infill_line_width": "0.23",
        "max_layer_height": ["0.16"],
        "min_layer_height": ["0.04"],
    },
    "0.6mm": {
        "nozzle_diameter": ["0.6"],
        "printer_settings_id": "Bambu Lab P2S 0.6 nozzle",
        "line_width": "0.62",                    # SOURCED — ~nozzle * 1.05
        "outer_wall_line_width": "0.62",
        "inner_wall_line_width": "0.65",
        "top_surface_line_width": "0.62",
        "sparse_infill_line_width": "0.65",
        "internal_solid_infill_line_width": "0.62",
        "support_line_width": "0.62",
        "initial_layer_line_width": "0.70",
        "skin_infill_line_width": "0.65",
        "skeleton_infill_line_width": "0.65",
        "max_layer_height": ["0.48"],
        "min_layer_height": ["0.10"],
    },
    "0.8mm": {
        # SOURCED — derived from Bambu's published 0.8mm P2S presets.
        # Untested on Mike's printer as of 2026-05-07. Confidence will upgrade
        # to VERIFIED after the first successful 0.8mm print is logged.
        "nozzle_diameter": ["0.8"],
        "printer_settings_id": "Bambu Lab P2S 0.8 nozzle",
        "line_width": "0.85",                    # SOURCED — Bambu 0.8mm default
        "outer_wall_line_width": "0.85",
        "inner_wall_line_width": "0.88",
        "top_surface_line_width": "0.85",
        "sparse_infill_line_width": "0.88",
        "internal_solid_infill_line_width": "0.85",
        "support_line_width": "0.85",
        "initial_layer_line_width": "0.95",
        "skin_infill_line_width": "0.88",
        "skeleton_infill_line_width": "0.88",
        "max_layer_height": ["0.64"],
        "min_layer_height": ["0.20"],
    },
}

# =============================================================================
# MATERIALS — temperatures, cooling, flow, bed type, retraction
# Each material is independent of nozzle size and quality tier.
# =============================================================================

MATERIALS = {
    "PLA Basic": {
        # VERIFIED — 220°C confirmed in multiple print-journal entries
        "filament_type": ["PLA"],
        "nozzle_temperature": ["220"],
        "nozzle_temperature_initial_layer": ["220"],
        "textured_plate_temp": ["55"],
        "textured_plate_temp_initial_layer": ["55"],
        "cool_plate_temp": ["35"],
        "cool_plate_temp_initial_layer": ["35"],
        "curr_bed_type": "Textured PEI Plate",
        "filament_flow_ratio": ["0.98"],
        "fan_max_speed": ["100"],
        "fan_min_speed": ["60"],
        "overhang_fan_speed": ["100"],
        "close_fan_the_first_x_layers": ["1"],
        "slow_down_for_layer_cooling": ["1"],
        "filament_max_volumetric_speed": ["21"],
        "filament_settings_id": ["Bambu PLA Basic @BBL P2S"],
    },
    "PLA Matte": {
        # VERIFIED — 230°C required, 220°C causes delamination (print-settings.md)
        # filament_settings_id is set per (nozzle, material) by FILAMENT_PRESET_IDS
        # below — Mike's user preset (Mike PLA Matte 230C ...) is the canonical
        # source of 230°C on this machine. Pointing at the system preset
        # ('Bambu PLA Matte @BBL P2S') causes BS to override our baked 230 with
        # the preset default of 220 (failure-log.md May 1).
        "filament_type": ["PLA"],
        "nozzle_temperature": ["230"],
        "nozzle_temperature_initial_layer": ["230"],
        "textured_plate_temp": ["65"],
        "textured_plate_temp_initial_layer": ["65"],
        "cool_plate_temp": ["35"],
        "cool_plate_temp_initial_layer": ["35"],
        "curr_bed_type": "Textured PEI Plate",
        "filament_flow_ratio": ["0.98"],
        "fan_max_speed": ["80"],               # SOURCED — reduce for thick parts, layer adhesion
        "fan_min_speed": ["60"],
        "overhang_fan_speed": ["100"],
        "close_fan_the_first_x_layers": ["1"],
        "slow_down_for_layer_cooling": ["1"],
        "filament_max_volumetric_speed": ["21"],
    },
    "PLA Silk+": {
        # VERIFIED — 230°C required, lower temps cause filament strand shredding
        # filament_settings_id resolved per (nozzle, material) via FILAMENT_PRESET_IDS.
        "filament_type": ["PLA"],
        "nozzle_temperature": ["230"],
        "nozzle_temperature_initial_layer": ["230"],
        "textured_plate_temp": ["65"],
        "textured_plate_temp_initial_layer": ["65"],
        "cool_plate_temp": ["35"],
        "cool_plate_temp_initial_layer": ["35"],
        "curr_bed_type": "Textured PEI Plate",
        "filament_flow_ratio": ["0.98"],
        "fan_max_speed": ["100"],
        "fan_min_speed": ["60"],
        "overhang_fan_speed": ["100"],
        "close_fan_the_first_x_layers": ["1"],
        "slow_down_for_layer_cooling": ["1"],
        "filament_max_volumetric_speed": ["21"],
    },
    "PETG-HF": {
        # VERIFIED — 260°C/80°C from Bambu's own PETG-HF profile, confirmed in 3MF
        "filament_type": ["PETG"],
        "nozzle_temperature": ["260"],
        "nozzle_temperature_initial_layer": ["260"],
        "textured_plate_temp": ["80"],
        "textured_plate_temp_initial_layer": ["80"],
        "cool_plate_temp": ["35"],
        "cool_plate_temp_initial_layer": ["35"],
        "eng_plate_temp": ["55"],
        "eng_plate_temp_initial_layer": ["55"],
        "curr_bed_type": "Textured PEI Plate",  # NOT Cool Plate for PETG
        "filament_flow_ratio": ["0.98"],
        "fan_max_speed": ["85"],               # SOURCED — bumped from 70 for detail (Ellis)
        "fan_min_speed": ["30"],
        "overhang_fan_speed": ["100"],
        "close_fan_the_first_x_layers": ["1"],
        "slow_down_for_layer_cooling": ["1"],
        "filament_max_volumetric_speed": ["4"],  # 0.2mm nozzle limit
        "retraction_length": ["0.5"],
        "retraction_speed": ["30"],
        "filament_settings_id": ["Bambu PETG HF @BBL P2S 0.2 nozzle"],
    },
}

# =============================================================================
# FILAMENT PRESET IDS — per (nozzle, material), resolved by compose_profile()
#
# Bambu Studio's `filament_settings_id` references a saved filament preset by
# its canonical `name` field. For PLA Matte and PLA Silk+ on this machine,
# Mike maintains user presets that override only the nozzle temperature
# (220°C → 230°C); everything else inherits from the matching system preset.
# Pointing at the system preset and trying to bake 230 on top fails because
# BS overrides our baked temperature with the preset default (failure-log.md
# May 1, 2026).
#
# Names are the canonical `name` field inside the preset JSON, NOT the file
# basename. Verify with:
#   python3 -c "import json; print(json.load(open('<preset>.json'))['name'])"
# =============================================================================

FILAMENT_PRESET_IDS = {
    # PLA Matte — user presets enforce 230°C
    ("0.4mm", "PLA Matte"):  "Mike PLA Matte 230C @BBL P2S (0.4 nozzle)",
    ("0.2mm", "PLA Matte"):  "Mike PLA Matte 230C @BBL P2S 0.2 nozzle",
    ("0.6mm", "PLA Matte"):  "Mike PLA Matte 230C @BBL P2S 0.6 nozzle",   # TODO: create user preset before first 0.6 PLA Matte print
    ("0.8mm", "PLA Matte"):  "Mike PLA Matte 230C @BBL P2S 0.8 nozzle",   # TODO: create user preset before first 0.8 PLA Matte print
    # PLA Silk+ — user presets enforce 230°C
    ("0.4mm", "PLA Silk+"):  "Mike PLA Silk+ 230C @BBL P2S (0.4 nozzle)",
    ("0.2mm", "PLA Silk+"):  "Mike PLA Silk+ 230C @BBL P2S 0.2 nozzle",
    ("0.6mm", "PLA Silk+"):  "Mike PLA Silk+ 230C @BBL P2S 0.6 nozzle",   # TODO: create user preset
    ("0.8mm", "PLA Silk+"):  "Mike PLA Silk+ 230C @BBL P2S 0.8 nozzle",   # TODO: create user preset
    # PLA Basic — no user preset; fall back to system
    ("0.4mm", "PLA Basic"):  "Bambu PLA Basic @BBL P2S",
    ("0.2mm", "PLA Basic"):  "Bambu PLA Basic @BBL P2S 0.2 nozzle",
    ("0.6mm", "PLA Basic"):  "Bambu PLA Basic @BBL P2S 0.6 nozzle",
    ("0.8mm", "PLA Basic"):  "Bambu PLA Basic @BBL P2S 0.8 nozzle",
    # PETG-HF — system preset is the right one (260°C is correct as-is)
    ("0.4mm", "PETG-HF"):    "Bambu PETG HF @BBL P2S 0.4 nozzle",
    ("0.2mm", "PETG-HF"):    "Bambu PETG HF @BBL P2S 0.2 nozzle",
    ("0.6mm", "PETG-HF"):    "Bambu PETG HF @BBL P2S 0.6 nozzle",
    ("0.8mm", "PETG-HF"):    "Bambu PETG HF @BBL P2S 0.8 nozzle",
}

# =============================================================================
# PROCESS PRESET IDS — per (nozzle, tier) → BS process preset name
#
# When a 3MF is retargeted from another printer (e.g. an A1 MakerWorld file
# being prepared for the P2S), its `print_settings_id` ends up empty or
# stale, and `print_compatible_printers` may still reference the old printer.
# BS rejects on slice with "The selected printer is not compatible with the
# process preset in the 3mf." (rc=-17). Fix: compose_profile() injects a
# valid P2S process preset matching the chosen nozzle and tier, and rewrites
# print_compatible_printers to match the chosen nozzle.
#
# Names match the canonical `name` field of the system preset JSON; verified
# against ~/Library/Application Support/BambuStudio/system/BBL/process/.
# Source-of-failure: 2026-05-08 wife-test on twisty golf ball MakerWorld 3MF.
# =============================================================================

PROCESS_PRESET_IDS = {
    # 0.4mm — system "@BBL P2S" presets (no nozzle suffix)
    ("0.4mm", "fast"):     "0.24mm Standard @BBL P2S",
    ("0.4mm", "standard"): "0.20mm Standard @BBL P2S",
    ("0.4mm", "quality"):  "0.16mm High Quality @BBL P2S",
    ("0.4mm", "premium"):  "0.12mm High Quality @BBL P2S",
    # 0.2mm — system "@BBL P2S 0.2 nozzle" presets
    ("0.2mm", "fast"):     "0.12mm Balanced Quality @BBL P2S 0.2 nozzle",
    ("0.2mm", "standard"): "0.10mm Standard @BBL P2S 0.2 nozzle",
    ("0.2mm", "quality"):  "0.12mm Balanced Quality @BBL P2S 0.2 nozzle",
    ("0.2mm", "premium"):  "0.08mm High Quality @BBL P2S 0.2 nozzle",
    # 0.6mm
    ("0.6mm", "fast"):     "0.30mm Standard @BBL P2S 0.6 nozzle",
    ("0.6mm", "standard"): "0.30mm Standard @BBL P2S 0.6 nozzle",
    ("0.6mm", "quality"):  "0.24mm Balanced Quality @BBL P2S 0.6 nozzle",
    ("0.6mm", "premium"):  "0.18mm Balanced Quality @BBL P2S 0.6 nozzle",
    # 0.8mm
    ("0.8mm", "fast"):     "0.40mm Standard @BBL P2S 0.8 nozzle",
    ("0.8mm", "standard"): "0.40mm Standard @BBL P2S 0.8 nozzle",
    ("0.8mm", "quality"):  "0.32mm Balanced Quality @BBL P2S 0.8 nozzle",
    ("0.8mm", "premium"):  "0.24mm Balanced Quality @BBL P2S 0.8 nozzle",
}

# (nozzle → P2S printer model name expected in print_compatible_printers)
COMPATIBLE_PRINTERS = {
    "0.4mm": ["Bambu Lab P2S 0.4 nozzle"],
    "0.2mm": ["Bambu Lab P2S 0.2 nozzle"],
    "0.6mm": ["Bambu Lab P2S 0.6 nozzle"],
    "0.8mm": ["Bambu Lab P2S 0.8 nozzle"],
}

# =============================================================================
# QUALITY TIERS — speeds, walls, layers, cooling behavior
# Keyed by (nozzle, tier). Layer heights follow the 0.04mm magic number rule.
# =============================================================================

QUALITY_TIERS = {
    # --- 0.4mm nozzle ---
    ("0.4mm", "fast"): {
        "layer_height": "0.28",
        "initial_layer_print_height": "0.28",
        "wall_loops": "2",
        "top_shell_layers": "3",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "200",
        "inner_wall_speed": "250",
        "sparse_infill_speed": "250",
        "top_surface_speed": "100",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "nearest",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.4mm", "standard"): {
        "layer_height": "0.20",
        "initial_layer_print_height": "0.20",
        "wall_loops": "3",
        "top_shell_layers": "4",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "150",
        "inner_wall_speed": "200",
        "sparse_infill_speed": "200",
        "top_surface_speed": "80",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.4mm", "quality"): {
        "layer_height": "0.16",
        "initial_layer_print_height": "0.16",
        "wall_loops": "4",
        "top_shell_layers": "5",
        "bottom_shell_layers": "4",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "80",
        "inner_wall_speed": "120",
        "sparse_infill_speed": "150",
        "top_surface_speed": "60",
        "bridge_speed": "30",
        "initial_layer_speed": "30",
        "travel_speed": "300",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["10"],        # SOURCED — Ellis
        "slow_down_min_speed": ["15"],
        "support_interface_speed": ["50", "50"],
        "print_settings_id": "",
    },
    ("0.4mm", "premium"): {
        "layer_height": "0.12",
        "initial_layer_print_height": "0.12",
        "wall_loops": "5",
        "top_shell_layers": "6",
        "bottom_shell_layers": "5",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "50",
        "inner_wall_speed": "80",
        "sparse_infill_speed": "120",
        "top_surface_speed": "40",
        "bridge_speed": "25",
        "initial_layer_speed": "20",
        "travel_speed": "250",
        "default_acceleration": "2000",
        "seam_position": "aligned",
        "seam_slope_type": "external",         # scarf seam
        "z_hop": "0.2",
        "reduce_crossing_wall": "1",
        "wipe": "1",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["12"],        # SOURCED — Ellis
        "slow_down_min_speed": ["10"],         # SOURCED — Ellis
        "support_interface_speed": ["40", "40"],  # SOURCED — Hubs/Simplify3D
        "top_surface_pattern": "monotonicline",
        "bottom_surface_pattern": "monotonic",
        "print_settings_id": "",
    },

    # --- 0.2mm nozzle ---
    ("0.2mm", "fast"): {
        "layer_height": "0.16",
        "initial_layer_print_height": "0.16",
        "wall_loops": "3",
        "top_shell_layers": "3",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "80",
        "inner_wall_speed": "120",
        "sparse_infill_speed": "150",
        "top_surface_speed": "60",
        "initial_layer_speed": "30",
        "travel_speed": "300",
        "seam_position": "nearest",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.2mm", "standard"): {
        "layer_height": "0.12",
        "initial_layer_print_height": "0.12",
        "wall_loops": "3",
        "top_shell_layers": "4",
        "bottom_shell_layers": "4",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "60",
        "inner_wall_speed": "100",
        "sparse_infill_speed": "130",
        "top_surface_speed": "50",
        "bridge_speed": "25",
        "initial_layer_speed": "25",
        "travel_speed": "250",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.2mm", "quality"): {
        # SOURCED — layer time, fan, support interface from Ellis/Simplify3D
        # Used on Hello Kitty PETG-HF v2 (Apr 16 2026)
        "layer_height": "0.08",
        "initial_layer_print_height": "0.12",
        "wall_loops": "4",
        "top_shell_layers": "6",
        "bottom_shell_layers": "5",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "50",
        "inner_wall_speed": "80",
        "sparse_infill_speed": "120",
        "top_surface_speed": "40",
        "bridge_speed": "25",
        "initial_layer_speed": "20",
        "travel_speed": "250",
        "seam_position": "aligned",
        "z_hop": "0.2",
        "reduce_crossing_wall": "1",
        "wipe": "1",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["12"],        # SOURCED — Ellis
        "slow_down_min_speed": ["15"],         # SOURCED — Ellis
        "support_interface_speed": ["40", "40"],
        "top_surface_pattern": "monotonicline",
        "bottom_surface_pattern": "monotonic",
        "print_settings_id": "",
    },
    ("0.2mm", "premium"): {
        # VERIFIED — used on NationalParkCoin, SmokiesToken, falcon badge
        "layer_height": "0.08",
        "initial_layer_print_height": "0.12",
        "wall_loops": "5",
        "top_shell_layers": "6",
        "bottom_shell_layers": "5",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "35",              # SOURCED — Ellis (was 30 in display preset)
        "inner_wall_speed": "80",
        "sparse_infill_speed": "120",
        "top_surface_speed": "40",
        "bridge_speed": "25",
        "initial_layer_speed": "20",
        "travel_speed": "250",
        "default_acceleration": "1500",
        "outer_wall_acceleration": "1000",
        "seam_position": "aligned",
        "seam_slope_type": "external",         # scarf seam
        "z_hop": "0.2",
        "reduce_crossing_wall": "1",
        "wipe": "1",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["12"],        # SOURCED — Ellis
        "slow_down_min_speed": ["10"],         # SOURCED — Ellis
        "support_interface_speed": ["40", "40"],  # SOURCED — Simplify3D/Hubs
        "top_surface_pattern": "monotonicline",
        "bottom_surface_pattern": "monotonic",
        "print_settings_id": "",
    },

    # --- 0.6mm nozzle ---
    # SOURCED — based on BS built-in 0.6mm P2S presets, adapted to our tier system
    ("0.6mm", "fast"): {
        "layer_height": "0.40",                # SOURCED — 0.6 * 0.67, fast draft
        "initial_layer_print_height": "0.36",
        "wall_loops": "2",
        "top_shell_layers": "3",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "200",
        "inner_wall_speed": "250",
        "sparse_infill_speed": "250",
        "top_surface_speed": "100",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "nearest",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.6mm", "standard"): {
        "layer_height": "0.30",                # SOURCED — matches BS 0.30mm Standard @P2S 0.6
        "initial_layer_print_height": "0.30",
        "wall_loops": "2",
        "top_shell_layers": "4",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "150",
        "inner_wall_speed": "200",
        "sparse_infill_speed": "200",
        "top_surface_speed": "80",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.6mm", "quality"): {
        "layer_height": "0.24",                # SOURCED — matches BS 0.24mm Balanced Quality @P2S 0.6
        "initial_layer_print_height": "0.24",
        "wall_loops": "3",
        "top_shell_layers": "5",
        "bottom_shell_layers": "4",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "100",
        "inner_wall_speed": "150",
        "sparse_infill_speed": "180",
        "top_surface_speed": "60",
        "bridge_speed": "30",
        "initial_layer_speed": "35",
        "travel_speed": "300",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["10"],
        "slow_down_min_speed": ["15"],
        "print_settings_id": "",
    },
    ("0.6mm", "premium"): {
        "layer_height": "0.18",                # SOURCED — matches BS 0.18mm Balanced Quality @P2S 0.6
        "initial_layer_print_height": "0.18",
        "wall_loops": "4",
        "top_shell_layers": "6",
        "bottom_shell_layers": "5",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "60",
        "inner_wall_speed": "100",
        "sparse_infill_speed": "150",
        "top_surface_speed": "50",
        "bridge_speed": "25",
        "initial_layer_speed": "30",
        "travel_speed": "250",
        "default_acceleration": "2000",
        "seam_position": "aligned",
        "seam_slope_type": "external",
        "z_hop": "0.2",
        "reduce_crossing_wall": "1",
        "wipe": "1",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["12"],
        "slow_down_min_speed": ["10"],
        "support_interface_speed": ["50", "50"],
        "top_surface_pattern": "monotonicline",
        "bottom_surface_pattern": "monotonic",
        "print_settings_id": "",
    },

    # --- 0.8mm nozzle ---
    # SOURCED — derived from Bambu's published 0.8mm P2S presets. No verified
    # prints on this machine yet (2026-05-07). First success bumps to VERIFIED.
    ("0.8mm", "fast"): {
        "layer_height": "0.56",                # SOURCED — Bambu 0.56mm Standard @P2S 0.8
        "initial_layer_print_height": "0.40",
        "wall_loops": "2",
        "top_shell_layers": "3",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "10%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "180",
        "inner_wall_speed": "230",
        "sparse_infill_speed": "230",
        "top_surface_speed": "100",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "nearest",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.8mm", "standard"): {
        "layer_height": "0.40",                # SOURCED — Bambu 0.40mm Standard @P2S 0.8
        "initial_layer_print_height": "0.36",
        "wall_loops": "2",
        "top_shell_layers": "3",
        "bottom_shell_layers": "3",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "150",
        "inner_wall_speed": "200",
        "sparse_infill_speed": "200",
        "top_surface_speed": "80",
        "initial_layer_speed": "50",
        "travel_speed": "400",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "print_settings_id": "",
    },
    ("0.8mm", "quality"): {
        "layer_height": "0.32",                # SOURCED — Bambu 0.32mm Strength @P2S 0.8
        "initial_layer_print_height": "0.32",
        "wall_loops": "3",
        "top_shell_layers": "4",
        "bottom_shell_layers": "4",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "100",
        "inner_wall_speed": "150",
        "sparse_infill_speed": "180",
        "top_surface_speed": "60",
        "bridge_speed": "30",
        "initial_layer_speed": "35",
        "travel_speed": "300",
        "seam_position": "aligned",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["10"],
        "slow_down_min_speed": ["15"],
        "print_settings_id": "",
    },
    ("0.8mm", "premium"): {
        "layer_height": "0.28",                # SOURCED — finer-than-default for 0.8 (~35% of nozzle)
        "initial_layer_print_height": "0.28",
        "wall_loops": "4",
        "top_shell_layers": "5",
        "bottom_shell_layers": "4",
        "sparse_infill_density": "20%",
        "sparse_infill_pattern": "gyroid",
        "outer_wall_speed": "60",
        "inner_wall_speed": "100",
        "sparse_infill_speed": "150",
        "top_surface_speed": "50",
        "bridge_speed": "25",
        "initial_layer_speed": "30",
        "travel_speed": "250",
        "default_acceleration": "2000",
        "seam_position": "aligned",
        "seam_slope_type": "external",
        "z_hop": "0.2",
        "reduce_crossing_wall": "1",
        "wipe": "1",
        "brim_type": "auto_brim",
        "slow_down_layer_time": ["12"],
        "slow_down_min_speed": ["10"],
        "support_interface_speed": ["50", "50"],
        "top_surface_pattern": "monotonicline",
        "bottom_surface_pattern": "monotonic",
        "print_settings_id": "",
    },
}


# =============================================================================
# COMPOSITION
# =============================================================================

def compose_profile(nozzle: str, material: str, tier: str) -> dict:
    """Compose a complete settings dict from nozzle base + material + quality tier.

    Later layers override earlier layers, so:
        nozzle_base (line widths) → material (temps/cooling) → tier (speeds/walls)
        → FILAMENT_PRESET_IDS (filament_settings_id resolved per nozzle+material)

    Tier settings win on conflicts (e.g., if tier sets fan_max_speed it overrides
    the material default). This lets premium tiers bump cooling beyond material defaults.

    Returns a flat dict suitable for export_3mf settings_overrides.
    """
    if nozzle not in NOZZLE_BASES:
        raise ValueError(f"Unknown nozzle: {nozzle!r}. Options: {list(NOZZLE_BASES)}")
    if material not in MATERIALS:
        raise ValueError(f"Unknown material: {material!r}. Options: {list(MATERIALS)}")
    key = (nozzle, tier)
    if key not in QUALITY_TIERS:
        raise ValueError(f"Unknown tier {tier!r} for {nozzle}. Options: "
                         f"{[k[1] for k in QUALITY_TIERS if k[0] == nozzle]}")

    result = {}
    result.update(NOZZLE_BASES[nozzle])
    result.update(MATERIALS[material])
    result.update(QUALITY_TIERS[key])

    # Adjust filament_max_volumetric_speed per nozzle if material didn't set it
    if nozzle == "0.2mm" and "filament_max_volumetric_speed" not in MATERIALS.get(material, {}):
        result["filament_max_volumetric_speed"] = ["4"]
    elif nozzle == "0.6mm" and "filament_max_volumetric_speed" not in MATERIALS.get(material, {}):
        result["filament_max_volumetric_speed"] = ["28"]  # SOURCED — higher flow for 0.6mm
    elif nozzle == "0.8mm" and "filament_max_volumetric_speed" not in MATERIALS.get(material, {}):
        result["filament_max_volumetric_speed"] = ["32"]  # SOURCED — Bambu 0.8mm default for PLA

    # Resolve filament_settings_id per (nozzle, material). For PLA Matte and
    # PLA Silk+ this prefers Mike's user preset (Mike PLA Matte/Silk+ 230C ...)
    # over the system preset, because the system preset bakes 220°C and BS
    # overrides our baked 230 with the preset default — see failure-log.md
    # May 1, 2026.
    preset_id = FILAMENT_PRESET_IDS.get((nozzle, material))
    if preset_id:
        result["filament_settings_id"] = [preset_id]

    # Resolve print_settings_id and print_compatible_printers per (nozzle, tier).
    # When bambu-easy retargets a foreign-printer 3MF (e.g. MakerWorld A1
    # source) onto the P2S, BS clears `print_settings_id` and leaves the
    # source's stale `print_compatible_printers`. BS then rejects the file
    # at slice time with "The selected printer is not compatible with the
    # process preset in the 3mf." (rc=-17). Injecting both here closes the
    # gap. Source-of-failure: 2026-05-08 wife-test, twisty golf ball.
    process_id = PROCESS_PRESET_IDS.get((nozzle, tier))
    if process_id:
        result["print_settings_id"] = process_id
    compatible = COMPATIBLE_PRINTERS.get(nozzle)
    if compatible:
        result["print_compatible_printers"] = list(compatible)

    # P2S-invariant pins so a printer-less / foreign source 3MF can't leak an
    # invalid INHERITED value past the merged-settings validation. These win
    # because bake applies the composed profile as overrides on top of the
    # source's project_settings.config. Source of failure: 2026-06-03 gridfinity
    # baseplate (bare-geometry 3MF from gridfinitylayouttool.com).
    #   - top/bottom_surface_pattern: BS CLI retarget of a printer-less 3MF
    #     injects 'zig-zag', which BS accepts only for infill, not surface
    #     patterns. setdefault so a tier that already pins a valid value wins.
    result.setdefault("top_surface_pattern", "monotonicline")
    result.setdefault("bottom_surface_pattern", "monotonic")
    #   - filament_extruder_variant: the P2S data model encodes 2 extruder
    #     variants; a length-1 array triggers std::out_of_range ('vector' parse
    #     error / "no geometry data") in BS. Always pin length 2.
    result["filament_extruder_variant"] = ["Direct Drive Standard",
                                           "Direct Drive High Flow"]
    #   - nozzle_volume_type: Mike's P2S runs STANDARD-flow nozzles only
    #     (0.2/0.4/0.6/0.8 hardened steel — no Bambu High Flow hotend owned). A
    #     source 3MF from a High Flow project (e.g. the 0.8 HF A/B test) leaks
    #     nozzle_volume_type=["High Flow"] through retarget, which BS cannot
    #     reconcile against the selected Standard extruder at slice time:
    #     "could not found extruder_type Direct Drive, nozzle_volume_type High
    #     Flow". Hard-pin Standard so a retargeted file always matches the
    #     physical nozzle. Source of failure: 2026-06-08 0.4/0.6 solid baskets
    #     (both inherited High Flow from the 0.8 source, manually patched twice).
    #     NOTE: add a flag here if Mike ever installs a Bambu High Flow hotend.
    result["nozzle_volume_type"] = ["Standard"]
    result.setdefault("default_nozzle_volume_type", ["Standard"])
    #   - printable_area: a printer-less source retargets with a stale 200x200
    #     bed, so BS rejects any part >200mm as "no object fully inside the
    #     plate" (rc=-50). Pin the P2S 256x256 bed polygon.
    result["printable_area"] = ["0x0", "256x0", "256x256", "0x256"]

    return result


def list_profiles() -> list[tuple[str, str, str]]:
    """Return all valid (nozzle, material, tier) combinations."""
    combos = []
    for nozzle in NOZZLE_BASES:
        for material in MATERIALS:
            for key in QUALITY_TIERS:
                if key[0] == nozzle:
                    combos.append((nozzle, material, key[1]))
    return combos


# =============================================================================
# CLI — inspect profiles from the command line
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Print profile dictionary for the Bambu Lab P2S",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python print_profiles.py --list
  python print_profiles.py --nozzle 0.2mm --material "PETG-HF" --tier quality
  python print_profiles.py --nozzle 0.4mm --material "PLA Basic" --tier fast
""")
    parser.add_argument("--list", action="store_true", help="List all profile combinations")
    parser.add_argument("--nozzle", choices=list(NOZZLE_BASES.keys()))
    parser.add_argument("--material", choices=list(MATERIALS.keys()))
    parser.add_argument("--tier", choices=sorted({k[1] for k in QUALITY_TIERS}))
    parser.add_argument("--diff", action="store_true",
                        help="Show only settings that differ from standard tier")

    args = parser.parse_args()

    if args.list:
        print("Available profiles:")
        print(f"  Nozzles:   {', '.join(NOZZLE_BASES.keys())}")
        print(f"  Materials: {', '.join(MATERIALS.keys())}")
        tiers = sorted({k[1] for k in QUALITY_TIERS})
        print(f"  Tiers:     {', '.join(tiers)}")
        print()
        print(f"  Total combinations: {len(list_profiles())}")
        print()
        # Show summary table
        print(f"  {'Nozzle':<8} {'Material':<14} {'Tier':<10} {'Layer':<8} {'Walls':<6} {'Outer Speed'}")
        print(f"  {'------':<8} {'--------':<14} {'----':<10} {'-----':<8} {'-----':<6} {'-----------'}")
        for nozzle, material, tier in list_profiles():
            p = compose_profile(nozzle, material, tier)
            lh = p.get("layer_height", "?")
            wl = p.get("wall_loops", "?")
            ow = p.get("outer_wall_speed", "?")
            print(f"  {nozzle:<8} {material:<14} {tier:<10} {lh:<8} {wl:<6} {ow} mm/s")
        return

    if not all([args.nozzle, args.material, args.tier]):
        parser.error("Specify --nozzle, --material, and --tier (or use --list)")

    profile = compose_profile(args.nozzle, args.material, args.tier)

    if args.diff:
        standard = compose_profile(args.nozzle, args.material, "standard")
        print(f"Settings that differ from {args.nozzle} / {args.material} / standard:")
        print()
        for k in sorted(profile):
            if profile[k] != standard.get(k):
                print(f"  {k}: {standard.get(k, '(not set)')} → {profile[k]}")
    else:
        print(f"Profile: {args.nozzle} / {args.material} / {args.tier}")
        print(f"({len(profile)} settings)")
        print()
        for k in sorted(profile):
            print(f"  {k}: {profile[k]}")


if __name__ == "__main__":
    main()
