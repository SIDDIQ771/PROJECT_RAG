import re
import base64
import requests
from config.settings import settings
from vectorstore.chroma_client import get_chroma_client
from ingestion.chunker import chunk_text

db = get_chroma_client()


def _build_confluence_headers():
    credentials = f"{settings.CONFLUENCE_EMAIL}:{settings.CONFLUENCE_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json"
    }


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    text = (text
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&nbsp;", " ")
            .replace("&quot;", '"'))
    return text


def _get_space_id(space_key: str) -> str | None:
    url = f"{settings.CONFLUENCE_BASE_URL}/wiki/api/v2/spaces"
    headers = _build_confluence_headers()
    params = {"keys": space_key}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ [Confluence] Failed to resolve space key '{space_key}': {response.text}")
        return None
    results = response.json().get("results", [])
    if not results:
        print(f"❌ [Confluence] No space found for key '{space_key}'.")
        return None
    space_id = str(results[0]["id"])
    print(f"[Confluence] Resolved space key '{space_key}' -> numeric ID {space_id}")
    return space_id


def process_confluence():
    headers = _build_confluence_headers()
    space_id = _get_space_id(settings.CONFLUENCE_SPACE_KEY)
    if not space_id:
        return
    url = f"{settings.CONFLUENCE_BASE_URL}/wiki/api/v2/spaces/{space_id}/pages"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("\n❌ [Confluence] FETCH ERROR")
        print("Status:", response.status_code)
        print("Response:", response.text)
        return
    pages = response.json().get("results", [])
    print(f"[Confluence] Retrieved {len(pages)} pages")
    for page in pages:
        process_single_confluence_page(page["id"])


def process_single_confluence_page(page_id: str):
    url = f"{settings.CONFLUENCE_BASE_URL}/wiki/api/v2/pages/{page_id}?body-format=storage"
    headers = _build_confluence_headers()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch Confluence page {page_id}: {response.text}")
        return

    data = response.json()
    title = data.get("title", "Untitled Page")
    raw_body = data.get("body", {}).get("storage", {}).get("value", "")
    plain_text = _strip_html(raw_body)

    if not plain_text.strip():
        print(f"[Confluence] ⚠️  Page {page_id} ({title}) has no extractable text, skipping.")
        return

    # Header prepended to every chunk so retrieval is always self-contained
    header = f"CONFLUENCE PAGE: {title}\nPAGE ID: {page_id}\n\n"
    full_text = header + plain_text

    # ✅ Chunk using optimized chunker
    raw_chunks = chunk_text(full_text)

    base_metadata = {
        "source":  f"CONFLUENCE-{page_id}",
        "page_id": page_id,
        "title":   title,
    }

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(raw_chunks):
        # Ensure title is in every chunk for self-contained retrieval
        if title not in chunk:
            chunk = header + chunk

        documents.append(chunk)
        metadatas.append({**base_metadata, "chunk_index": i, "total_chunks": len(raw_chunks)})
        ids.append(f"confluence-{page_id}-chunk-{i}")

    db.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[Confluence] Upserted {len(documents)} chunks for page {page_id} ({title}).")