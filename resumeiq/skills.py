"""Skill taxonomy used for skill extraction.

Each canonical skill maps to a list of aliases that may appear in a resume
or job description. Matching is case-insensitive and respects word boundaries.
"""

SKILL_CATEGORIES = {
    "Programming Languages": {
        "Python": ["python"],
        "Java": ["java"],
        "JavaScript": ["javascript", "js", "es6"],
        "TypeScript": ["typescript", "ts"],
        "C": ["c programming", "c language"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "csharp"],
        "Go": ["golang"],
        "Kotlin": ["kotlin"],
        "SQL": ["sql"],
        "R": ["r programming", "r language"],
    },
    "Web Development": {
        "HTML": ["html", "html5"],
        "CSS": ["css", "css3"],
        "React": ["react", "reactjs", "react.js"],
        "Angular": ["angular", "angularjs"],
        "Vue": ["vue", "vuejs", "vue.js"],
        "Node.js": ["node", "nodejs", "node.js"],
        "Express": ["express", "expressjs", "express.js"],
        "Django": ["django"],
        "Flask": ["flask"],
        "FastAPI": ["fastapi"],
        "Spring Boot": ["spring boot", "springboot", "spring"],
        "REST API": ["rest api", "restful", "rest apis"],
        "GraphQL": ["graphql"],
        "Tailwind CSS": ["tailwind", "tailwindcss"],
        "Bootstrap": ["bootstrap"],
    },
    "Databases": {
        "MySQL": ["mysql"],
        "PostgreSQL": ["postgresql", "postgres"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "Oracle": ["oracle db", "oracle database", "oracle"],
        "Firebase": ["firebase"],
    },
    "Cloud & DevOps": {
        "AWS": ["aws", "amazon web services"],
        "Azure": ["azure"],
        "GCP": ["gcp", "google cloud"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "CI/CD": ["ci/cd", "cicd", "continuous integration"],
        "Jenkins": ["jenkins"],
        "Git": ["git", "github", "gitlab"],
        "Linux": ["linux", "unix"],
    },
    "Data & AI": {
        "Machine Learning": ["machine learning", "ml"],
        "Deep Learning": ["deep learning", "dl"],
        "NLP": ["nlp", "natural language processing"],
        "Computer Vision": ["computer vision", "opencv"],
        "TensorFlow": ["tensorflow"],
        "PyTorch": ["pytorch"],
        "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Data Analysis": ["data analysis", "data analytics"],
        "Power BI": ["power bi", "powerbi"],
        "Tableau": ["tableau"],
        "Generative AI": ["generative ai", "genai", "llm", "llms"],
    },
    "CS Fundamentals": {
        "Data Structures": ["data structures", "dsa"],
        "Algorithms": ["algorithms"],
        "OOP": ["oop", "oops", "object oriented", "object-oriented"],
        "DBMS": ["dbms"],
        "Operating Systems": ["operating systems"],
        "Computer Networks": ["computer networks", "networking"],
        "System Design": ["system design"],
    },
    "Tools & Practices": {
        "Agile": ["agile", "scrum"],
        "Unit Testing": ["unit testing", "pytest", "junit", "jest"],
        "Postman": ["postman"],
        "Jira": ["jira"],
        "Microservices": ["microservices", "microservice"],
        "Salesforce": ["salesforce", "apex"],
        "MuleSoft": ["mulesoft"],
    },
}


def build_alias_index():
    """Return a list of (alias, canonical_skill, category) sorted longest-first.

    Longest-first ordering lets multi-word aliases such as "spring boot"
    be matched before shorter ones such as "spring".
    """
    index = []
    for category, skills in SKILL_CATEGORIES.items():
        for canonical, aliases in skills.items():
            for alias in aliases:
                index.append((alias.lower(), canonical, category))
    index.sort(key=lambda item: len(item[0]), reverse=True)
    return index


ALIAS_INDEX = build_alias_index()
SKILL_TO_CATEGORY = {
    canonical: category
    for category, skills in SKILL_CATEGORIES.items()
    for canonical in skills
}
