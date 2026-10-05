import json
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.prompts import FORMATTER_SYSTEM_PROMPT
from app.core.llm_pool import load_keys_from_env, RotatingChatModel

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = load_keys_from_env()
    return _pool

_formatter_model = None

def _get_formatter_model():
    global _formatter_model
    if _formatter_model is None:
        _formatter_model = RotatingChatModel(_get_pool(), model_name="openai/gpt-oss-20b")
    return _formatter_model

def format_reply(
    vehicle_summary: str,
    fluid_type: str,
    specs_source: str,
    specs_data: dict | None,
    products_status: str,
    products: list,
    warnings: list,
    clarifications: list,
    verification: dict | None,
    rationale: str,
    confidence: str,
    fallback_message: str = "",
) -> str:
    input_block = (
        "DATA TO FORMAT:\n"
        f"- Vehicle: {vehicle_summary}\n"
        f"- Fluid type: {fluid_type}\n"
        f"- Specs source: {specs_source}\n"
        f"- Specs: {json.dumps(specs_data, ensure_ascii=False) if specs_data else 'null'}\n"
        f"- Products status: {products_status}\n"
        f"- Products: {json.dumps(products, ensure_ascii=False)}\n"
        f"- Warnings: {json.dumps(warnings, ensure_ascii=False)}\n"
        f"- Clarifications: {json.dumps(clarifications, ensure_ascii=False)}\n"
        f"- Verification: {json.dumps(verification, ensure_ascii=False) if verification else 'null'}\n"
        f"- Rationale: {rationale}\n"
        f"- Confidence: {confidence}\n"
        f"- Fallback message (use only if specs are missing or an error occurred): {fallback_message}\n"
    )
    messages = [
        SystemMessage(content=FORMATTER_SYSTEM_PROMPT),
        HumanMessage(content=input_block),
    ]
    response = _get_formatter_model().invoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content.strip()
