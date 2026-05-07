"""Source-3MF printer-identity detection."""
import json
import shutil
import zipfile

from bambu_easy.source_check import check_source_3mf


def _rewrite_psi(src_path, dst_path, new_psi, new_compatible):
    """Helper: clone a 3MF with a different printer_settings_id."""
    with zipfile.ZipFile(src_path, "r") as zf:
        settings = json.loads(zf.read("Metadata/project_settings.config").decode())
        others = {n: zf.read(n) for n in zf.namelist()
                  if n != "Metadata/project_settings.config"}
    settings["printer_settings_id"] = new_psi
    settings["print_compatible_printers"] = json.dumps(new_compatible)
    with zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Metadata/project_settings.config",
                    json.dumps(settings, indent=2))
        for n, data in others.items():
            zf.writestr(n, data)


def test_p2s_source_passes(squish_3mf):
    """The bundled fixture is already a P2S 3MF."""
    r = check_source_3mf(str(squish_3mf))
    assert r.is_p2s is True
    assert r.detected_printer is None  # only set on non-P2S


def test_a1_mini_source_detected(squish_3mf, tmp_path):
    """A1 mini upload (the LoZ_Layered_1AMS.3mf real-world case)."""
    raw = tmp_path / "raw_a1.3mf"
    shutil.copy(squish_3mf, raw)
    _rewrite_psi(
        raw, raw,
        "Bambu Lab A1 mini 0.4 nozzle",
        ["Bambu Lab A1 mini 0.4 nozzle"],
    )
    r = check_source_3mf(str(raw))
    assert r.is_p2s is False
    assert "A1 mini" in r.detected_printer


def test_x1c_source_detected(squish_3mf, tmp_path):
    raw = tmp_path / "raw_x1c.3mf"
    shutil.copy(squish_3mf, raw)
    _rewrite_psi(
        raw, raw,
        "Bambu Lab X1 Carbon 0.4 nozzle",
        ["Bambu Lab X1 Carbon 0.4 nozzle"],
    )
    r = check_source_3mf(str(raw))
    assert r.is_p2s is False
    assert "X1" in r.detected_printer


def test_p1s_source_detected(squish_3mf, tmp_path):
    raw = tmp_path / "raw_p1s.3mf"
    shutil.copy(squish_3mf, raw)
    _rewrite_psi(
        raw, raw,
        "Bambu Lab P1S 0.4 nozzle",
        ["Bambu Lab P1S 0.4 nozzle"],
    )
    r = check_source_3mf(str(raw))
    assert r.is_p2s is False
    assert "P1S" in r.detected_printer


def test_missing_metadata_is_permissive(tmp_path):
    """Junk file → should not crash; should defer to downstream pipeline."""
    junk = tmp_path / "junk.3mf"
    junk.write_bytes(b"not a zip")
    r = check_source_3mf(str(junk))
    assert r.is_p2s is True  # be permissive — let bake step surface the real error
