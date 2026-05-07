from bambu_easy.nozzle_picker import (
    NozzleDecision,
    pick_nozzle,
    read_nozzle_from_3mf,
    _normalize,
)


def test_normalize():
    assert _normalize("0.4") == "0.4"
    assert _normalize("0.4mm") == "0.4"
    assert _normalize("0.40") == "0.4"
    assert _normalize("0.40mm") == "0.4"


def test_read_nozzle_from_fixture(squish_3mf):
    assert read_nozzle_from_3mf(str(squish_3mf)) == "0.4"


def test_pick_nozzle_baked(squish_3mf):
    dec = pick_nozzle(str(squish_3mf), attached_diameter=None)
    assert dec.nozzle == "0.4mm"
    assert "baked" in dec.source
    assert dec.mismatch is False


def test_pick_nozzle_override(squish_3mf):
    dec = pick_nozzle(str(squish_3mf), attached_diameter="0.4", override="0.2")
    assert dec.nozzle == "0.2mm"
    assert dec.mismatch is True
    assert dec.attached == "0.4"


def test_pick_nozzle_match(squish_3mf):
    dec = pick_nozzle(str(squish_3mf), attached_diameter="0.4")
    assert dec.nozzle == "0.4mm"
    assert dec.mismatch is False


def test_pick_nozzle_default_when_missing(tmp_path):
    import zipfile, json
    p = tmp_path / "x.3mf"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({}))
    dec = pick_nozzle(str(p), attached_diameter=None)
    assert dec.nozzle == "0.4mm"
    assert "default" in dec.source.lower()
