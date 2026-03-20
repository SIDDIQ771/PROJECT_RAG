from ingestion.docs_ingest import process_documents
from ingestion.jira_ingest import process_jira
from ingestion.confluence_ingest import process_confluence


def run_all_ingestion():
    print("\n=== Starting Full Ingestion Pipeline ===\n")

    print("→ Processing Documents...")
    process_documents()

    print("\n→ Processing JIRA Tickets...")
    process_jira()

    print("\n→ Processing Confluence Pages...")
    process_confluence()

    print("\n=== Ingestion Pipeline Completed Successfully ===")


if __name__ == "__main__":
    run_all_ingestion()
