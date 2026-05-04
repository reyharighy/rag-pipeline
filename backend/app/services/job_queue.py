import os
from redis import Redis
from rq import Queue

redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
job_queue_conn = Redis.from_url(redis_url)
file_embedding_queue = Queue(name="file_embedding_queue", connection=job_queue_conn)
