
import logging
import os
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Deque

from groq import Groq
from dotenv import load_dotenv

from config import (
    GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS, SYSTEM_PROMPT, MAX_HISTORY
)
from vector_store import search_similar, build_or_load_index

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | chatbot | %(message)s")
logger = logging.getLogger(__name__)

_sessions: Dict[str, Deque[Dict]] = {}
SESSION_TTL_HOURS = 24
TOP_K = 10   # Increased from 5 to 10 for better retrieval


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found in .env file")
    return Groq(api_key=api_key)


def cleanup_old_sessions():
    now = datetime.utcnow()
    to_delete = []
    for sid, history in _sessions.items():
        if history:
            last_ts = history[-1].get("timestamp")
            if last_ts and (now - last_ts) > timedelta(hours=SESSION_TTL_HOURS):
                to_delete.append(sid)
    for sid in to_delete:
        del _sessions[sid]


def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, Deque[Dict]]:
    cleanup_old_sessions()
    if not session_id:
        session_id = str(uuid.uuid4())
    if session_id not in _sessions:
        _sessions[session_id] = deque(maxlen=MAX_HISTORY)
    return session_id, _sessions[session_id]


def add_to_history(session_id: str, role: str, content: str):
    _, history = get_or_create_session(session_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })


def get_history_for_prompt(session_id: str) -> List[Dict]:
    if session_id not in _sessions:
        return []
    return [{"role": m["role"], "content": m["content"]} for m in _sessions[session_id]]


def retrieve_context(query: str, top_k: int = TOP_K) -> tuple[str, List[Dict]]:
    results = search_similar(query, top_k=top_k)
    if not results:
        return "", []

    context_parts = []
    sources = []
    for i, r in enumerate(results, 1):
        chunk = r.get("chunk_text", "").strip()
        if chunk:
            context_parts.append(f"[Source {i}]\n{chunk}")
            sources.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "score": round(r.get("score", 0), 3)
            })

    context_str = "\n\n---\n\n".join(context_parts)
    return context_str, sources


def generate_answer(question: str, session_id: Optional[str] = None, top_k: int = TOP_K) -> Dict:
    try:
        build_or_load_index()
        session_id, _ = get_or_create_session(session_id)
        add_to_history(session_id, "user", question)

        context, sources = retrieve_context(question, top_k=top_k)

        if not context:
            answer = "Sorry, I could not find that information in the knowledge base."
            add_to_history(session_id, "assistant", answer)
            return {
                "answer": answer,
                "session_id": session_id,
                "sources": [],
                "error": None
            }

        history_msgs = get_history_for_prompt(session_id)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Relevant content from website:\n\n{context}"}
        ]
        messages.extend(history_msgs[-8:])
        messages.append({"role": "user", "content": question})

        client = get_groq_client()
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
            top_p=0.9
        )

        answer = completion.choices[0].message.content.strip()
        add_to_history(session_id, "assistant", answer)

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": sources[:5],
            "error": None
        }

    except Exception as e:
        logger.error(f"Error in generate_answer: {e}")
        return {
            "answer": "Sorry, I could not find that information in the knowledge base.",
            "session_id": session_id or str(uuid.uuid4()),
            "sources": [],
            "error": str(e)
        }