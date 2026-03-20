from fastapi import APIRouter, Request
from ingestion.jira_ingest import process_single_jira_issue

router = APIRouter()

@router.post("/jira/webhook")
async def jira_webhook(request: Request):
    data = await request.json()
    issue_key = data["issue"]["key"]
    print(f"[Webhook] JIRA updated: {issue_key}")
    process_single_jira_issue(issue_key)
    return {"status": "ok"}
