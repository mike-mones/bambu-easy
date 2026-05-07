# P2S Print Settings Guide

> Use this for P2S print setting recommendations, 3MF baking, material selection, and Bambu Studio setting names. Values are starting points unless marked **VERIFIED** by a user's own successful print.

---

## Recommendation rules

1. Identify the use case: decorative, prototype, toy, storage, functional, heat-exposed, load-bearing.
2. Identify filament, nozzle, plate type, and quality priority.
3. Use exact Bambu Studio labels from [bambu-studio-ui.md](bambu-studio-ui.md).
4. Prefer baking settings into the 3MF with `bambu-easy` over giving a manual checklist.
5. If you must recommend manual changes, include the exact UI path.
6. Classify confidence: **VERIFIED**, **SOURCED**, or **INFERRED**.
7. Validate with `bambu-easy --self-test` for the fixture or the full `bambu-easy file.3mf` pipeline for a real file before calling a 3MF print-ready.

Local users should track their own filament inventory however they like: spreadsheet, notes app, AMS memory, or a JSON file. The important data is material, brand, color, dryness state, loaded AMS slot, and remaining mass.

---

## P2S baseline materials

| Material | Nozzle temp | Bed / plate | Fan | Max volumetric speed | Notes |
|---|---:|---|---|---:|---|
| PLA Basic | 210–225°C | Textured PEI 55–60°C or Cool Plate per BS guidance | 80–100% | 18–21 mm³/s | Easiest default |
| PLA Matte | 220–235°C | Textured PEI 55–60°C | 80–100% | 15–18 mm³/s | Matte additives can weaken layer adhesion; hotter often helps |
| PLA Silk / Silk+ | 220–235°C | Textured PEI 55–60°C | 100% for consistent sheen | 10–14 mm³/s | Slower walls improve gloss; avoid ironing if sheen matters |
| PETG / PETG-HF | 240–260°C | Textured PEI 70–80°C | 40–80% depending brand | 10–14 mm³/s | Dry first; expect some stringing |
| ABS | 250–270°C | Textured PEI 90–110°C, enclosed | low to moderate | 10–16 mm³/s | Ventilate; warps without enclosure |
| ASA | 250–270°C | Textured PEI 90–110°C, enclosed | low to moderate | 10–16 mm³/s | Better UV resistance than ABS |
| TPU | 220–240°C | Textured PEI 35–50°C | low to moderate | 2–6 mm³/s | Slow down; avoid long retractions |

**SOURCED note:** always check the filament manufacturer's spool label. Brand-specific values override generic tables.

---

## P2S quality tiers

These map to how `bambu-easy` thinks about a 0.4 mm nozzle. Use them as intent labels, not immutable engineering truth.

| Tier | Layer height | Typical use | Starting settings |
|---|---:|---|---|
| Fast | 0.28 mm | prototypes, brackets, hidden parts | 2–3 walls, 10–15% infill |
| Standard | 0.20 mm | most prints | 3 walls, 15–20% infill |
| Quality | 0.16 mm | visible parts | 3–4 walls, 15–20% infill |
| Premium | 0.12 mm | figurines, display pieces | 4 walls, slower outer/top surfaces |

For 0.2 mm nozzle cosmetic work, common layer heights are 0.06–0.10 mm; print time increases sharply.

---

## Nozzle-dependent settings

| Setting | 0.2 mm | 0.4 mm | 0.6 mm | 0.8 mm | Rule |
|---|---:|---:|---:|---:|---|
| `nozzle_diameter` | 0.2 | 0.4 | 0.6 | 0.8 | Exact match |
| Layer height range | 0.04–0.12 | 0.08–0.28 | 0.15–0.36 | 0.20–0.48 | Keep ≤80% nozzle |
| Line width | 0.20–0.24 | 0.40–0.50 | 0.60–0.72 | 0.80–0.96 | 100–120% nozzle |
| Initial layer line width | ~0.24 | ~0.50 | ~0.72 | ~0.95 | Wider for adhesion |
| Retraction baseline | 0.3–0.5 | 0.5–0.8 | 0.5–0.8 | 0.6–1.0 | Direct-drive; tune by filament |
| Max flow expectation | 3–6 | 12–21 | 18–28 | 24–36 | Material/hotend-limited |

When changing nozzles, update printer preset, nozzle diameter, line widths, layer height, retraction, and max volumetric speed together.

---

## Common use-case profiles

| Use case | Material | Layer | Walls | Infill | Supports | Notes |
|---|---|---:|---:|---:|---|---|
| MakerWorld default print | CLI auto-pick | source/standard | source/standard | source/standard | source | Use `bambu-easy file.3mf` |
| Functional bracket | PLA/PETG | 0.20 | 3–5 | 20–35% gyroid | as needed | Analyze load first |
| Decorative display | PLA Matte/Silk | 0.12–0.16 | 3–4 | 10–15% | minimize scars | Hide seam on rear |
| Toy / handled object | PETG/PLA Tough | 0.20 | 4 | 20–30% | avoid sharp scars | Check choking/edge risks |
| Storage basket | PLA/PETG | 0.20–0.28 | 2–3 | 10–20% | avoid internal supports | Use self-supporting perforations |
| Tiny figurine | PLA or PETG-HF | 0.06–0.12 with 0.2 nozzle | 3–5 | 10–15% | tree(auto), tuned interface | Geometry may dominate quality |
| Multicolor text/inlay | PLA | 0.12–0.20 | 3 | 10–15% | usually off | Validate AMS mapping and purge |

---

## Setting categories checklist

When optimizing, cover every relevant category in one pass:

### Process settings
- **Layers:** Layer height, First layer height.
- **Line widths:** Default, outer wall, inner wall, top surface, initial layer.
- **Walls:** Wall loops, Wall generator, wall order.
- **Top/bottom:** Top shell layers, Bottom shell layers, Top surface pattern.
- **Infill:** Sparse infill density, Sparse infill pattern.
- **Speed:** Outer wall, Inner wall, Sparse infill, Top surface, Bridge, Initial layer, Travel.
- **Acceleration:** default and outer wall acceleration if needed.
- **Support:** Enable support, Type, support interface.
- **Bed adhesion:** Brim type, Brim width.
- **Seam:** Seam position, scarf seam when appropriate.
- **Ironing:** only for large flat top surfaces.
- **Z hop / retraction:** tune only when symptoms justify it.

### Filament settings
- **Temperature:** Nozzle temperature and initial layer temperature.
- **Bed:** Bed temperature and plate type.
- **Cooling:** min/max fan, overhang fan, slow down for better layer cooling.
- **Flow:** Flow ratio and max volumetric speed.
- **Retraction:** length, speed, wipe.

---

## Volumetric speed ceiling

Requested speed is not always actual speed. Flow is:

`mm³/s = speed × layer_height × extrusion_width`

Examples:
- 0.20 mm layer × 0.50 mm line × 250 mm/s = 25 mm³/s, above many PLA limits.
- If Bambu Studio Preview shows a segment's flow exactly at the filament max, it is flow-capped.

Use **Filament Settings → Setting Overrides → Max volumetric speed** to set a safe ceiling. Lower it for matte, silk, PETG, flexible, or wet filament.

---

## Cooling and layer time

For small objects, each layer may complete before the previous layer cools. Use **Filament Settings → Cooling → Slow printing down for better layer cooling**.

| Layer/nozzle | Min layer time |
|---|---:|
| 0.08 mm on 0.2 mm nozzle | 8–12 s |
| 0.12 mm on 0.4 mm nozzle | 8–10 s |
| 0.20 mm on 0.4 mm nozzle | 5–7 s |
| 0.28 mm on 0.4 mm nozzle | 4–6 s |

Do not overdo minimum layer time on tiny isolated posts: too much nozzle dwell can re-melt features. Printing 2–3 copies spread apart often cools better.

---

## Seams, top surfaces, and cosmetic quality

- **Seam position:** use **Aligned** or **Rear** for geometric objects; random seam scatters zits.
- **Scarf seam:** useful on premium cosmetic prints; avoid on highly structural outer walls unless tested.
- **Top surface pattern:** **Monotonic** or **Monotonic lines** gives more consistent top finish.
- **Top surface speed:** 40–80 mm/s for premium tops; 100–150 mm/s for balanced functional parts.
- **Ironing:** useful on large flat PLA tops; avoid on metallic/silk finishes if it dulls the sheen.
- **Wall loops:** 4+ can hide infill telegraphing on visible walls.

---

## Supports and brim defaults

- Use **Tree(auto)** for organic shapes and figurines.
- Use normal supports for tight low-clearance regions where trees cannot reach.
- Add support interface layers for cleaner undersides.
- Use brim for tall/narrow parts, low bed contact, batches, or warp-prone material.
- Avoid supports inside inaccessible lattice or enclosed cavities.

---

## Multicolor and AMS notes

- Confirm every object/part has the intended filament number.
- In Preview, scrub color changes and prime tower layers.
- Use distinct filament colors in project metadata; identical colors can confuse visual mapping.
- Prime towers waste material but stabilize color transitions. Reducing tower size is safer than disabling it on purge-sensitive prints.
- For small colored text on a large body, purge waste can exceed part mass. That is acceptable only when the file is otherwise high-confidence.

---

## 3MF baking notes

3MF files are ZIP archives with mesh plus metadata. Bambu Studio may load preset defaults if preset IDs point to built-in profiles. For robust settings:

1. Use `bambu-easy` for ordinary MakerWorld-to-P2S preparation.
2. For custom generators, write all relevant settings into the 3MF rather than asking the user to manually change Bambu Studio.
3. Validate with a headless Bambu Studio slice where available.
4. Check embedded filament settings, project settings, plate metadata, and nozzle/printer metadata together.
5. Never edit a user's global Bambu Studio preset folder except via a documented install command such as `bambu-easy --install-presets`.

---

## Filament drying

| Material | Drying temp | Time |
|---|---:|---:|
| PLA | 45–50°C | 4–6 h |
| PETG | 60–65°C | 6–8 h |
| ABS/ASA | 65–75°C | 4–8 h |
| Nylon | 70–80°C | 8–12 h |
| TPU | 45–55°C | 4–8 h |

Wet filament symptoms: popping, sizzling, rough surface, stringing, weak layers, inconsistent extrusion.

---

## Troubleshooting pointer

For symptom-based diagnosis, use [troubleshooting.md](troubleshooting.md). For geometry limits, use [fdm-design-rules.md](fdm-design-rules.md). For calibration procedures, use [calibration.md](calibration.md).
