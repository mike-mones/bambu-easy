import pytest
from bambu_easy.filament_picker import (
    FilamentResolutionError,
    pick_filament,
    _map_name_to_material,
    read_filament_from_3mf,
)


def test_map_name():
    assert _map_name_to_material("Bambu PLA Matte @BBL P2S") == "PLA Matte"
    assert _map_name_to_material("Mike PLA Matte 230C @BBL P2S (0.4 nozzle)") == "PLA Matte"
    assert _map_name_to_material("Bambu PLA Silk+ ...") == "PLA Silk+"
    assert _map_name_to_material("Bambu PLA Basic @BBL P2S") == "PLA Basic"
    assert _map_name_to_material("Bambu PETG HF @BBL P2S 0.4 nozzle") == "PETG-HF"
    assert _map_name_to_material("Generic ABS") is None


def test_override(squish_3mf):
    dec = pick_filament(str(squish_3mf), spools=None, override="PLA Basic")
    assert dec.material == "PLA Basic"
    assert "override" in dec.source


def test_override_unsupported(squish_3mf):
    with pytest.raises(FilamentResolutionError):
        pick_filament(str(squish_3mf), spools=None, override="ABS")


def test_baked_fallback(squish_3mf):
    fid = read_filament_from_3mf(str(squish_3mf))
    assert "PLA Matte" in fid
    dec = pick_filament(str(squish_3mf), spools=None, override=None)
    assert dec.material == "PLA Matte"
    assert "baked" in dec.source


def test_ams_most_filled(squish_3mf):
    spools = [
        {"slot": "A1", "type": "PLA", "sub_brand": "PLA Basic", "remain": 30},
        {"slot": "A2", "type": "PLA", "sub_brand": "PLA Matte", "remain": 90},
        {"slot": "A3", "type": "PLA", "sub_brand": "PLA Silk", "remain": 50},
    ]
    dec = pick_filament(str(squish_3mf), spools=spools)
    assert dec.material == "PLA Matte"
    assert dec.slot == "A2"


def test_ams_slot_hint(squish_3mf):
    spools = [
        {"slot": "A1", "type": "PLA", "sub_brand": "PLA Basic", "remain": 30},
        {"slot": "A2", "type": "PLA", "sub_brand": "PLA Matte", "remain": 90},
    ]
    dec = pick_filament(str(squish_3mf), spools=spools, slot_hint="A1")
    assert dec.material == "PLA Basic"
    assert dec.slot == "A1"


def test_no_resolution(tmp_path):
    import zipfile, json
    p = tmp_path / "empty.3mf"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({}))
    with pytest.raises(FilamentResolutionError):
        pick_filament(str(p), spools=[])
