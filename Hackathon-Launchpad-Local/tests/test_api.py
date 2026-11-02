from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import store


def test_shopping_approval_order_and_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "test.db")
    with TestClient(app) as client:
        products = client.get("/api/products?q=rice")
        assert products.status_code == 200
        assert products.json()["products"][0]["id"] == "p1"

        proposal = client.post(
            "/api/proposals",
            json={
                "items": [{"product_id": "p1", "quantity": 1}],
                "budget": 300,
                "address": "12 Demo Road, Bengaluru",
            },
        )
        assert proposal.status_code == 201
        proposal_id = proposal.json()["id"]
        assert proposal.json()["total"] == 289

        denied = client.post(
            f"/api/proposals/{proposal_id}/approve",
            json={"approved": False, "idempotency_key": "test-key-denied"},
        )
        assert denied.status_code == 422
        assert client.get("/api/orders").json()["orders"] == []

        approval = {
            "approved": True,
            "idempotency_key": "test-key-approved",
        }
        order = client.post(f"/api/proposals/{proposal_id}/approve", json=approval)
        assert order.status_code == 200
        assert order.json()["payment_status"] == "simulated_not_charged"

        duplicate = client.post(
            f"/api/proposals/{proposal_id}/approve",
            json={**approval, "idempotency_key": "another-key"},
        )
        assert duplicate.json()["id"] == order.json()["id"]
        receipt = client.get(f"/api/orders/{order.json()['id']}/receipt")
        assert receipt.status_code == 200
        assert receipt.headers["content-type"] == "application/pdf"


def test_budget_and_unknown_product_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "test.db")
    with TestClient(app) as client:
        payload = {
            "items": [{"product_id": "p3", "quantity": 1}],
            "budget": 100,
            "address": "12 Demo Road, Bengaluru",
        }
        assert client.post("/api/proposals", json=payload).status_code == 422
        payload["budget"] = 270
        assert client.post("/api/proposals", json=payload).status_code == 422
        payload["budget"] = None
        payload["items"][0]["product_id"] = "not-a-product"
        assert client.post("/api/proposals", json=payload).status_code == 404


def test_voice_turn_transcribes_answers_and_returns_speech(monkeypatch):
    calls = {}

    def transcribe(**kwargs):
        calls["audio"] = kwargs
        return SimpleNamespace(transcript="I need rice")

    def complete(**kwargs):
        calls["chat"] = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="How much rice?"))]
        )

    def synthesize(**kwargs):
        calls["speech"] = kwargs
        return SimpleNamespace(audios=["d2F2"])

    client = SimpleNamespace(
        speech_to_text=SimpleNamespace(transcribe=transcribe),
        chat=SimpleNamespace(completions=complete),
        text_to_speech=SimpleNamespace(convert=synthesize),
    )
    monkeypatch.setattr(routes.settings, "SARVAM_API_KEY", "configured")
    monkeypatch.setattr(routes, "get_sarvam_client", lambda: client)

    response = TestClient(app).post(
        "/api/voice/turn",
        data={
            "messages": '{"messages":[{"role":"user","content":"Hello"}]}',
            "language_code": "en-IN",
        },
        files={"audio": ("voice.webm", b"sample audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["transcript"] == "I need rice"
    assert response.json()["reply"] == "How much rice?"
    assert response.json()["audio_base64"] == "d2F2"
    assert calls["audio"]["model"] == "saaras:v4"
    assert calls["speech"]["model"] == "bulbul:v3"


def test_voice_turn_requires_model_key(monkeypatch):
    monkeypatch.setattr(routes.settings, "SARVAM_API_KEY", "")
    response = TestClient(app).post(
        "/api/voice/turn",
        data={"messages": '{"messages":[]}', "language_code": "en-IN"},
        files={"audio": ("voice.webm", b"sample audio", "audio/webm")},
    )
    assert response.status_code == 503
