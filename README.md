# bambu-easy

Take a 3MF file. Get back a 3MF that's ready to print on Mike's Bambu Lab P2S — with the right
nozzle, the right temperatures, and zero settings warnings in Bambu Studio.

This is a wrapper around proven logic from Mike's full 3D-printing workspace, packaged for
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
3. Ask for your printer's IP, access code, and serial number

Find those values in Bambu Studio: **Device → Settings → LAN Only Mode**.

After setup:

```bash
source .venv/bin/activate
bambu-easy --doctor   # confirms everything is wired up
```

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
| `Printer offline` / `did not respond` | Check the printer is on, on Wi-Fi, and that LAN Only Mode is enabled with the access code in `printer_config.json`. |
| `Nozzle mismatch` | Either swap the physical nozzle on the printer to match, or re-run without `-n`. Use `--force` only if you know what you're doing. |
| `Could not determine filament` | Either load a recognized spool in the AMS, or pass `-f "PLA Matte"` (etc.) explicitly. |
| `Source 3MF was built for <printer>. Retargeting...` | Just informational — the file was uploaded for a non-P2S printer; bambu-easy is calling Bambu Studio CLI to convert it. Takes ~10s. |
| `Auto-conversion failed` | Open Bambu Studio at least once so it has its system presets installed. If it still fails, follow the manual fallback printed beneath the error. |
| `BS slice validation FAILED` | Open the output `_ready.3mf` in Bambu Studio to see the toast error. The validator caught a setting BS won't accept; try a different quality tier or report the file. |

| `--skip-bs-validate` | Skip the headless BS slice (saves 10–30s, less safe) |
| `--no-open` | Don't auto-open the result in Bambu Studio (default opens automatically) |
| `--force` | Bypass nozzle-mismatch hard-stop (NOT recommended) |
| `--debug` | Show full Python traceback on unexpected errors |

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

---

For advanced model editing or designing from scratch, see Mike's full workspace at
**<TODO: link to Mike's 3D Printing repo>**.
