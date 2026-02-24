# DocuMind Local Lab

Phase 1 delivers local PDF ↔ Word conversion with batch support and a clean UI.

## Phase Roadmap
1. Phase 1: Conversion core + batch UI (current)
2. Phase 2: OCR + PDF text extraction
3. Phase 3: Gemini chatbot + embeddings memory

## Local Requirements
- Windows
- Python 3.10+
- Node 18+
- Microsoft Word installed (for Word → PDF)
- Tesseract OCR installed and on PATH (for PDF → Text OCR)
- Poppler installed and on PATH, or set `POPPLER_BIN` (for PDF → Text OCR)
- Gemini or Groq API key (for Chat)

## Run Backend
1. Create venv and install deps:
   - `python -m venv .venv`
   - `.venv\\Scripts\\pip.exe install -r backend\\requirements-core.txt`
   - Optional heavy deps for conversion:
     - `.venv\\Scripts\\pip.exe install -r backend\\requirements-heavy.txt --default-timeout=300`
   - Optional OCR deps for PDF → Text:
     - `.venv\\Scripts\\pip.exe install -r backend\\requirements-ocr.txt --default-timeout=300`
   - Optional Gemini chat deps:
     - `.venv\\Scripts\\pip.exe install -r backend\\requirements-gemini.txt --default-timeout=300`
   - Optional Groq chat deps:
     - `.venv\\Scripts\\pip.exe install -r backend\\requirements-groq.txt --default-timeout=300`
2. Create `.env` in project root (auto-loaded):
   - `CHAT_PROVIDER=groq` (or `gemini`)
   - `CHAT_API_KEY=your_key_here`
   - `CHAT_MODEL=llama-3.1-8b-instant` (or `gemini-2.0-flash`)
   - `TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
   - `POPPLER_BIN=C:\\Tools\\poppler\\Library\\bin`
3. Start API:
   - `.venv\\Scripts\\uvicorn.exe app.main:app --reload --app-dir backend`

## Run Frontend
1. Install deps:
   - `npm install`
2. Start dev server:
   - `npm run dev`

The frontend expects the backend at `http://localhost:8000`.
