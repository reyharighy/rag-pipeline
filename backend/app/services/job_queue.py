import os
from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL is None:
    raise ValueError("'REDIS_URL' is not found")


def _embed_job_result_ttl() -> int:
    raw = os.getenv("EMBED_JOB_RESULT_TTL", "-1").strip().lower()

    if raw in ("", "-1", "forever"):
        return -1

    return int(raw)


EMBED_JOB_RESULT_TTL = _embed_job_result_ttl()

job_queue_conn = Redis.from_url(REDIS_URL)
file_embedding_queue = Queue(name="file_embedding_queue", connection=job_queue_conn)
