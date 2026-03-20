import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import signal
import threading
import gradio as gr

# ── Start orchestrator in background immediately ──────────────────────────────
_ingestion_done = threading.Event()

def run_orchestrator():
    from orchestrator import start_orchestrator
    start_orchestrator()
    _ingestion_done.set()

threading.Thread(target=run_orchestrator, daemon=True).start()

# ── Signal handler in main thread ─────────────────────────────────────────────
def shutdown(signum=None, frame=None):
    print("\n[Shutdown] Stopping pipeline...")
    try:
        from orchestrator import stop_webhook_server
        stop_webhook_server()
    except Exception:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ── Wait for ingestion to finish before launching UI ─────────────────────────
print("[App] Waiting for ingestion to complete...")
_ingestion_done.wait()
print("[App] Ingestion complete — launching UI at http://localhost:7860")

# ── Query handler ─────────────────────────────────────────────────────────────
def handle_query(query, history):
    from main import answer_query
    if not query.strip():
        return "Please enter a question."
    start = time.perf_counter()
    answer = answer_query(query)
    elapsed = round(time.perf_counter() - start, 2)
    return f"{answer}\n\n⏱️ *Total time: {elapsed}s*"

# ── Gradio UI ─────────────────────────────────────────────────────────────────
with gr.Blocks(title="RAG Assistant", css="""
    .generating, .eta-bar, footer { display: none !important; }
""") as demo:
    gr.Markdown("# 📘 Project RAG Assistant")
    gr.Markdown("Ask anything about your project documents, JIRA tickets, or Confluence pages.")
    gr.ChatInterface(
        fn=handle_query,
        chatbot=gr.Chatbot(height=500, show_label=False),
        textbox=gr.Textbox(placeholder="Enter your question...", container=False, scale=7),
    )

demo.launch(server_port=7860, share=False, inbrowser=True)