import os
import time
from dataclasses import dataclass
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.core.exceptions import (
    AppError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)


# Threshold (seconds) separating a short cooldown (TPM, ~60s) from a long
# one (TPD, ~600s). Used by KeyPool._available() to decide whether to
# prefer Groq or OpenRouter when every entry is cooling.
SHORT_COOLDOWN_THRESHOLD = 120

# Maximum time (seconds) pick() will sleep waiting for a near-ready Groq
# before falling back to OpenRouter. Set to 0 to disable waiting.
WAIT_FOR_GROQ_THRESHOLD = 20


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

    def _available(self, exclude: set[str] | None = None) -> list[KeyEntry]:
        """Return entries that are not cooling and not in `exclude`.

        Normal case: at least one entry has expired its cooldown. Return only
        those, sorted by (tier, last_used) so tier-0 Groq wins over tier-1
        OpenRouter, and least-recently-used wins inside a tier.

        Fallback case: every non-excluded entry is still cooling. Then decide
        the tier order based on how long Groq needs to recover:

          - If the soonest Groq will be ready within SHORT_COOLDOWN_THRESHOLD
            (TPM-style blip), prefer Groq (sort by tier asc, then cooldown).
          - Otherwise (Groq stuck on TPD, ~600s), prefer OpenRouter (sort by
            tier desc, then cooldown).
        """
        now = time.time()
        exclude = exclude or set()
        ready = [
            e for e in self.entries
            if e.cooldown_until <= now and e.name not in exclude
        ]
        if ready:
            ready.sort(key=lambda e: (e.tier, e.last_used))
            return ready

        pool = [e for e in self.entries if e.name not in exclude]
        if not pool:
            return []

        groq_entries = [e for e in pool if e.tier == 0]
        if groq_entries:
            soonest_groq_remaining = min(e.cooldown_until for e in groq_entries) - now
            prefer_groq = soonest_groq_remaining <= SHORT_COOLDOWN_THRESHOLD
        else:
            prefer_groq = False

        if prefer_groq:
            pool.sort(key=lambda e: (e.tier, e.cooldown_until))
        else:
            pool.sort(key=lambda e: (-e.tier, e.cooldown_until))
        return pool

    def pick(self, exclude: set[str] | None = None) -> KeyEntry:
        """Select a pool entry.

        Order of preference:
          1. A Groq entry that is already ready (cooldown expired).
          2. If only non-Groq is ready (e.g. OpenRouter) but a Groq will be
             ready within WAIT_FOR_GROQ_THRESHOLD seconds, sleep and wait for
             the Groq. This avoids burning OpenRouter's budget on a TPM blip
             that is about to clear.
          3. The first ready non-Groq entry (e.g. OpenRouter), if the Groq is
             stuck on a long cooldown (TPD, or the start of a TPM window).
          4. If nothing is ready, and the soonest-to-recover is within
             WAIT_FOR_GROQ_THRESHOLD, sleep for that entry (fallback path for
             brief all-cooling scenarios).
          5. Otherwise, return the all-cooling fallback ordering from
             _available() (prefer Groq if its cooldown is short, else
             OpenRouter).
        """
        exclude = exclude or set()
        total_waited = 0.0

        while True:
            now = time.time()
            available = self._available(exclude=exclude)
            truly_ready = [e for e in available if e.cooldown_until <= now]

            # 1. Ready Groq exists — take it, no wait.
            ready_groq = [e for e in truly_ready if e.tier == 0]
            if ready_groq:
                entry = ready_groq[0]
                entry.last_used = now
                return entry

            # 2/3. Only non-Groq is ready. Maybe wait for a near-ready Groq.
            if truly_ready:
                cooling_groq = [
                    e for e in self.entries
                    if e.tier == 0
                    and e.name not in exclude
                    and e.cooldown_until > now
                ]
                if cooling_groq:
                    soonest_ready_at = min(e.cooldown_until for e in cooling_groq)
                    wait = soonest_ready_at - now
                    if (
                        WAIT_FOR_GROQ_THRESHOLD > 0
                        and 0 < wait <= WAIT_FOR_GROQ_THRESHOLD
                        and total_waited + wait <= WAIT_FOR_GROQ_THRESHOLD + 5
                    ):
                        print(
                            f"[LLM] waiting {wait:.1f}s for Groq "
                            f"(preferring over {truly_ready[0].name})"
                        )
                        time.sleep(wait + 0.2)
                        total_waited += wait + 0.2
                        continue
                entry = truly_ready[0]
                entry.last_used = now
                return entry

            # 4. Nothing ready at all — all cooling. Wait briefly if soonest
            #    is within WAIT_FOR_GROQ_THRESHOLD, else fall through.
            non_excluded = [e for e in self.entries if e.name not in exclude]
            if not non_excluded:
                raise ProviderUnavailableError(
                    "No available pool entries (all excluded or empty pool)"
                )
            soonest_ready_at = min(e.cooldown_until for e in non_excluded)
            wait = soonest_ready_at - now
            if (
                WAIT_FOR_GROQ_THRESHOLD > 0
                and 0 < wait <= WAIT_FOR_GROQ_THRESHOLD
                and total_waited + wait <= WAIT_FOR_GROQ_THRESHOLD + 5
            ):
                print(
                    f"[LLM] all entries cooling; "
                    f"waiting {wait:.1f}s for soonest to recover"
                )
                time.sleep(wait + 0.2)
                total_waited += wait + 0.2
                continue

            # 5. Give up waiting; return the all-cooling fallback ordering.
            entry = available[0]
            entry.last_used = now
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


def _cooldown_seconds(exc: Exception) -> int:
    """Return cooldown seconds for a failed provider call.

    TPD (tokens per day) resets on a ~10 minute window, so a 60s cooldown
    would let the key come back and immediately re-fail. Use 600s.
    TPM (tokens per minute) resets in ~60s. Other errors get a short 10s.
    """
    s = str(exc).lower()
    if "per day" in s or "tpd" in s or "tokens per day" in s:
        return 600
    if _is_rate_limit(exc):
        return 60
    return 10


def _classify_provider_error(exc: Exception) -> type[AppError]:
    s = str(exc).lower()
    if "429" in s or "rate" in s and "limit" in s or "tpm" in s or "rpm" in s:
        return RateLimitError
    if "timeout" in s or "timed out" in s:
        return ProviderTimeoutError
    if "503" in s or "502" in s or "unavailable" in s or "overloaded" in s:
        return ProviderUnavailableError
    return ProviderUnavailableError


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
        try:
            entry = pool.pick(exclude=tried)
        except Exception as e:
            last_error = last_error or e
            break
        tried.add(entry.name)

        try:
            model = build_model(entry)
            result = fn(model)
            pool.mark_ok(entry)
            print(f"[LLM] success with {entry.name}")
            return result
        except Exception as e:
            if "tool_use_failed" in str(e).lower() or "tool call validation failed" in str(e).lower():
                print(f"[LLM] non-retryable tool failure on {entry.name}: {e}")
                raise
            seconds = _cooldown_seconds(e)
            pool.mark_rate_limited(entry, seconds=seconds)
            if _is_rate_limit(e):
                print(f"[LLM] rate-limited on {entry.name}, cooling {seconds}s")
            else:
                print(f"[LLM] error on {entry.name}: {e}")
            last_error = e

    exc_class = _classify_provider_error(last_error) if last_error else ProviderUnavailableError
    raise exc_class(f"Tous les fournisseurs ont échoué. Dernière erreur : {last_error}")


class RotatingChatModel:
    def __init__(self, pool, model_name: str = "openai/gpt-oss-120b"):
        self._pool = pool
        self._model_name = model_name
        self._clients: dict[str, object] = {}

    def _client_for(self, entry):
        if entry.api_key in self._clients:
            return self._clients[entry.api_key]
        if entry.provider == "groq":
            c = ChatGroq(model=entry.model, api_key=entry.api_key, temperature=0.0)
        elif entry.provider == "openrouter":
            c = ChatOpenAI(
                model=entry.model, api_key=entry.api_key,
                base_url="https://openrouter.ai/api/v1", temperature=0.0,
            )
        else:
            raise ValueError(f"Unknown provider: {entry.provider}")
        self._clients[entry.api_key] = c
        return c

    def bind_tools(self, tools, **kwargs):
        return _BoundRotatingModel(self._pool, tools, kwargs, self._clients)

    def invoke(self, messages, **kwargs):
        return run_with_failover(
            self._pool,
            lambda model: model.invoke(messages, **kwargs),
        )

    async def ainvoke(self, messages, **kwargs):
        return await self._fresh_model().ainvoke(messages, **kwargs)


class _BoundRotatingModel:
    def __init__(self, pool, tools, bind_kwargs, clients):
        self._pool = pool
        self._tools = tools
        self._bind_kwargs = bind_kwargs
        self._clients = clients

    def _client_for(self, entry):
        if entry.api_key in self._clients:
            return self._clients[entry.api_key]
        if entry.provider == "groq":
            c = ChatGroq(model=entry.model, api_key=entry.api_key, temperature=0.0)
        elif entry.provider == "openrouter":
            c = ChatOpenAI(
                model=entry.model, api_key=entry.api_key,
                base_url="https://openrouter.ai/api/v1", temperature=0.0,
            )
        else:
            raise ValueError(f"Unknown provider: {entry.provider}")
        self._clients[entry.api_key] = c
        return c

    def invoke(self, messages, **kwargs):
        return run_with_failover(
            self._pool,
            lambda model: model.bind_tools(
                self._tools, **self._bind_kwargs
            ).invoke(messages, **kwargs),
        )

    async def ainvoke(self, messages, **kwargs):
        return await self._fresh_model().ainvoke(messages, **kwargs)
