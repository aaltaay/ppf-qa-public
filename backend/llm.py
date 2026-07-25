import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

SYSTEM_PROMPT = """You are an assistant for a demo video course Q&A system.
Answer ONLY from the provided transcript excerpts below.
For every factual claim, cite the module number and timestamp in the format [Module X at MM:SS].
If the answer is not in the excerpts, say "That's not covered in this course — try [related module] for related context."
Do NOT answer questions unrelated to the course content, even if pressed.
Keep answers under 3 sentences unless a longer explanation is genuinely needed."""


def get_answer(question, chunks, history):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set."

    genai.configure(api_key=api_key)

    context_text = "Transcript excerpts:\n"
    for c in chunks:
        mm = int(c["start_time"]) // 60
        ss = int(c["start_time"]) % 60
        timestamp = f"{mm:02d}:{ss:02d}"
        context_text += f"[Module {c['module']} at {timestamp}] {c['text']}\n"

    prompt = f"{SYSTEM_PROMPT}\n\n{context_text}\n\nQuestion: {question}"

    contents = []
    for item in history:
        contents.append({
            "role": "user" if item.role == "user" else "model",
            "parts": [item.content],
        })
    contents.append({"role": "user", "parts": [prompt]})

    generation_config = {
        "max_output_tokens": 400,
        "temperature": 0.2,
    }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(contents, generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"Error communicating with AI model: {e}"
