import fitz
from docx import Document

def extract_text(file_path: str, filename: str) -> str:
    if filename.endswith(".pdf"):
        text = ""
        pdf = fitz.open(file_path)
        for page in pdf:
            text += page.get_text()
        return text.strip()

    if filename.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs]).strip()

    return ""