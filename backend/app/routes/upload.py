from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

ALLOWED_TYPES = ["application/pdf", "text/plain"]

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT allowed",
        )

    return {
        "filename": file.filename,
        "message": "File uploaded successfully"
    }
