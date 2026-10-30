# ClipSutra

### Turn Video into Knowledge.

**ClipSutra** is an AI-powered video learning workspace that transforms YouTube videos into structured study notes and key insights. It extracts available video transcripts, translates non-English content into English when requested, generates concise topics and detailed notes with Google Gemini, and exports the results as a PDF.

It also prepares transcript chunks, creates local embeddings with Hugging Face, and stores them in ChromaDB to support semantic retrieval and the project's RAG backend.

> **From a video link to organized learning material — in one workspace.**

---

## Preview

![ClipSutra application preview](screenshots/Preview.jpeg)

*ClipSutra interface showing YouTube video input, active video details, AI-synthesized notes, key topics, and PDF export.*

---

## Features

- **YouTube transcript extraction** — retrieves available captions using `youtube-transcript-api`.
- **Multilingual support** — accepts a transcript language code and can translate non-English transcripts into English using Gemini.
- **AI-generated key topics** — identifies the main concepts and highlights from the transcript.
- **Structured notes** — turns transcript content into organized, readable notes.
- **PDF export** — downloads generated notes and key topics as a formatted PDF.
- **Semantic indexing** — splits transcript text into chunks, creates local Hugging Face embeddings, and stores them in ChromaDB.
- **RAG-ready backend** — includes a retrieval-based question-answering function and `/api/chat` endpoint for video-context questions.

---

## How It Works

ClipSutra transforms YouTube videos into structured learning material through an AI-powered workflow.

1. **YouTube Video Input:** Users provide a YouTube video URL and select their preferred transcript language.

2. **Transcript Extraction:** The application extracts the video ID and retrieves the available transcript using `youtube-transcript-api`.

3. **Transcript Translation:** Non-English transcripts are translated into English using Google Gemini when required.

4. **AI Content Synthesis:** Google Gemini analyzes the transcript and generates important topics, key highlights, and structured notes.

5. **Text Chunking:** LangChain's `RecursiveCharacterTextSplitter` divides the transcript into smaller chunks for efficient processing.

6. **Embedding Generation:** Hugging Face's `sentence-transformers/all-mpnet-base-v2` model converts text chunks into numerical vector embeddings.

7. **Vector Storage:** ChromaDB stores the generated embeddings, enabling semantic retrieval and supporting the RAG-based question-answering backend.

8. **PDF Generation:** The generated notes and key topics are converted into a professionally formatted PDF using ReportLab, allowing users to download their learning material.

---

## Technology Stack

| Area | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| LLM | Google Gemini via LangChain |
| LLM integration | `langchain-google-genai` |
| RAG framework | LangChain |
| Embeddings | Hugging Face — `sentence-transformers/all-mpnet-base-v2` |
| Vector database | ChromaDB |
| Transcript extraction | `youtube-transcript-api` |
| PDF generation | ReportLab |

**Configured Gemini model:** `gemini-3.5-flash-lite` (make sure this matches the model configured in `support_functions.py`).

---

## Project Structure

```text
ClipSutra/
├── app.py                  # Flask application and API routes
├── support_functions.py    # Transcript, Gemini, chunking, embeddings and RAG logic
├── pdf_generator.py        # PDF layout and export
├── requirements.txt        # Python dependencies
├── .env           # Environment variable template
├── .gitignore
│
├── templates/
│   └── index.html          # Main application page
│
├── static/
│   ├── style.css           # Application styling
│   └── app.js              # Frontend interactions and API requests

```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/vbuilds432/ClipSutra.git
cd ClipSutra
```

### 2. Create and activate a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root. You can use `.env.example` as a template.

```env
GOOGLE_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_random_secret_key
```

- Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- Use a strong, randomly generated value for `FLASK_SECRET_KEY`.

### 5. Run the application

```bash
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

Paste a YouTube video URL, choose the transcript language code, and select **Process Video**. When processing completes, review the generated topics and notes, then use **Download Notes as PDF** to export them.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Loads the ClipSutra interface |
| `POST` | `/api/process` | Processes a YouTube video and generates notes/topics |
| `POST` | `/api/chat` | Answers a question using the processed video's vector store |
| `POST` | `/api/download-pdf` | Generates and downloads the notes PDF |
| `POST` | `/api/reset` | Clears the current in-memory video session |

---

## Notes and Limitations

- Transcript extraction depends on captions being available for the selected video and language.
- Translation and content generation require a valid Google Gemini API key and may be subject to API quotas and model availability.
- The first embedding run may take additional time while the Hugging Face model is downloaded and initialized.
- The current video-session cache is stored in application memory. Processing state can be lost when the Flask server restarts.
- The current Flask development server is intended for local development, not production deployment.

---

## Future Improvements

- Add an interactive video-context chat interface.
- Add persistent storage for video sessions and vector collections.
- Cache transcripts and generated results to avoid unnecessary repeat processing.
- Display actual backend processing progress instead of simulated frontend stages.
- Add support for saved video libraries and multiple processed videos.

---

<p align="center">
  <strong>ClipSutra</strong><br>
  Turn Video into Knowledge.
</p>
