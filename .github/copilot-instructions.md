# Copilot Instructions for `bambu-easy`

This is a small, opinionated CLI for the Bambu Lab P2S 3D printer. It takes a
3MF file (typically downloaded from MakerWorld) and prepares it for printing
by baking in correct nozzle/filament/temperature settings.

## Your job when helping a user

Most users came here to **print a model their friend or spouse already
configured for them**. They are NOT here to learn 3D printing internals. The
tool itself is designed to do everything automatically — your job is to help
them install it and then get out of the way.

### If a user asks "set this up" / "install this" / "get me started":

Run these in order. Don't skip steps. Don't suggest "advanced" alternatives.

1. **Verify Python 3.10+** is installed: `python3 --version`. If it's missing,
   point them at <https://www.python.org/downloads/> and stop.
2. **Verify Bambu Studio** is installed at the standard location for their OS.
   - macOS: `/Applications/BambuStudio.app`
   - Windows: usually `C:\Program Files\Bambu Studio\`
   - If it's missing, point them at <https://bambulab.com/en/download/studio>
     and tell them to open it once before continuing (BS creates user-data
     folders on first launch — `bambu-easy --install-presets` needs them).
3. **Create a venv and install bambu-easy** from the repo root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate
   pip install -e .
   ```
4. **Run the setup wizard:**
   ```bash
   bambu-easy --setup
   ```
   It walks them through printer config, preset install, and a doctor check.
   Trust it — don't try to do those steps manually.
5. If `--setup` reported any failures, run `bambu-easy --doctor` to see the
   current state and address what it flags.

### If a user asks "how do I print this file":

```bash
bambu-easy /path/to/the/file.3mf
```

That's it. The tool will:
- Auto-retarget the file to the P2S if it was uploaded for another printer.
- Pick the right nozzle and filament based on what's in the AMS.
- Bake in correct settings (this is the whole point of the tool).
- Validate by running a headless Bambu Studio slice.
- Open the result in Bambu Studio so they can press Print.

If the user has a preference, surface the flags:
- `-q quality` for visible parts (slower, finer layers).
- `-q fast` for prototypes / brackets.
- `-f "PLA Basic"` to override the auto-picked filament.

### What NOT to do

- **Don't edit `bambu_easy/_engine/*` files.** They are vendored copies of
  validated logic from another repo. Bambu-easy-specific changes go in the
  `bambu_easy/` top level.
- **Don't suggest the user manually edit `printer_config.json`** — `--setup`
  handles it. Sending them to a JSON editor is a regression of UX.
- **Don't offer to "tune" the slicer settings** the tool bakes in. Those
  values are pinned for a reason (e.g., the May 2026 230°C bug — wrong
  filament_settings_id silently regresses PLA Matte to 220°C).
- **Don't speculate about the printer being broken** if a print fails. The
  most common cause of "BS rejected the file" is the user has not installed
  the user presets — confirm with `bambu-easy --doctor` first.
- **Don't write new scripts** for problems the existing CLI flags already
  solve. Read `bambu-easy --help` first.

### Useful commands

| Command | What it does |
|---|---|
| `bambu-easy --setup` | Interactive first-time wizard. |
| `bambu-easy --doctor` | Health check (BS install, presets, printer reachable). |
| `bambu-easy --install-presets` | Re-install the bundled filament presets. |
| `bambu-easy --self-test` | Bake the bundled fixture file end-to-end. |
| `bambu-easy <file.3mf>` | Prepare a 3MF for printing. |
| `bambu-easy --help` | Show all flags. |

### Tone

Be concise. Most users came here from "my friend told me to use this" —
they want it to work, not a lecture.
