from fastapi import APIRouter, Header, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
from typing import Dict, List, Optional
from app.services.converter import ensure_workdirs, save_upload, safe_unlink, extract_pdf_text

router = APIRouter()

_SESSIONS: Dict[str, List[dict]] = {}
_DOCS: Dict[str, str] = {}
_MAX_TURNS = 20


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    configured: bool
    provider: str


def _get_history(session_id: str) -> List[dict]:
    history = _SESSIONS.setdefault(session_id, [])
    return history[-_MAX_TURNS:]


def _generate_reply(
    provider: str,
    api_key: str,
    model: str,
    history: List[dict],
    doc_context: str,
    prompt: Optional[str] = None,
) -> ChatResponse:
    if provider == "gemini":
        try:
            from google import genai
        except Exception:
            return ChatResponse(
                reply="Gemini SDK not installed. Install requirements-gemini.txt.",
                configured=False,
                provider=provider,
            )

        try:
            client = genai.Client(api_key=api_key)
            conversation_lines = ["System: You are DocuMind, a concise local document assistant."]
            if doc_context:
                conversation_lines.append(f"Document context:\n{doc_context}")
            if prompt:
                conversation_lines.append(f"User: {prompt}")
            else:
                for msg in history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    conversation_lines.append(f"{role.capitalize()}: {content}")
            conversation = "\n".join(conversation_lines)
            resp = client.models.generate_content(
                model=model,
                contents=conversation,
            )
            reply = getattr(resp, "text", None) or "No response text."
        except Exception as exc:
            return ChatResponse(
                reply=f"Gemini error: {exc}",
                configured=False,
                provider=provider,
            )
    elif provider == "groq":
        try:
            from groq import Groq
        except Exception:
            return ChatResponse(
                reply="Groq SDK not installed. Install requirements-groq.txt.",
                configured=False,
                provider=provider,
            )

        try:
            client = Groq(api_key=api_key)
            messages = [
                {"role": "system", "content": "You are DocuMind, a concise local document assistant."},
            ]
            if doc_context:
                messages.append({"role": "system", "content": f"Document context:\n{doc_context}"})
            if prompt:
                messages.append({"role": "user", "content": prompt})
            else:
                messages.extend(history)

            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
            )
            reply = resp.choices[0].message.content or "No response text."
        except Exception as exc:
            return ChatResponse(
                reply=f"Groq error: {exc}",
                configured=False,
                provider=provider,
            )
    else:
        return ChatResponse(
            reply="Unknown provider. Set CHAT_PROVIDER=groq or gemini.",
            configured=False,
            provider=provider,
        )

    return ChatResponse(reply=reply, configured=True, provider=provider)


@router.post("/")
def chat(
    req: ChatRequest,
    x_session_id: Optional[str] = Header(default=None),
) -> ChatResponse:
    session_id = x_session_id or "default"
    provider = os.environ.get("CHAT_PROVIDER", "groq").strip().lower()
    api_key = os.environ.get("CHAT_API_KEY", "").strip()
    model = os.environ.get("CHAT_MODEL", "llama-3.1-8b-instant").strip()

    if not api_key:
        return ChatResponse(
            reply="Chatbot is not configured yet. Set CHAT_API_KEY to enable Gemini.",
            configured=False,
            provider=provider,
        )

    history = _get_history(session_id)
    doc_context = _DOCS.get(session_id, "")
    history.append({"role": "user", "content": req.message})

    resp = _generate_reply(provider, api_key, model, history, doc_context)
    if resp.configured:
        history.append({"role": "assistant", "content": resp.reply})
        _SESSIONS[session_id] = history[-_MAX_TURNS:]
    return resp


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(default=None),
):
    session_id = x_session_id or "default"
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    ensure_workdirs()
    src_path = await save_upload(file)

    try:
        text = extract_pdf_text(src_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        background_tasks.add_task(safe_unlink, src_path)

    if not text:
        raise HTTPException(status_code=500, detail="No text extracted from PDF.")

    _DOCS[session_id] = text
    return {"status": "ok", "chars": len(text)}


@router.post("/summary")
def summarize(
    x_session_id: Optional[str] = Header(default=None),
) -> ChatResponse:
    session_id = x_session_id or "default"
    provider = os.environ.get("CHAT_PROVIDER", "groq").strip().lower()
    api_key = os.environ.get("CHAT_API_KEY", "").strip()
    model = os.environ.get("CHAT_MODEL", "llama-3.1-8b-instant").strip()

    doc_context = _DOCS.get(session_id, "")
    if not doc_context:
        return ChatResponse(
            reply="No document loaded. Use 'Attach PDF to Chat' first.",
            configured=False,
            provider=provider,
        )

    prompt = "Summarize the document in 6-10 bullet points. Use concise language."
    return _generate_reply(provider, api_key, model, [], doc_context, prompt=prompt)
