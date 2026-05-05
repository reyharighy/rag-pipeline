import os
from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL is None:
    raise ValueError("'REDIS_URL' is not found")

job_queue_conn = Redis.from_url(REDIS_URL)
file_embedding_queue = Queue(name="file_embedding_queue", connection=job_queue_conn)
