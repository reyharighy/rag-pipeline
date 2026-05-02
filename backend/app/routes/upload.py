import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from rq.job import Job

from app import STORAGE_DIR, pipeline_queue, redis_conn, process_file

router = APIRouter()

ALLOWED_TYPES = ["application/pdf", "text/plain"]
JOB_TIMEOUT = 5 * 60

def check_file_compatibility(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        return {
            "status_code": 400,
            "detail": "Only PDF and TXT allowed",
        }

    return True

def fetch_jobs(ids: list[str], status: str):
    jobs = Job.fetch_many(
        ids,
        connection=redis_conn
    )

    return [
        {
            "job_id": job.id,
            "status": status,
            "filename": job.args[1] if job.args else None,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
        }

        for job in jobs if job is not None
    ]

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_compatibility = check_file_compatibility(file)

    if file_compatibility is True:
        file_path = STORAGE_DIR / Path(str(file.filename))

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        pipeline_queue.enqueue(
            process_file,
            file_path,
            file.filename,
            file.content_type,
            job_timeout=JOB_TIMEOUT,
        )

        return {
            "file_name": file.filename,
            "message": "File uploaded successfully"
        }

    raise HTTPException(**file_compatibility)

@router.get("/upload/jobs")
def get_all_jobs():
    queued_ids   = pipeline_queue.job_ids
    started_ids  = pipeline_queue.started_job_registry.get_job_ids()
    finished_ids = pipeline_queue.finished_job_registry.get_job_ids()
    failed_ids   = pipeline_queue.failed_job_registry.get_job_ids()

    return {
        "queued":   fetch_jobs(queued_ids, "queued"),
        "started":  fetch_jobs(started_ids, "started"),
        "finished": fetch_jobs(finished_ids, "finished"),
        "failed":   fetch_jobs(failed_ids, "failed"),
    }
