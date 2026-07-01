import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever


def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])


def format_history(history: list) -> str:
    """history = list of (question, answer) tuples"""
    if not history:
        return "No previous conversation yet."
    lines = []
    for q, a in history[-5:]:          # sirf last 5 exchanges rakho, prompt bloat na ho
        lines.append(f"User: {q}\nAssistant: {a}")
    return "\n\n".join(lines)


def _build_chain(vector_store):
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question
based on the meeting transcript context provided below.

Use the recent conversation history ONLY to resolve references like
"the first point", "explain that again", "what about the second one" — 
figure out what the user is referring to from the history, then answer
using the transcript context.

If the answer is not found in the context, say:
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Meeting transcript context:
{context}

Recent conversation history:
{chat_history}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": (lambda x: x["question"]) | retriever | RunnableLambda(format_docs),
            "chat_history": lambda x: format_history(x.get("chat_history", [])),
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def build_rag_chain(transcript: str):
    vector_store = build_vector_store(transcript)
    return _build_chain(vector_store)


def load_rag_chain():
    vector_store = load_vector_store()
    return _build_chain(vector_store)


def ask_question(rag_chain, question: str, chat_history: list = None) -> str:
    chat_history = chat_history or []
    print(f"Question : {question}")
    answer = rag_chain.invoke({"question": question, "chat_history": chat_history})
    print(f"answer :{answer}")
    return answer