import os
import time
from dataclasses import dataclass
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


@dataclass
class KeyEntry:
    name: str
    provider: str          # "groq" | "openrouter"
    api_key: str
    model: str
    tier: int              # 0 = primary (Groq), 1 = backup (OpenRouter)
    cooldown_until: float = 0.0
    last_used: float = 0.0
    failure_count: int = 0


class KeyPool:
    def __init__(self, entries: list[KeyEntry]):
        self.entries = entries

    def _available(self) -> list[KeyEntry]:
        now = time.time()
        ready = [e for e in self.entries if e.cooldown_until <= now]
        return ready if ready else self.entries  # all cooling → try soonest anyway

    def pick(self) -> KeyEntry:
        ready = self._available()
        ready.sort(key=lambda e: (e.tier, e.last_used))
        entry = ready[0]
        entry.last_used = time.time()
        return entry

    def mark_rate_limited(self, entry: KeyEntry, seconds: int = 60):
        entry.cooldown_until = time.time() + seconds
        entry.failure_count += 1

    def mark_ok(self, entry: KeyEntry):
        entry.failure_count = 0


def build_model(entry: KeyEntry):
    if entry.provider == "groq":
        return ChatGroq(model=entry.model, api_key=entry.api_key, temperature=0.0)
    if entry.provider == "openrouter":
        return ChatOpenAI(
            model=entry.model,
            api_key=entry.api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.0,
        )
    raise ValueError(f"Unknown provider: {entry.provider}")


def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc).lower()
    return ("429" in s) or ("rate" in s and "limit" in s) or ("tpm" in s) or ("rpm" in s)


def load_keys_from_env() -> KeyPool:
    """GROQ_KEYS=key1,key2,key3  OPENROUTER_KEYS=key1,key2"""
    entries: list[KeyEntry] = []

    for i, k in enumerate(os.getenv("GROQ_KEYS", "").split(",")):
        k = k.strip()
        if k:
            entries.append(KeyEntry(
                name=f"groq-{i+1}",
                provider="groq",
                api_key=k,
                model="openai/gpt-oss-120b",
                tier=0,
            ))

    for i, k in enumerate(os.getenv("OPENROUTER_KEYS", "").split(",")):
        k = k.strip()
        if k:
            entries.append(KeyEntry(
                name=f"openrouter-{i+1}",
                provider="openrouter",
                api_key=k,
                model="nvidia/nemotron-3.5-lightning:free",
                tier=1,
            ))

    if not entries:
        raise RuntimeError("No API keys configured.")
    return KeyPool(entries)


def run_with_failover(pool: KeyPool, fn):
    """Try each pool entry until one succeeds. fn(model) -> result."""
    tried: set[str] = set()
    last_error: Exception | None = None

    for _ in range(len(pool.entries)):
        entry = pool.pick()
        if entry.name in tried:
            break
        tried.add(entry.name)

        try:
            model = build_model(entry)
            result = fn(model)
            pool.mark_ok(entry)
            print(f"[LLM] success with {entry.name}")
            return result
        except Exception as e:
            if _is_rate_limit(e):
                pool.mark_rate_limited(entry, seconds=60)
                print(f"[LLM] rate-limited on {entry.name}, cooling 60s")
            else:
                pool.mark_rate_limited(entry, seconds=10)
                print(f"[LLM] error on {entry.name}: {e}")
            last_error = e

    raise RuntimeError(f"All API keys exhausted. Last error: {last_error}")