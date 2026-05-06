import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from rq.job import Job

from app.storage import STORAGE_DIR
from app.services import EMBED_JOB_RESULT_TTL, file_embedding_queue, job_queue_conn
from app.workers import embed_file_and_store

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


def _enqueue_upload_job(file: UploadFile) -> dict:
    file_compatibility = check_file_compatibility(file)

    if file_compatibility is not True:
        return {"ok": False, **file_compatibility}

    file_path = STORAGE_DIR / Path(str(file.filename))

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_embedding_queue.enqueue(
        embed_file_and_store,
        file_path,
        file.filename,
        file.content_type,
        file_path.stat().st_size,
        job_timeout=JOB_TIMEOUT,
        result_ttl=EMBED_JOB_RESULT_TTL,
    )

    return {"ok": True, "file_name": file.filename}


def fetch_jobs(ids: list[str], status: str):
    jobs = Job.fetch_many(ids, connection=job_queue_conn)
    pipeline_jobs = []

    for job in jobs:
        if job is None:
            continue

        file_metadata = {
            "name": job.args[1],
            "type": job.args[2],
            "size": job.args[3],
        }

        job_metadata = {
            "id": job.id,
            "status": status,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }

        job_result = job.result or {}

        pipeline_jobs.append(
            {
                "file_metadata": file_metadata,
                "job_metadata": job_metadata,
                "job_result": {
                    "chunks": job_result.get("chunks"),
                    "result": job_result.get("result") or {},
                },
            }
        )

    return pipeline_jobs


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    out = _enqueue_upload_job(file)

    if not out["ok"]:
        raise HTTPException(status_code=out["status_code"], detail=out["detail"])

    return {"file_name": out["file_name"], "message": "File uploaded successfully"}


@router.post("/upload/batch")
async def upload_batch(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    succeeded: list[dict] = []
    failed: list[dict] = []

    for file in files:
        out = _enqueue_upload_job(file)
        name = file.filename or "(unnamed)"

        if out["ok"]:
            succeeded.append(
                {"file_name": out["file_name"], "message": "File uploaded successfully"}
            )
        else:
            failed.append({"file_name": name, "detail": out["detail"]})

    return {"succeeded": succeeded, "failed": failed}


@router.get("/upload/jobs")
def get_all_jobs():
    enqueued_ids = file_embedding_queue.job_ids
    started_ids = file_embedding_queue.started_job_registry.get_job_ids()
    finished_ids = file_embedding_queue.finished_job_registry.get_job_ids()
    failed_ids = file_embedding_queue.failed_job_registry.get_job_ids()

    return {
        "enqueued": fetch_jobs(enqueued_ids, "enqueued"),
        "started": fetch_jobs(started_ids, "started"),
        "finished": fetch_jobs(finished_ids, "finished"),
        "failed": fetch_jobs(failed_ids, "failed"),
    }
