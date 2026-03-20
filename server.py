from fastapi import FastAPI
from ingestion.jira_webhook import router as jira_router
from ingestion.confluence_webhook import router as confluence_router

app = FastAPI()

app.include_router(jira_router)
app.include_router(confluence_router)

@app.get("/")
def root():
    return {"status": "running"}
