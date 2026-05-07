# Designing Models From Scratch

> Use this before generating any original model with build123d, OpenSCAD, cadquery, or raw trimesh. The goal is math-first design, not preview-and-pray iteration.

---

## Mandatory process

### Phase -1: Feasibility gate for complex geometry

Run this before booleans, mechanism adaptation, organic mesh edits, or multi-part assemblies.

1. **Source compatibility:** does the target shape physically support the mechanism or cut?
2. **Reference study:** if working examples exist, analyze how they solve the problem; do not copy superficial dimensions.
3. **Failure modes:** name the top 1–2 likely failures.
4. **Fallback:** define what you will do if this approach fails after a few iterations.
5. **Proof of concept:** for high-risk work, run a cheap boolean/cross-section/profile test before full implementation.

Skip this for simple boxes, brackets, labels, pockets, and plain extrusions.

---

## Phase 0: reference analysis

If a user provides a photo, screenshot, URL, or existing model:
- Extract dimensions and proportions.
- Convert all units to millimeters.
- Identify mechanisms: sliding, snapping, magnet, screw, hinge, detent.
- Identify material and load assumptions.
- State the geometry in words before coding.

Do not start with vague inspiration. Turn references into concrete dimensions.

---

## Phase 0.5: graph parametric shapes first

Any mathematically defined profile should be plotted in 2D before becoming 3D: rounded cross-sections, wave profiles, cam paths, latch teeth, pocket outlines, or ergonomic curves.

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-half_width, half_width, 300)
plt.plot(x, profile_a(x), label="profile A")
plt.plot(x, profile_b(x), label="profile B")
plt.axis("equal")
plt.grid(True)
plt.legend()
plt.savefig("Models/profile_options.png", dpi=150)
```

A 2D plot catches most shape mistakes faster than full STL regeneration.

---

## Phase 1: coordinate system declaration

Every generator should start with a fixed coordinate comment:

```python
# COORDINATE SYSTEM (fixed):
#   X = width, +X right
#   Y = depth/length, -Y front/entry, +Y back
#   Z = height, +Z up from bed
```

Then verify every feature sign. Front wall features should have negative Y, back stops positive Y, bottom pockets near Z=0, and assemblies should use one clearly documented coordinate space.

---

## Phase 2: dimension sheet

Put all primary and derived dimensions in one place with formulas:

```python
# DIMENSION SHEET
# Body outer: W=80, D=50, H=22
# Wall: 2.0, floor: 1.6
# Body inner: W - 2*wall = 76, D - 2*wall = 46
# Lid inner: body_outer + 2*clearance = 80.6 x 50.6
# Lid outer: lid_inner + 2*lid_wall = 83.0 x 53.0
# CHECK: lid_inner_w > body_w
# CHECK: pocket_depth <= wall - 0.4
```

Derived dimensions should not be duplicated as independent constants.

---

## Phase 3: cross-section reasoning

Before coding a mechanism, draw a 2D cross-section in comments. If you cannot draw it, you do not understand the geometry enough to generate it.

For a sliding lid, include body wall, lid plate, rails/grooves, clearance, stops, and insertion direction. For snap-fits, include ramp angle, retention face, flexing member thickness, and clearance after snap.

---

## Phase 4: interface-first design

For multi-part assemblies, design the mating interface first:
1. Define base part outer dimensions.
2. Define mating part inner dimensions from base + clearance.
3. Define wall/rail/groove from interface dimensions.
4. Add cosmetic or secondary features last.

Never independently define a dimension that should derive from the mating part.

---

## Mechanism catalog

### Sliding lid

- Body has grooves/channels near the rim.
- Lid has rails/tongues that fit the grooves.
- Clearance: 0.2–0.5 mm per side depending required smoothness.
- Groove must extend through the entry wall with 0.1–0.2 mm overshoot.
- Add retention: magnet, detent bump, latch, or friction feature.

### Sleeve lid

- Sleeve inner = body outer + clearance.
- Sleeve should cover the full width and length of the body, not a partial axis by accident.
- Clearance: 0.3–0.5 mm per side.
- Print body and sleeve in orientations that avoid trapped supports.

### Snap-fit lid

- Use PETG or tougher material for repeated flexing.
- Ridge height: ~0.3–0.5 mm for small consumer parts.
- Lip thickness: ~0.8–1.2 mm.
- Entry ramp: 30–45°.
- Test one latch before committing to a whole product.

### Hinge

- Pin diameter ≥3 mm for practical printed hinges.
- Print-in-place clearance: 0.3 mm minimum, 0.4–0.5 mm safer.
- Avoid PLA living hinges; use TPU/nylon or mechanical pins for repeated use.

### Magnets and pockets

- Pocket diameter: magnet diameter + 0.1–0.3 mm depending glue/press-fit target.
- Pocket depth: magnet thickness + 0.1–0.2 mm unless it must sit perfectly flush.
- Leave at least 0.4–0.5 mm material behind blind pockets.
- For rotational stability, use two spaced magnets or three non-collinear constraints.
- Mark polarity in assembly instructions.

---

## build123d patterns

Reliable patterns:
- Use subtractive construction for boxes and lids: start solid, subtract voids.
- Use additive construction only when bodies overlap with real volume, not edge-only contact.
- Use `RectangleRounded()` + `extrude()` for rounded boxes.
- Use `Circle()` + `extrude(mode=Mode.SUBTRACT)` for pockets/holes.
- Extend cuts 0.05–0.1 mm beyond target faces to avoid coincident faces.
- Apply fillets after creating the main solid.
- Re-export through trimesh for robust STL output.

Common mistakes:
- Forgetting `Mode.SUBTRACT` for pockets.
- Extruding the wrong direction from an offset plane.
- Corner radius ≥ half of the smaller rectangle dimension.
- Additive union of thin touching bodies that only share an edge.
- Nested build contexts that make geometry hard to reason about.

---

## trimesh patterns

Use trimesh for loading, validating, transformations, boolean checks, bounds verification, and preview exports.

Rules:
- Prefer `process=True` for validation, but compare to original if processing changes topology.
- Use `engine="manifold"` for booleans when available.
- Check `mesh.is_watertight`, body count, bounds, and face count after every boolean.
- `contains()` is useful for interference, not for connectivity.

---

## Pre-generation verification

Every generator should print checks before making the final mesh:

```python
def verify_dimensions():
    checks = [
        (lid_inner_w > body_outer_w, "lid inner width clears body"),
        (pocket_depth <= wall_t - 0.4, "blind pocket leaves wall"),
        (rail_w > 2 * nozzle, "rail is printable"),
        (clearance >= 0.2, "clearance is printable"),
    ]
    for ok, label in checks:
        print(f"{label}: {'OK' if ok else 'FAIL'}")
        if not ok:
            raise ValueError(label)
```

Check feature centers/extents, coordinate signs, mating clearances, remaining material, minimum feature size, and overhang/support implications.

---

## Post-generation verification

After generating each part:
1. Load through trimesh.
2. Print dimensions and compare to expected.
3. Check watertightness.
4. Check body count; booleans can create disconnected bodies.
5. For assemblies, position parts in assembled configuration.
6. Run interference checks both directions.
7. Export separate part previews and an assembled preview.
8. Bake print settings into a 3MF and validate the slice if printing.

Example assembly check:

```python
body = trimesh.load("body.stl", process=True)
lid = trimesh.load("lid.stl", process=True)
lid_placed = lid.copy()
lid_placed.apply_translation([0, 0, closed_z])
inside = body.contains(lid_placed.vertices).sum()
if inside:
    raise ValueError(f"lid has {inside} vertices inside body material")
```

---

## Preview workflow

For generated/modified models:
- Print-ready STL: Z-up, no viewer-only transforms.
- Preview STL: copy transformed as needed for the viewer.
- For multi-part work, preview each part and the assembled state.
- Do not rely only on screenshots; inspect dimensions and slice preview.

---

## Anti-patterns

- Fixing one visible defect without recomputing all related dimensions.
- Guessing a mating profile instead of reusing the exact same parameters.
- Adding runtime `--fast`/`--premium` toggles that change verified dimensions.
- Telling the user to manually set important Bambu Studio settings instead of baking them.
- Continuing after a slicer warning because it "seems harmless."
- Debugging a failed print without writing down the resulting rule in docs.

---

## Validation checklist before print

- Geometry obeys [fdm-design-rules.md](fdm-design-rules.md).
- Fit checks pass.
- Meshes are watertight or known-safe non-watertight with a reason.
- Slicer Preview shows expected first layers, supports, bridges, and top surfaces.
- Settings are baked by `bambu-easy` or a documented 3MF exporter.
- Confidence is tagged: VERIFIED / SOURCED / INFERRED.
