"""FastAPI server tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from forgefix.server import app

FIXTURES = Path(__file__).parent / "fixtures"
BROKEN = FIXTURES / "broken_repo"
MINIMAL = FIXTURES / "minimal_repo"

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_doctor_endpoint_scans_path() -> None:
    response = client.get("/doctor", params={"path": str(BROKEN)})
    assert response.status_code == 200
    body = response.json()
    assert body["score"]["total"] == 40
    assert len(body["findings"]) == 12
    assert body["plugins"] == ["example"]


def test_doctor_endpoint_default_path_is_cwd() -> None:
    response = client.get("/doctor")
    assert response.status_code == 200
    assert response.json()["path"] == str(Path.cwd().resolve())


def test_report_endpoint_returns_markdown() -> None:
    response = client.get("/report", params={"path": str(MINIMAL)})
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 100
    assert "# ForgeFix health report" in body["markdown"]


def test_invalid_path_returns_400() -> None:
    response = client.get("/doctor", params={"path": "/definitely/not/a/dir"})
    assert response.status_code == 400
