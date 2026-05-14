import json
import logging

from fastapi import APIRouter, Response

from app.health_checks import (
    ModelStatus,
    WorkerStatus,
    StorageStatus,
    VectorDbStatus,
    check_worker,
    check_storage,
    check_vector_db,
    get_cached_provider_model_statuses,
)

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


def _log_component(
    comp: ModelStatus | VectorDbStatus | WorkerStatus,
) -> dict[str, str | None]:
    out: dict[str, str | None] = {"status": comp["status"]}

    if "name" in comp:
        out["name"] = comp["name"]

    if comp["status"] != "ok" and comp.get("detail"):
        out["detail"] = comp["detail"]

    if "probe" in comp:
        out["probe"] = comp["probe"]

    if "last_live_probe_at" in comp:
        out["last_live_probe_at"] = comp["last_live_probe_at"]

    return out


def _log_storage(comp: StorageStatus) -> dict[str, str | int | None]:
    out: dict[str, str | int | None] = {
        "status": comp["status"],
        "file_count": comp.get("file_count"),
    }

    if comp["status"] != "ok" and comp.get("detail"):
        out["detail"] = comp["detail"]

    return out


@router.get("/health")
def check_health(response: Response):
    embedding, llm = get_cached_provider_model_statuses()
    vector_db = check_vector_db()
    worker = check_worker()
    storage = check_storage()

    all_ok = (
        embedding["status"] == "ok"
        and llm["status"] == "ok"
        and vector_db["status"] == "ok"
        and worker["status"] == "ok"
        and storage["status"] == "ok"
    )

    if not all_ok:
        response.status_code = 503

    body: dict = {
        "status": "healthy" if all_ok else "unhealthy",
        "model": {
            "embedding": embedding,
            "llm": llm,
        },
        "vector_db": vector_db,
        "worker": worker,
        "storage": storage,
    }

    http_status = 200 if all_ok else 503

    log_record = {
        "event": "health_check",
        "http_status": http_status,
        "overall": body["status"],
        "model": {
            "embedding": _log_component(embedding),
            "llm": _log_component(llm),
        },
        "vector_db": _log_component(vector_db),
        "worker": _log_component(worker),
        "storage": _log_storage(storage),
    }

    log_line = json.dumps(log_record, ensure_ascii=False, separators=(",", ":"))

    if all_ok:
        logger.info("%s", log_line)
    else:
        logger.warning("%s", log_line)

    return body
