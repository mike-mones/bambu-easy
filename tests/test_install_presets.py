"""Test the install_presets module."""
import json

from bambu_easy.install_presets import (
    bs_user_data_root,
    find_active_user_dir,
    install_presets,
    list_vendored_presets,
    verify_preset_names_match_engine,
)


def test_vendored_presets_exist():
    """The 4 user presets must ship with the package."""
    presets = list_vendored_presets()
    names = {p.stem for p in presets}
    assert "Mike PLA Matte 230C @BBL P2S (0.4 nozzle)" in names
    assert "Mike PLA Matte 230C @BBL P2S 0.2 nozzle" in names
    assert "Mike PLA Silk+ 230C @BBL P2S (0.4 nozzle)" in names
    assert "Mike PLA Silk+ 230C @BBL P2S 0.2 nozzle" in names


def test_vendored_presets_are_valid_json():
    for p in list_vendored_presets():
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("type") == "filament"
        assert data.get("name") == p.stem
        # Must inherit a system preset so it's portable across users
        assert "inherits" in data and data["inherits"]


def test_engine_preset_names_match_vendored():
    """FILAMENT_PRESET_IDS for 0.2/0.4mm nozzles must reference shipped presets."""
    ok, missing = verify_preset_names_match_engine()
    assert ok, f"Missing vendored preset(s): {missing}"


def test_install_presets_into_temp_dir(tmp_path):
    """Mimic a clean BS install + signed-in user, then install."""
    user_id = "1234567890"
    user_dir = tmp_path / "user" / user_id / "filament"
    user_dir.mkdir(parents=True)
    # BambuStudio.conf hint
    (tmp_path / "BambuStudio.conf").write_text(f"preset_folder = {user_id}\n")

    result = install_presets(overwrite=False, bs_root=tmp_path)
    assert result.success
    assert len(result.installed) == 4
    assert len(result.skipped) == 0

    # Idempotent: re-run skips
    result2 = install_presets(overwrite=False, bs_root=tmp_path)
    assert result2.success
    assert len(result2.installed) == 0
    assert len(result2.skipped) == 4

    # Overwrite=True replaces
    result3 = install_presets(overwrite=True, bs_root=tmp_path)
    assert result3.success
    assert len(result3.installed) == 4


def test_install_presets_missing_bs(tmp_path):
    """BS user-data folder doesn't exist → friendly error."""
    fake_root = tmp_path / "nonexistent"
    result = install_presets(bs_root=fake_root)
    assert not result.success
    assert "not found" in result.message.lower()


def test_install_presets_no_user_account(tmp_path):
    """BS root exists but no user/<id>/ subfolders → friendly error."""
    (tmp_path / "user").mkdir()
    result = install_presets(bs_root=tmp_path)
    assert not result.success
    assert "user account" in result.message.lower() or "no bambu studio user" in result.message.lower()


def test_find_active_user_picks_conf_hint(tmp_path):
    """When BambuStudio.conf names a preset_folder, use that one even if
    other folders are newer."""
    (tmp_path / "user" / "111").mkdir(parents=True)
    (tmp_path / "user" / "222").mkdir(parents=True)
    (tmp_path / "BambuStudio.conf").write_text("preset_folder = 111\n")
    active = find_active_user_dir(tmp_path)
    assert active is not None
    assert active.name == "111"


def test_find_active_user_falls_back_to_mtime(tmp_path):
    """Without BambuStudio.conf, pick most-recently-modified subfolder."""
    import time
    a = tmp_path / "user" / "111"
    b = tmp_path / "user" / "222"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    # Make b newer
    time.sleep(0.01)
    (b / "marker").write_text("x")
    active = find_active_user_dir(tmp_path)
    assert active is not None
    assert active.name == "222"


def test_bs_user_data_root_returns_path():
    """Smoke check: should return a Path on Mac/Win/Linux."""
    root = bs_user_data_root()
    # On these 3 OSes it returns a Path; we can't assert it exists.
    assert root is not None
