"""End-to-end: bake the bundled fixture, verify settings + static validation."""
import json
import zipfile

from bambu_easy.prepare import prepare_3mf


def test_e2e_bake_pla_matte_standard(squish_3mf, tmp_path):
    out = tmp_path / "out_ready.3mf"
    result = prepare_3mf(
        input_path=str(squish_3mf),
        output_path=str(out),
        nozzle="0.4mm",
        material="PLA Matte",
        tier="standard",
        do_bs_validate=False,  # CI: BS may not be installed
    )
    assert out.exists()
    assert result.static_ok
    assert result.bs_ok is None  # skipped

    # Verify the merged 3MF settings
    with zipfile.ZipFile(out) as zf:
        merged = json.loads(zf.read("Metadata/project_settings.config"))

    # Critical: PLA Matte at 230 backed by Mike's user preset
    assert merged["nozzle_temperature"] == ["230"]
    assert merged["filament_settings_id"][0].startswith("Mike PLA Matte 230C")
    # Nozzle base wired through
    assert merged["nozzle_diameter"] == ["0.4"]
    # Standard tier
    assert merged["layer_height"] == "0.20"
    # print_settings_id now points at the matching P2S process preset
    # (was '' pre-2026-05-08; see PROCESS_PRESET_IDS in print_profiles.py)
    assert merged["print_settings_id"] == "0.20mm Standard @BBL P2S"
    # print_compatible_printers must reflect the chosen nozzle, not the source
    assert merged["print_compatible_printers"] == ["Bambu Lab P2S 0.4 nozzle"]


def test_e2e_petg_hf(squish_3mf, tmp_path):
    out = tmp_path / "petg.3mf"
    prepare_3mf(
        input_path=str(squish_3mf),
        output_path=str(out),
        nozzle="0.4mm",
        material="PETG-HF",
        tier="quality",
        do_bs_validate=False,
    )
    with zipfile.ZipFile(out) as zf:
        merged = json.loads(zf.read("Metadata/project_settings.config"))
    assert merged["nozzle_temperature"] == ["260"]
    assert merged["curr_bed_type"] == "Textured PEI Plate"


def test_e2e_all_nozzles(squish_3mf, tmp_path):
    for nozzle in ("0.2mm", "0.4mm", "0.6mm", "0.8mm"):
        out = tmp_path / f"out_{nozzle}.3mf"
        prepare_3mf(
            input_path=str(squish_3mf),
            output_path=str(out),
            nozzle=nozzle,
            material="PLA Basic",
            tier="standard",
            do_bs_validate=False,
        )
        with zipfile.ZipFile(out) as zf:
            merged = json.loads(zf.read("Metadata/project_settings.config"))
        assert merged["nozzle_diameter"] == [nozzle.replace("mm", "")]


def test_e2e_converts_x1c_makerworld_to_p2s(squish_3mf, tmp_path):
    """Simulates a raw MakerWorld download targeted at an X1C — the user has
    NOT pre-opened it in BS to swap to the P2S preset. bambu-easy must
    overwrite the printer / preset / bed-type / temp fields completely so
    the output is a proper P2S 3MF.

    Verified end-to-end against the live BS CLI on 2026-05-07: BS sliced
    the converted file with rc=0. This test enforces the field-level
    contract; the BS-CLI confirmation is what validates that contract is
    actually sufficient for BS to accept the file.
    """
    import shutil
    raw = tmp_path / "raw_x1c.3mf"
    shutil.copy(squish_3mf, raw)

    # Rewrite source to look like an X1C upload from MakerWorld
    other_files = {}
    with zipfile.ZipFile(raw, "r") as zf:
        src = json.loads(zf.read("Metadata/project_settings.config").decode())
        for n in zf.namelist():
            if n != "Metadata/project_settings.config":
                other_files[n] = zf.read(n)
    src["printer_settings_id"] = "Bambu Lab X1 Carbon 0.4 nozzle"
    src["print_settings_id"] = "0.20mm Standard @BBL X1C"
    src["filament_settings_id"] = ["Bambu PLA Basic @BBL X1C"]
    src["nozzle_temperature"] = ["220"]
    src["curr_bed_type"] = "Cool Plate"  # X1C default — wrong for our PLA Matte
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Metadata/project_settings.config", json.dumps(src, indent=2))
        for n, data in other_files.items():
            zf.writestr(n, data)

    out = tmp_path / "x1c_to_p2s_ready.3mf"
    prepare_3mf(
        input_path=str(raw),
        output_path=str(out),
        nozzle="0.4mm",
        material="PLA Matte",
        tier="standard",
        do_bs_validate=False,
    )

    with zipfile.ZipFile(out) as zf:
        merged = json.loads(zf.read("Metadata/project_settings.config"))

    # Every X1C-specific field must be replaced with the P2S equivalent
    assert merged["printer_settings_id"] == "Bambu Lab P2S 0.4 nozzle"
    assert merged["print_settings_id"] == "0.20mm Standard @BBL P2S"
    assert merged["print_compatible_printers"] == ["Bambu Lab P2S 0.4 nozzle"]
    assert merged["filament_settings_id"][0].startswith("Mike PLA Matte 230C")
    assert merged["nozzle_temperature"] == ["230"]
    assert merged["curr_bed_type"] == "Textured PEI Plate"
    assert merged["nozzle_diameter"] == ["0.4"]
