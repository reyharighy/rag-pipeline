import os
from redis import Redis
from rq import Queue

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(redis_url)

pipeline_queue = Queue(name="pipeline", connection=redis_conn)
