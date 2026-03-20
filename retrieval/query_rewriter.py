# query_rewriter.py — lightweight rewriter using simple heuristics
# Replaced flan-t5 rewriting (adds 3-5s latency) with fast rule-based expansion

def rewrite_query(query: str) -> str:
    """
    Fast rule-based query expansion — no LLM needed.
    Expands common short queries into more searchable forms.
    """
    q = query.strip()

    # Already a detailed query — return as-is
    if len(q.split()) >= 6:
        return q

    # Expand common short patterns
    expansions = {
        "requirements": "project requirements specifications features",
        "architecture": "system architecture design components",
        "status": "current status progress update",
        "bugs": "bug issues errors problems",
        "timeline": "project timeline schedule milestones deadline",
    }

    q_lower = q.lower()
    for keyword, expansion in expansions.items():
        if keyword in q_lower:
            return f"{q} {expansion}"

    return q