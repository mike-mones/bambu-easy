"""Unit tests for the on-plate centering step (Bug 4, failure-log Jun 3, 2026).

bambu-easy historically had no arrange step, so bare-geometry / web-tool 3MFs
(and BS-CLI retargets of them) could land off the plate and BS would refuse to
slice with rc=-50. `_ensure_on_plate` recentres off-plate objects and is a
no-op for files already on the plate.
"""
import re
import shutil
import zipfile

from bambu_easy.prepare import _ensure_on_plate, _P2S_BED_MM


def _build_transform(path: str) -> list[float]:
    with zipfile.ZipFile(path) as zf:
        model = zf.read("3D/3dmodel.model").decode("utf-8", "ignore")
    build = re.search(r"<build.*?</build>", model, re.S).group(0)
    nums = re.search(r'transform="([^"]+)"', build).group(1)
    return [float(x) for x in nums.split()]


def _set_build_translation(path: str, tx: float, ty: float) -> None:
    """Rewrite the build item's translation in-place (test helper)."""
    with zipfile.ZipFile(path) as zf:
        names = zf.infolist()
        blobs = {i.filename: zf.read(i.filename) for i in names}

    model = blobs["3D/3dmodel.model"].decode("utf-8", "ignore")

    def _repl(m):
        nums = m.group(2).split()
        nums[9], nums[10] = f"{tx:g}", f"{ty:g}"
        return m.group(1) + " ".join(nums) + m.group(3)

    new_model = re.sub(
        r'(<item\b[^>]*\btransform=")([^"]+)("[^>]*/>)', _repl, model, count=1
    )
    blobs["3D/3dmodel.model"] = new_model.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for i in names:
            zout.writestr(i.filename, blobs[i.filename])


def test_already_on_plate_is_noop(squish_3mf, tmp_path):
    work = tmp_path / "on_plate.3mf"
    shutil.copy(squish_3mf, work)
    before = _build_transform(str(work))

    moved, msg = _ensure_on_plate(str(work))

    assert moved == 0, f"should not move an on-plate file (msg={msg})"
    assert _build_transform(str(work)) == before


def test_off_plate_gets_recentred(squish_3mf, tmp_path):
    work = tmp_path / "off_plate.3mf"
    shutil.copy(squish_3mf, work)
    # Shove the object far off the front of the plate (negative Y), mirroring
    # the retarget bug that put gridfinity pieces at Y -294..-40.
    _set_build_translation(str(work), tx=128.0, ty=-180.0)

    moved, msg = _ensure_on_plate(str(work))

    assert moved == 1, f"should recentre an off-plate file (msg={msg})"
    tnums = _build_transform(str(work))
    # After centering, the object's world XY centre should land on the plate
    # centre. The squish pad is symmetric about its local origin, so the
    # translation itself should be ~(128, 128).
    assert abs(tnums[9] - _P2S_BED_MM / 2) < 1.0
    assert abs(tnums[10] - _P2S_BED_MM / 2) < 1.0


def test_recentre_is_idempotent(squish_3mf, tmp_path):
    work = tmp_path / "twice.3mf"
    shutil.copy(squish_3mf, work)
    _set_build_translation(str(work), tx=10.0, ty=-200.0)

    moved_first, _ = _ensure_on_plate(str(work))
    assert moved_first == 1
    after_first = _build_transform(str(work))

    moved_second, _ = _ensure_on_plate(str(work))
    assert moved_second == 0, "second pass should be a no-op"
    assert _build_transform(str(work)) == after_first
