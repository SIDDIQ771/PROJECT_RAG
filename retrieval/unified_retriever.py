from retrieval.intent_parser import parse_intent
from retrieval.query_rewriter import rewrite_query

# Threshold for JIRA/Confluence — tighter since these are structured
JIRA_DISTANCE_THRESHOLD = 0.70

# Threshold for docs — looser to catch rare single mentions deep in large docs
DOC_DISTANCE_THRESHOLD = 0.80

# Global threshold for mixed queries
GLOBAL_DISTANCE_THRESHOLD = 0.75


def _filter(results: dict, threshold: float) -> list[tuple[str, dict]]:
    return [
        (doc, meta)
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
        if dist <= threshold
    ]


def unified_retrieve(query: str, db):
    intent = parse_intent(query)

    # 1. Lookup ticket intent → JIRA-only semantic search
    if intent["lookup_ticket"]:
        results = db.query(query_texts=[query], n_results=10,
                           include=["documents", "metadatas", "distances"])
        if not results["metadatas"] or not results["metadatas"][0]:
            return None, []

        jira_hits = [
            (doc, meta)
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
            if meta.get("source", "").startswith("JIRA-") and dist <= JIRA_DISTANCE_THRESHOLD
        ]
        if not jira_hits:
            return None, []

        top_doc, top_meta = jira_hits[0]
        issue_key = top_meta.get("issue_key", "")
        summary   = top_meta.get("summary", "No summary available.")
        status    = top_meta.get("status", "")
        assignee  = top_meta.get("assignee", "Unassigned")

        return (
            f"JIRA-{issue_key} — {summary}\n"
            f"Status: {status} | Assignee: {assignee}"
        ), [f"JIRA-{issue_key}"]

    # 2. Issue key present → exact match
    if intent["issue_key"]:
        key = intent["issue_key"]
        results = db.query(query_texts=[key], n_results=5,
                           where={"issue_key": {"$eq": key}},
                           include=["documents", "metadatas", "distances"])
        if not results["documents"] or not results["documents"][0]:
            return None, []
        hits = _filter(results, JIRA_DISTANCE_THRESHOLD)
        if not hits:
            return None, []
        return hits[0][0], [f"JIRA-{key}"]

    # 3. Expand query for better semantic matching
    expanded_query = rewrite_query(query)

    # ✅ Fetch more results — critical for rare single mentions in large docs
    results = db.query(query_texts=[expanded_query], n_results=20,
                       include=["documents", "metadatas", "distances"])

    if not results["documents"] or not results["documents"][0]:
        return None, []

    # 4. Resource-specific filtering with appropriate thresholds
    if intent["resource"] == "docs":
        hits = [(doc, meta) for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0])
                if meta.get("source", "").startswith("DOC-")
                and dist <= DOC_DISTANCE_THRESHOLD]

    elif intent["resource"] == "confluence":
        hits = [(doc, meta) for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0])
                if meta.get("source", "").startswith("CONFLUENCE-")
                and dist <= JIRA_DISTANCE_THRESHOLD]

    else:
        # Global — use per-source thresholds
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            src = meta.get("source", "")
            if src.startswith("DOC-") and dist <= DOC_DISTANCE_THRESHOLD:
                hits.append((doc, meta))
            elif (src.startswith("JIRA-") or src.startswith("CONFLUENCE-")) \
                    and dist <= JIRA_DISTANCE_THRESHOLD:
                hits.append((doc, meta))

    if not hits:
        return None, []

    # Group by source
    grouped = {}
    for doc, meta in hits:
        src = meta.get("source", "unknown")
        grouped.setdefault(src, []).append(doc)

    if len(grouped) == 1:
        src = list(grouped.keys())[0]
        return "\n\n".join(grouped[src]), [src]

    combined = "\n\n".join(t for group in grouped.values() for t in group)
    return combined, list(grouped.keys())