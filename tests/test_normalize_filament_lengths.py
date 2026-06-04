"""Regression tests for per-filament array length re-alignment.

Guards the 2026-06-04 "Invalid configuration file" bug: the bake step shrank
some per-filament arrays to length 1 while leaving others at the source's
filament count, producing a project the BS GUI rejects (headless slicer
tolerated it). The fix re-aligns every per-filament array to the source's
filament count, broadcasting the baked value across all slots.
"""
import json
import zipfile

from bambu_easy.prepare import (
    _is_per_filament_key,
    _normalize_filament_array_lengths,
    _read_source_lengths,
)


def _write_3mf(path, settings: dict) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Metadata/project_settings.config",
                   json.dumps(settings, indent=4))
        z.writestr("[Content_Types].xml", "<Types/>")


def _read(path) -> dict:
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("Metadata/project_settings.config"))


def test_is_per_filament_key_classification():
    assert _is_per_filament_key("filament_settings_id")
    assert _is_per_filament_key("filament_retraction_length")
    assert _is_per_filament_key("nozzle_temperature")
    assert _is_per_filament_key("nozzle_temperature_initial_layer")
    assert _is_per_filament_key("textured_plate_temp")
    assert _is_per_filament_key("cool_plate_temp_initial_layer")
    assert _is_per_filament_key("fan_max_speed")
    assert _is_per_filament_key("slow_down_for_layer_cooling")
    # Process / geometry scalars are NOT per-filament
    assert not _is_per_filament_key("layer_height")
    assert not _is_per_filament_key("inner_wall_speed")
    assert not _is_per_filament_key("sparse_infill_density")
    assert not _is_per_filament_key("wall_loops")


def test_realign_restores_source_lengths(tmp_path):
    # A self-consistent 2-filament source (what BS GUI accepts).
    source = tmp_path / "source.3mf"
    _write_3mf(source, {
        "filament_settings_id": ["Generic PLA", "Bambu PLA Basic"],
        "nozzle_temperature": ["220", "220", "220", "220"],     # len 4
        "textured_plate_temp": ["55", "55"],                    # len 2
        "filament_retraction_length": ["0.8", "0.8", "0.8", "0.8"],
        "fan_max_speed": ["100", "100"],
        "inner_wall_speed": ["300", "600"],                     # process
    })
    src_lengths = _read_source_lengths(str(source))
    assert src_lengths["nozzle_temperature"] == 4
    assert src_lengths["textured_plate_temp"] == 2
    # process key is not collected
    assert "inner_wall_speed" not in src_lengths

    # The bake output: per-filament arrays shrunk to length 1 (the bug).
    out = tmp_path / "out.3mf"
    _write_3mf(out, {
        "filament_settings_id": ["Mike PLA Matte 230C @BBL P2S (0.4 nozzle)"],
        "nozzle_temperature": ["230"],
        "textured_plate_temp": ["65"],
        "filament_retraction_length": ["0.8", "0.8", "0.8", "0.8"],
        "fan_max_speed": ["80"],
        "inner_wall_speed": 200,  # process scalar, must stay untouched
    })

    fixed = _normalize_filament_array_lengths(str(out), src_lengths)
    assert fixed >= 4

    merged = _read(out)
    # Every per-filament array is back to the source length...
    assert len(merged["filament_settings_id"]) == 2
    assert merged["filament_settings_id"] == [
        "Mike PLA Matte 230C @BBL P2S (0.4 nozzle)"] * 2
    assert merged["nozzle_temperature"] == ["230"] * 4   # baked value broadcast
    assert merged["textured_plate_temp"] == ["65", "65"]
    assert merged["fan_max_speed"] == ["80", "80"]
    # ...the already-correct array is left alone...
    assert merged["filament_retraction_length"] == ["0.8"] * 4
    # ...and the process scalar is never touched.
    assert merged["inner_wall_speed"] == 200


def test_realign_is_idempotent(tmp_path):
    source = tmp_path / "source.3mf"
    _write_3mf(source, {
        "filament_settings_id": ["A", "B"],
        "nozzle_temperature": ["230", "230"],
    })
    src_lengths = _read_source_lengths(str(source))
    out = tmp_path / "out.3mf"
    _write_3mf(out, {
        "filament_settings_id": ["X", "X"],
        "nozzle_temperature": ["230", "230"],
    })
    first = _normalize_filament_array_lengths(str(out), src_lengths)
    assert first == 0  # already source length -> nothing changed
    second = _normalize_filament_array_lengths(str(out), src_lengths)
    assert second == 0


def test_color_broadcast_across_slots(tmp_path):
    source = tmp_path / "source.3mf"
    _write_3mf(source, {
        "filament_settings_id": ["A", "B"],
        "filament_colour": ["#FFFFFF", "#000000"],
    })
    src_lengths = _read_source_lengths(str(source))
    out = tmp_path / "out.3mf"
    _write_3mf(out, {
        "filament_settings_id": ["X"],
        "filament_colour": ["#A7A6A8"],
    })
    _normalize_filament_array_lengths(str(out), src_lengths, color="#28282B")
    merged = _read(out)
    assert merged["filament_colour"] == ["#28282B", "#28282B"]
