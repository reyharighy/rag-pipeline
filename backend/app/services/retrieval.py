import os

_RAW = os.getenv("RETRIEVAL_TOP_K", "8").strip()

try:
    RETRIEVAL_TOP_K = int(_RAW)
except ValueError as err:
    raise ValueError("RETRIEVAL_TOP_K must be an integer") from err

if RETRIEVAL_TOP_K < 1:
    raise ValueError("RETRIEVAL_TOP_K must be >= 1")
