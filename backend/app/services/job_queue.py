import os
from redis import Redis
from rq import Queue

redis_url = os.getenv("REDIS_URL", None)

if redis_url is None:
    raise ValueError("'REDIS_URL' is not found")

job_queue_conn = Redis.from_url(redis_url)
file_embedding_queue = Queue(name="file_embedding_queue", connection=job_queue_conn)
