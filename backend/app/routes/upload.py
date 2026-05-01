import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app import STORAGE_DIR

router = APIRouter()

ALLOWED_TYPES = ["application/pdf", "text/plain"]

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT allowed",
        )

    if file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="File must have name",
        )

    file_path = STORAGE_DIR / Path(file.filename)

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "message": "File uploaded successfully"
    }
