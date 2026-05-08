# Changelog

All notable changes to bambu-easy. Newest first.

## 0.1.1 — 2026-05-08

### Fixed (CRITICAL — wife test)

- **MakerWorld 3MFs from non-P2S printers no longer crash BS at slice with rc=-17**
  ("The selected printer is not compatible with the process preset in the 3mf").
  Root cause: after auto-retargeting via the BS CLI, the bake step was leaving
  `print_settings_id` empty and `print_compatible_printers` stale (still
  referencing the source printer's nozzle). BS rejected on slice. Fix:
  `_engine/print_profiles.py` `compose_profile()` now injects both fields
  from new `PROCESS_PRESET_IDS` (per nozzle×tier) and `COMPATIBLE_PRINTERS`
  (per nozzle) tables; `_engine/bake_3mf_settings.py` now respects a caller-
  provided `print_settings_id` override instead of blindly clearing it.
  Source-of-failure: `Models/TwistyGolfBall/twisty_golf_ball.3mf` —
  the wife's earlier attempt produced a file BS silently refused to slice,
  with no actionable error in the bambu-easy output.

- **Single-color bakes from multi-filament source 3MFs no longer leave
  orphaned per-filament arrays** that confuse the AMS Send dialog (and
  historically caused real print failures — see `3D Printing/Reference/
  failure-log.md` Mar 19 PSA card holder, where mismatched array lengths
  caused an extruder to default to 0°C). New `_normalize_to_single_filament`
  helper in `prepare.py` trims `filament_colour`, `hot_plate_temp`,
  `cool_plate_temp`, `eng_plate_temp`, `textured_plate_temp`,
  `supertack_plate_temp` (and their `_initial_layer` siblings) to length 1
  whenever the user is baking a single-filament profile.

### Added

- `--slot <SLOT>` flag — pin filament to a specific AMS slot (e.g. `--slot A2`)
  instead of the default "most filled" pick. Matters when multiple slots
  carry the same material (e.g. two PLA Matte spools, different colors).
- `--color <#RRGGBB>` flag — set `filament_colour` explicitly. When omitted,
  bambu-easy now auto-fills from the AMS slot color (via MQTT poll's
  `tray_color`) so the AMS Send dialog displays the correct color
  out-of-the-box.

### Tests

- 36/36 passing (`pytest tests/ -q`). Two `test_end_to_end.py` assertions
  updated to reflect the new `print_settings_id` / `print_compatible_printers`
  injection (regression coverage for the wife-test fix).

## 0.1.0 — 2026-05-07

Initial release. Wife-friendly wrapper around the 3D-printing repo's
proven P2S preparation logic.
