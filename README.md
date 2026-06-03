# bambu-easy

Take a 3MF file. Get back a 3MF that's ready to print on a Bambu Lab P2S — with the right
nozzle, the right temperatures, and zero settings warnings in Bambu Studio.

This is a wife-friendly wrapper around proven P2S preparation logic, packaged for
non-technical users. It does **not** start prints — you still hit Print in Bambu Studio. It just
makes sure the file is correct before you do.

## Install in 5 minutes

```bash
git clone <repo-url> bambu-easy
cd bambu-easy
./setup.sh
```

The script will:
1. Create a Python virtual environment (`.venv/`)
2. Install `bambu-easy`
3. Launch an interactive wizard that:
   - Asks for your printer's IP, serial number, and 8-character access code (find these on the printer's touchscreen or in Bambu Studio — the wizard tells you exactly where)
   - Installs the bundled filament presets into your Bambu Studio install
   - Runs a doctor check to confirm everything works

Already have it installed and just need to redo something?

```bash
source .venv/bin/activate
bambu-easy --setup            # re-run the full wizard
bambu-easy --install-presets  # just refresh the BS presets
bambu-easy --doctor           # health check
```

> **Got Copilot?** Just open this folder and ask it: "set this up for me."
> The included `.github/copilot-instructions.md` tells Copilot exactly what to do.

## Your first print

1. Download a `.3mf` file from MakerWorld.
2. Run:

   ```bash
   bambu-easy ~/Downloads/cool_thing.3mf
   ```

3. Open the new `cool_thing_ready.3mf` in Bambu Studio and press **Print**.

That's it. No tweaking sliders. No filament profile dropdowns.

> **You do NOT need to pre-open the MakerWorld file in Bambu Studio first.** Even if the file was uploaded for a different printer (X1C, A1 mini, P1S, etc.), `bambu-easy` automatically calls Bambu Studio's CLI to retarget the file to your P2S, then bakes the right filament/temperature/process settings on top. The headless BS validator confirms the result before the file is handed back to you.

## Quality tiers

Pass `-q <tier>`:

| Tier | What it means |
|---|---|
| `fast` | Coarsest layers (0.28mm on 0.4 nozzle), lower walls, max speed. Good for prototypes and brackets. |
| `standard` | Default. Balanced quality and speed (0.20mm). Right for most prints. |
| `quality` | Finer layers (0.16mm), more walls. Use for visible parts. |
| `premium` | Slowest, highest detail (0.12mm). Use for figurines and miniatures. |

## Filament

By default `bambu-easy` picks the most-filled spool currently loaded in your AMS that maps to a
supported material. Override with `-f`:

```bash
bambu-easy myfile.3mf -f "PLA Matte"
```

Supported: `PLA Matte`, `PLA Basic`, `PLA Silk+`, `PETG-HF`.

## Nozzle

By default `bambu-easy` reads the nozzle the source 3MF was prepared for, then checks that the
printer currently has that nozzle attached. **If they differ, the tool stops with an error** —
this prevents silently slicing for the wrong tool head.

Override with `-n`:

```bash
bambu-easy myfile.3mf -n 0.2
```

Supported: `0.2`, `0.4`, `0.6`, `0.8` mm.

## Troubleshooting

| Message | What to do |
|---|---|
| `Bambu Studio CLI NOT found` | Install Bambu Studio from <https://bambulab.com/en/download/studio>. The CLI is bundled with the GUI. |
| `Printer offline` / `did not respond` | Check the printer is on and on the same Wi-Fi network. Re-verify the IP and access code (the IP can change after router reboots). LAN Only Mode does NOT need to be enabled — only enable it as a last resort if MQTT polling keeps failing on older firmware. |
| `Nozzle mismatch` | Either swap the physical nozzle on the printer to match, or re-run without `-n`. Use `--force` only if you know what you're doing. |
| `Could not determine filament` | Either load a recognized spool in the AMS, or pass `-f "PLA Matte"` (etc.) explicitly. |
| `Source 3MF was built for <printer>. Retargeting...` | Just informational — the file was uploaded for a non-P2S printer; bambu-easy is calling Bambu Studio CLI to convert it. Takes ~10s. |
| `Re-arranged object onto plate: centred...` | Just informational — the source was a bare-geometry / web-tool export (no printer arrangement) that landed off the plate, so bambu-easy recentred it on the P2S bed. MakerWorld files already arranged on a plate are left untouched. |
| `Auto-conversion failed` | Open Bambu Studio at least once so it has its system presets installed. If it still fails, follow the manual fallback printed beneath the error. |
| `BS slice validation FAILED` | Open the output `_ready.3mf` in Bambu Studio to see the toast error. The validator caught a setting BS won't accept; try a different quality tier or report the file. |

| `--skip-bs-validate` | Skip the headless BS slice (saves 10–30s, less safe) |
| `--no-open` | Don't auto-open the result in Bambu Studio (default opens automatically) |
| `--force` | Bypass nozzle-mismatch hard-stop (NOT recommended) |
| `--slot <SLOT>` | Pin filament to a specific AMS slot (e.g. `A2`). Defaults to "most filled". |
| `--color <#RRGGBB>` | Set the filament color hex explicitly. Defaults to the AMS slot color. |
| `--debug` | Show full Python traceback on unexpected errors |

## For power users: optional Copilot agent

`bambu-easy` also ships with Copilot agent instructions and a small `Reference/` knowledge base. If you have GitHub Copilot CLI or VS Code Copilot, open this folder and ask for advanced P2S help: model design, failed-print diagnosis, calibration plans, multicolor risk checks, or custom 3D-model scripts.

The regular CLI remains the right tool for ordinary MakerWorld files. The agent is for the 5% of jobs where you want an engineer, not just a one-command bake.

Reference docs are browsable without an agent:

- [`Reference/fdm-design-rules.md`](Reference/fdm-design-rules.md) — FDM geometry, tolerances, orientation, supports, material limits.
- [`Reference/bambu-studio-ui.md`](Reference/bambu-studio-ui.md) — exact Bambu Studio labels, shortcuts, and setting paths.
- [`Reference/print-settings.md`](Reference/print-settings.md) — P2S filament/nozzle/profile settings and 3MF baking notes.
- [`Reference/hole-filling.md`](Reference/hole-filling.md) — imported mesh hole repair and trimesh mesh-surgery workflow.
- [`Reference/model-design-from-scratch.md`](Reference/model-design-from-scratch.md) — math-first build123d/trimesh model design workflow.
- [`Reference/calibration.md`](Reference/calibration.md) — first layer, flow, pressure advance, temperature, retraction, and max-flow procedures.
- [`Reference/troubleshooting.md`](Reference/troubleshooting.md) — symptom-to-cause-to-fix tables for common P2S print failures.

## What lives where

```
bambu_easy/
  cli.py              # argparse, friendly errors
  prepare.py          # bake + validate orchestrator
  nozzle_picker.py    # nozzle resolution + mismatch check
  filament_picker.py  # filament resolution from AMS / source 3MF
  printer.py          # config + read-only MQTT poll
  _engine/            # FROZEN VENDORED COPIES from the source repo
    print_profiles.py    # all settings (nozzle × material × tier)
    bs_validation.py     # static + headless-BS validation
    bake_3mf_settings.py # 3MF rewrite logic
    mqtt_poll.py         # connect-and-listen extraction
```

Run `tools/sync_engine.sh` to refresh the `_engine/` files from the source repo.
