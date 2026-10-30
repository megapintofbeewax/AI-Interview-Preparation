import os
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract readable text content from PDF or DOCX file.
    """
    text = ""
    try:
        if file_type == "pdf":
            reader = PdfReader(file_path)
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            text = "\n".join(pages_text).strip()

        elif file_type == "docx":
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs).strip()

    except Exception as e:
        print(f"Error parsing resume file {file_path}: {e}")
        text = ""

    return text
