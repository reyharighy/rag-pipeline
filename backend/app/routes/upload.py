import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app import STORAGE_DIR

router = APIRouter()

ALLOWED_TYPES = ["application/pdf", "text/plain"]

def check_file_compatibility(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        return {
            "status_code": 400,
            "detail": "Only PDF and TXT allowed",
        }

    return True

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_compatibility = check_file_compatibility(file)

    if file_compatibility is True:
        file_path = STORAGE_DIR / Path(file.filename or "no-filename")

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": file.filename,
            "message": "File uploaded successfully"
        }

    raise HTTPException(**file_compatibility)
