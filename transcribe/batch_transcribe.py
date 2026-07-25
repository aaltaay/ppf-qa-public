"""
Batch transcription script for course video modules.
Iterates over module MP4 files and transcribes each using the Gemini API.
Usage: python batch_transcribe.py [--force] [--modules 1 2 3]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from run_whisper import run_transcription

MODULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")
CHUNKS_OUTPUT = os.path.join(os.path.dirname(__file__), "chunks.json")


def get_existing_modules(chunks_path):
    """Return set of module numbers already transcribed."""
    if not os.path.exists(chunks_path):
        return set()
    try:
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        return {c.get("module") for c in chunks}
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser(description="Batch transcribe course modules")
    parser.add_argument("--force", action="store_true", help="Re-transcribe even if module already exists")
    parser.add_argument("--modules", nargs="+", type=int, help="Specific modules to process")
    args = parser.parse_args()

    target_modules = args.modules if args.modules else list(range(1, 4))
    existing = get_existing_modules(CHUNKS_OUTPUT)

    print("=== Course Batch Transcription ===")
    print(f"Modules dir: {MODULES_DIR}")
    print(f"Output: {CHUNKS_OUTPUT}")
    print(f"Target modules: {target_modules}")
    print(f"Already transcribed: {sorted(existing)}")
    print()

    for mod_num in target_modules:
        video_path = os.path.join(MODULES_DIR, f"module {mod_num}.mp4")

        if not os.path.exists(video_path):
            print(f"[WARN] Module {mod_num}: File not found at {video_path}, skipping.")
            continue

        if mod_num in existing and not args.force:
            print(f"[SKIP] Module {mod_num}: Already transcribed. (use --force to redo)")
            continue

        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"[PROCESSING] Module {mod_num}: ({file_size_mb:.1f} MB)...")

        try:
            run_transcription(video_path, CHUNKS_OUTPUT, mod_num)
            print(f"[DONE] Module {mod_num}: Success!")
        except Exception as e:
            print(f"[ERROR] Module {mod_num}: Failed - {e}")

    final_modules = get_existing_modules(CHUNKS_OUTPUT)
    if os.path.exists(CHUNKS_OUTPUT):
        with open(CHUNKS_OUTPUT, "r", encoding="utf-8") as f:
            all_chunks = json.load(f)
        print("\n=== Summary ===")
        print(f"Total modules transcribed: {len(final_modules)}")
        print(f"Total chunks: {len(all_chunks)}")
        for m in sorted(final_modules):
            count = len([c for c in all_chunks if c.get("module") == m])
            print(f"  Module {m}: {count} chunks")
        demo_path = os.path.join(os.path.dirname(__file__), "demo_chunks.json")
        print(f"\nNext: copy {CHUNKS_OUTPUT} → {demo_path}, then run: python -m backend.ingest_chunks")


if __name__ == "__main__":
    main()
