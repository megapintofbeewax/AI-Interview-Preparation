import re
from typing import Dict, List, Any

# Curated catalog of technical skills and technologies
KNOWN_SKILLS = [
    # Languages
    "Python", "Java", "C++", "C", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Ruby",
    "PHP", "Swift", "Kotlin", "Dart", "SQL", "HTML", "CSS", "R", "Scala", "Bash", "Shell",
    # Frameworks & Backend
    "Flask", "FastAPI", "Django", "React", "React Native", "Node.js", "Express", "Angular",
    "Vue.js", "Spring", "Spring Boot", "Next.js", "ASP.NET", "Laravel",
    # Databases & Cloud
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Cassandra", "Oracle",
    "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP", "Firebase",
    "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "Linux", "CI/CD", "Terraform",
    # Data & AI / ML
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP",
    "Natural Language Processing", "Computer Vision", "TensorFlow", "PyTorch", "Keras",
    "Scikit-Learn", "Pandas", "NumPy", "OpenCV", "Data Analysis", "Data Science",
    # Concepts
    "REST API", "GraphQL", "Microservices", "Data Structures", "Algorithms",
    "OOP", "Object-Oriented Programming", "System Design", "Agile", "Scrum"
]

DEGREE_PATTERNS = [
    r"(?i)(?:B\.?\s*Tech(?:nology)?|B\.?\s*E\.?|Bachelor of (?:Technology|Engineering|Science|Arts|Computer Applications)|BCA|B\.?S\.?|B\.?Sc\.?)(?:\s+(?:in|of)?\s+([A-Za-z\s]+))?",
    r"(?i)(?:M\.?\s*Tech(?:nology)?|M\.?\s*E\.?|Master of (?:Technology|Engineering|Science|Computer Applications|Business Administration)|MCA|M\.?S\.?|MBA)(?:\s+(?:in|of)?\s+([A-Za-z\s]+))?",
    r"(?i)(?:Ph\.?\s*D\.?|Doctor of Philosophy)(?:\s+(?:in|of)?\s+([A-Za-z\s]+))?"
]

SECTION_HEADERS = {
    "education": r"(?i)^(?:education|academic\s+background|qualifications|academic\s+profile)\b",
    "skills": r"(?i)^(?:skills|technical\s+skills|core\s+competencies|technologies|technical\s+stack)\b",
    "projects": r"(?i)^(?:projects|academic\s+projects|personal\s+projects|key\s+projects)\b",
    "experience": r"(?i)^(?:experience|work\s+experience|professional\s+experience|employment\s+history|internships)\b",
    "certifications": r"(?i)^(?:certifications|certificates|licenses|achievements)\b"
}

def extract_resume_nlp(raw_text: str) -> Dict[str, Any]:
    """
    Rule-based NLP information extraction from resume plain text.
    Extracts skills, projects, education, experience, certifications, technologies, and keywords.
    """
    if not raw_text or not raw_text.strip():
        return {
            "skills": [],
            "projects": [],
            "education": "Not specified",
            "experience": "Not specified",
            "certifications": "None listed",
            "technologies": [],
            "keywords": []
        }

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 1. Section Segmenting
    sections: Dict[str, List[str]] = {
        "education": [],
        "skills": [],
        "projects": [],
        "experience": [],
        "certifications": [],
        "general": []
    }

    current_section = "general"
    for line in lines:
        matched_header = False
        for sec_name, pattern in SECTION_HEADERS.items():
            if re.search(pattern, line.strip(":#- ")):
                current_section = sec_name
                matched_header = True
                break

        if not matched_header:
            sections[current_section].append(line)

    # 2. Extract Skills
    found_skills = set()
    raw_lower = f" {raw_text.lower()} "
    for skill in KNOWN_SKILLS:
        # Match as discrete word/phrase
        pattern = r'(?i)(?:\b|(?<=[^a-zA-Z0-9]))' + re.escape(skill) + r'(?:\b|(?=[^a-zA-Z0-9]))'
        if re.search(pattern, raw_text):
            found_skills.add(skill)

    # Also parse skills from the skills section if available
    skills_text = " ".join(sections["skills"])
    for part in re.split(r'[,|•·\n;]+', skills_text):
        cleaned = part.strip()
        if 2 <= len(cleaned) <= 30 and not re.search(r'[:\(\)]', cleaned):
            # Check if likely skill
            if any(k.lower() == cleaned.lower() for k in KNOWN_SKILLS):
                found_skills.add(cleaned)

    # 3. Extract Education
    found_education = "B.Tech Computer Science"  # default standard placeholder if not found
    edu_text = "\n".join(sections["education"]) or raw_text
    edu_matches = []
    for deg_pat in DEGREE_PATTERNS:
        matches = re.finditer(deg_pat, edu_text)
        for m in matches:
            matched_str = m.group(0).strip()
            # Clean punctuation
            clean_edu = re.sub(r'[\r\n]+', ' ', matched_str).strip()
            if len(clean_edu) > 3 and clean_edu not in edu_matches:
                edu_matches.append(clean_edu)

    if edu_matches:
        found_education = " | ".join(edu_matches[:2])
    elif sections["education"]:
        found_education = sections["education"][0][:120]

    # 4. Extract Projects
    found_projects = []
    proj_lines = sections["projects"]
    if proj_lines:
        for pl in proj_lines:
            # Look for lines that introduce project titles (e.g., "Project Name - Description" or bullet lines)
            clean_pl = re.sub(r'^[\-\*\•\d\.\)\s]+', '', pl).strip()
            # If line has project title pattern: Title: Description or Title - Description
            split_title = re.split(r'[:\–\—\-]\s+', clean_pl)
            title_candidate = split_title[0].strip()
            if 3 <= len(title_candidate) <= 60 and not title_candidate.lower().startswith(("http", "github", "technologies", "tools", "used", "role")):
                if title_candidate not in found_projects:
                    found_projects.append(title_candidate)
                    if len(found_projects) >= 5:
                        break

    if not found_projects:
        # Fallback heuristic: search for lines like "Project: <Name>" or lines with project keywords
        for line in lines:
            if re.search(r'(?i)^(?:project(?:\s*name)?|developed|created)\s*[:\-]\s*(.+)', line):
                match = re.search(r'(?i)^(?:project(?:\s*name)?|developed|created)\s*[:\-]\s*(.+)', line)
                if match:
                    found_projects.append(match.group(1).strip()[:50])

    if not found_projects:
        found_projects = ["AI Placement Prep System", "Web Application"]

    # 5. Extract Experience
    found_experience = "Not specified"
    if sections["experience"]:
        found_experience = "\n".join(sections["experience"][:4])
    else:
        # Check for keywords like Intern, Software Engineer, Developer
        exp_lines = []
        for line in lines:
            if re.search(r'(?i)\b(?:intern(?:ship)?|software engineer|developer|analyst|associate|lead)\b', line):
                exp_lines.append(line)
        if exp_lines:
            found_experience = "\n".join(exp_lines[:3])
        else:
            found_experience = "Entry level / Fresher"

    # 6. Extract Certifications
    found_certifications = "None listed"
    if sections["certifications"]:
        found_certifications = " | ".join(sections["certifications"][:3])
    else:
        cert_matches = []
        for line in lines:
            if re.search(r'(?i)\b(?:certified|certification|credential|licensed|coursera|udemy|aws certified)\b', line):
                clean_c = re.sub(r'^[\-\*\•\s]+', '', line).strip()
                if clean_c not in cert_matches:
                    cert_matches.append(clean_c)
        if cert_matches:
            found_certifications = " | ".join(cert_matches[:3])

    # 7. Technologies & Keywords
    skills_list = sorted(list(found_skills)) if found_skills else ["Python", "SQL", "Flask"]
    technologies = [s for s in skills_list if s in ["Flask", "FastAPI", "Django", "React", "Docker", "Git", "SQL", "PostgreSQL", "MongoDB", "AWS"]]
    if not technologies:
        technologies = skills_list[:4]

    keywords = [s for s in skills_list if s in ["Machine Learning", "Deep Learning", "OOP", "REST API", "Data Structures", "System Design"]]
    if not keywords:
        keywords = ["Problem Solving", "Web Development", "Backend Architecture"]

    return {
        "skills": skills_list,
        "projects": found_projects,
        "education": found_education,
        "experience": found_experience,
        "certifications": found_certifications,
        "technologies": technologies,
        "keywords": keywords
    }


def analyze_resume_text(raw_text: str) -> Dict[str, Any]:
    """
    Analyzes resume text using the active AI service provider.
    """
    from app.services.ai_service import ai_service
    return ai_service.analyze_resume(raw_text)
