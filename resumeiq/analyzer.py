"""Core resume analysis logic.

The analyzer combines two signals into a single ATS-style score:

1. Skill match   - which skills required by the job description appear in
                   the resume (rule-based extraction over a skill taxonomy).
2. Text similarity - TF-IDF vectors of both documents compared with cosine
                   similarity, which captures overall wording overlap.

It also checks resume structure (sections, contact details) and produces
actionable suggestions.
"""

import re
from dataclasses import dataclass, field, asdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import ALIAS_INDEX, SKILL_TO_CATEGORY

SKILL_WEIGHT = 0.65
SIMILARITY_WEIGHT = 0.35

SECTION_PATTERNS = {
    "Education": r"\b(education|academic|qualification)s?\b",
    "Experience": r"\b(experience|internships?|work history|employment)\b",
    "Projects": r"\bprojects?\b",
    "Skills": r"\b(skills|technical skills|technologies)\b",
    "Certifications": r"\b(certifications?|certificates?|courses)\b",
    "Achievements": r"\b(achievements?|awards?|accomplishments?)\b",
}

CONTACT_PATTERNS = {
    "Email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "Phone": r"(\+?\d[\d\s-]{8,}\d)",
    "LinkedIn": r"linkedin\.com/in/[\w-]+",
    "GitHub": r"github\.com/[\w-]+",
}

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "led",
    "optimized", "improved", "deployed", "automated", "integrated",
    "reduced", "increased", "engineered", "architected", "launched",
}


@dataclass
class AnalysisResult:
    score: float
    skill_score: float
    similarity_score: float
    verdict: str
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    extra_skills: list = field(default_factory=list)
    skills_by_category: dict = field(default_factory=dict)
    sections_found: list = field(default_factory=list)
    sections_missing: list = field(default_factory=list)
    contact: dict = field(default_factory=dict)
    word_count: int = 0
    suggestions: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def normalize(text):
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _alias_pattern(alias):
    # Custom boundaries so aliases like "c++", "c#" and "node.js" match
    # correctly while "js" inside "node.js" or "git" inside "github" do not.
    return re.compile(r"(?<![\w+#.])" + re.escape(alias) + r"(?![\w+#])")


_COMPILED = [(_alias_pattern(a), canonical) for a, canonical, _ in ALIAS_INDEX]


def extract_skills(text):
    """Return the sorted set of canonical skills mentioned in ``text``."""
    text = normalize(text)
    found = set()
    for pattern, canonical in _COMPILED:
        if pattern.search(text):
            found.add(canonical)
    return sorted(found)


def text_similarity(resume_text, jd_text):
    """Cosine similarity of TF-IDF vectors, in the range 0..1."""
    docs = [normalize(resume_text), normalize(jd_text)]
    if not docs[0] or not docs[1]:
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform(docs)
    except ValueError:  # only stop words / empty vocabulary
        return 0.0
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def detect_sections(text):
    lowered = normalize(text)
    found = [name for name, pat in SECTION_PATTERNS.items() if re.search(pat, lowered)]
    missing = [name for name in SECTION_PATTERNS if name not in found]
    return found, missing


def detect_contact(text):
    return {name: bool(re.search(pat, text or "", re.IGNORECASE)) for name, pat in CONTACT_PATTERNS.items()}


def verdict_for(score):
    if score >= 75:
        return "Strong match"
    if score >= 55:
        return "Good match"
    if score >= 35:
        return "Partial match"
    return "Weak match"


def build_suggestions(missing_skills, sections_missing, contact, resume_text, word_count):
    tips = []
    if missing_skills:
        top = ", ".join(missing_skills[:6])
        tips.append(f"Add the job's missing skills if you have them, for example: {top}.")
    for section in sections_missing:
        if section in ("Projects", "Skills", "Education"):
            tips.append(f"Add a clear '{section}' section; ATS parsers look for it.")
    if not contact.get("Email") or not contact.get("Phone"):
        tips.append("Make sure your email and phone number are at the top of the resume.")
    if not contact.get("GitHub"):
        tips.append("Add your GitHub profile link so recruiters can see your code.")
    if not contact.get("LinkedIn"):
        tips.append("Add your LinkedIn profile URL.")
    words = set(re.findall(r"[a-z]+", normalize(resume_text)))
    if len(words & ACTION_VERBS) < 3:
        tips.append("Start bullet points with action verbs such as Built, Developed, Optimized, Deployed.")
    if not re.search(r"\d+\s?%|\b\d{2,}\b", resume_text or ""):
        tips.append("Quantify impact with numbers, e.g. 'reduced load time by 40%' or 'served 500+ users'.")
    if word_count < 250:
        tips.append("The resume looks short; describe your projects and internships in more detail.")
    elif word_count > 900:
        tips.append("The resume is long; freshers should aim for a single page (about 400-700 words).")
    return tips


def analyze(resume_text, jd_text):
    """Analyze a resume against a job description and return an AnalysisResult."""
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(jd_text))

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)

    skill_score = len(matched) / len(jd_skills) if jd_skills else 0.0
    similarity = text_similarity(resume_text, jd_text)
    # Raw TF-IDF cosine between two different documents rarely exceeds ~0.6,
    # so rescale it to make the number intuitive for users.
    similarity_scaled = min(similarity / 0.6, 1.0)

    if jd_skills:
        score = SKILL_WEIGHT * skill_score + SIMILARITY_WEIGHT * similarity_scaled
    else:
        score = similarity_scaled
    score = round(score * 100, 1)

    by_category = {}
    for skill in sorted(resume_skills):
        by_category.setdefault(SKILL_TO_CATEGORY[skill], []).append(skill)

    sections_found, sections_missing = detect_sections(resume_text)
    contact = detect_contact(resume_text)
    word_count = len(re.findall(r"\b\w+\b", resume_text or ""))

    return AnalysisResult(
        score=score,
        skill_score=round(skill_score * 100, 1),
        similarity_score=round(similarity_scaled * 100, 1),
        verdict=verdict_for(score),
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        skills_by_category=by_category,
        sections_found=sections_found,
        sections_missing=sections_missing,
        contact=contact,
        word_count=word_count,
        suggestions=build_suggestions(missing, sections_missing, contact, resume_text, word_count),
    )


def rank_resumes(resumes, jd_text):
    """Rank several resumes against one job description.

    ``resumes`` is a list of (name, text) tuples. Returns a list of dicts
    sorted by score, highest first.
    """
    ranked = []
    for name, text in resumes:
        result = analyze(text, jd_text)
        ranked.append({
            "name": name,
            "score": result.score,
            "verdict": result.verdict,
            "matched_skills": result.matched_skills,
            "missing_skills": result.missing_skills,
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    for position, row in enumerate(ranked, start=1):
        row["rank"] = position
    return ranked
