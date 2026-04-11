def rewrite_query(query: str) -> str:
    """
    Fast rule-based query expansion — expands queries to better match stored chunks.
    """
    q = query.strip()
    q_lower = q.lower()

    expansions = {
        "objective":      "objectives goals aims purpose of the project",
        "requirement":    "project requirements specifications features functional",
        "architecture":   "system architecture design components structure",
        "status":         "current status progress update",
        "bug":            "bug issues errors problems defects",
        "timeline":       "project timeline schedule milestones deadline",
        "scope":          "project scope boundaries deliverables",
        "design":         "design architecture approach methodology",
        "implementation": "implementation development coding solution",
        "evaluation":     "evaluation metrics validation testing results",
        "ingestion":      "ingestion pipeline data loading processing",
        "retrieval":      "retrieval search query semantic vector",
        "background":     "background context motivation problem statement",
        "requirements":   "project requirements specifications features",
        "architecture":   "system architecture design components",
        "bugs":           "bug issues errors problems",
        "timeline":       "project timeline schedule milestones deadline",
    }

    for keyword, expansion in expansions.items():
        if keyword in q_lower:
            return f"{q} {expansion}"

    # Already detailed — return as-is
    if len(q.split()) >= 6:
        return q

    return q