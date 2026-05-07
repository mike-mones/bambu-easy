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
    # print_settings_id cleared so BS uses our process settings
    assert merged["print_settings_id"] == ""


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
