# Changelog

All notable changes to bambu-easy. Newest first.

# Changelog

All notable changes to bambu-easy. Newest first.

## 0.1.3 — 2026-06-04

### Fixed (CRITICAL — GUI "Invalid configuration file" on multi-filament sources)

- **MakerWorld 3MFs that embed multiple filaments (one per AMS slot) no longer
  produce a file the Bambu Studio GUI rejects with "Invalid configuration
  file"** — even though the headless BS slice oracle passed `rc=0`. Root cause:
  the old `_normalize_to_single_filament` trimmed a hardcoded ~11-key whitelist
  of per-filament arrays to length 1, while `bake`/`compose` independently
  shrank `filament_settings_id`, `nozzle_temperature`, plate temps, etc. to
  length 1. The remaining ~70 `filament_*` arrays stayed at the source's
  filament count N. The result declared 1 filament in some keys and N in
  others — an inconsistency the headless slicer tolerates (it reads only the
  first entry it needs) but the GUI validator rejects.
- Reducing the project to a *true* single filament is not robust: ground truth
  from a valid single-filament 3MF shows per-key single-filament lengths are
  idiosyncratic (e.g. `flush_volumes_vector` is length 8 for ONE filament), so
  there is no `length = source_len / N` formula.
- **Fix**: replaced `_normalize_to_single_filament` with
  `_normalize_filament_array_lengths`, which reads the SOURCE 3MF's per-filament
  array lengths and re-aligns every per-filament array in the output to the
  source count, **broadcasting the baked value across all slots**. The output
  stays as self-consistent as the GUI-valid source; only the values change. For
  a single-color model the extra slot is harmless (both slots carry the same
  filament). Per-filament keys are detected by `_is_per_filament_key`
  (`filament*` / `nozzle_temperature*` / `*plate_temp*` / cooling-fan keys).
  Idempotent — bare-geometry single-filament sources are untouched.
- Regression coverage: `tests/test_normalize_filament_lengths.py` (4 tests).
  Full suite 43 passing.

## 0.1.2 — 2026-06-03

### Fixed (CRITICAL — off-plate bare-geometry sources)

- **Bare-geometry / web-tool 3MFs (e.g. gridfinitylayouttool.com exports) no
  longer fail BS slice with rc=-50** ("object is not fully inside the plate").
  Root cause: bambu-easy assumed MakerWorld-style pre-arranged sources and had
  no arrange/centre step. When the BS CLI retargets a printer-less 3MF it
  re-centres the mesh's *local* coords to the origin but leaves a build-item
  translation that drops the object off the front of the plate (world Y
  -294..-40 for the gridfinity piece). `--arrange 1` on the BS CLI does **not**
  fix this. Fix: new `_ensure_on_plate()` in `prepare.py` rewrites the build
  `<item transform>` translation so the object's world XY bbox centres on the
  P2S plate (128,128). It runs after the bake/normalize step (so the 256×256
  printable_area is already in place) and before BS slice validation. The step
  is idempotent — files already fully on the plate (all MakerWorld arranged
  sources) are untouched. The CLI now prints a "🪄 Re-arranged object onto
  plate" line when a shift was applied.
  Source-of-failure: `gridfinity-baseplate-5x12-padded-connectors_piece-a.3mf`.

### Fixed

- **PLA Matte / PLA Silk+ now bake the Textured PEI bed at 65°C** (was 55°C).
  The 55°C value in `_engine/print_profiles.py` MATERIALS contradicted the
  VERIFIED first-layer-adhesion temp; every Matte/Silk+ bake was 10°C low.
  PLA Basic stays 55°C, PETG-HF 80°C.

### Tests

- Added `tests/test_ensure_on_plate.py` (centring, idempotency, no-op on an
  already-on-plate file). Suite now 39 passing.

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
