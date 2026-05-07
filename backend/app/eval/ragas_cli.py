from __future__ import annotations

from pathlib import Path


def _load_dotenv() -> None:
    from dotenv import find_dotenv, load_dotenv

    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    repo_root = here.parents[3]

    candidates = [
        Path.cwd() / ".env",
        backend_root / ".env",
        repo_root / ".env",
    ]

    found = find_dotenv(usecwd=True)

    if found:
        candidates.append(Path(found))

    seen: set[Path] = set()

    for path in candidates:
        resolved = path.resolve()

        if resolved in seen:
            continue

        seen.add(resolved)

        if resolved.is_file():
            load_dotenv(resolved, override=False)


def _ensure_database_url() -> None:
    import os
    from urllib.parse import quote_plus

    if (os.getenv("DATABASE_URL") or "").strip():
        return

    user = os.getenv("POSTGRES_USER")
    db = os.getenv("POSTGRES_DB")

    if not user or not db:
        return

    password = os.getenv("POSTGRES_PASSWORD", "")
    host = (os.getenv("POSTGRES_HOST") or "localhost").strip()
    port = (os.getenv("POSTGRES_PORT") or "5432").strip()
    user_q = quote_plus(user)
    pass_q = quote_plus(password)

    os.environ["DATABASE_URL"] = (
        f"postgresql+psycopg://{user_q}:{pass_q}@{host}:{port}/{db}"
    )


def _ensure_redis_url() -> None:
    """Compose sets ``REDIS_URL`` for containers; host CLI often lacks it in ``.env``."""
    import os

    if (os.getenv("REDIS_URL") or "").strip():
        return

    host = (os.getenv("REDIS_HOST") or "localhost").strip()
    port = (os.getenv("REDIS_PORT") or "6379").strip()
    os.environ["REDIS_URL"] = f"redis://{host}:{port}/0"


_load_dotenv()
_ensure_database_url()
_ensure_redis_url()

import argparse
import json
import logging
import math
from typing import Any

from datasets import Dataset
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.dataset_schema import EvaluationResult
from ragas.metrics._answer_relevance import answer_relevancy
from ragas.metrics._faithfulness import faithfulness
from ragas.run_config import RunConfig

from app.agent import Context, Graph, get_initial_state
from app.services import get_embedding_service
from app.services.language_model import LLM_MODEL
from app.utils import last_assistant_text, texts_from_documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("ragas_eval")


def _eval_dir() -> Path:
    return Path(__file__).resolve().parent


def _aggregate_metric_means(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {}

    keys = rows[0].keys()
    out: dict[str, float] = {}

    for k in keys:
        vals: list[float] = []

        for r in rows:
            v = r.get(k)

            if v is None:
                continue

            fv = float(v)

            if math.isnan(fv):
                continue

            vals.append(fv)

        out[k] = sum(vals) / len(vals) if vals else float("nan")

    return out


def load_questions(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    qs = raw.get("questions")

    if not isinstance(qs, list) or not all(isinstance(q, str) for q in qs):
        raise ValueError("JSON must contain a 'questions' array of strings")

    stripped = [q.strip() for q in qs if q.strip()]

    if not stripped:
        raise ValueError("No non-empty questions in file")

    return stripped


def run_rag_batch(questions: list[str]) -> tuple[list[str], list[str], list[list[str]]]:
    graph = Graph().build_graph()
    ctx = Context(history_messages=[])

    user_inputs: list[str] = []
    responses: list[str] = []
    all_contexts: list[list[str]] = []

    for i, q in enumerate(questions):
        logger.info("RAG inference %s/%s", i + 1, len(questions))
        state = get_initial_state(q)
        result = graph.invoke(state, context=ctx)
        docs = result.get("relevant_docs")

        if not isinstance(docs, list):
            docs = None

        user_inputs.append(q)
        responses.append(last_assistant_text(result["messages"]))
        all_contexts.append(texts_from_documents(docs))

    return user_inputs, responses, all_contexts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RAGAS evaluation on LangGraph RAG pipeline"
    )

    p.add_argument(
        "--questions",
        type=Path,
        default=_eval_dir() / "questions.sample.json",
        help='JSON file with {"questions": ["...", ...]}',
    )

    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON report (scores + per-row metrics) to this path",
    )

    p.add_argument(
        "--ragas-model",
        default=None,
        help="Groq model id for RAGAS judge LLM (default: LLM_MODEL env / language_model default)",
    )

    return p.parse_args()


def main() -> int:
    args = parse_args()
    questions_path = args.questions.resolve()

    if not questions_path.is_file():
        logger.error("Questions file not found: %s", questions_path)
        return 1

    questions = load_questions(questions_path)
    logger.info("Loaded %s questions from %s", len(questions), questions_path)

    user_inputs, responses, retrieved_contexts = run_rag_batch(questions)

    eval_dataset = Dataset.from_dict(
        {
            "user_input": user_inputs,
            "response": responses,
            "retrieved_contexts": retrieved_contexts,
        }
    )

    judge_model = args.ragas_model or LLM_MODEL

    llm = ChatGroq(
        model=judge_model,
        temperature=0,
        reasoning_format="parsed",
        reasoning_effort="low",
    )

    emb = get_embedding_service()
    run_config = RunConfig(timeout=180, seed=42)

    logger.info(
        "Running RAGAS (faithfulness, answer_relevancy), judge model=%s", judge_model
    )

    result = evaluate(
        eval_dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=llm,
        embeddings=emb,
        run_config=run_config,
        raise_exceptions=True,
    )

    if not isinstance(result, EvaluationResult):
        raise TypeError("expected EvaluationResult from ragas.evaluate()")

    print(result)

    if args.output:
        report = {
            "questions_file": str(questions_path),
            "judge_model": judge_model,
            "aggregate": _aggregate_metric_means(result.scores),
            "scores": result.scores,
            "samples": [
                {
                    "user_input": u,
                    "response": r,
                    "context_chunks": len(c),
                }
                for u, r, c in zip(user_inputs, responses, retrieved_contexts)
            ],
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Wrote report to %s", args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
