import os
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from text_extractor import extract_text
from validator import validate_document, load_references, supported_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Extract + cache all reference documents once when the server starts.
    load_references()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/supported-categories")
async def get_supported_categories():
    """
    Categories that currently have a reference template loaded
    (i.e. a matching <CODE>_Template.pdf/docx file exists in reference/).
    The frontend uses this to flag which categories are ready to validate.
    """
    return {"supported_categories": supported_categories()}


@app.post("/validate-document")
async def validate_uploaded_document(
    category: str = Form(...),
    file: UploadFile = File(...),
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text(file_path, file.filename.lower())

    if not extracted_text:
        return {
            "predicted_category": "N/A",
            "confidence": 0,
            "structure_score": 0,
            "content_score": 0,
            "decision": "REJECT",
            "reason": "No extractable text found. File may be empty, scanned, corrupted, or password-protected.",
            "missing_sections": [],
            "is_spam_or_irrelevant": True,
        }

    result = validate_document(category, extracted_text)
    return result