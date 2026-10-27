import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("GEMINI_API_KEY", "")  # force the rule-based advisor
    monkeypatch.setenv("GEMINI_API_KEY_BACKUP", "")
    get_settings.cache_clear()
    yield TestClient(create_app())
    get_settings.cache_clear()


def parse_pdf(client, data: bytes, department: str = "cs"):
    return client.post(
        "/api/transcripts/parse",
        data={"department": department},
        files={"file": ("transcript.pdf", data, "application/pdf")},
    )


def test_health_reports_whether_ai_is_enabled(client):
    assert client.get("/api/health").json() == {"status": "ok", "ai_enabled": False}


def test_departments_and_plan_are_served(client):
    departments = client.get("/api/departments").json()
    plan = client.get("/api/departments/cs/plan").json()

    assert {item["code"] for item in departments} == {"cs", "net"}
    assert plan["total_hours"] == 112
    assert plan["courses"][0]["code"] == "CS 101"


def test_unknown_department_returns_a_coded_error(client):
    response = client.get("/api/departments/zzz/plan")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "department_not_found"


def test_uploading_a_transcript_returns_the_recognised_courses(client, make_pdf):
    data = make_pdf(["CS 101 Introduction to Computing 3 A", "CS 102 Programming 1 4 IP"])

    response = parse_pdf(client, data)

    assert response.status_code == 200
    body = response.json()
    assert [(c["code"], c["status"]) for c in body["courses"]] == [
        ("CS 101", "passed"),
        ("CS 102", "in_progress"),
    ]


def test_non_pdf_upload_is_rejected(client):
    response = parse_pdf(client, b"hello")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_pdf"


def test_scanned_pdf_is_reported_as_unreadable(client, blank_pdf):
    response = parse_pdf(client, blank_pdf)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "no_text_in_pdf"


def test_oversized_upload_is_rejected(client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "100")
    get_settings.cache_clear()

    response = parse_pdf(TestClient(create_app()), b"%PDF-" + b"0" * 500)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_recommendation_round_trip(client):
    response = client.post(
        "/api/recommendations",
        json={
            "department": "cs",
            "term": "fall",
            "completed": [{"code": "cs101", "grade": "A"}, {"code": "CS 102", "grade": "B"}],
            "gpa": 3.0,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["source"] == "rules"
    assert body["min_hours"] <= body["total_hours"] <= body["max_hours"]
    assert {"ar", "en"} <= set(body["courses"][0]["reason"])


def test_recommendation_with_unknown_course_is_a_coded_error(client):
    response = client.post(
        "/api/recommendations",
        json={"department": "cs", "term": "fall", "completed": [{"code": "XX 999"}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_course"


def test_recommendation_rejects_an_invalid_term(client):
    response = client.post(
        "/api/recommendations",
        json={"department": "cs", "term": "winter", "completed": []},
    )

    assert response.status_code == 422
