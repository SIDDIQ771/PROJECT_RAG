from retrieval.intent_parser import parse_intent
from retrieval.query_rewriter import rewrite_query

# ✅ Raised slightly from 0.70 to 0.75 — was rejecting exact issue key matches
# that scored just above 0.70 (e.g. RAG-7 scored 0.7014)
JIRA_DISTANCE_THRESHOLD = 0.75
DOC_DISTANCE_THRESHOLD  = 0.80
VIDEO_DISTANCE_THRESHOLD = 0.80


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
        # ✅ For exact issue key matches, skip distance filter entirely
        # — if the user typed RAG-7 explicitly, always return it
        docs_and_metas = list(zip(results["documents"][0], results["metadatas"][0]))
        if not docs_and_metas:
            return None, []
        return docs_and_metas[0][0], [f"JIRA-{key}"]

    # 3. Expand query for better semantic matching
    expanded_query = rewrite_query(query)

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
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            src = meta.get("source", "")
            if src.startswith("DOC-") and dist <= DOC_DISTANCE_THRESHOLD:
                hits.append((doc, meta))
            elif src.startswith("VIDEO-") and dist <= VIDEO_DISTANCE_THRESHOLD:
                hits.append((doc, meta))
            elif (src.startswith("JIRA-") or src.startswith("CONFLUENCE-")) \
                    and dist <= JIRA_DISTANCE_THRESHOLD:
                hits.append((doc, meta))

    if not hits:
        return None, []

    grouped = {}
    for doc, meta in hits:
        src = meta.get("source", "unknown")
        grouped.setdefault(src, []).append(doc)

    if len(grouped) == 1:
        src = list(grouped.keys())[0]
        return "\n\n".join(grouped[src]), [src]

    combined = "\n\n".join(t for group in grouped.values() for t in group)
    return combined, list(grouped.keys())