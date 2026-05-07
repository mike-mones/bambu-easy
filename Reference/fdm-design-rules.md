# FDM Design Rules for the Bambu Lab P2S

> Use this before designing, modifying, or approving any model for FDM printing. These are physics constraints: slicer tuning cannot rescue geometry that violates them.
>
> Confidence: mostly **SOURCED** from Prusa Knowledge Base, Simplify3D Print Quality Guide, Hubs/Protolabs design rules, Formlabs FDM comparisons, and common Bambu Studio practice. Treat dimensions as starting points; promote to **VERIFIED** only after your own successful print.

---

## Confidence tags

- **VERIFIED** — proven by a successful print on your machine/material/nozzle.
- **SOURCED** — from manufacturer docs or reputable FDM guides.
- **INFERRED** — engineering reasoning; validate before committing a long or expensive print.

---

## The 45° overhang rule

Any surface that extends outward more than about **45° from vertical** needs support or redesign.

| Overhang angle from vertical | Expected result |
|---|---|
| 0–30° | Clean, self-supporting |
| 30–45° | Usually acceptable |
| 45–60° | Visible sag; consider supports |
| 60–75° | Heavy sag; likely rough or failed |
| 75–90° | Unsupported plastic falls/curls |

**Design rule:** never approve >45° overhangs unless support contact, removal access, and surface scarring have been considered.

### Better than supports

- Replace shelves with 45° chamfers.
- Use teardrop holes for horizontal holes.
- Split the model and glue/screw parts together.
- Rotate the model so critical surfaces are self-supporting.

---

## Bridging

Bridging is printing a horizontal span between two supported edges. PLA bridges best; PETG usually sags more.

| Bridge length | Expected result |
|---|---|
| <10 mm | Clean |
| 10–20 mm | Minor sag |
| 20–50 mm | Visible sag; supports often help |
| >50 mm | Do not rely on unsupported bridging |

For important bridges: slow bridge speed, use strong cooling, and avoid wet filament. See [troubleshooting.md](troubleshooting.md) for poor-bridge symptoms.

---

## Minimum feature and wall sizes

| Nozzle | Printable single wall | Recommended minimum wall | Practical minimum detail |
|---|---:|---:|---:|
| 0.2 mm | 0.2 mm | 0.4 mm | ~0.25–0.35 mm |
| 0.4 mm | 0.4 mm | 0.8 mm | ~0.5–0.7 mm |
| 0.6 mm | 0.6 mm | 1.2 mm | ~0.8–1.0 mm |
| 0.8 mm | 0.8 mm | 1.6 mm | ~1.0–1.3 mm |

Rules:
- Functional parts need at least **2 wall loops**; 3–5 is common.
- Strength comes more from wall loops than from high infill.
- Embossed/engraved text should be at least **0.6 mm stroke width and 2 mm tall** on a 0.4 mm nozzle.
- Thin ribs around cutouts need extra thickness; for large perforated baskets, start around **2.0 mm wall thickness**.

---

## Layer adhesion and Z-axis strength

FDM parts are anisotropic. XY extrusions are stronger than Z layer bonds.

Factors affecting layer adhesion:
- **Nozzle temperature:** too low causes splitting, peeling, weak strands.
- **Layer height:** keep layer height below ~80% of nozzle diameter. With 0.4 mm nozzle, 0.32 mm is a practical maximum.
- **Cooling:** more cooling improves overhangs but can reduce layer fusion.
- **Speed:** slower walls give hotter material more time to bond.
- **Filament dryness:** moisture causes popping, roughness, weak bonding.

Orientation rule: put tensile loads along layers when possible. A hook printed flat on its side is usually far stronger than the same hook printed upright.

---

## Dimensional accuracy and tolerances

Generic FDM accuracy is often around **±0.5% with a lower limit around ±0.5 mm**. The P2S can do better, but fit-critical parts should still be tested.

Common tolerance starting points:

| Fit type | Starting clearance |
|---|---:|
| Sliding/nesting fit | 0.3–0.5 mm per side |
| Nice printed-on-same-printer fit | 0.15–0.30 mm per side |
| Light press fit | 0.00 to -0.10 mm interference |
| Glue pocket | +0.2–0.4 mm |
| Bearing/bushing hole | +0.1–0.2 mm, then ream if needed |

Design rules:
- Prototype one mating feature before printing a full assembly.
- Horizontal circular holes print slightly undersized and sag at the top; use teardrops or post-process when precision matters.
- Account for elephant's foot on first-layer-facing edges.

---

## First layer and bed adhesion

| Material | Recommended P2S plate | Notes |
|---|---|---|
| PLA / PLA Matte / PLA Silk | Textured PEI or Cool Plate | Textured PEI is the safe default |
| PETG / PETG-HF | Textured PEI | Avoid unsafe smooth-plate pairings; PETG can bond too strongly |
| ABS / ASA | Textured PEI, enclosed | Control drafts and warping |
| TPU | Textured PEI or smooth plate with care | May need glue stick as release layer |

Bed adhesion rules:
- Clean plate with dish soap for grease; IPA is maintenance, not a full degreaser.
- Use brim for tall/narrow parts or batches.
- If a first layer shows gaps between lines, tune Z/squish before changing random slicer settings.
- If corners lift, add brim, improve enclosure/draft control, or raise bed temperature within filament limits.

---

## Supports

Use supports deliberately; they leave scars and can damage thin geometry.

Supports are required for:
- Floating geometry with no material below.
- Overhangs above ~45° that cannot be redesigned.
- Horizontal holes or arches too large to bridge cleanly.

Avoid supports when:
- They are trapped inside enclosed spaces.
- They touch visible cosmetic surfaces.
- They attach to thin lattice/perforated walls.

Support strategy:
- Use tree supports for organic shapes and figurines.
- Use normal supports when tight, low-clearance features need predictable columns.
- Add support interface layers for cleaner undersides, but expect removal marks.

---

## Print orientation and load direction

| Part type | Preferred orientation | Why |
|---|---|---|
| Hook / hanger | On its side | Load stays in XY layers |
| L-bracket | Usually upright with the L visible from front | Bending load stays in stronger plane |
| Box / basket | Upright | Floor and walls print predictably |
| Clip / snap-fit | Flex direction along layers | Avoids peeling layers apart |
| Tube / pipe | Upright when possible | Avoids support scars inside bore |
| Flat plate | Flat on bed | Strong, stable, minimal supports |

For any load-bearing part, state the load case before changing wall loops or infill. "Functional" is not a load case.

| Load case | Typical force | Starting recipe |
|---|---:|---|
| Decorative/light handling | <20 lbf | 2 walls, 10–15% infill |
| Light functional bracket/tool body | 20–50 lbf | 3 walls, 15–25% gyroid/cubic |
| Hand-loaded clamp or threaded inserts | 50–200 lbf | 4–5 walls, 25–35% gyroid |
| Bodyweight/safety-critical | 200+ lbf | Do not rely on casual FDM design; engineer and test |

---

## Fasteners, inserts, and joints

| Screw | Self-tapping pilot | Clearance hole |
|---|---:|---:|
| M3 | 2.5 mm | 3.4 mm |
| M4 | 3.3 mm | 4.5 mm |
| M5 | 4.2 mm | 5.5 mm |

Boss diameter should be at least **2× screw diameter**. Heat-set insert starting holes: M3 4.0–4.2 mm, M4 5.3–5.6 mm, M5 6.4–6.8 mm. Leave at least 1.5 mm boss wall around inserts.

Snap-fits: use PETG or tougher material for repeated flexing; PLA snap-fits fatigue quickly. Use 0.5–1.0 mm undercut and 30–45° entry ramps.

---

## Thermal and material limits

| Material | Approx. glass transition | Practical service temp | Use warning |
|---|---:|---:|---|
| PLA | ~60°C | ~50°C | Hot cars, windowsills, dishwashers can deform it |
| PETG | ~80°C | ~70°C | Better heat resistance, still not dishwasher-safe by default |
| ABS/ASA | ~105°C | ~90°C | Needs enclosure/ventilation; better for heat and outdoor use |
| TPU | varies | varies | Flexible, slower, moisture-sensitive |

If the part lives in a car, sun, dishwasher, near electronics, or near appliances, flag PLA as risky.

---

## Safety and suitability

- FDM layer lines can harbor bacteria; do not assume food safety.
- Small printed parts are choking hazards for children under 3.
- PLA can shatter into sharp edges; avoid for rough child handling.
- Do not use hobby FDM parts for climbing, vehicle safety, medical use, or other safety-critical loads without proper engineering validation.

---

## Validation before printing

1. Slice in Bambu Studio.
2. Open **Preview** and scrub the first layers, support contact regions, bridges, and top layers.
3. Treat slicer warnings as blockers until understood.
4. For fit-critical work, print a small tolerance coupon first.
5. For tall/long prints, consider a shortened test section before the full part.

See [print-settings.md](print-settings.md) for P2S settings and [troubleshooting.md](troubleshooting.md) for symptom-based fixes.
