# Event-Driven RAG Pipeline

A production-ready, multi-source Retrieval-Augmented Generation (RAG) system 
that ingests project artifacts (documents, transcripts, JIRA tickets), stores them 
in a vector database, and answers queries using Llama-3.1-8B-Instant.

## Features
- Event-driven ingestion (docs, videos, JIRA)
- Hybrid Whisper transcription
- Chunking + embedding + ChromaDB
- Unified retrieval (no intent routing)
- Query rewriting
- Ranking + context assembly
- LLM answer generation with citations
- Streamlit UI with evidence viewer
- Evaluation framework

## Setup
```bash
pip install -r requirements.txt

# Event‑Driven RAG Pipeline for Dynamic Project Artifacts

## Overview
This project implements a production‑grade, event‑driven Retrieval‑Augmented Generation (RAG) system designed to unify heterogeneous project artifacts such as:

- JIRA tickets  
- Confluence pages  
- Shared folder documents (PDF, DOCX, TXT, MD)  

The system continuously ingests, embeds, and retrieves these artifacts in real time using:

- Folder watchers  
- Webhooks  
- Scheduled ingestion  
- Metadata‑driven vector storage  

The goal is to reduce cognitive load for developers by enabling natural‑language querying across all project knowledge sources.

---

## Key Features

### 🔹 Event‑Driven Ingestion
- JIRA ingestion via `/rest/api/3/search/jql`
- Confluence ingestion via REST API v2
- Shared folder ingestion with file watchers
- Real‑time updates via webhooks

### 🔹 Metadata‑Driven Storage (Option B)
Each artifact is stored in ChromaDB with rich metadata:
- `issue_key`, `status`, `priority`, `assignee`, `reporter`
- `created`, `updated`
- `filename`, `path`
- `page_id`, `title`

This enables precise filtering and exact‑answer extraction.

---

## Retrieval Architecture

### 1. Intent Parser
Understands:
- JIRA field queries (status, summary, description, etc.)
- JIRA ticket lookup (“Which ticket tracks X?”)
- Resource routing (JIRA / Docs / Confluence)
- Multi‑source queries

### 2. Unified Retriever
- Exact match for issue keys  
- JIRA‑only semantic search for ticket lookup  
- Resource‑aware filtering  
- Multi‑source summarization  

### 3. Exact Answer Extractor
Returns literal field values when possible.

---

## Running the System

### Full Ingestion
```bash
python -m ingestion.ingest_all

First run - ngrok http 8000
Then update the webhook url
Then execute - python -m orchestrator
Then python -m main

