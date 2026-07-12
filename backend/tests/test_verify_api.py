import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app.api import verify as verify_module
from app.main import app

client = TestClient(app)


@pytest.fixture
def extracted_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(verify_module, "EXTRACTED_DIR", tmp_path)
    return tmp_path


def _write_spec_requirements(extracted_dir: Path) -> None:
    requirements = [
        {
            "req_id": "MECH-3.4.2",
            "equipment_class": "chiller",
            "parameter": "cooling_capacity",
            "operator": ">=",
            "value": 500.0,
            "unit": "TR",
            "condition": "@35C ambient",
            "source_doc": "spec.pdf",
            "source_page": 1,
            "source_bbox": [72.0, 690.0, 540.0, 730.0],
        }
    ]
    (extracted_dir / "spec.requirements.json").write_text(json.dumps(requirements))


def test_verify_404_when_submittal_not_found(extracted_dir: Path) -> None:
    _write_spec_requirements(extracted_dir)

    response = client.post("/api/verify/nonexistent")

    assert response.status_code == 404


def test_verify_404_when_spec_requirements_missing(extracted_dir: Path) -> None:
    (extracted_dir / "submittal.values.json").write_text("[]")

    response = client.post("/api/verify/submittal")

    assert response.status_code == 404


def test_verify_catches_planted_deviation(extracted_dir: Path) -> None:
    _write_spec_requirements(extracted_dir)
    values = [
        {
            "equipment_class": "chiller",
            "parameter": "cooling_capacity",
            "value": 480.0,
            "unit": "TR",
            "condition": "@35C ambient",
            "source_doc": "submittal.pdf",
            "source_page": 1,
            "source_bbox": [72.0, 600.0, 400.0, 630.0],
            "extraction_confidence": 0.95,
        }
    ]
    (extracted_dir / "submittal.values.json").write_text(json.dumps(values))

    response = client.post("/api/verify/submittal")

    assert response.status_code == 200
    verdicts = response.json()
    assert len(verdicts) == 1
    assert verdicts[0]["status"] == "NON_CONFORMANCE"
    assert verdicts[0]["delta_pct"] == pytest.approx(-4.0)
