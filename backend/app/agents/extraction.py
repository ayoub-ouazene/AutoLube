import json
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.prompts import INTENT_SYSTEM_PROMPT
from app.core.llm_pool import load_keys_from_env, RotatingChatModel

_pool = None
_extraction_model = None


def _get_extraction_model():
    global _pool, _extraction_model
    if _extraction_model is None:
        _pool = load_keys_from_env()
        _extraction_model = RotatingChatModel(_pool, model_name="openai/gpt-oss-20b")
    return _extraction_model

def _compact_history(history: list, max_items: int = 4) -> list[dict]:
    """Return only the last N messages, with assistant replies truncated."""
    out = []
    for m in history[-max_items:]:
        role = "user" if type(m).__name__ == "HumanMessage" else "assistant"
        content = getattr(m, "content", "")
        if isinstance(content, list):
            content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
        out.append({"role": role, "text": content[:300]})
    return out

def extract_intent(user_message: str, history: list, current_vehicle: dict) -> dict:
    payload = {
        "message": user_message,
        "recent_history": _compact_history(history),
        "current_vehicle": current_vehicle or {},
    }
    messages = [
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ]
    response = _get_extraction_model().invoke(messages)
    raw = response.content
    if isinstance(raw, list):
        raw = "".join(b.get("text", "") for b in raw if isinstance(b, dict))
    raw = raw.strip()
    # Strip code fences if the model adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[extraction] JSON parse failed: {e}\nRaw: {raw[:400]}")
        return {
            "flow": "conversational",
            "params": {},
            "missing": [],
            "reply_hint": "Je n'ai pas compris votre message. Pouvez-vous reformuler ?",
        }
