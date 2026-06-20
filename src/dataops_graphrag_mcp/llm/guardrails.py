"""
Lightweight LLM guardrails for input screening (report §5).

Runs an inexpensive content-safety check on the user question before the
main pipeline executes.  When the LLM is not configured the check is skipped
so that local/test environments still work without credentials.
"""

import json
from dataops_graphrag_mcp.common.logging import get_logger
from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.llm.prompts import GUARDRAIL_INPUT_PROMPT

_log = get_logger(__name__)

# Keywords that bypass the LLM call and are immediately rejected.
# Kept intentionally narrow to avoid false positives.
_HARD_BLOCK_TERMS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your system prompt",
    "you are now",
    "jailbreak",
]


def _hard_block(message: str) -> bool:
    lower = message.lower()
    return any(term in lower for term in _HARD_BLOCK_TERMS)


def check_input(message: str) -> dict:
    """
    Return {"safe": bool, "reason": str}.

    Order of checks:
    1. Hard keyword block (no LLM call needed).
    2. LLM-based classification when API key is present.
    3. Default-allow when LLM is not configured.
    """
    if not message or not message.strip():
        return {"safe": False, "reason": "Empty message."}

    if _hard_block(message):
        _log.warning("Guardrail hard-blocked message (prompt injection pattern).")
        return {"safe": False, "reason": "Prompt injection pattern detected."}

    if not settings.anthropic_api_key:
        return {"safe": True, "reason": "Guardrail LLM check skipped (no API key)."}

    try:
        from dataops_graphrag_mcp.llm.provider import get_chat_model

        response = get_chat_model().invoke(
            GUARDRAIL_INPUT_PROMPT.format(message=message)
        )
        result = json.loads(response.content)
        return {"safe": bool(result.get("safe", True)), "reason": result.get("reason", "")}
    except json.JSONDecodeError:
        _log.warning("Guardrail JSON parse error; defaulting to safe=True.")
        return {"safe": True, "reason": "Guardrail parse error; allowed through."}
    except Exception as exc:
        _log.error("Guardrail check failed (%s); defaulting to safe=True.", exc)
        return {"safe": True, "reason": f"Guardrail error: {exc}"}
