import os
import whisper   # now points to openai-whisper
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_and_store

TRANSCRIPT_EXT = [".txt", ".vtt", ".srt"]

def find_existing_transcript(video_path):
    base = os.path.splitext(video_path)[0]
    for ext in TRANSCRIPT_EXT:
        transcript_path = base + ext
        if os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                return f.read()
    return None

def generate_transcript(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    transcript = result["text"]
    transcript_path = os.path.splitext(video_path)[0] + ".txt"
    with open(transcript_path, "w", encoding="utf-8") as f: f.write(transcript)
    return transcript

def process_video(video_path):
    transcript = find_existing_transcript(video_path) or generate_transcript(video_path)
    chunks = chunk_text(transcript)
    embed_and_store(chunks, metadata={"source": video_path})
