from fastapi import APIRouter, Request
from ingestion.jira_ingest import process_single_jira_issue

router = APIRouter()

@router.post("/jira/webhook")
async def jira_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "reason": "invalid JSON"}

    issue_key = data.get("issue", {}).get("key")
    if not issue_key:
        print(f"[Webhook] JIRA: could not extract issue key from payload")
        return {"status": "ignored"}

    event_type = data.get("webhookEvent", "unknown")
    print(f"[Webhook] JIRA event={event_type} issue={issue_key} — re-ingesting...")
    process_single_jira_issue(issue_key)
    print(f"[Webhook] JIRA issue {issue_key} updated in vector DB.")
    return {"status": "ok"}