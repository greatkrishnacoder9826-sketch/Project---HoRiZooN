import yt_dlp
from pydub import AudioSegment
import os
import platform
import shutil
import glob

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

IS_WINDOWS = platform.system() == "Windows"
FFMPEG_EXE_NAME = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
FFPROBE_EXE_NAME = "ffprobe.exe" if IS_WINDOWS else "ffprobe"


def find_ffmpeg_dir() -> str:
    """
    ffmpeg/ffprobe ko dhoondta hai:
    1. Pehle system PATH mein check karta hai (shutil.which) — Linux/Streamlit Cloud
       par packages.txt se installed ffmpeg yahin milega.
    2. Windows par WinGet ke common install location mein glob se search karta hai
       (hardcoded version folder ki jagah).
    3. Agar kahin nahi mila, clear error deta hai
    """
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return os.path.dirname(ffmpeg_in_path)

    if IS_WINDOWS:
        # WinGet ke under version folder ka naam badalta rehta hai (e.g. ffmpeg-8.1.1-full_build)
        winget_pattern = os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*-full_build\bin"
        )
        matches = glob.glob(winget_pattern)
        for match in matches:
            if os.path.isfile(os.path.join(match, "ffmpeg.exe")):
                return match

    raise FileNotFoundError(
        "ffmpeg nahi mila! Windows par 'winget install Gyan.FFmpeg' chalao aur terminal "
        "restart karo. Linux/Streamlit Cloud par packages.txt mein 'ffmpeg' add karo, "
        "ya FFMPEG_PATH env variable set karo apne ffmpeg bin folder ke path se."
    )


# Agar user ne env variable se manually path diya hai to wahi use karo,
# warna auto-detect karo
FFMPEG_PATH = os.getenv("FFMPEG_PATH") or find_ffmpeg_dir()

ffmpeg_exe = os.path.join(FFMPEG_PATH, FFMPEG_EXE_NAME)
ffprobe_exe = os.path.join(FFMPEG_PATH, FFPROBE_EXE_NAME)

if not os.path.isfile(ffmpeg_exe):
    raise FileNotFoundError(f"{FFMPEG_EXE_NAME} nahi mila yaha: {ffmpeg_exe}")

if not os.path.isfile(ffprobe_exe):
    raise FileNotFoundError(
        f"{FFPROBE_EXE_NAME} nahi mila yaha: {ffprobe_exe}\n"
        "Iska matlab aapka ffmpeg install incomplete hai (sirf ffmpeg hai, ffprobe nahi). "
        "Windows: 'winget uninstall Gyan.FFmpeg' karke phir 'winget install Gyan.FFmpeg' se "
        "fresh full_build install karo, ya https://www.gyan.dev/ffmpeg/builds/ se "
        "'ffmpeg-release-full' zip manually download karke usme se ffmpeg.exe aur ffprobe.exe "
        "dono ek hi bin folder mein rakho."
    )

AudioSegment.converter = ffmpeg_exe
AudioSegment.ffprobe   = ffprobe_exe

# IMPORTANT: pydub ka internal mediainfo_json (probing ke liye) AudioSegment.ffprobe
# attribute ko IGNORE karta hai — wo sirf system PATH mein "ffprobe" naam dhoondta hai
# (apne which() helper se). Isliye sirf attribute set karna kaafi nahi hai —
# ffmpeg ka bin folder PATH mein bhi add karna zaroori hai, warna probing step
# par phir se WinError 2 aayega.
if FFMPEG_PATH not in os.environ["PATH"]:
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ["PATH"]

print(f"Using ffmpeg from: {FFMPEG_PATH}")

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": FFMPEG_PATH,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video to wav format using pydub"""
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
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def process_input(source: str) -> list:
    """URL ya local file — dono handle karta hai"""
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)  # pehle download
        converted = convert_to_wav(wav_path)        # phir convert
    else:
        print("Detected local file. Converting to wav...")
        converted = convert_to_wav(source)

    print("Chunking audio...")
    chunks = split_audio(converted)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks