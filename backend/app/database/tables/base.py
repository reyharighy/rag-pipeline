from abc import ABC, abstractmethod
from typing import Any, Optional

from psycopg.errors import DuplicateTable


class Table(ABC):
    @staticmethod
    def is_duplicate_table_error(exc: BaseException) -> bool:
        seen: set[int] = set()
        cur: BaseException | None = exc

        while cur is not None and len(seen) < 16:
            if id(cur) in seen:
                break

            seen.add(id(cur))

            if isinstance(cur, DuplicateTable):
                return True

            nxt = getattr(cur, "orig", None)

            if isinstance(nxt, BaseException):
                cur = nxt
                continue

            cur = cur.__cause__

        msg = str(exc).lower()

        return "already exists" in msg and "relation" in msg

    @staticmethod
    def create_table() -> None: ...

    @abstractmethod
    def add(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def get(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def similarity_search(self, **kwargs: Any) -> Any: ...
