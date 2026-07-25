import argparse
import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

def run_transcription(video_path, output_path, module_number):
    print(f"Uploading {video_path} to Gemini...")
    
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return
        
    genai.configure(api_key=api_key)
    
    try:
        video_file = genai.upload_file(path=video_path)
        print(f"Uploaded as {video_file.name}. Waiting for processing...")
        
        while video_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            print("Video processing failed.")
            return
            
        print("\nProcessing complete. Requesting transcription...")
        
        prompt = f"""You are a professional transcriber. Transcribe the spoken text in this video accurately. 
Group the transcription into roughly 30-second continuous segments.
Output the transcription purely as a JSON array of objects. 
Do not include markdown blocks or any other text.
Each object should have exactly the following structure:
{{
    "module": {module_number},
    "start_time": <start time in seconds as float>,
    "end_time": <end time in seconds as float>,
    "text": "<transcribed text>"
}}"""
        
        # Let's use 2.5-flash for speed and lower latency, as Flash is very good at transcriptions.
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            [video_file, prompt],
            generation_config={"temperature": 0.0}
        )
        
        # Clean up response text
        output_text = response.text.strip()
        if output_text.startswith("```json"):
            output_text = output_text[7:]
        if output_text.endswith("```"):
            output_text = output_text[:-3]
        output_text = output_text.strip()
            
        chunks = json.loads(output_text)
        
        # Now use the same appending logic as chunk_transcripts.py
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_chunks = json.load(f)
            except Exception:
                existing_chunks = []
        else:
            existing_chunks = []
            
        # Remove existing chunks for this module to avoid duplicates
        existing_chunks = [c for c in existing_chunks if c.get("module") != module_number]
        existing_chunks.extend(chunks)
        
        # Ensure the backend directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(existing_chunks, f, indent=2, ensure_ascii=False)
            
        print(f"\nFinal chunks saved to {output_path}")
        
    except Exception as e:
        print(f"\nTranscription failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to the video file")
    parser.add_argument("--output", required=True, help="Path to save chunks.json")
    parser.add_argument("--module", type=int, required=True, help="Module number")
    
    args = parser.parse_args()
    run_transcription(args.video, args.output, args.module)
