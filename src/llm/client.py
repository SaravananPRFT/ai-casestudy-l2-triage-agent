"""
LLM client factory.

Perficient's Portkey gateway exposes an OpenAI-compatible API
(/v1/chat/completions), so we use ChatOpenAI — exactly the same pattern
as CertMasterAI's generate_with_portkey().

Required env vars:
  PORTKEY_BASE_URL   — https://portkeygateway.perficient.com/v1
  PORTKEY_API_KEY    — Portkey auth token
  EXTRA_HEADERS      — e.g. x-portkey-provider:@aws-bedrock-use2
  ANTHROPIC_MODEL    — e.g. us.anthropic.claude-sonnet-4-6
"""
import os
from functools import lru_cache

DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-6"


def _parse_extra_headers(raw: str) -> dict[str, str]:
    """Parse 'key:value,key2:value2' into a dict."""
    headers: dict[str, str] = {}
    for part in (raw or "").split(","):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            headers[k.strip()] = v.strip()
    return headers


@lru_cache(maxsize=1)
def get_llm(model: str | None = None):
    """Return a cached ChatOpenAI client pointed at the Perficient Portkey gateway."""
    from langchain_openai import ChatOpenAI

    resolved    = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    base_url    = os.getenv("PORTKEY_BASE_URL", "https://portkeygateway.perficient.com/v1")
    api_key     = os.getenv("PORTKEY_API_KEY", "")
    extra_raw   = os.getenv("EXTRA_HEADERS", "")

    return ChatOpenAI(
        model=resolved,
        base_url=base_url,
        api_key=api_key,
        default_headers=_parse_extra_headers(extra_raw),
        temperature=0,
        max_tokens=1024,
    )
