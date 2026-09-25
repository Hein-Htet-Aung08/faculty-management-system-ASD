import json
from pathlib import Path

from rag_pipeline import retrieve_context

RESULTS_FILE = Path(__file__).resolve().parent / "eval_results.json"


def precision_at_k(retrieved_ids, relevant_ids, k=5):
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(top_k)


def recall_at_k(retrieved_ids, relevant_ids, k=5):
    if not relevant_ids:
        return None
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def run_evaluation(eval_queries, k=5):
    results = []
    for item in eval_queries:
        retrieved = retrieve_context(item["query"], k=k)
        retrieved_ids = [r["id"] for r in retrieved]
        p = precision_at_k(retrieved_ids, item["relevant_ids"], k=k)
        r = recall_at_k(retrieved_ids, item["relevant_ids"], k=k)
        results.append(
            {
                "query": item["query"],
                "precision_at_k": p,
                "recall_at_k": r,
                "retrieved_ids": retrieved_ids,
                "relevant_ids": item["relevant_ids"],
            }
        )
    return results


def summarize(results):
    scored = [r for r in results if r["relevant_ids"]]
    avg_p = sum(r["precision_at_k"] for r in scored) / len(scored)
    avg_r = sum(r["recall_at_k"] for r in scored) / len(scored)
    return {"avg_precision_at_5": avg_p, "avg_recall_at_5": avg_r, "n_queries": len(scored)}


if __name__ == "__main__":
    from eval_queries import EVAL_QUERIES

    results = run_evaluation(EVAL_QUERIES)
    summary = summarize(results)

    print("Per-query results:")
    for r in results:
        recall_display = f"{r['recall_at_k']:.2f}" if r["recall_at_k"] is not None else "N/A (no-answer query)"
        print(f"  '{r['query']}' -> P@5={r['precision_at_k']:.2f}, R@5={recall_display}")

    print("\nSummary:", summary)

    RESULTS_FILE.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
    print(f"\nResults saved to {RESULTS_FILE}")
