import base64
import requests
from config.settings import settings
from vectorstore.chroma_client import get_chroma_client
from ingestion.chunker import chunk_text

db = get_chroma_client()


def _build_jira_headers():
    credentials = f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def _extract_adf_text(adf) -> str:
    if not adf:
        return ""
    if isinstance(adf, str):
        return adf
    text_parts = []
    node_type = adf.get("type", "")
    if node_type == "text":
        return adf.get("text", "")
    for child in adf.get("content", []):
        part = _extract_adf_text(child)
        if part:
            text_parts.append(part)
    separator = "\n" if node_type in ("paragraph", "heading", "bulletList", "listItem", "blockquote") else " "
    return separator.join(text_parts)


def _build_chunks_and_metadata(issue: dict) -> tuple[list[str], list[dict], list[str]]:
    """
    Build optimized chunks for a JIRA issue.
    - Always prepend issue key + summary to EVERY chunk so context is never lost
    - Chunk long descriptions and comments separately
    - Short issues stored as single chunk
    """
    issue_key = issue["key"]
    fields = issue["fields"]

    description_text = _extract_adf_text(fields.get("description"))
    comments = fields.get("comment", {}).get("comments", [])

    # Extract all comments, not just last one
    all_comments = "\n\n".join(
        f"Comment by {c.get('author', {}).get('displayName', 'Unknown')}:\n{_extract_adf_text(c.get('body'))}"
        for c in comments
    ) if comments else ""

    last_comment_text = _extract_adf_text(comments[-1].get("body")) if comments else ""

    # Base metadata shared across all chunks of this issue
    base_metadata = {
        "source":       f"JIRA-{issue_key}",
        "issue_key":    issue_key,
        "summary":      fields.get("summary") or "",
        "description":  description_text,
        "status":       fields["status"]["name"] if fields.get("status") else "",
        "priority":     fields["priority"]["name"] if fields.get("priority") else "",
        "assignee":     fields["assignee"]["displayName"] if fields.get("assignee") else "",
        "reporter":     fields["reporter"]["displayName"] if fields.get("reporter") else "",
        "created":      fields.get("created") or "",
        "updated":      fields.get("updated") or "",
        "last_comment": last_comment_text,
    }

    # Header prepended to every chunk so retrieval always has full context
    header = (
        f"JIRA TICKET: {issue_key}\n"
        f"SUMMARY: {base_metadata['summary']}\n"
        f"STATUS: {base_metadata['status']} | "
        f"PRIORITY: {base_metadata['priority']} | "
        f"ASSIGNEE: {base_metadata['assignee']}\n\n"
    )

    # Build full text body
    body = ""
    if description_text:
        body += f"DESCRIPTION:\n{description_text}\n\n"
    if all_comments:
        body += f"COMMENTS:\n{all_comments}"

    full_text = header + (body if body.strip() else "No description or comments available.")

    # ✅ Chunk using optimized chunker — handles long tickets properly
    # Prepend header to each chunk so every chunk is self-contained
    raw_chunks = chunk_text(full_text)

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(raw_chunks):
        # Ensure header is in every chunk for self-contained retrieval
        if issue_key not in chunk:
            chunk = header + chunk

        documents.append(chunk)
        metadatas.append({**base_metadata, "chunk_index": i, "total_chunks": len(raw_chunks)})
        ids.append(f"jira-{issue_key}-chunk-{i}")

    return documents, metadatas, ids


def process_jira():
    """Fetch ALL issues in one API call, chunk and batch upsert."""
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/search/jql"
    headers = _build_jira_headers()
    payload = {
        "jql": f"project = {settings.JIRA_PROJECT_KEY} ORDER BY created DESC",
        "maxResults": 100,
        "fields": [
            "summary", "description", "comment", "status",
            "priority", "assignee", "reporter", "created", "updated"
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("\n❌ [JIRA] SEARCH ERROR")
        print("Status:", response.status_code)
        print("Response:", response.text)
        return

    issues = response.json().get("issues", [])
    print(f"[JIRA] Retrieved {len(issues)} issues — chunking and batch upserting...")

    all_documents, all_metadatas, all_ids = [], [], []
    for issue in issues:
        docs, metas, ids = _build_chunks_and_metadata(issue)
        all_documents.extend(docs)
        all_metadatas.extend(metas)
        all_ids.extend(ids)

    if all_documents:
        db.upsert(documents=all_documents, metadatas=all_metadatas, ids=all_ids)
        print(f"[JIRA] Batch upserted {len(all_documents)} chunks from {len(issues)} issues.")


def process_single_jira_issue(issue_key: str):
    """Used by webhook — fetch single ticket, chunk and upsert."""
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    headers = _build_jira_headers()

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch issue {issue_key}: {response.text}")
        return

    issue = {"key": issue_key, "fields": response.json()["fields"]}
    docs, metas, ids = _build_chunks_and_metadata(issue)

    db.upsert(documents=docs, metadatas=metas, ids=ids)
    print(f"[JIRA] Upserted {len(docs)} chunks for issue {issue_key}.")