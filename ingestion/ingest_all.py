from ingestion.jira_ingest import process_jira
from ingestion.confluence_ingest import process_confluence
from ingestion.shared_folder_ingest import process_shared_folder


def ingest_all():
    print("\n=== Running Full Ingestion Pipeline ===\n")

    print("\n[1] Ingesting JIRA issues...")
    process_jira()

    print("\n[2] Ingesting Confluence pages...")
    process_confluence()

    print("\n[3] Ingesting Shared Folder documents...")
    process_shared_folder()

    print("\n=== Ingestion Complete ===\n")


if __name__ == "__main__":
    ingest_all()
