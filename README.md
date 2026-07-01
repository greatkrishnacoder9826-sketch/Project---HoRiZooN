# 🐉 HoRiZooN

**AI-powered meeting intelligence** — turn any meeting recording or YouTube video into a searchable, summarized, action-ready document. Transcribe, summarize, extract decisions, and chat with your meeting using a Retrieval-Augmented Generation (RAG) pipeline.

![theme](https://img.shields.io/badge/theme-neon%20red%20%2F%20black-ff1744?style=flat-square)
![python](https://img.shields.io/badge/python-3.11-blue?style=flat-square)
![streamlit](https://img.shields.io/badge/built%20with-Streamlit-ff4b4b?style=flat-square)

---

## ✨ Features

- 🎙️ **Transcription** from YouTube URLs or local audio/video files (via `yt-dlp` + `faster-whisper` / Sarvam API)
- 🌐 **Bilingual support** — English or Hinglish transcription output
- 📌 **Auto-generated title** for every meeting
- 📋 **Summary** in clean bullet points (map-reduce over long transcripts)
- ✅ **Action items** extraction — task, owner, deadline
- 🔑 **Key decisions** extraction
- ❓ **Open questions** extraction
- 💬 **Chat with your meeting** — ask follow-up questions against the transcript using a RAG pipeline (Mistral + Chroma + HuggingFace embeddings), with short-term conversation memory
- 🎨 **Neon red / black glassmorphic UI** built with Streamlit

---

## 🗂️ Project Structure

```
Project_Horizon/
├── app.py                  # Streamlit UI (main entry point for the web app)
├── main.py                 # CLI entry point
├── logo.png                # Project logo (used in the UI header)
├── requirements.txt         # Python dependencies
├── packages.txt              # System-level deps for Streamlit Cloud (ffmpeg)
├── core/
│   ├── transcriber.py       # Speech-to-text (Sarvam API + Whisper fallback)
│   ├── summarize.py          # Transcript summarization + title generation
│   ├── extractor.py          # Action items / decisions / open questions
│   ├── engine.py              # RAG chain (retriever + LLM + chat memory)
│   └── vector_store.py        # Chroma vector store + embeddings
└── utils/
    └── audio_processor.py    # Download, convert, and chunk audio
```

---

## ⚙️ Setup (Local)

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/horizoon.git
cd horizoon
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg
- **Windows:** `winget install Gyan.FFmpeg` (restart your terminal after)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 5. Set up environment variables

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key   # optional — falls back to Whisper if not set
```

### 6. Run it

**Streamlit UI:**
```bash
streamlit run app.py
```

**CLI:**
```bash
python main.py
```

---

## ☁️ Deploying to Streamlit Community Cloud

1. **Push this project to a GitHub repo** (make sure `.env` is in `.gitignore` — never commit API keys).

2. **Make sure these files exist at the repo root** (already included here):
   - `requirements.txt` — Python packages
   - `packages.txt` — contains `ffmpeg` (installs the system binary Streamlit Cloud doesn't have by default)

3. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.

4. Click **"New app"** → select your repo, branch, and set the main file path to `app.py`.

5. Before deploying, click **"Advanced settings"** → **Secrets**, and add your API keys in TOML format:
   ```toml
   MISTRAL_API_KEY = "your_mistral_api_key"
   SARVAM_API_KEY = "your_sarvam_api_key"
   ```
   (Streamlit Cloud injects these as environment variables, so `os.getenv(...)` in the code will pick them up automatically.)

6. Click **Deploy**. First build can take a few minutes (downloading Whisper/embedding models).

7. Once live, your app will be available at:
   ```
   https://<your-app-name>.streamlit.app
   ```

### Notes for cloud deployment
- Whisper (`faster-whisper`) runs on CPU on Streamlit Cloud — larger models will be slow. `base` model (already used) is a reasonable default.
- Streamlit Cloud's free tier has limited RAM — very long meetings/videos may need chunking tuned smaller, or a paid tier.
- The vector store is now built fresh and in-memory per session (no cross-session data leakage), so no persistent disk storage is required for the RAG chat feature.

---

## 🧠 How the RAG Chat Works

1. The transcript is split into ~500-character overlapping chunks.
2. Each chunk is embedded using `all-MiniLM-L6-v2` (HuggingFace) and stored in an isolated, in-memory Chroma collection for that session.
3. When you ask a question, the top-matching chunks are retrieved and passed to Mistral (`mistral-small-latest`) along with your recent conversation history, so follow-ups like *"explain the first point again"* work correctly.
4. If the answer isn't found in the transcript, the assistant says so explicitly instead of hallucinating.

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit (custom glassmorphic CSS) |
| Audio download | yt-dlp |
| Audio processing | pydub + ffmpeg |
| Transcription | Sarvam API (Hindi) / faster-whisper (fallback) |
| LLM | Mistral (`mistral-small-latest`) via LangChain |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector store | Chroma |
| Orchestration | LangChain (LCEL) |

---

## 📄 License

Add your license here (MIT, Apache-2.0, etc.)

---

## 🙋 Support

Issues and feature requests welcome — open a GitHub issue.
