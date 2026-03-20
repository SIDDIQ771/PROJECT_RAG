def extract_exact_answer(query: str, text: str, metadata: dict):
    q = query.lower()

    # If metadata contains the field, return directly
    field_map = {
        "status": "status",
        "summary": "summary",
        "description": "description",
        "last_comment": "last_comment",
        "assignee": "assignee",
        "priority": "priority",
        "created": "created",
        "updated": "updated",
        "reporter": "reporter"
    }

    for key, meta_key in field_map.items():
        if key in q and meta_key in metadata:
            return metadata[meta_key]

    # Fallback → return text
    return text.strip()
