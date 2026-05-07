from retrieval.intent_parser import parse_intent
from retrieval.query_rewriter import rewrite_query

# ==========================================================
# DISTANCE THRESHOLDS
# Lower distance = better semantic match
# ==========================================================

JIRA_DISTANCE_THRESHOLD = 0.75
DOC_DISTANCE_THRESHOLD = 0.80
VIDEO_DISTANCE_THRESHOLD = 0.80

# ==========================================================
# SOURCE LIMITING
# Prevent noisy multi-source retrieval
# ==========================================================

MAX_SOURCES = 3


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

    # ==========================================================
    # 1. LOOKUP TICKET INTENT → JIRA-ONLY SEARCH
    # ==========================================================

    if intent["lookup_ticket"]:

        results = db.query(
            query_texts=[query],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )

        if not results["metadatas"] or not results["metadatas"][0]:
            return None, []

        jira_hits = []

        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):

            src = meta.get("source", "")

            if src.startswith("JIRA-") and dist <= JIRA_DISTANCE_THRESHOLD:

                similarity = 1 - dist

                print(
                    f"[Retriever] {src} | Distance: {dist:.4f} "
                    f"| Similarity: {similarity:.4f}"
                )

                jira_hits.append((doc, meta, dist))

        if not jira_hits:
            return None, []

        # Sort by best semantic match
        jira_hits.sort(key=lambda x: x[2])

        top_doc, top_meta, top_dist = jira_hits[0]

        issue_key = top_meta.get("issue_key", "")
        summary = top_meta.get("summary", "No summary available.")
        status = top_meta.get("status", "")
        assignee = top_meta.get("assignee", "Unassigned")

        return (
            f"JIRA-{issue_key} — {summary}\n"
            f"Status: {status} | Assignee: {assignee}"
        ), [f"JIRA-{issue_key}"]

    # ==========================================================
    # 2. EXACT ISSUE KEY MATCH
    # ==========================================================

    if intent["issue_key"]:

        key = intent["issue_key"]

        results = db.query(
            query_texts=[key],
            n_results=5,
            where={"issue_key": {"$eq": key}},
            include=["documents", "metadatas", "distances"]
        )

        if not results["documents"] or not results["documents"][0]:
            return None, []

        docs_and_metas = list(
            zip(
                results["documents"][0],
                results["metadatas"][0]
            )
        )

        if not docs_and_metas:
            return None, []

        return docs_and_metas[0][0], [f"JIRA-{key}"]

    # ==========================================================
    # 3. QUERY REWRITING
    # ==========================================================

    expanded_query = rewrite_query(query)

    results = db.query(
        query_texts=[expanded_query],
        n_results=20,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"] or not results["documents"][0]:
        return None, []

    # ==========================================================
    # 4. RESOURCE-SPECIFIC FILTERING
    # ==========================================================

    hits = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):

        src = meta.get("source", "")

        similarity = 1 - dist

        print(
            f"[Retriever] {src} | Distance: {dist:.4f} "
            f"| Similarity: {similarity:.4f}"
        )

        # DOC FILTERING
        if intent["resource"] == "docs":

            if (
                src.startswith("DOC-")
                and dist <= DOC_DISTANCE_THRESHOLD
            ):
                hits.append((doc, meta, dist))

        # CONFLUENCE FILTERING
        elif intent["resource"] == "confluence":

            if (
                src.startswith("CONFLUENCE-")
                and dist <= JIRA_DISTANCE_THRESHOLD
            ):
                hits.append((doc, meta, dist))

        # GENERAL MULTI-SOURCE SEARCH
        else:

            if (
                src.startswith("DOC-")
                and dist <= DOC_DISTANCE_THRESHOLD
            ):
                hits.append((doc, meta, dist))

            elif (
                src.startswith("VIDEO-")
                and dist <= VIDEO_DISTANCE_THRESHOLD
            ):
                hits.append((doc, meta, dist))

            elif (
                src.startswith("JIRA-")
                or src.startswith("CONFLUENCE-")
            ) and dist <= JIRA_DISTANCE_THRESHOLD:

                hits.append((doc, meta, dist))

    if not hits:
        return None, []

    # ==========================================================
    # 5. SORT RESULTS BY BEST MATCH
    # Lower distance = better match
    # ==========================================================

    hits.sort(key=lambda x: x[2])

    # ==========================================================
    # 6. GROUP BY SOURCE
    # ==========================================================

    grouped = {}

    for doc, meta, dist in hits:

        src = meta.get("source", "unknown")

        if src not in grouped:
            grouped[src] = {
                "docs": [],
                "best_distance": dist
            }

        grouped[src]["docs"].append(doc)

        # Keep best distance per source
        if dist < grouped[src]["best_distance"]:
            grouped[src]["best_distance"] = dist

    # ==========================================================
    # 7. SORT SOURCES BY RELEVANCE
    # ==========================================================

    sorted_sources = sorted(
        grouped.items(),
        key=lambda x: x[1]["best_distance"]
    )

    # ==========================================================
    # 8. LIMIT NUMBER OF SOURCES
    # Prevent noisy irrelevant citations
    # ==========================================================

    sorted_sources = sorted_sources[:MAX_SOURCES]

    final_sources = []
    final_docs = []

    for src, data in sorted_sources:

        final_sources.append(src)

        final_docs.extend(data["docs"])

    # ==========================================================
    # 9. SINGLE SOURCE RESPONSE
    # ==========================================================

    if len(final_sources) == 1:

        return (
            "\n\n".join(final_docs),
            final_sources
        )

    # ==========================================================
    # 10. MULTI-SOURCE RESPONSE
    # ==========================================================

    combined = "\n\n".join(final_docs)

    return combined, final_sources