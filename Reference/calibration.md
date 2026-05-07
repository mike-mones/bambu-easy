# P2S Calibration Procedures

> Step-by-step calibration workflows for Bambu Lab P2S owners. The P2S works well with defaults; calibrate when changing hardware/materials or when a visible symptom points to calibration.

---

## When to calibrate

Run calibration when changing nozzle size, opening a new filament brand/material family, switching to a difficult color/additive blend, print quality changes suddenly, or diagnosing first-layer/stringing/corner/under-extrusion symptoms.

Do not calibrate endlessly when a model has bad geometry. Use [fdm-design-rules.md](fdm-design-rules.md) and [troubleshooting.md](troubleshooting.md) first.

---

## Recommended order

1. **First layer squish / bed contact** — foundation for every print.
2. **Flow Rate** — top surface and dimensional consistency.
3. **Flow Dynamics / Pressure Advance** — corners, starts/stops, blobs.
4. **Temperature tower** — per material/spool when symptoms justify it.
5. **Retraction tower** — only after temperature is reasonable.
6. **Max volumetric flow** — speed ceiling for fast printing.

Re-run first layer and max-flow after a nozzle change. Re-run flow rate and flow dynamics for new filament brands/colors.

---

## 1. First layer squish

**Goal:** lines merge enough to bond to the bed without being crushed into a glossy smear.

### Procedure

1. Clean the plate with dish soap and warm water; dry completely.
2. Install the intended plate and nozzle.
3. Run printer auto-leveling.
4. Print a single-layer square or first-layer calibration pattern, ideally 80–120 mm wide, at normal first-layer height.
5. Let it cool, then inspect.

### Read the result

| Observation | Diagnosis | Fix |
|---|---|---|
| Lines touch, faint line texture, matte/even | Correct | Keep settings |
| Smooth glossy smear, ridges pushed outward | Over-squished | Raise Z offset slightly |
| Gaps between lines, strands separate | Under-squished | Lower Z offset slightly |
| One side good, other side bad | Bed/plate not seated or leveling issue | Reseat plate, clean underside, rerun auto-level |
| Corners lift despite good center | Adhesion/warping | Clean plate, add brim, adjust bed temp/enclosure |

Use small changes: ±0.02–0.04 mm. Reprint after each adjustment.

---

## 2. Flow Rate

**Goal:** correct extrusion volume for a specific filament.

### Bambu Studio built-in method

1. Open Bambu Studio.
2. Use top menu **Calibration → Flow Rate**.
3. Run Pass 1.
4. Choose the best-looking patch: smooth top, no ridges, no gaps.
5. Run Pass 2 for fine adjustment if offered.
6. Save the result to the filament preset or record the flow ratio.

### Manual cube method

Print 30 × 30 × 3 mm top-surface cubes at flow ratios such as 0.94, 0.96, 0.98, 1.00. Use many top layers, moderate infill, monotonic top pattern, no ironing.

| Observation | Flow state |
|---|---|
| Gaps/valleys between top lines | Too low |
| Rough ridges, plowing, raised edges | Too high |
| Smooth, consistent, lightly glossy/matte depending material | Good |

Adjust in **Filament Settings → Filament → Flow ratio**.

---

## 3. Flow Dynamics / Pressure Advance

**Goal:** compensate for pressure lag in the extrusion system so corners and starts/stops look clean.

1. Use Bambu Studio top menu **Calibration → Flow Dynamics Calibration**.
2. Run it for the current filament.
3. Save the result if Bambu Studio offers a per-filament value.
4. Re-test when switching to a non-Bambu filament or a very different material.

| Symptom | Likely pressure advance issue |
|---|---|
| Bulging corners | Too low / under-compensated |
| Gaps at line starts | Too high / over-compensated |
| Blobs at direction changes | Too low or retraction/wipe interaction |

Do not tune pressure advance before flow rate; bad flow can mimic PA problems.

---

## 4. Temperature tower

**Goal:** find the best temperature range for a filament, balancing layer adhesion, stringing, overhangs, and surface finish.

1. Choose a tower model from MakerWorld, Teaching Tech, Orca/Bambu resources, or another reputable source.
2. Set segments across the filament's rated range: PLA example 230 → 225 → 220 → 215 → 210°C; PETG example 260 → 255 → 250 → 245 → 240°C.
3. Use the same fan and speed you expect to print with.
4. Print and inspect every segment.

| Observation | Meaning |
|---|---|
| Weak layer adhesion, matte under-extruded lines, rough gaps | Too cold |
| Heavy stringing, droopy bridges, soft detail | Too hot |
| Clean bridges, strong snap test, good surface | Candidate temperature |
| Best cosmetic and best strength differ | Prefer strength for functional parts; cosmetics for display parts |

Pick the lowest temperature that still gives strong layer adhesion and clean extrusion. For structural parts, bias slightly hotter.

---

## 5. Retraction tower

Retraction and temperature interact. Run a temperature tower first unless the filament's temperature is already known.

1. Pick the best temperature.
2. Print retraction towers around that temperature, or one tower per temperature if stringing is severe.
3. Sweep retraction distance in small steps.
4. Keep travel speed and z-hop representative of real prints.

| Material | Retraction length starting range |
|---|---:|
| PLA | 0.5–0.8 mm |
| PETG | 0.8–1.4 mm |
| TPU | 0.2–0.8 mm, slow |

Avoid going above ~2 mm on direct-drive unless you have a strong reason. PETG often retains light hair-like strings; if a heat-gun pass removes them, stop tuning.

---

## 6. Max volumetric flow

**Goal:** find the maximum reliable extrusion flow for a filament/nozzle/hotend combination.

`flow = speed × layer_height × extrusion_width`

1. Use a max-flow ramp model that gradually increases requested flow.
2. Print with the target nozzle, layer height, line width, and filament.
3. Watch/listen for under-extrusion: gaps, matte starvation, clicking, rough walls.
4. Note the flow where under-extrusion begins.
5. Set safe max = failure flow × 0.85–0.90.
6. Enter it in **Filament Settings → Setting Overrides → Max volumetric speed**.

| Material/nozzle | Typical safe range |
|---|---:|
| PLA, 0.4 mm | 17–21 mm³/s |
| PLA Matte/Silk, 0.4 mm | 12–18 mm³/s |
| PETG-HF, 0.4 mm | 10–14 mm³/s |
| 0.2 mm nozzle | Often 3–6 mm³/s |

These are SOURCED/INFERRED baselines. Your own tower result wins.

---

## Optional maintenance checks

### Filament moisture check

If a previously good filament starts stringing, popping, or printing rough: dry it, reprint a known-good small model, then tune if drying does not help.

### Nozzle health check

Suspect nozzle wear/clog if flow calibration drifts, first layer gets inconsistent with a clean bed, max volumetric flow drops, or walls show random thin/thick segments. Try a cold pull, then replace nozzle if symptoms persist.

---

## Documentation habit

When a calibration print succeeds, record printer/nozzle, filament brand/material/color, dryness state, plate type, resulting flow, pressure advance, temperature, retraction, max flow, and notes on why that value won. That is how a SOURCED setting becomes VERIFIED for a specific printer.
