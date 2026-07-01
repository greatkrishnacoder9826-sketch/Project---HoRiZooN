import yt_dlp
from pydub import AudioSegment
import os
import platform
import shutil
import glob
import tempfile

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

IS_WINDOWS = platform.system() == "Windows"
FFMPEG_EXE_NAME = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
FFPROBE_EXE_NAME = "ffprobe.exe" if IS_WINDOWS else "ffprobe"


def find_ffmpeg_dir() -> str:
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return os.path.dirname(ffmpeg_in_path)

    if IS_WINDOWS:
        winget_pattern = os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*-full_build\bin"
        )
        matches = glob.glob(winget_pattern)
        for match in matches:
            if os.path.isfile(os.path.join(match, "ffmpeg.exe")):
                return match

    raise FileNotFoundError(
        "ffmpeg nahi mila! Windows par 'winget install Gyan.FFmpeg' chalao. "
        "Linux/Streamlit Cloud par packages.txt mein 'ffmpeg' add karo."
    )


FFMPEG_PATH = os.getenv("FFMPEG_PATH") or find_ffmpeg_dir()
ffmpeg_exe = os.path.join(FFMPEG_PATH, FFMPEG_EXE_NAME)
ffprobe_exe = os.path.join(FFMPEG_PATH, FFPROBE_EXE_NAME)

if not os.path.isfile(ffmpeg_exe):
    raise FileNotFoundError(f"{FFMPEG_EXE_NAME} nahi mila yaha: {ffmpeg_exe}")

if not os.path.isfile(ffprobe_exe):
    raise FileNotFoundError(f"{FFPROBE_EXE_NAME} nahi mila yaha: {ffprobe_exe}")

AudioSegment.converter = ffmpeg_exe
AudioSegment.ffprobe   = ffprobe_exe

if FFMPEG_PATH not in os.environ["PATH"]:
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ["PATH"]

print(f"Using ffmpeg from: {FFMPEG_PATH}")


def get_cookies_file() -> str | None:
    # Pehle local cookies.txt check karo
    local_cookies = "cookies.txt"
    if os.path.isfile(local_cookies):
        print("Using local cookies.txt")
        return local_cookies

    # Streamlit secrets se check karo
    try:
        import streamlit as st
        cookies_content = st.secrets.get("YOUTUBE_COOKIES", None)
        if cookies_content:
            tmp = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            )
            tmp.write(cookies_content)
            tmp.close()
            print("Using cookies from Streamlit secrets")
            return tmp.name
    except Exception:
        pass

    # Env variable se try karo
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        tmp = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        )
        tmp.write(cookies_content)
        tmp.close()
        return tmp.name

    print("Warning: No cookies found — YouTube may block download (403)")
    return None


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {                                        # ✅ function ke andar
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": FFMPEG_PATH,
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded", "mweb"],
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    }

    cookies_file = get_cookies_file()
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")

    if cookies_file and cookies_file != "cookies.txt":
        try:
            os.unlink(cookies_file)
        except Exception:
            pass

    return filename


def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_convert.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def split_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
        converted = convert_to_wav(wav_path)
    else:
        print("Detected local file. Converting to wav...")
        converted = convert_to_wav(source)

    print("Chunking audio...")
    chunks = split_audio(converted)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks