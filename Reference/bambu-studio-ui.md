# Bambu Studio UI Reference

> Exact Bambu Studio terminology, menu paths, shortcuts, and setting locations. Use these labels rather than Cura/PrusaSlicer/generic names.

---

## Terminology corrections

| Avoid saying | Bambu Studio term | Notes |
|---|---|---|
| Add instance | **Clone** | Ctrl+K |
| Assemble | **Merge** | Recent versions use Merge; **Add part → Load…** is also common |
| Build plate | **Plate** | Bambu Studio supports multiple plates |
| Perimeters | **Wall loops** | JSON key: `wall_loops` |
| Infill density | **Sparse infill density** | JSON key: `sparse_infill_density` |
| Layer view | **Preview** | Left-side tab: Prepare / Preview |
| Profile | **Preset** | Printer, Filament, Process presets |
| Slicer | **Bambu Studio** | Be specific |

---

## Main workflow buttons

1. **Prepare** tab — arrange models and edit settings.
2. **Slice plate** — slices the selected plate.
3. **Slice All** — slices all plates in a multi-plate project.
4. **Preview** tab — inspect generated toolpaths.
5. **Print plate** — sends current plate to the printer.
6. **Send** — sends sliced file to printer/storage without starting immediately.

Always tell users to **Slice → Preview → scrub layers** before committing material.

---

## Top toolbar

| Button / tool | Shortcut | Purpose |
|---|---|---|
| **Add** | Ctrl+I | Import .3mf, .stl, .step/.stp, .obj, .amf |
| **Add Plate** | — | Add another print plate |
| **Auto Orient** | R / Shift+R current plate | Rotate for printability |
| **Arrange** | A / Shift+A current plate | Pack models on plates |
| **Variable Layer Height** | — | Region-specific layer height |
| **Split to Objects** | — | Separate independent meshes |
| **Split to Parts** | — | Keep pieces under one object |
| **Move** | — | Translate selected object |
| **Lay on Face** | — | Place selected face flat on plate |
| **Cut Tool** | — | Plane-cut a model |
| **Mesh Boolean** | — | Union/subtract/intersect mesh volumes |
| **Support Painting** | — | Paint support enforcers/blockers |
| **Seam** | — | Paint seam position |
| **Text Shape** | — | Add 3D text |
| **Color Painting Tool** | — | Assign colors/material regions |
| **Measurement Tool** | — | Measure distances/angles |
| **Assembly View** | — | Show assembled plates |
| **Brim Ear** | — | Add local brim tabs |

---

## Right-click context menu

On an object:
- **Clone** (Ctrl+K)
- **Copy** / **Paste**
- **Delete**
- **Merge**
- **Simplify Model**
- **Fix Model** (available on some platforms/builds)
- **Add Modifier** → Cube / Cylinder / Sphere / Load…
- **Height Range Modifier**
- **Change Type** → Part / Modifier / Negative Part / Support Enforcer / Support Blocker
- **Negative Part** — subtracts from the parent object at slice time
- **Set as Instance of…**

If **Merge** is unavailable, use **Object List → right-click object → Add part → Load…** to attach an STL as a part of the selected object.

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+I | **Add** |
| Ctrl+K | **Clone** |
| Ctrl+C / Ctrl+V | Copy / Paste |
| Delete / Backspace | Delete selected |
| Ctrl+A | Select All |
| Ctrl+Z / Ctrl+Y | Undo / Redo |
| Escape | Deselect All |
| A / Shift+A | Arrange all / arrange current plate |
| R / Shift+R | Auto Orient all / current plate |
| Ctrl+0 | Plate overview |
| Ctrl+1–7 | Top, Bottom, Front, Rear, Left, Right, Isometric |
| Ctrl+E | Toggle object labels |
| Ctrl+L | Toggle overhang display |
| 1–9 | Assign filament number to selected object |
| Arrow keys | Nudge 10 mm |
| Shift+Arrow keys | Nudge 1 mm |

Navigation: left-drag empty area rotates, right/middle-drag pans, scroll zooms, Alt+left-click selects a part/volume.

---

## Sidebar anatomy

### Left sidebar: Object List

Hierarchy: **Plates → Objects → Parts → Modifiers**.

Use **Global / Objects** mode to switch between whole-project settings and object-specific overrides. Parameter override order is **Global → Object → Part → Modifier**.

### Right sidebar: preset selectors

- **Printer** dropdown — printer model and nozzle.
- **Filament** dropdown — filament presets per AMS slot/material.
- **Process** dropdown — layer height and process quality preset.
- **Plate type** dropdown — e.g. Textured PEI Plate.

---

## Common setting locations

| Need | Exact path |
|---|---|
| Layer height | **Process Settings → Quality → Layer height** |
| First layer height | **Process Settings → Quality → First layer height** |
| Wall loops | **Process Settings → Strength → Wall loops** |
| Sparse infill density | **Process Settings → Strength → Sparse infill density** |
| Sparse infill pattern | **Process Settings → Strength → Sparse infill pattern** |
| Top surface pattern | **Process Settings → Strength → Top surface pattern** |
| Enable support | **Process Settings → Support → Enable support** |
| Support type | **Process Settings → Support → Type** |
| Brim | **Process Settings → Others → Bed adhesion / Brim** |
| Seam position | **Process Settings → Others → Seam position** |
| Ironing | **Process Settings → Others → Ironing** |
| Wall generator | **Process Settings → Quality → Wall generator** |
| Outer wall speed | **Process Settings → Speed → Outer wall** |
| Top surface speed | **Process Settings → Speed → Top surface** |
| Nozzle temperature | **Filament Settings → Filament → Nozzle temperature** |
| Bed temperature | **Filament Settings → Filament → Bed temperature** |
| Flow ratio | **Filament Settings → Filament → Flow ratio** |
| Max volumetric speed | **Filament Settings → Setting Overrides → Max volumetric speed** |
| Retraction length | **Filament Settings → Setting Overrides → Retraction length** |
| Fan speeds | **Filament Settings → Cooling** |
| Flow calibration | Top menu **Calibration → Flow Rate** |
| Flow dynamics / pressure advance | Top menu **Calibration → Flow Dynamics Calibration** |

Some settings require Advanced or Developer mode. Enable the more advanced UI mode before assuming a setting is unavailable.

---

## Cooling fan labels

In **Filament Settings → Cooling**, the min/max fan rows are tied to layer-time thresholds:

| Row | Meaning |
|---|---|
| **Min fan speed threshold → Fan speed** | Fan speed when layer time is long |
| **Max fan speed threshold → Fan speed** | Fan speed when layer time is short |

To set a constant fan speed, set both fan-speed cells to the same value. Do not reduce **Fan speed for overhangs** unless you have a specific reason; overhangs and bridges need cooling.

---

## Plates management

- Bambu Studio supports multiple plates in one project.
- Each plate is a separate print job.
- Add plates with **Add Plate**.
- Delete a plate with its X icon.
- Move objects between plates by dragging them.
- Lock a plate to keep arrangement from changing it.

---

## Preview checklist

After slicing, inspect:
1. First 5 layers: adhesion, brim, missing islands.
2. Support contact regions: scars and unsupported areas.
3. Bridges and overhangs.
4. Thin features and text.
5. Color/AMS transitions and prime tower behavior.
6. Top surfaces for gaps or infill telegraphing.

Treat unexpected warnings or toolpaths as blockers until understood.
