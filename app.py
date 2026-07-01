import os
import base64
import tempfile
import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.engine import build_rag_chain, ask_question

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────
# LOGO
# ──────────────────────────────────────────────────────────────────────────
LOGO_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png"),           # app.py ke bagal mein
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png"), # assets/ folder mein
]
LOGO_PATH = next((p for p in LOGO_CANDIDATES if os.path.exists(p)), LOGO_CANDIDATES[0])


def _logo_base64() -> str | None:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


LOGO_B64 = _logo_base64()

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HoRiZooN",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🐉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────
# THEME — Neon Red / Black Glassmorphism
# ──────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

:root {
    --neon-red: #ff1744;
    --neon-red-bright: #ff4569;
    --neon-red-dim: rgba(255, 23, 68, 0.35);
    --glass-bg: rgba(20, 9, 10, 0.45);
    --glass-border: rgba(255, 23, 68, 0.35);
}

/* Base app background */
.stApp {
    background:
        radial-gradient(circle at 15% 20%, rgba(255, 23, 68, 0.16) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(255, 23, 68, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 50% 50%, rgba(120, 0, 20, 0.10) 0%, transparent 60%),
        #050203;
    background-attachment: fixed;
    font-family: 'Rajdhani', sans-serif;
    color: #f5e6e8;
}

/* Animated grid overlay */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,23,68,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,23,68,0.045) 1px, transparent 1px);
    background-size: 42px 42px;
    pointer-events: none;
    z-index: 0;
}

/* Header / Hero */
.hz-hero {
    text-align: center;
    padding: 2.2rem 1rem 1.6rem 1rem;
    margin-bottom: 1.5rem;
}
.hz-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 3rem;
    letter-spacing: 4px;
    color: #fff;
    text-shadow:
        0 0 8px var(--neon-red),
        0 0 22px var(--neon-red),
        0 0 45px rgba(255,23,68,0.6);
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
}
.hz-logo {
    height: 120px;
    width: auto;
    filter:
        drop-shadow(0 0 6px var(--neon-red))
        drop-shadow(0 0 18px rgba(255,23,68,0.7));
}
.hz-logo-small {
    height: 34px;
    width: auto;
    filter:
        drop-shadow(0 0 5px var(--neon-red))
        drop-shadow(0 0 12px rgba(255,23,68,0.6));
}
.hz-subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 500;
    letter-spacing: 3px;
    color: rgba(255, 200, 210, 0.65);
    text-transform: uppercase;
    font-size: 0.85rem;
    margin-top: 0.4rem;
}
.hz-divider {
    height: 2px;
    width: 140px;
    margin: 1rem auto 0 auto;
    background: linear-gradient(90deg, transparent, var(--neon-red), transparent);
    box-shadow: 0 0 12px var(--neon-red);
}

/* Glass card */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(18px) saturate(140%);
    -webkit-backdrop-filter: blur(18px) saturate(140%);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow:
        0 4px 30px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 0 22px rgba(255, 23, 68, 0.10);
    position: relative;
    z-index: 1;
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(255, 23, 68, 0.65);
    box-shadow:
        0 4px 30px rgba(0, 0, 0, 0.55),
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 0 32px rgba(255, 23, 68, 0.25);
}
.glass-card h3 {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.05rem;
    letter-spacing: 1.5px;
    color: var(--neon-red-bright);
    text-shadow: 0 0 10px rgba(255, 23, 68, 0.6);
    margin-top: 0;
    margin-bottom: 0.8rem;
    text-transform: uppercase;
}
.glass-card p, .glass-card li {
    font-size: 1rem;
    line-height: 1.6;
    color: #ecdadd;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10,3,4,0.95) 0%, rgba(15,5,7,0.98) 100%);
    border-right: 1px solid var(--glass-border);
}
section[data-testid="stSidebar"] * {
    color: #f2dde0 !important;
}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    font-family: 'Orbitron', sans-serif;
    color: var(--neon-red-bright) !important;
    text-shadow: 0 0 8px rgba(255,23,68,0.5);
    letter-spacing: 1px;
}

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stFileUploader section {
    background: rgba(255, 23, 68, 0.06) !important;
    border: 1px solid rgba(255, 23, 68, 0.4) !important;
    border-radius: 10px !important;
    color: #f5e6e8 !important;
}
.stTextInput input:focus {
    box-shadow: 0 0 0 2px rgba(255, 23, 68, 0.5) !important;
}

/* Buttons */
.stButton button, .stFormSubmitButton button {
    background: linear-gradient(135deg, #b3001b, #ff1744) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1.5px;
    font-weight: 700 !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 0 18px rgba(255, 23, 68, 0.45);
    transition: all 0.25s ease;
}
.stButton button:hover, .stFormSubmitButton button:hover {
    box-shadow: 0 0 30px rgba(255, 23, 68, 0.85), 0 0 60px rgba(255,23,68,0.3);
    transform: translateY(-1px);
}

/* Radio */
div[role="radiogroup"] label {
    color: #f2dde0 !important;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(14px);
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 16px rgba(255,23,68,0.12);
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(255,23,68,0.06) !important;
    border-radius: 10px !important;
    color: var(--neon-red-bright) !important;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #0a0304; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #ff1744, #7a000f);
    border-radius: 10px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,23,68,0.05);
    border-radius: 10px 10px 0 0;
    color: #f2dde0;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,23,68,0.18) !important;
    color: var(--neon-red-bright) !important;
    box-shadow: 0 0 14px rgba(255,23,68,0.4);
}

/* Status / spinner text */
.stSpinner > div { border-top-color: var(--neon-red) !important; }

/* Hide default footer/menu for cleaner look */
#MainMenu, footer { visibility: hidden; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa_pairs" not in st.session_state:
    st.session_state.qa_pairs = []          # (question, answer) tuples for RAG memory

# ──────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ──────────────────────────────────────────────────────────────────────────
logo_img_tag = f'<img src="data:image/png;base64,{LOGO_B64}" class="hz-logo" />' if LOGO_B64 else "🎙️"

st.markdown(
    f"""
    <div class="hz-hero">
        <div class="hz-title">{logo_img_tag} HoRiZooN</div>
        <div class="hz-subtitle">Meeting Intelligence · Transcribe · Summarize · Chat</div>
        <div class="hz-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR — INPUT CONTROLS
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f'<div style="text-align:center; margin-bottom:0.6rem;">'
            f'<img src="data:image/png;base64,{LOGO_B64}" class="hz-logo-small" /></div>',
            unsafe_allow_html=True,
        )
    st.markdown("#INPUT")

    source_type = st.radio("Source type", ["YouTube URL", "Upload local file"])

    source = None
    if source_type == "YouTube URL":
        source = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
    else:
        uploaded_file = st.file_uploader(
            "Upload audio / video file",
            type=["mp3", "wav", "m4a", "mp4", "mkv", "webm"],
        )
        if uploaded_file is not None:
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = tmp_path

    language = st.selectbox("Language", ["english", "hinglish"])

    st.markdown("---")
    run_clicked = st.button("Run Pipeline", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────
# PIPELINE EXECUTION
# ──────────────────────────────────────────────────────────────────────────
def run_pipeline(source: str, language: str = "english") -> dict:
    chunks = process_input(source)
    transcript = transcribe_all(chunks, language)
    title = generate_title(transcript)
    summary = summarize(transcript)
    action_item = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


if run_clicked:
    if not source:
        st.error("Please provide a YouTube URL or upload a file first.")
    else:
        with st.spinner("Processing… transcribing, summarizing, extracting insights"):
            try:
                st.session_state.result = run_pipeline(source, language)
                st.session_state.chat_history = []
                st.session_state.qa_pairs = []
                st.success(" Pipeline complete!")
            except Exception as e:
                st.error(f" Pipeline failed: {e}")

# ──────────────────────────────────────────────────────────────────────────
# RESULTS DISPLAY
# ──────────────────────────────────────────────────────────────────────────
result = st.session_state.result

if result:
    st.markdown(
        f"""
        <div class="glass-card">
            <h3>📌 Title</h3>
            <p>{result['title']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript = st.tabs(
        ["Sanshipt", "Maksad", "Conclusions", "Open Questions", "Transcript"]
    )

    with tab_summary:
        st.markdown(f'<div class="glass-card"><p>{result["summary"]}</p></div>', unsafe_allow_html=True)

    with tab_actions:
        st.markdown(f'<div class="glass-card"><p>{result["action_items"]}</p></div>', unsafe_allow_html=True)

    with tab_decisions:
        st.markdown(f'<div class="glass-card"><p>{result["key_decisions"]}</p></div>', unsafe_allow_html=True)

    with tab_questions:
        st.markdown(f'<div class="glass-card"><p>{result["open_questions"]}</p></div>', unsafe_allow_html=True)

    with tab_transcript:
        with st.expander("Show full transcript", expanded=False):
            st.markdown(f'<div class="glass-card"><p>{result["transcript"]}</p></div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────
    # CHAT WITH MEETING (RAG)
    # ──────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hz-hero" style="padding-top:0.5rem;">
            <div class="hz-title" style="font-size:1.8rem;">Chat With Your Meeting</div>
            <div class="hz-divider" style="width:90px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    question = st.chat_input("Ask something about this meeting…")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    answer = ask_question(
                        result["rag_chain"], question, st.session_state.qa_pairs
                    )
                except Exception as e:
                    answer = f" Error answering question: {e}"
                st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))
        st.session_state.qa_pairs.append((question, answer))
else:
    st.markdown(
        """
        <div class="glass-card" style="text-align:center; padding:2.5rem;">
            <h3>We Never Bow Down</h3>
            <p>Built By Krishna-Great <b>  Powered by PARADOX</b>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )