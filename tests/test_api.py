import io
from pathlib import Path

import pytest
from docx import Document

from resumeiq import create_app

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


@pytest.fixture
def jd():
    return (SAMPLES / "job_description.txt").read_text()


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"ResumeIQ" in res.data


def test_analyze_with_json(client, jd):
    resume = (SAMPLES / "resume_strong.txt").read_text()
    res = client.post("/api/analyze", json={"resume_text": resume, "job_description": jd})
    assert res.status_code == 200
    data = res.get_json()
    assert 0 <= data["score"] <= 100
    assert "React" in data["matched_skills"]


def test_analyze_with_txt_upload(client, jd):
    data = {
        "resume": (io.BytesIO((SAMPLES / "resume_strong.txt").read_bytes()), "resume.txt"),
        "job_description": jd,
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200


def test_analyze_with_docx_upload(client, jd):
    doc = Document()
    for line in (SAMPLES / "resume_strong.txt").read_text().splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    res = client.post(
        "/api/analyze",
        data={"resume": (buf, "resume.docx"), "job_description": jd},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert "MongoDB" in res.get_json()["matched_skills"]


def test_rejects_unsupported_file(client, jd):
    data = {"resume": (io.BytesIO(b"hello"), "photo.png"), "job_description": jd}
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "Unsupported" in res.get_json()["error"]


def test_rejects_empty_input(client):
    res = client.post("/api/analyze", json={"resume_text": "", "job_description": ""})
    assert res.status_code == 400


def test_rank_endpoint(client, jd):
    data = {
        "job_description": jd,
        "resumes": [
            (io.BytesIO((SAMPLES / "resume_weak.txt").read_bytes()), "weak.txt"),
            (io.BytesIO((SAMPLES / "resume_strong.txt").read_bytes()), "strong.txt"),
        ],
    }
    res = client.post("/api/rank", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    results = res.get_json()["results"]
    assert results[0]["name"] == "strong.txt"
