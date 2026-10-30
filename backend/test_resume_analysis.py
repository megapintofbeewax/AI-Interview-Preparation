import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from docx import Document
from app.main import app

client = TestClient(app)

def create_rich_sample_docx() -> io.BytesIO:
    doc = Document()
    doc.add_heading("John Doe", 0)
    doc.add_heading("Education", level=1)
    doc.add_paragraph("B.Tech Computer Science and Engineering - 2024")
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph("Python, Java, SQL, Flask, Machine Learning, Docker, Git")
    doc.add_heading("Key Projects", level=1)
    doc.add_paragraph("AI Diet Planner: Personalized nutrition recommendation engine using Flask and ML.")
    doc.add_paragraph("Self-Healing Network: Autonomous system failure detection and remediation using Python.")
    doc.add_heading("Work Experience", level=1)
    doc.add_paragraph("Software Engineering Intern at Tech Corp (6 months). Built REST APIs with Flask and PostgreSQL.")
    doc.add_heading("Certifications", level=1)
    doc.add_paragraph("AWS Certified Developer Associate")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def test_resume_analysis_flow():
    print(">>> 1. Authenticating test user...")
    user_payload = {
        "name": "NLP Candidate",
        "email": "nlp.candidate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "nlp.candidate@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Uploading rich resume document...")
    doc_file = create_rich_sample_docx()
    resp = client.post(
        "/api/resume/upload",
        files={"file": ("john_doe_resume.docx", doc_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers
    )
    assert resp.status_code == 201
    print("[PASS] Resume uploaded")

    print("\n>>> 3. Triggering NLP analysis (POST /api/resume-analysis/analyze)...")
    resp = client.post("/api/resume-analysis/analyze", headers=headers)
    assert resp.status_code == 200, f"Analysis failed: {resp.text}"
    analysis = resp.json()
    print("[PASS] Analysis completed. Extracted data:")
    print("   Skills:", analysis["skills"])
    print("   Projects:", analysis["projects"])
    print("   Education:", analysis["education"])
    print("   Experience:", analysis["experience"])

    # Assertions on extracted entities
    assert any("Python" in s for s in analysis["skills"]), "Python not found in skills"
    assert any("Flask" in s for s in analysis["skills"]), "Flask not found in skills"
    assert any("SQL" in s for s in analysis["skills"]), "SQL not found in skills"
    assert "Computer Science" in analysis["education"] or "B.Tech" in analysis["education"]
    assert any("AI Diet Planner" in p for p in analysis["projects"])
    assert any("Self-Healing Network" in p for p in analysis["projects"])

    print("\n>>> 4. Testing GET /api/resume-analysis...")
    resp = client.get("/api/resume-analysis", headers=headers)
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["id"] == analysis["id"]
    print("[PASS] Analysis fetched successfully")

    print("\n>>> 5. Testing PUT /api/resume-analysis (User review & correction)...")
    updated_skills = ["Python", "Java", "SQL", "Flask", "Machine Learning", "Kubernetes"]
    updated_projects = ["AI Diet Planner", "Self-Healing Network", "Cloud Load Balancer"]
    resp = client.put(
        "/api/resume-analysis",
        json={
            "skills": updated_skills,
            "projects": updated_projects,
            "education": "B.Tech Computer Science (Honors)",
            "experience": "Senior Backend Intern at Tech Corp"
        },
        headers=headers
    )
    assert resp.status_code == 200
    corrected = resp.json()
    assert "Kubernetes" in corrected["skills"]
    assert "Cloud Load Balancer" in corrected["projects"]
    assert corrected["education"] == "B.Tech Computer Science (Honors)"
    print("[PASS] User corrections saved and verified persistent")

    print("\n>>> 6. Testing unauthenticated access...")
    resp = client.get("/api/resume-analysis")
    assert resp.status_code == 401
    print("[PASS] Unauthenticated access blocked")

    print("\n=========================================")
    print("ALL RESUME ANALYSIS TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_resume_analysis_flow()
