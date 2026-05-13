from redis import Redis
from rq import Queue

from app.config import get_settings

_job_queue_cfg = get_settings().job_queue

job_queue_conn = Redis.from_url(_job_queue_cfg.url)
file_embedding_queue = Queue(name="file_embedding_queue", connection=job_queue_conn)
