"""
RAG evaluation script — Phase 4 Section 7, computes Precision@5 / NDCG@5
against the golden dataset in data/evaluation/rag_golden_dataset.json.

Usage:
    python scripts/evaluate_rag.py
"""

from __future__ import annotations

import asyncio
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from forgesight.config.database import session_scope
from forgesight.config.logging import get_logger
from forgesight.rag.retrieval import search_technical_sops

logger = get_logger(__name__)

GOLDEN_DATASET_PATH = Path("data/evaluation/rag_golden_dataset.json")
RESULTS_DIR = Path("data/evaluation/results")

PRECISION_AT_K_THRESHOLD = 0.80
NDCG_AT_K_THRESHOLD = 0.75
K = 5


def _dcg(relevances: list[int]) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def _ndcg_at_k(relevances: list[int], k: int) -> float:
    dcg = _dcg(relevances[:k])
    ideal = _dcg(sorted(relevances, reverse=True)[:k])
    return dcg / ideal if ideal > 0 else 0.0


async def evaluate_query(session, item: dict) -> dict:
    query = item["query"]
    expected_documents = set(item["expected_documents"])

    passages = await search_technical_sops(session, query=query)
    retrieved_doc_ids = [p.document_id for p in passages[:K]]

    relevances = [1 if doc_id in expected_documents else 0 for doc_id in retrieved_doc_ids]
    while len(relevances) < K:
        relevances.append(0)

    return {
        "query": query,
        "expected_documents": list(expected_documents),
        "retrieved_documents": retrieved_doc_ids,
        "precision_at_5": sum(relevances) / K,
        "ndcg_at_5": _ndcg_at_k(relevances, K),
    }


async def main() -> None:
    if not GOLDEN_DATASET_PATH.exists():
        logger.error("golden_dataset_not_found", extra={"path": str(GOLDEN_DATASET_PATH)})
        return

    golden_dataset = json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))

    results = []
    async with session_scope() as session:
        for item in golden_dataset:
            results.append(await evaluate_query(session, item))

    avg_precision = sum(r["precision_at_5"] for r in results) / len(results)
    avg_ndcg = sum(r["ndcg_at_5"] for r in results) / len(results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"rag_eval_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["query", "expected_documents", "retrieved_documents", "precision_at_5", "ndcg_at_5"],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    **row,
                    "expected_documents": ";".join(row["expected_documents"]),
                    "retrieved_documents": ";".join(row["retrieved_documents"]),
                }
            )

    logger.info(
        "rag_evaluation_complete",
        extra={
            "avg_precision_at_5": avg_precision,
            "avg_ndcg_at_5": avg_ndcg,
            "precision_threshold_met": avg_precision >= PRECISION_AT_K_THRESHOLD,
            "ndcg_threshold_met": avg_ndcg >= NDCG_AT_K_THRESHOLD,
            "results_file": str(output_path),
        },
    )

    print(f"Average Precision@5: {avg_precision:.3f} (threshold {PRECISION_AT_K_THRESHOLD})")
    print(f"Average NDCG@5:      {avg_ndcg:.3f} (threshold {NDCG_AT_K_THRESHOLD})")
    print(f"Results written to:  {output_path}")


if __name__ == "__main__":
    asyncio.run(main())