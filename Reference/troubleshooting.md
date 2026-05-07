# P2S Troubleshooting Guide

> Generic symptom → cause → fix guide for Bambu Lab P2S FDM prints. Start with visible symptoms, identify the most likely causes, then make one change at a time.

---

## Quick triage

1. Did Bambu Studio show a warning? Treat it as real until understood.
2. Did the first layer look right? If not, fix that first.
3. Is the filament dry and appropriate for the model?
4. Is the model printable under [fdm-design-rules.md](fdm-design-rules.md)?
5. Did settings actually bake into the 3MF? If using this repo, rerun `bambu-easy` or `bambu-easy --doctor`.

---

## Layer adhesion failures

Symptoms: layers split/peel, strands separate, part snaps along layer lines, rough under-extruded walls.

Top causes:
1. Nozzle temperature too low.
2. Layer height too large or speed too high.
3. Too much cooling or wet filament.

Fixes: raise nozzle temperature 5–10°C within spec, lower layer height, slow outer walls, dry filament, reduce part cooling modestly while keeping overhang fan high, and reorient load along XY layers. See [fdm-design-rules.md](fdm-design-rules.md).

---

## Bed adhesion failures

Symptoms: first layer gaps, corners curl upward, part pops off, brim detaches.

Top causes:
1. Dirty plate or wrong plate.
2. Bad first-layer squish/Z offset.
3. Warping from drafts, low bed temp, or too little brim.

Fixes: wash plate with dish soap, reseat plate, run auto-leveling, print a squish test, use correct plate, add brim, raise bed temperature within limits, and reduce drafts. See [calibration.md](calibration.md).

---

## Stringing and oozing

Symptoms: hairs between towers, wisps inside lattice, blobs at travel endpoints, furry PETG.

Top causes:
1. Wet filament.
2. Temperature too high.
3. Retraction/wipe not tuned.

Fixes: dry filament first, run a temperature tower, run a retraction tower after temperature is chosen, increase travel speed if safe, and accept light PETG hairing if a heat-gun pass removes it. See [calibration.md](calibration.md).

---

## Ringing / ghosting

Symptoms: echoes after sharp corners or text, repeating ripples on outer walls, wavy cosmetic faces.

Top causes:
1. Acceleration/speed too high.
2. Tall/thin model vibration.
3. Loose belts, unstable table, or printer resonance.

Fixes: reduce **Process Settings → Speed → Outer wall**, reduce acceleration if exposed, orient details away from high-speed direction changes, run available calibration, and check printer stability.

---

## Dimensional inaccuracy

Symptoms: pegs do not fit holes, lids bind/rattle, holes undersized, large parts miss target size.

Top causes:
1. Clearance too small.
2. Elephant's foot.
3. Flow ratio or shrinkage not calibrated.

Fixes: add 0.2–0.5 mm per-side clearance for sliding parts, use teardrop or vertical orientation for holes, add elephant foot compensation or bottom chamfers, run Flow Rate calibration, and print a tolerance coupon. See [fdm-design-rules.md](fdm-design-rules.md).

---

## Support scarring and poor undersides

Symptoms: rough support underside, pits after support removal, broken thin features, trapped supports.

Top causes:
1. Orientation puts visible surfaces on supports.
2. Support interface distance/density is wrong.
3. Geometry should have been redesigned to self-support.

Fixes: reorient scars to hidden surfaces, use tree supports for organic models, use normal supports for tight regions, tune top Z distance/interface layers, split the model, or redesign overhangs. See [fdm-design-rules.md](fdm-design-rules.md).

---

## Poor bridging / sagging overhangs

Symptoms: drooping strands across gaps, rough roofs over infill/holes, curling ledges, spaghetti on thin near-horizontal tips.

Top causes:
1. Bridge too long or overhang too steep.
2. Cooling too low or bridge speed too high.
3. PETG/wet filament sagging more than PLA.

Fixes: redesign under 45° or add supports, shorten spans with ribs, increase bridge cooling, slow bridge speed, dry filament, or use PLA when material requirements allow. See [fdm-design-rules.md](fdm-design-rules.md) §Bridging.

---

## Multicolor / AMS issues

Symptoms: wrong color, send dialog cannot map filaments, prime tower fails, color bleed, purge waste shock.

Top causes:
1. Object/part assignments or metadata colors are wrong.
2. AMS slot material does not match project filament type.
3. Prime tower/brim/purge settings are too aggressive.

Fixes: verify object filament numbers, scrub color transitions in Preview, keep prime tower enabled for color-critical transitions, use distinct filament colors, confirm AMS material and remaining filament, and test small multicolor samples when confidence is low.

---

## Filament issues

Symptoms: popping/sizzling, brittle filament, sudden stringing, rough foamy surface, under-extrusion at normal speeds.

Top causes:
1. Moisture absorption.
2. Wrong filament preset/temperature.
3. Clog, worn nozzle, or spool feed friction.

Fixes: dry filament, confirm preset matches material, run a known-good test, check AMS/spool path, cold pull, or replace nozzle if unresolved. See [print-settings.md](print-settings.md).

---

## Under-extrusion / clogs

Symptoms: thin walls, gaps, missing infill, extruder clicking, print starts fine then starves.

Top causes:
1. Max volumetric speed too high.
2. Partial clog or heat creep.
3. Wet/dirty filament or path restriction.

Fixes: lower **Filament Settings → Setting Overrides → Max volumetric speed**, run max-flow calibration, dry filament, check spool path, cold pull, and replace nozzle if unresolved. See [calibration.md](calibration.md).

---

## Blobs, zits, and seams

Symptoms: vertical line of bumps, random zits, bulging corners, blobs after travel.

Top causes:
1. Seam position/wipe/retraction issue.
2. Pressure advance not calibrated.
3. Wet filament or temperature too high.

Fixes: use **Process Settings → Others → Seam position → Aligned** or Rear, try scarf seam for premium cosmetic walls, run Flow Dynamics calibration, dry filament, retest temperature, and tune retraction only after flow/temperature are reasonable.

---

## Warping

Symptoms: corners lift, large flat parts bow, layers split near corners, ABS/ASA cracks.

Top causes:
1. Material shrinkage and drafts.
2. Bed temperature/adhesion too low.
3. Large sharp-corner footprint.

Fixes: add brim or mouse ears, round/chamfer base corners, use enclosure/closed door for ABS/ASA, raise bed temperature within limits, split large parts, or change orientation.

---

## Failure-response protocol

When a print fails:
1. Stop changing multiple settings at once.
2. Photograph first layer, failure point, and Bambu Studio Preview at that layer.
3. Identify which category above matches symptoms.
4. Make one change and reprint a small test if possible.
5. Record what worked so it becomes VERIFIED for your machine.
