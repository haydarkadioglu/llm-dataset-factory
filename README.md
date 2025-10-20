# Dataset Factory (Groq + Gemini)

Generate LLM fine-tuning datasets (JSONL) from text/markdown/PDF files using Groq or Gemini.

## Setup

1. Python 3.10+
2. Create and fill env:
   
   ```bash
   copy .env.example .env
   # then edit .env to set GROQ_API_KEY and/or GEMINI_API_KEY
   ```
3. Install deps:
   
   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
python main.py
```

- Add one or more `.txt`, `.md`, or `.pdf` files
- Choose provider (Groq or Gemini)
- Choose model (defaults: Groq `llama-3.1-70b-versatile`, Gemini `gemini-1.5-pro`)
- Choose number of QA pairs per chunk
- Generate and save a `.jsonl` file

## Output Format

Each line is a JSON object:

```json
{"source":"path/to/file.txt","input":"question","output":"answer"}
```

## Notes
- PDF extraction uses `pdfplumber` basic text; quality depends on the source.
- If provider returns non-JSON, fallback stores a single summarize record.
