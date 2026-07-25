import json
import argparse
import os

def chunk_segments(raw_segments, module_number, chunk_duration=30.0):
    chunks = []
    current_chunk = {
        "module": module_number,
        "start_time": 0.0,
        "end_time": 0.0,
        "text": ""
    }
    
    chunk_start = None
    
    for seg in raw_segments:
        start = seg.get("start", 0.0)
        end = seg.get("end", start + 2.0)
        text = seg.get("text", "").strip()
        
        if chunk_start is None:
            chunk_start = start
            current_chunk["start_time"] = start
            
        current_chunk["end_time"] = end
        if current_chunk["text"]:
            current_chunk["text"] += " " + text
        else:
            current_chunk["text"] = text
            
        if end - chunk_start >= chunk_duration:
            chunks.append(current_chunk)
            current_chunk = {
                "module": module_number,
                "start_time": end,
                "end_time": end,
                "text": ""
            }
            chunk_start = None

    if current_chunk["text"]:
        chunks.append(current_chunk)
        
    return chunks

def process_file(raw_file, output_file, module_number):
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = data.get("segments", data) if isinstance(data, dict) else data
    chunks = chunk_segments(segments, module_number)
    
    # If the output file already exists, append to it (read, extend, write)
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
        except Exception:
            existing_chunks = []
    else:
        existing_chunks = []
        
    # Remove existing chunks for this module to avoid duplicates if re-running
    existing_chunks = [c for c in existing_chunks if c.get("module") != module_number]
    existing_chunks.extend(chunks)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_chunks, f, indent=2, ensure_ascii=False)
        
    print(f"Added {len(chunks)} chunks for Module {module_number} to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="Path to raw whisper segments JSON")
    parser.add_argument("--output", required=True, help="Path to final chunks.json")
    parser.add_argument("--module", type=int, required=True, help="Module number")
    
    args = parser.parse_args()
    process_file(args.raw, args.output, args.module)
