from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_and_project_flow(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MUSIC_STUDIO_DATA", str(tmp_path))
    import importlib
    import music_studio.api as api_module

    importlib.reload(api_module)
    client = TestClient(api_module.app)
    assert client.get("/api/health").json()["status"] == "ok"

    created = client.post(
        "/api/projects",
        json={"name": "API Song", "tempo": 90, "key": "A minor", "bars": 1},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    composed = client.post(
        f"/api/projects/{project_id}/compose",
        json={"style": "ambient", "instruments": ["piano", "strings"], "seed": 2},
    )
    assert composed.status_code == 200
    assert len(composed.json()["tracks"]) == 2
