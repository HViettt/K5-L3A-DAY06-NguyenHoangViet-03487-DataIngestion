"""Evaluate retrieved evidence and preserve per-query traces."""
from typing import Any
import unicodedata


def clean_text_for_match(text: str) -> str:
    """Normalize Unicode and whitespace for robust substring matching."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", text)
    return " ".join(norm.split()).lower()


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and gold evidence; record hit@1 and hit@3 trace."""
    gold_page = question["gold_page"]
    gold_evidence = clean_text_for_match(question.get("evidence_quote", ""))
    
    evaluated_hits = []
    hit_at_1 = False
    hit_at_3 = False
    
    for rank, hit in enumerate(hits, start=1):
        hit_page = hit.get("page")
        hit_text_clean = clean_text_for_match(hit.get("text", ""))
        
        # Check criteria: same page and contains gold evidence substring
        is_page_match = (hit_page == gold_page)
        is_evidence_match = (gold_evidence in hit_text_clean) if gold_evidence else False
        is_valid_hit = is_page_match and is_evidence_match
        
        if rank == 1 and is_valid_hit:
            hit_at_1 = True
        if rank <= 3 and is_valid_hit:
            hit_at_3 = True
            
        evaluated_hits.append({
            "rank": rank,
            "chunk_id": hit.get("chunk_id"),
            "page": hit_page,
            "score": hit.get("score"),
            "distance": hit.get("distance"),
            "is_page_match": is_page_match,
            "is_evidence_match": is_evidence_match,
            "is_valid_hit": is_valid_hit,
            "text_snippet": hit.get("text", "")[:200]
        })
        
    return {
        "id": question["id"],
        "split": question.get("split", "dev"),
        "type": question.get("type", "direct"),
        "question": question["question"],
        "gold_page": gold_page,
        "evidence_quote": question.get("evidence_quote", ""),
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hits": evaluated_hits
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    splits = ["all", "dev", "test"]
    summary = {}
    
    for sp in splits:
        if sp == "all":
            subset = traces
        else:
            subset = [t for t in traces if t["split"] == sp]
            
        total = len(subset)
        if total == 0:
            summary[sp] = {
                "total": 0,
                "hit1_count": 0,
                "hit1_rate": 0.0,
                "hit3_count": 0,
                "hit3_rate": 0.0
            }
            continue
            
        hit1_cnt = sum(1 for t in subset if t["hit_at_1"])
        hit3_cnt = sum(1 for t in subset if t["hit_at_3"])
        
        summary[sp] = {
            "total": total,
            "hit1_count": hit1_cnt,
            "hit1_ratio": f"{hit1_cnt}/{total}",
            "hit1_rate": round(hit1_cnt / total, 4),
            "hit3_count": hit3_cnt,
            "hit3_ratio": f"{hit3_cnt}/{total}",
            "hit3_rate": round(hit3_cnt / total, 4)
        }
        
    return summary
