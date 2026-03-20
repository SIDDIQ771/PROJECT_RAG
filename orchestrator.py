import threading
from ingestion.folder_watcher import start_folder_watcher
from config.settings import settings
import uvicorn
from server import app
from ingestion.jira_ingest import process_jira
from ingestion.docs_ingest import process_documents
from ingestion.confluence_ingest import process_confluence

_uvicorn_server = None


def start_webhook_server():
    global _uvicorn_server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
    _uvicorn_server = uvicorn.Server(config)
    try:
        _uvicorn_server.run()
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            print("[Webhooks] ⚠️  Port 8000 already in use — kill existing process and restart.")
        else:
            raise


def stop_webhook_server():
    if _uvicorn_server:
        _uvicorn_server.should_exit = True


def start_orchestrator():
    print("\n=== Starting Event-Driven Ingestion Pipeline ===\n")

    print("[Startup] Running initial JIRA ingestion...")
    process_jira()
    print("[Startup] Initial JIRA ingestion complete.\n")

    print("[Startup] Running initial Confluence ingestion...")
    process_confluence()
    print("[Startup] Initial Confluence ingestion complete.\n")

    print("[Startup] Running initial Shared Folder ingestion...")
    process_documents()
    print("[Startup] Initial Shared Folder ingestion complete.\n")

    t1 = threading.Thread(target=start_folder_watcher, args=(settings.SHARED_FOLDER_PATH,))
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=start_webhook_server)
    t2.daemon = False
    t2.start()

    print("\n=== Pipeline Running (Folder Watcher + Webhooks) ===")


if __name__ == "__main__":
    start_orchestrator()