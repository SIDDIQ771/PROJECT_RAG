from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingestion.docs_ingest import process_single_document
import time

class FolderEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"[Watcher] New file: {event.src_path}")
            process_single_document(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[Watcher] Modified file: {event.src_path}")
            process_single_document(event.src_path)

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
