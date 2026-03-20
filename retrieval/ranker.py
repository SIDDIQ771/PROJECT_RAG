def rank_results(results):
    ranked = []
    for r in results:
        # Cosine distance is 0-2; score = 1 - distance gives -1 to 1
        # Clamp to 0 minimum so score is always non-negative
        score = max(0.0, 1 - r["distance"])
        ranked.append({**r, "score": round(score, 4)})
    return sorted(ranked, key=lambda x: x["score"], reverse=True)