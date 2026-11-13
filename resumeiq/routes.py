"""HTTP routes: the web UI and a small JSON REST API."""

from flask import Blueprint, jsonify, render_template, request

from . import __version__
from .analyzer import analyze, extract_skills, rank_resumes
from .parser import UnsupportedFileError, extract_text

bp = Blueprint("main", __name__)

MIN_TEXT_LENGTH = 30


def _error(message, status=400):
    return jsonify({"error": message}), status


def _resume_text_from_request():
    """Read resume text from an uploaded file or from the 'resume_text' field."""
    upload = request.files.get("resume")
    if upload and upload.filename:
        return extract_text(upload.filename, upload.read())
    if request.is_json:
        return (request.get_json(silent=True) or {}).get("resume_text", "")
    return request.form.get("resume_text", "")


def _jd_text_from_request():
    if request.is_json:
        return (request.get_json(silent=True) or {}).get("job_description", "")
    return request.form.get("job_description", "")


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/health")
def health():
    return jsonify({"status": "ok", "version": __version__})


@bp.post("/api/analyze")
def api_analyze():
    try:
        resume_text = _resume_text_from_request()
    except UnsupportedFileError as exc:
        return _error(str(exc))
    except Exception:  # corrupt or unreadable file
        return _error("Could not read the uploaded file. Try another PDF/DOCX or paste the text.")

    jd_text = _jd_text_from_request()
    if len(resume_text.strip()) < MIN_TEXT_LENGTH:
        return _error("Resume text is empty or too short.")
    if len(jd_text.strip()) < MIN_TEXT_LENGTH:
        return _error("Job description is empty or too short.")

    return jsonify(analyze(resume_text, jd_text).to_dict())


@bp.post("/api/rank")
def api_rank():
    """Recruiter mode: rank several uploaded resumes against one job description."""
    jd_text = request.form.get("job_description", "")
    files = request.files.getlist("resumes")
    if len(jd_text.strip()) < MIN_TEXT_LENGTH:
        return _error("Job description is empty or too short.")
    if not files:
        return _error("Upload at least one resume.")

    resumes, skipped = [], []
    for upload in files:
        try:
            text = extract_text(upload.filename, upload.read())
        except Exception:
            skipped.append(upload.filename)
            continue
        if len(text.strip()) >= MIN_TEXT_LENGTH:
            resumes.append((upload.filename, text))
        else:
            skipped.append(upload.filename)

    return jsonify({"results": rank_resumes(resumes, jd_text), "skipped": skipped})


@bp.post("/api/skills")
def api_skills():
    data = request.get_json(silent=True) or {}
    return jsonify({"skills": extract_skills(data.get("text", ""))})


@bp.app_errorhandler(413)
def too_large(_err):
    return _error("File too large. Maximum size is 5 MB.", 413)
