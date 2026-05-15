from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.storage import STORAGE_DIR
from app.config import get_settings


class ComponentStatus(TypedDict):
    status: Literal["ok", "error"]
    detail: str | None


class ModelStatus(ComponentStatus, total=False):
    name: str
    probe: Literal["live", "cached"]
    last_live_probe_at: str


class VectorDbStatus(ComponentStatus, total=False):
    name: str


class WorkerStatus(ComponentStatus, total=False):
    name: str


class StorageStatus(TypedDict):
    status: Literal["ok", "error"]
    detail: str | None
    file_count: int | None


_provider_lock = threading.Lock()
_provider_cache_expires_at: float | None = None
_cached_embedding: ModelStatus | None = None
_cached_llm: ModelStatus | None = None
_cached_provider_probe_iso: str | None = None

_database_cfg = get_settings().database
_job_queue_cfg = get_settings().job_queue
_embedding_cfg = get_settings().embedding


def _parse_provider_cache_ttl_seconds() -> float:
    raw = os.getenv("HEALTH_PROVIDER_CACHE_TTL_SECONDS", "300").strip()

    try:
        v = float(raw)
    except ValueError:
        return 300.0
    return max(0.0, v)


def _annotate_model_probe(
    base: ModelStatus, probe: Literal["live", "cached"], iso: str
) -> ModelStatus:
    out: ModelStatus = {**base, "probe": probe, "last_live_probe_at": iso}
    return out


def _truncate(msg: str, max_len: int = 240) -> str:
    msg = msg.strip()

    if len(msg) <= max_len:
        return msg

    return msg[: max_len - 3] + "..."


def _count_storage_files(root: Path) -> int:
    if not root.is_dir():
        return 0

    return sum(1 for p in root.iterdir() if p.is_file() and p.name != "__init__.py")


def check_embedding_model() -> ModelStatus:
    from app.services.embedding import get_embedding_service

    try:
        emb = get_embedding_service()
        emb.embed_query("health")
    except Exception as e:  # noqa: BLE001 — surface any provider/transport failure
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "name": _embedding_cfg.model,
        }

    return {
        "status": "ok",
        "detail": None,
        "name": _embedding_cfg.model,
    }


def check_llm_model() -> ModelStatus:
    from app.services.language_model import (
        LLM_MODEL,
        get_language_model,
        with_retry_exception,
    )

    try:
        from langchain_core.messages import HumanMessage

        llm = with_retry_exception(get_language_model(max_tokens=8))
        llm.invoke([HumanMessage(content="ping")])
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "name": LLM_MODEL,
        }

    return {
        "status": "ok",
        "detail": None,
        "name": LLM_MODEL,
    }


def check_vector_db() -> VectorDbStatus:
    engine = create_engine(_database_cfg.url, poolclass=NullPool)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "name": "pgvector",
        }
    finally:
        engine.dispose()

    return {"status": "ok", "detail": None, "name": "pgvector"}


def check_worker() -> WorkerStatus:
    from redis import Redis

    client: Redis | None = None

    try:
        client = Redis.from_url(
            _job_queue_cfg.url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

        client.ping()
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "name": "redis-queue",
        }
    finally:
        if client is not None:
            client.close()

    return {"status": "ok", "detail": None, "name": "redis-queue"}


def check_storage() -> StorageStatus:
    root = STORAGE_DIR

    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "file_count": None,
        }

    if not os.access(root, os.W_OK):
        return {
            "status": "error",
            "detail": f"storage path is not writable: {root}",
            "file_count": None,
        }

    probe = root / f".health_probe_{uuid.uuid4().hex}"

    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as e:
        return {
            "status": "error",
            "detail": _truncate(str(e)),
            "file_count": None,
        }

    return {
        "status": "ok",
        "detail": None,
        "file_count": _count_storage_files(root),
    }


def get_cached_provider_model_statuses() -> tuple[ModelStatus, ModelStatus]:
    global \
        _cached_embedding, \
        _cached_llm, \
        _cached_provider_probe_iso, \
        _provider_cache_expires_at

    ttl = _parse_provider_cache_ttl_seconds()
    iso_now = datetime.now(timezone.utc).isoformat()

    if ttl <= 0:
        emb = check_embedding_model()
        llm = check_llm_model()

        return _annotate_model_probe(emb, "live", iso_now), _annotate_model_probe(
            llm, "live", iso_now
        )

    now = time.monotonic()

    with _provider_lock:
        if (
            _provider_cache_expires_at is not None
            and now < _provider_cache_expires_at
            and _cached_embedding is not None
            and _cached_llm is not None
            and _cached_provider_probe_iso is not None
        ):
            iso = _cached_provider_probe_iso

            return (
                _annotate_model_probe(_cached_embedding, "cached", iso),
                _annotate_model_probe(_cached_llm, "cached", iso),
            )

        emb = check_embedding_model()
        llm = check_llm_model()
        _cached_embedding = emb
        _cached_llm = llm
        _cached_provider_probe_iso = iso_now
        _provider_cache_expires_at = now + ttl

        return (
            _annotate_model_probe(emb, "live", iso_now),
            _annotate_model_probe(llm, "live", iso_now),
        )
