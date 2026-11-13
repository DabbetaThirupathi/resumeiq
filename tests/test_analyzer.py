from pathlib import Path

import pytest

from resumeiq.analyzer import analyze, extract_skills, rank_resumes, text_similarity, verdict_for

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def jd():
    return (SAMPLES / "job_description.txt").read_text()


@pytest.fixture
def strong():
    return (SAMPLES / "resume_strong.txt").read_text()


@pytest.fixture
def weak():
    return (SAMPLES / "resume_weak.txt").read_text()


def test_extract_skills_handles_aliases_and_symbols():
    skills = extract_skills("Worked with ReactJS, node.js, C++, C# and sklearn on AWS")
    for expected in ["React", "Node.js", "C++", "C#", "scikit-learn", "AWS"]:
        assert expected in skills


def test_extract_skills_respects_word_boundaries():
    # "git" must not match inside "digital"; "java" must not come from "javascript"
    skills = extract_skills("Digital marketing with JavaScript")
    assert "Git" not in skills
    assert "Java" not in skills
    assert "JavaScript" in skills


def test_multiword_alias_beats_single_word():
    assert "Spring Boot" in extract_skills("Built services in Spring Boot")


def test_similarity_bounds(jd, strong):
    assert text_similarity("", jd) == 0.0
    value = text_similarity(strong, jd)
    assert 0.0 < value <= 1.0


def test_strong_resume_scores_higher_than_weak(jd, strong, weak):
    good = analyze(strong, jd)
    bad = analyze(weak, jd)
    assert good.score > bad.score
    assert good.score >= 55
    assert bad.score < 35


def test_missing_skills_reported(jd, weak):
    result = analyze(weak, jd)
    assert "React" in result.missing_skills
    assert "Projects" in result.sections_missing
    assert result.suggestions


def test_contact_detection(strong):
    result = analyze(strong, "Need a Java developer with SQL and Git experience for backend work.")
    assert all(result.contact.values())


def test_rank_resumes_orders_by_score(jd, strong, weak):
    ranked = rank_resumes([("weak.txt", weak), ("strong.txt", strong)], jd)
    assert [r["name"] for r in ranked] == ["strong.txt", "weak.txt"]
    assert ranked[0]["rank"] == 1


@pytest.mark.parametrize("score,label", [(80, "Strong match"), (60, "Good match"), (40, "Partial match"), (10, "Weak match")])
def test_verdicts(score, label):
    assert verdict_for(score) == label
