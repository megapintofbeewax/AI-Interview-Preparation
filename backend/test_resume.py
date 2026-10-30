import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfWriter
from app.main import app

client = TestClient(app)

def create_sample_docx(text: str) -> io.BytesIO:
    doc = Document()
    doc.add_heading("Resume: John Doe", 0)
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def create_sample_pdf(text: str) -> io.BytesIO:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf

def test_resume_flow():
    print(">>> 1. Authenticating user for resume testing...")
    user_payload = {
        "name": "Resume Tester",
        "email": "resume.tester@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "resume.tester@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Testing rejection of unsupported file extension (.txt)...")
    fake_txt = io.BytesIO(b"Hello world")
    resp = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", fake_txt, "text/plain")},
        headers=headers
    )
    assert resp.status_code == 400, f"Expected 400 for unsupported format, got: {resp.status_code}"
    print(f"[PASS] Unsupported file rejected: {resp.json()['detail']}")

    print("\n>>> 3. Testing rejection of empty file...")
    empty_pdf = io.BytesIO(b"")
    resp = client.post(
        "/api/resume/upload",
        files={"file": ("empty.pdf", empty_pdf, "application/pdf")},
        headers=headers
    )
    assert resp.status_code == 400
    print("[PASS] Empty file rejected correctly")

    print("\n>>> 4. Testing upload of valid PDF resume...")
    pdf_file = create_sample_pdf("Skills: Python, FastAPI, Docker")
    resp = client.post(
        "/api/resume/upload",
        files={"file": ("sample_resume.pdf", pdf_file, "application/pdf")},
        headers=headers
    )
    assert resp.status_code == 201, f"PDF upload failed: {resp.text}"
    data = resp.json()
    assert data["filename"] == "sample_resume.pdf"
    assert data["file_type"] == "pdf"
    assert data["message"] == "Resume uploaded successfully."
    print("[PASS] PDF uploaded successfully:", data)

    print("\n>>> 5. Testing upload of valid DOCX resume...")
    docx_file = create_sample_docx("Skills: Python, React, SQL. Projects: AI Interview Prep.")
    resp = client.post(
        "/api/resume/upload",
        files={"file": ("sample_resume.docx", docx_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers
    )
    assert resp.status_code == 201, f"DOCX upload failed: {resp.text}"
    docx_data = resp.json()
    assert docx_data["filename"] == "sample_resume.docx"
    assert docx_data["file_type"] == "docx"
    assert "AI Interview Prep" in docx_data["preview_text"]
    print("[PASS] DOCX uploaded and text extracted successfully")

    print("\n>>> 6. Testing GET /api/resume/latest...")
    resp = client.get("/api/resume/latest", headers=headers)
    assert resp.status_code == 200
    latest = resp.json()
    assert latest["filename"] == "sample_resume.docx"
    print("[PASS] Latest resume retrieved correctly:", latest["filename"])

    print("\n>>> 7. Testing unauthenticated upload rejection...")
    resp = client.post("/api/resume/upload", files={"file": ("sample.pdf", create_sample_pdf("test"), "application/pdf")})
    assert resp.status_code == 401
    print("[PASS] Unauthenticated upload blocked")

    print("\n=========================================")
    print("ALL RESUME TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_resume_flow()
