"""Smoke-test compose_profile for all 64 (nozzle × material × tier) combos."""
from bambu_easy._engine.print_profiles import (
    NOZZLE_BASES, MATERIALS, QUALITY_TIERS, compose_profile, list_profiles,
)
from bambu_easy._engine.bs_validation import validate_bs_settings


def test_all_combos_compose_and_validate():
    combos = list_profiles()
    assert len(combos) > 0
    seen = 0
    for nozzle, material, tier in combos:
        profile = compose_profile(nozzle=nozzle, material=material, tier=tier)
        assert "nozzle_diameter" in profile
        assert "filament_settings_id" in profile
        # All profiles must pass static BS validation
        errs = validate_bs_settings(profile)
        assert not errs, f"{nozzle}/{material}/{tier} static errors: {errs}"
        seen += 1
    # 4 nozzles × 4 materials × 4 tiers = 64
    assert seen == 64


def test_pla_matte_uses_user_preset_for_230c():
    """The whole point of the May-1 fix: PLA Matte must point at Mike's preset."""
    for nozzle in ("0.2mm", "0.4mm", "0.6mm", "0.8mm"):
        p = compose_profile(nozzle=nozzle, material="PLA Matte", tier="standard")
        fid = p["filament_settings_id"][0]
        assert fid.startswith("Mike PLA Matte 230C"), \
            f"{nozzle} PLA Matte filament_settings_id is {fid!r}"
        assert p["nozzle_temperature"] == ["230"]


def test_pla_silk_plus_user_preset():
    for nozzle in ("0.2mm", "0.4mm", "0.6mm", "0.8mm"):
        p = compose_profile(nozzle=nozzle, material="PLA Silk+", tier="standard")
        fid = p["filament_settings_id"][0]
        assert fid.startswith("Mike PLA Silk+ 230C"), fid
        assert p["nozzle_temperature"] == ["230"]


def test_petg_temps():
    p = compose_profile(nozzle="0.4mm", material="PETG-HF", tier="standard")
    assert p["nozzle_temperature"] == ["260"]


def test_pla_basic_220c():
    p = compose_profile(nozzle="0.4mm", material="PLA Basic", tier="standard")
    assert p["nozzle_temperature"] == ["220"]


def test_nozzle_volume_type_pinned_standard():
    """Mike's P2S runs Standard-flow nozzles only; compose must hard-pin
    nozzle_volume_type=Standard so a High Flow source 3MF can't leak through
    retarget and break the BS slice. Source of failure: 2026-06-08 baskets."""
    for nozzle in ("0.2mm", "0.4mm", "0.6mm", "0.8mm"):
        for material in MATERIALS:
            p = compose_profile(nozzle=nozzle, material=material, tier="standard")
            assert p["nozzle_volume_type"] == ["Standard"], \
                f"{nozzle}/{material} nozzle_volume_type is {p.get('nozzle_volume_type')!r}"
            assert p["default_nozzle_volume_type"] == ["Standard"]
