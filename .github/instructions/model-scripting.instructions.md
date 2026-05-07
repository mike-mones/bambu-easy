---
description: "Use when writing or modifying Python scripts that generate, edit, or analyze 3D models (STL, 3MF). Covers trimesh/build123d patterns, preview workflow, and mesh safety."
applyTo: '**/*.py'
---
# 3D Model Scripting Rules

## Scope

These rules apply to Python scripts that generate, modify, inspect, repair, or package 3D models. They are meant for advanced users extending this repo beyond the normal `bambu-easy file.3mf` workflow.

## First principles

- Prefer the existing `bambu-easy` CLI for ordinary MakerWorld 3MF preparation.
- Do not edit `bambu_easy/_engine/*`; those are frozen vendored engine files.
- Do not modify the user's Bambu Studio preset folder except through `bambu-easy --install-presets`.
- If a script produces a printable file, bake settings into the 3MF rather than giving the user manual Bambu Studio steps.

## From-scratch model design

Before writing a generator for a new model:
1. Read `Reference/model-design-from-scratch.md`.
2. Declare the coordinate system at the top of the script.
3. Write a dimension sheet with formulas for derived values.
4. Design mating interfaces first.
5. Print pre-generation checks before creating geometry.
6. Validate generated dimensions with trimesh.

Use comments for constraints that must not regress:

```python
# 6.15 mm = 6 mm magnet + 0.15 mm clearance for this print profile.
# VERIFIED by local test print. Do not change without a new fit test.
SIDE_MAGNET_HOLE_DIA = 6.15
```

## build123d patterns

- Prefer subtractive construction: start with a solid and subtract voids/pockets.
- Use additive construction only when bodies overlap with real volume, not edge-only contact.
- Extend subtractive sketches 0.05–0.1 mm beyond target faces to avoid coincident-face artifacts.
- Check `RectangleRounded` radii are smaller than half the smallest dimension.
- Use one clear build context per part.
- Re-export build123d STL output through trimesh for viewer/slicer robustness.

## trimesh patterns

- Load validation meshes with `process=True` unless preserving exact source topology matters.
- After every boolean or repair, print bounds, watertight status, body count, vertex count, and face count.
- Use `engine="manifold"` for booleans when available.
- If boolean union creates disconnected bodies, treat it as a failure even if `is_watertight` is true.
- Use `contains()` for collision/interference checks, not as proof of connectivity.
- Avoid full voxel grids and brute-force point clouds.

## Mesh repair / hole filling

Before imported-mesh surgery, read `Reference/hole-filling.md`.

Rules:
- Keep the original file unchanged.
- Prefer cross-sections over coarse ray grids for detecting holes/features.
- Use connectivity-aware face flood fill for deleting hole walls.
- For cosmetic curved surfaces, fit a local surface and fill with blended rings, not a flat fan.
- Validate watertightness and preview before printing.

## Multi-part assemblies

Every generated part must pass independently before assembly:
- dimensions match expected values
- watertight if intended
- body count is expected
- no missing pockets/features

Then verify assembled fit:
- transform parts into assembled coordinates once
- print bounds after each transform
- run interference checks both directions
- export an assembled preview

Do not show side-by-side previews when the actual question is fit.

## 3MF and settings export

For any script that creates a print-ready 3MF:
- Use the repo's public CLI/prepare path where possible.
- Keep printer/nozzle/material settings consistent with `Reference/print-settings.md`.
- Bake all relevant settings into the 3MF.
- Validate with Bambu Studio slicing when available.
- Print a summary of layer height, nozzle, filament, temperatures, walls, infill, supports, brim, and output path.

Never ask the user to manually fix settings in Bambu Studio if the script can bake them.

## Preview workflow

For model generation or mesh modification:
1. Export print-ready STL in normal Z-up coordinates.
2. Export a separate preview STL if the viewer needs a transform.
3. For assemblies, export each part and the assembled state.
4. Inspect the preview and Bambu Studio Preview before calling it print-ready.
5. Remove or clearly label throwaway preview files when done.

## Memory and runtime safety

- Estimate memory before loading high-poly meshes.
- Avoid algorithms that scale as dense 3D grids unless the grid is tiny.
- Put bounds on loops and sampling counts.
- Print progress for steps that may take more than a few seconds.
- Fail loudly when validation fails; do not continue to export a known-bad model.

## Anti-regression rules

- Do not add `--fast`, `--draft`, or `--premium` toggles that silently change verified dimensions.
- If a value is marked VERIFIED, only change it with a new test plan.
- Make one geometric fix at a time and rerun validation.
- Treat slicer warnings as blockers unless explicitly classified as an accepted INFERRED risk.
