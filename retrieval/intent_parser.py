import re

def parse_intent(query: str):
    q = query.lower()

    intent = {
        "issue_key": None,
        "field": None,
        "resource": None,
        "lookup_ticket": False
    }

    # Detect JIRA issue key
    match = re.search(r"(rag-\d+)", q)
    if match:
        intent["issue_key"] = match.group(1).upper()
        intent["resource"] = "jira"

    # Detect field-level intent
    field_map = {
        "status": "status",
        "summary": "summary",
        "description": "description",
        "last comment": "last_comment",
        "latest comment": "last_comment",
        "assignee": "assignee",
        "priority": "priority",
        "created": "created",
        "updated": "updated",
        "reporter": "reporter"
    }
    for key, value in field_map.items():
        if key in q:
            intent["field"] = value

    # Detect lookup intent — check this BEFORE resource detection
    lookup_patterns = [
        "which jira ticket",
        "which ticket",
        "what ticket",
        "where is this tracked",
        "which issue covers",
        "which story",
        "which epic",
        "what jira",
        "find ticket",
        "find the ticket",
        "find jira",
        "ticket for",
        "issue for",
        "jira for",
    ]
    if any(p in q for p in lookup_patterns):
        intent["lookup_ticket"] = True
        intent["resource"] = "jira"

    # ✅ FIX: Only set resource if lookup_ticket is NOT already set
    # This prevents "designing" triggering "design" → resource="docs" overwriting jira
    if not intent["lookup_ticket"] and intent["resource"] != "jira":

        # Detect shared folder intent — use whole-word matching to avoid false positives
        doc_words = ["document", "pdf", "shared folder", "file", "spec"]
        if any(word in q for word in doc_words):
            intent["resource"] = "docs"

        # Detect confluence intent
        if any(word in q for word in ["confluence", "wiki", "page", "space"]):
            intent["resource"] = "confluence"

    return intent