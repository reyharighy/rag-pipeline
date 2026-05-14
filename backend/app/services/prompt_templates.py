from __future__ import annotations

import logging
import re
from typing import Final

from app.prompts import PROMPTS_DEFAULTS_DIR
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
_database_cfg = get_settings().database

REFINE_SYSTEM: Final = "refine_system"
RESPONSE_SYSTEM: Final = "response_system"
RESPONSE_USER: Final = "response_user"
_REFINE_USER_FILE_KEY: Final = "refine_user"

TEMPLATE_KEYS: Final[tuple[str, ...]] = (
    REFINE_SYSTEM,
    RESPONSE_SYSTEM,
    RESPONSE_USER,
)

_REQUIRED_PLACEHOLDERS: dict[str, frozenset[str]] = {
    RESPONSE_USER: frozenset({"context", "question"}),
}

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def _read_default_file(key: str) -> str:
    path = PROMPTS_DEFAULTS_DIR / f"{key}.txt"

    if not path.is_file():
        raise FileNotFoundError(f"Missing default prompt file: {path}")

    return path.read_text(encoding="utf-8")


def init_prompt_templates_table() -> None:
    with _database_cfg.psycopg_connection.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_templates (
                template_key TEXT PRIMARY KEY,
                body TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    _database_cfg.psycopg_connection.commit()
    logger.info("Prompt templates table is ready (CREATE IF NOT EXISTS).")


def seed_prompt_templates_if_needed() -> None:
    for key in TEMPLATE_KEYS:
        with _database_cfg.psycopg_connection.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM prompt_templates WHERE template_key = %s",
                (key,),
            )

            if cur.fetchone() is not None:
                continue

            body = _read_default_file(key)

            cur.execute(
                """
                INSERT INTO prompt_templates (template_key, body)
                VALUES (%s, %s)
                """,
                (key, body),
            )

    _database_cfg.psycopg_connection.commit()
    logger.info("Prompt templates seeded from defaults where missing.")


def get_refinement_user_message_template() -> str:
    return _read_default_file(_REFINE_USER_FILE_KEY)


def list_prompt_templates() -> list[dict[str, str]]:
    with _database_cfg.psycopg_connection.cursor() as cur:
        cur.execute(
            """
            SELECT template_key, body, updated_at::text
            FROM prompt_templates
            WHERE template_key = ANY(%s)
            ORDER BY template_key
            """,
            (list(TEMPLATE_KEYS),),
        )

        rows = cur.fetchall()

    return [{"key": row[0], "body": row[1], "updated_at": row[2]} for row in rows]


def get_template_body(key: str) -> str:
    if key not in TEMPLATE_KEYS:
        raise KeyError(key)

    with _database_cfg.psycopg_connection.cursor() as cur:
        cur.execute(
            "SELECT body FROM prompt_templates WHERE template_key = %s",
            (key,),
        )

        row = cur.fetchone()

    if row is None:
        raise LookupError(f"Prompt template not found in database: {key}")

    return str(row[0])


def validate_template_placeholders(key: str, body: str) -> None:
    required = _REQUIRED_PLACEHOLDERS.get(key)

    if required is None:
        return

    found = frozenset(_PLACEHOLDER_RE.findall(body))
    missing = required - found

    if missing:
        names = ", ".join(sorted(f"{{{{{n}}}}}" for n in missing))
        raise ValueError(f"Template {key!r} must include placeholders: {names}")


def set_template_body(key: str, body: str) -> None:
    if key not in TEMPLATE_KEYS:
        raise KeyError(key)

    validate_template_placeholders(key, body)

    with _database_cfg.psycopg_connection.cursor() as cur:
        cur.execute(
            """
            UPDATE prompt_templates
            SET body = %s, updated_at = NOW()
            WHERE template_key = %s
            """,
            (body, key),
        )

        if cur.rowcount != 1:
            raise LookupError(f"Prompt template not found for update: {key}")

    _database_cfg.psycopg_connection.commit()


def render_mustache_template(template: str, variables: dict[str, str]) -> str:
    names_in_template = set(_PLACEHOLDER_RE.findall(template))
    missing = names_in_template - set(variables.keys())

    if missing:
        raise ValueError(
            "Missing values for placeholders: "
            + ", ".join(sorted(f"{{{{{n}}}}}" for n in missing))
        )

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)

        return variables[name]

    return _PLACEHOLDER_RE.sub(repl, template)
