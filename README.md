# AI Personal Student Assistant

A local-first Streamlit study companion for asking questions about your notes, creating revision plans, and generating practice quizzes.

## Features
- Chat with a Gemini model or a local Ollama model.
- Upload PDF, TXT, or Markdown study material and ask grounded questions about it.
- Build a simple study plan from subjects, available days, and a target date.
- Generate practice questions from your uploaded notes.
- Local document retrieval with TF-IDF; uploaded files are processed in memory for the current session.

## Setup
Requires CPython 3.11.9 (Python 3.11 recommended). Install Ollama separately for local model use; a GPU is optional.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Set `GEMINI_API_KEY` in `.env` to use Gemini. For local chat, install and start [Ollama](https://ollama.com), pull a model (for example `ollama pull llama3.2`), then choose Ollama in the app. You can change the model and Ollama URL in `.env`.

## Notes
- Gemini requests send your prompt and any selected document excerpts to Google's API. Use Ollama for local inference.
- This starter app does not persist conversations or uploaded documents.
- Study plans and generated quizzes are suggestions; review them against your course materials.
