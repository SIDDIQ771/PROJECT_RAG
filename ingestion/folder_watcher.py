import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingestion.docs_ingest import process_single_document
from ingestion.video_transcriber import process_video, VIDEO_EXT

SUPPORTED_DOC_EXT = {".pdf", ".docx", ".txt", ".md"}


class FolderEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"[Watcher] New file: {event.src_path}")
            time.sleep(1)  # wait for file to finish writing
            _route_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[Watcher] Modified file: {event.src_path}")
            time.sleep(1)
            _route_file(event.src_path)


def _route_file(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext in VIDEO_EXT:
        process_video(path)
    elif ext in SUPPORTED_DOC_EXT:
        process_single_document(path)
    else:
        print(f"[Watcher] Skipping unsupported file: {path}")


def start_folder_watcher(folder_path):
    observer = Observer()
    observer.schedule(FolderEventHandler(), folder_path, recursive=False)
    observer.start()
    print(f"[Watcher] Monitoring folder: {folder_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()