from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.summarize import summarize, generate_title

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.summarize import summarize, generate_title

source = "https://youtu.be/JKCxiBghzwI"

print("Step 1: Downloading & chunking audio...")
chunks = process_input(source)
print(f"Step 1 done. {len(chunks)} chunk(s) created.\n")

print("Step 2: Transcribing...")
transcript = transcribe_all(chunks)
print("Step 2 done.\n")
print("=== TRANSCRIPT ===")
print(transcript[:1000], "...\n")  # poora transcript bohot lamba ho sakta hai, isliye preview

print("Step 3: Generating title...")
title = generate_title(transcript)
print(f"\n=== TITLE ===\n{title}\n")

print("Step 4: Summarizing...")
summary = summarize(transcript)
print(f"\n=== SUMMARY ===\n{summary}\n")

print("Step 5: Extracting action items...")
actions = extract_action_items(transcript)
print(f"\n=== ACTION ITEMS ===\n{actions}\n")

print("Step 6: Extracting key decisions...")
decisions = extract_key_decisions(transcript)
print(f"\n=== KEY DECISIONS ===\n{decisions}\n")

print("Step 7: Extracting open questions...")
questions = extract_questions(transcript)
print(f"\n=== OPEN QUESTIONS ===\n{questions}\n")