from fastapi import APIRouter, Request
from ingestion.confluence_ingest import process_single_confluence_page

router = APIRouter()

@router.post("/confluence/webhook")
async def confluence_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "reason": "invalid JSON payload"}

    # ✅ FIX 3: Safely extract page_id — Confluence sends different shapes
    # depending on event type (page_created, page_updated, page_removed, etc.)
    page = data.get("page") or data.get("data", {}).get("page", {})

    if not page:
        print(f"[Webhook] Confluence: no 'page' key in payload — ignoring. Payload: {data}")
        return {"status": "ignored", "reason": "no page in payload"}

    page_id = page.get("id") or page.get("self", "").split("/")[-1]

    if not page_id:
        print(f"[Webhook] Confluence: could not extract page_id from payload: {data}")
        return {"status": "ignored", "reason": "could not extract page_id"}

    event_type = data.get("eventType", "unknown")
    print(f"[Webhook] Confluence event={event_type} page_id={page_id}")

    # Don't re-ingest removed pages
    if "removed" in event_type.lower() or "deleted" in event_type.lower():
        print(f"[Webhook] Confluence: page {page_id} was removed — skipping ingestion.")
        return {"status": "ok", "action": "skipped_removal"}

    process_single_confluence_page(str(page_id))
    return {"status": "ok"}