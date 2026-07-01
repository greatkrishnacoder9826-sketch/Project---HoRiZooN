from faster_whisper import WhisperModel
import os
import requests

# Whisper fallback ke liye
whisper_model = None

# Sarvam config
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


def load_whisper():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print("Whisper model loaded successfully")


def transcribe_with_sarvam(chunk_path: str) -> str:
    """Sarvam API se Hindi transcription"""
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY .env mein nahi hai!")

    with open(chunk_path, "rb") as f:
        response = requests.post(
            SARVAM_STT_URL,
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": (os.path.basename(chunk_path), f, "audio/wav")},
            data={"language_code": "hi-IN", "model": "saaras:v2.5"}
        )

    if response.status_code == 200:
        return response.json().get("transcript", "")
    else:
        print(f"Sarvam error: {response.status_code} — Whisper pe fallback")
        return None


def transcribe_with_whisper(chunk_path: str, translate: bool = False) -> str:
    """Whisper fallback"""
    load_whisper()
    task = "translate" if translate else "transcribe"
    segments, _ = whisper_model.transcribe(chunk_path, task=task, language="hi")
    return " ".join([seg.text for seg in segments])


def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:
    """Pehle Sarvam try karo, fail hone pe Whisper"""
    if SARVAM_API_KEY:
        result = transcribe_with_sarvam(chunk_path)
        if result:
            return result
    return transcribe_with_whisper(chunk_path, translate)


def transcribe_all(chunks: list, language: str = "english") -> str:
    """language: 'english' -> Whisper translate mode (final text English mein aayega)
    'hinglish' -> original language transcribe (mixed Hindi/English jaisa bola gaya waisa)"""
    translate = language.lower().strip() == "english"

    full_text = ""
    for i, chunk in enumerate(chunks):
        print(f"Transcribing Chunk {i+1}/{len(chunks)}...")
        full_text += transcribe_chunk(chunk, translate=translate) + " "
    return full_text.strip()