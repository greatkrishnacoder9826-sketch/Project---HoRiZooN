from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2
    )

def build_chain(system_prompt: str):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}"),
    ])
    return prompt | llm | StrOutputParser()


def extract_action_items(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )
    return chain.invoke({"text": transcript})


def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )
    return chain.invoke({"text": transcript})


def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )
    return chain.invoke({"text": transcript})


def chunk_transcript(transcript: str, chunk_size: int = 8000, chunk_overlap: int = 500):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(transcript)


def extract_action_items_long(transcript: str) -> str:
    chunks = chunk_transcript(transcript)

    if len(chunks) == 1:
        return extract_action_items(transcript)

    map_chain = build_chain(
        "You are analyzing PART of a longer meeting transcript. "
        "Extract any action items found in THIS PORTION only. "
        "For each provide: Task, Owner, Deadline (if mentioned, else 'Not specified'). "
        "If none found in this part, just say 'None in this part.' "
        "Don't worry about duplicates across parts, that will be handled later."
    )

    partial_results = []
    for i, chunk in enumerate(chunks):
        result = map_chain.invoke({"text": chunk})
        partial_results.append(f"--- Part {i+1} ---\n{result}")

    combined = "\n\n".join(partial_results)

    reduce_chain = build_chain(
        "You are given action items extracted from different parts of the SAME "
        "meeting transcript. Merge them into one clean, deduplicated list. "
        "If the same task appears in multiple parts (even if worded slightly "
        "differently), merge into one entry. "
        "Format as numbered list: Task, Owner, Deadline. "
        "If nothing found anywhere, say 'No action items found.'"
    )

    return reduce_chain.invoke({"text": combined})