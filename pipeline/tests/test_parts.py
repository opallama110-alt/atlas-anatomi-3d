import json

import numpy as np
import pytest

from atlas_pipeline.parts import Part, write_body


def tri(x0):
    return np.array([[x0, 1.0, 0.0], [x0 + 0.1, 1.0, 0.0], [x0, 2.0, 0.1]]), np.array([[0, 1, 2]])


def test_write_body_translates_and_writes_optional_fields(tmp_path):
    v1, f = tri(0.2)
    v2, _ = tri(-0.4)
    parts = [Part("BH:FEMUR_LEFT", "skeletal", "left", "perempuan-asli", "bonehub", "FEMUR_LEFT",
                  {"en": "Left femur"}, v1, f, fma="FMA24474", notes=("pose-disesuaikan",)),
             Part("HRA:x", "digestive", "none", "perempuan-asli", "hra", "x", {"en": "X"}, v2, f, uberon="UBERON:1")]
    manifest = write_body(parts, tmp_path, "female")
    femur, other = manifest["parts"]
    assert femur["bounds"][0][1] == 0.0 and femur["notes"] == ["pose-disesuaikan"] and "uberon" not in femur
    assert other["uberon"] == "UBERON:1" and "notes" not in other and "fma" not in other
    assert femur["sourceRef"] == "FEMUR_LEFT" and femur["file"] == "skeletal.glb" and femur["triangles"] == 1
    assert sorted(p.name for p in (tmp_path / "female").glob("*.glb")) == ["digestive.glb", "skeletal.glb"]
    assert json.loads((tmp_path / "female" / "manifest.draft.json").read_text("utf-8")) == manifest


def test_write_body_rejects_parts_without_triangles(tmp_path):
    v, _ = tri(0.0)
    with pytest.raises(ValueError, match="HRA:empty"):
        write_body([Part("HRA:empty", "digestive", "none", "perempuan-asli", "hra", "e", {"en": "E"},
                         v, np.zeros((0, 3), dtype=np.int64))], tmp_path, "female")
