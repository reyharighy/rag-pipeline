from abc import ABC, abstractmethod
from typing import Any, Optional

from psycopg.errors import DuplicateTable


class Table(ABC):
    def is_duplicate_table_error(self, exc: BaseException) -> bool:
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

    @abstractmethod
    def create_table(self) -> None: ...

    @abstractmethod
    def add(self, entry: Any) -> None: ...

    @abstractmethod
    def get(self, query: Optional[Any]) -> Any: ...
