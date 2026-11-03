import json
from pathlib import Path

import numpy as np
import trimesh

from atlas_pipeline.package_body import build_male

FIX = Path(__file__).parent / "fixtures" / "bp3d"
LABELS = {"FMA5018": {"id": "tulang paha", "la": "femur"}}


def build(tmp_path):
    return build_male(FIX, tmp_path, LABELS)


def test_writes_one_glb_per_system_and_manifest(tmp_path):
    manifest = build(tmp_path)
    files = sorted(p.name for p in (tmp_path / "male").glob("*.glb"))
    assert files == ["arterial.glb", "connective.glb", "skeletal.glb", "urinary.glb"]
    assert len(manifest["parts"]) == 4
    assert json.loads((tmp_path / "male" / "manifest.draft.json").read_text("utf-8")) == manifest


def test_floor_is_zero_and_body_centered(tmp_path):
    parts = build(tmp_path)["parts"]
    lo = np.min([p["bounds"][0] for p in parts], axis=0)
    hi = np.max([p["bounds"][1] for p in parts], axis=0)
    assert abs(lo[1]) < 1e-9
    assert abs((lo[0] + hi[0]) / 2) < 1e-9 and abs((lo[2] + hi[2]) / 2) < 1e-9


def test_left_parts_are_positive_x_and_face_is_front(tmp_path):
    parts = {p["names"]["en"]: p for p in build(tmp_path)["parts"]}
    center_x = lambda p: (p["bounds"][0][0] + p["bounds"][1][0]) / 2
    assert center_x(parts["Left test femur"]) > 0 > center_x(parts["Right test artery"])
    nose_z = parts["Test nose"]["bounds"][1][2]
    assert nose_z == max(p["bounds"][1][2] for p in parts.values())


def test_glb_nodes_are_part_ids(tmp_path):
    build(tmp_path)
    scene = trimesh.load(tmp_path / "male" / "skeletal.glb", force="scene")
    assert set(scene.graph.nodes_geometry) == {"BP3D:FJ1"}


def test_names_side_origin_and_report(tmp_path):
    manifest = build(tmp_path)
    femur = next(p for p in manifest["parts"] if p["id"] == "BP3D:FJ1")
    assert femur["names"] == {"en": "Left test femur", "id": "tulang paha", "la": "femur"}
    assert (femur["side"], femur["origin"], femur["source"]) == ("left", "laki-laki-asli", "bodyparts3d")
    report = json.loads((tmp_path / "male" / "classification-report.json").read_text("utf-8"))
    assert report["default"] == ["Test nose"]


def test_side_corrections_flip_side_and_drop_labels(tmp_path, monkeypatch):
    from atlas_pipeline import package_body
    monkeypatch.setattr(package_body, "SIDE_CORRECTIONS", {"FJ1": "right"})
    femur = next(p for p in build(tmp_path)["parts"] if p["id"] == "BP3D:FJ1")
    assert femur["side"] == "right" and femur["names"] == {"en": "Right test femur"}
