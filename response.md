# Part A — Pool shape

The inspection loaded `backend/.env` locally, printed metadata only, and made no API calls.

## Pool entries

```text
entry_count: 5
1: name=groq-1, provider=groq, model=openai/gpt-oss-120b, org_field=False
2: name=groq-2, provider=groq, model=openai/gpt-oss-120b, org_field=False
3: name=groq-3, provider=groq, model=openai/gpt-oss-120b, org_field=False
4: name=groq-4, provider=groq, model=openai/gpt-oss-120b, org_field=False
5: name=openrouter-1, provider=openrouter, model=nvidia/nemotron-3.5-lightning:free, org_field=False
openrouter_present: True
```

No pool entry contains an organization identifier. Organization separation is implicit in the API keys, not represented in `KeyEntry`.

The OpenRouter entry is:

```text
provider=openrouter
name=openrouter-1
model=nvidia/nemotron-3.5-lightning:free
tier=1
```

## Relevant grep output

```text
7:from app.core.exceptions import (
22:    cooldown_until: float = 0.0
33:        ready = [e for e in self.entries if e.cooldown_until <= now]
34:        return ready if ready else self.entries  # all cooling → try soonest anyway
43:    def mark_rate_limited(self, entry: KeyEntry, seconds: int = 60):
44:        entry.cooldown_until = time.time() + seconds
64:def _is_rate_limit(exc: Exception) -> bool:
128:        except Exception as e:
130:                print(f"[LLM] non-retryable tool failure on {entry.name}: {e}")
132:            if _is_rate_limit(e):
133:                pool.mark_rate_limited(entry, seconds=60)
134:                print(f"[LLM] rate-limited on {entry.name}, cooling 60s")
136:                pool.mark_rate_limited(entry, seconds=10)
```

## Environment-variable names

The requested shell command produced no names:

```text
--- ENV NAMES ---
```

That means `GROQ...` and `OPENROUTER...` were not exported in the shell process. They are loaded from `backend/.env` by application code. No values were printed.

---

# Part B — Retry and failover path

There are two materially different call paths:

1. `run_with_failover(...)` — catches exceptions and rotates entries.
2. `RotatingChatModel.invoke(...)` — picks exactly one entry and calls it directly, with no exception handling or retry.

The extraction crash went through path 2.

## `RotatingChatModel._client_for`

`backend/app/core/llm_pool.py`, lines 150–163:

```python
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
```

## `RotatingChatModel.invoke`

`backend/app/core/llm_pool.py`, lines 168–170:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).invoke(messages, **kwargs)
```

There is no `try`, `except`, loop, cooldown update, or secondary provider call here.

## Bound-model equivalent

The tool-bound wrapper has the same single-attempt behavior, lines 198–200:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).bind_tools(
        self._tools, **self._bind_kwargs
    ).invoke(messages, **kwargs)
```

## Cooldown helper

`backend/app/core/llm_pool.py`, lines 43–45:

```python
def mark_rate_limited(self, entry: KeyEntry, seconds: int = 60):
    entry.cooldown_until = time.time() + seconds
    entry.failure_count += 1
```

This helper is used by `run_with_failover`, but not by `RotatingChatModel.invoke`.

## Rate-limit classifier

Lines 64–66:

```python
def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc).lower()
    return (
        ("429" in s)
        or ("rate" in s and "limit" in s)
        or ("tpm" in s)
        or ("rpm" in s)
    )
```

Final error classification, lines 69–77:

```python
def _classify_provider_error(exc: Exception) -> type[AppError]:
    s = str(exc).lower()
    if "429" in s or "rate" in s and "limit" in s or "tpm" in s or "rpm" in s:
        return RateLimitError
    if "timeout" in s or "timed out" in s:
        return ProviderTimeoutError
    if "503" in s or "502" in s or "unavailable" in s or "overloaded" in s:
        return ProviderUnavailableError
    return ProviderUnavailableError
```

Neither classifier mentions TPD explicitly, but a TPD exception containing `429` is classified as rate-limited.

## Full `run_with_failover` body

Lines 111–141:

```python
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
            if (
                "tool_use_failed" in str(e).lower()
                or "tool call validation failed" in str(e).lower()
            ):
                print(
                    f"[LLM] non-retryable tool failure "
                    f"on {entry.name}: {e}"
                )
                raise
            if _is_rate_limit(e):
                pool.mark_rate_limited(entry, seconds=60)
                print(
                    f"[LLM] rate-limited on {entry.name}, "
                    "cooling 60s"
                )
            else:
                pool.mark_rate_limited(entry, seconds=10)
                print(f"[LLM] error on {entry.name}: {e}")
            last_error = e

    exc_class = (
        _classify_provider_error(last_error)
        if last_error
        else ProviderUnavailableError
    )
    raise exc_class(
        f"Tous les fournisseurs ont échoué. "
        f"Dernière erreur : {last_error}"
    )
```

## B1 — Which exceptions are caught?

The retry path catches every standard exception:

```python
except Exception as e:
```

It does **not** explicitly name or import `groq.RateLimitError`. A `groq.RateLimitError` is caught indirectly by `except Exception` when the call goes through `run_with_failover`.

However, `RotatingChatModel.invoke` has no `except` clause at all:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).invoke(messages, **kwargs)
```

Therefore, a `groq.RateLimitError` raised from this path propagates immediately.

## B2 — Does it distinguish TPM from TPD?

No. There is no TPM-versus-TPD distinction.

The only rate-limit test is string matching:

```python
def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc).lower()
    return ("429" in s) or ("rate" in s and "limit" in s) or ("tpm" in s) or ("rpm" in s)
```

The implementation does not parse:

- `type`
- `code`
- `Retry-After`
- `Please try again in 10m21.216s`
- a reset timestamp
- `TPD`
- the organization identifier

A TPD error is recognized only because it contains `429` or rate-limit wording.

## B3 — Is there a cooldown-wait threshold?

No cooldown threshold exists.

There is no comparison against 60, 120, 300, 600, or the provider’s requested retry duration. There is no branch equivalent to “retry window is too long, skip this key” or “do not retry.”

Instead, every recognized rate limit gets the same fixed 60-second cooldown:

```python
if _is_rate_limit(e):
    pool.mark_rate_limited(entry, seconds=60)
    print(f"[LLM] rate-limited on {entry.name}, cooling 60s")
```

That code is only reached through `run_with_failover`.

## B4 — What cooldown expiry is stored?

Cooldown is fixed:

```python
def mark_rate_limited(self, entry: KeyEntry, seconds: int = 60):
    entry.cooldown_until = time.time() + seconds
    entry.failure_count += 1
```

For a 429, the caller passes exactly 60 seconds:

```python
if _is_rate_limit(e):
    pool.mark_rate_limited(entry, seconds=60)
    print(f"[LLM] rate-limited on {entry.name}, cooling 60s")
```

It is not based on `Retry-After`. Thus a TPD response saying “try again in 10m21s” would still receive only a 60-second cooldown—if it passed through `run_with_failover`.

## B5 — Does `invoke` retry in the same call?

`RotatingChatModel.invoke` does not retry:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).invoke(messages, **kwargs)
```

It makes exactly one attempt. If that attempt fails, the raw provider exception escapes.

`run_with_failover`, by contrast, contains:

```python
for _ in range(len(pool.entries)):
    entry = pool.pick()
    if entry.name in tried:
        break
    tried.add(entry.name)
```

With the current five-entry pool, its nominal maximum is five attempts. It can make fewer attempts because encountering an already-tried entry causes an immediate `break`.

If no call succeeds, it raises a translated application exception:

```python
exc_class = _classify_provider_error(last_error) if last_error else ProviderUnavailableError
raise exc_class(f"Tous les fournisseurs ont échoué. Dernière erreur : {last_error}")
```

The crash in `extract_intent` did not use this retry loop.

## B6 — What happens when all Groq keys are cooling?

Selection logic:

```python
def _available(self) -> list[KeyEntry]:
    now = time.time()
    ready = [e for e in self.entries if e.cooldown_until <= now]
    return ready if ready else self.entries  # all cooling → try soonest anyway
```

Then:

```python
def pick(self) -> KeyEntry:
    ready = self._available()
    ready.sort(key=lambda e: (e.tier, e.last_used))
    entry = ready[0]
    entry.last_used = time.time()
    return entry
```

Important consequences:

1. If the four Groq entries are cooling but OpenRouter is ready, `ready` contains OpenRouter, so it can be selected.
2. If all five entries are cooling, `_available` returns every entry, including cooling entries.
3. Sorting prioritizes `tier=0` Groq over `tier=1` OpenRouter, regardless of cooldown expiry.
4. It does not actually pick the “soonest” cooldown despite the comment; it sorts by `(tier, last_used)`, not `cooldown_until`.
5. In `run_with_failover`, if this selection returns an already-tried entry, the retry loop breaks immediately:

```python
entry = pool.pick()
if entry.name in tried:
    break
tried.add(entry.name)
```

For the extraction crash specifically, none of this retry logic executes. `RotatingChatModel.invoke` makes one selection and one API call.

It also does not mark the failed extraction key as cooling. Therefore, the next extraction call may select that same TPD-exhausted key again, depending on `last_used` ordering.

## B7 — Does pool exhaustion fall back to OpenRouter?

### In `run_with_failover`

OpenRouter is part of the same pool and can be selected:

```python
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
```

And it can be constructed:

```python
if entry.provider == "openrouter":
    return ChatOpenAI(
        model=entry.model,
        api_key=entry.api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0,
    )
```

Therefore, OpenRouter is wired into `run_with_failover` as a tier-1 pool entry.

### In `RotatingChatModel.invoke`

There is **no cross-provider fallback after a failed call**. It may select an OpenRouter entry only if `pool.pick()` chooses one before the call. Once a selected Groq call raises, the exception propagates:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).invoke(messages, **kwargs)
```

For `RotatingChatModel.invoke`, the accurate statement is:

> no cross-provider fallback after provider failure

---

# Part C — The extraction call that crashed

## `_get_extraction_model`

`backend/app/agents/extraction.py`, lines 10–15:

```python
def _get_extraction_model():
    global _pool, _extraction_model
    if _extraction_model is None:
        _pool = load_keys_from_env()
        _extraction_model = RotatingChatModel(
            _pool,
            model_name="openai/gpt-oss-20b",
        )
    return _extraction_model
```

`extract_intent` invokes it directly, lines 34–38:

```python
messages = [
    SystemMessage(content=INTENT_SYSTEM_PROMPT),
    HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
]
response = _get_extraction_model().invoke(messages)
```

## Model requested versus model actually built

The constructor requests:

```python
model_name="openai/gpt-oss-20b"
```

But `RotatingChatModel._client_for` ignores `self._model_name` and uses the pool entry model:

```python
if entry.provider == "groq":
    c = ChatGroq(model=entry.model, api_key=entry.api_key, temperature=0.0)
```

Every Groq pool entry currently has:

```python
model="openai/gpt-oss-120b",
tier=0,
```

Therefore, despite `_get_extraction_model()` passing `openai/gpt-oss-20b`, the actual Groq client produced by this implementation uses `openai/gpt-oss-120b`.

This likely explains why the reported TPD request was large, but it is separate from why failover did not occur.

## Does extraction use the same pool as the other stages?

No. The components use the same environment-based pool configuration, but they construct **separate `KeyPool` instances** with independent cooldown state.

### Extraction pool

```python
_pool = load_keys_from_env()
_extraction_model = RotatingChatModel(_pool, model_name="openai/gpt-oss-20b")
```

### Formatter pool

```python
def _get_pool():
    global _pool
    if _pool is None:
        _pool = load_keys_from_env()
    return _pool
```

```python
def _get_formatter_model():
    global _formatter_model
    if _formatter_model is None:
        _formatter_model = RotatingChatModel(_get_pool(), model_name="openai/gpt-oss-20b")
    return _formatter_model
```

### Search-synthesis pool

```python
_pool = load_keys_from_env()
```

The synthesiser uses the retrying wrapper:

```python
def _run(model):
    return model.invoke(messages)

response = run_with_failover(_pool, _run)
```

### Per-page extraction pool

```python
extractor_llm = small_groq_model
_page_pool = load_keys_from_env()
```

Per-page extraction also uses the retrying wrapper:

```python
def _run(model):
    return model.invoke(messages)

response = run_with_failover(_page_pool, _run)
```

Thus:

- `extract_intent`: separate pool + non-retrying `RotatingChatModel.invoke`
- `format_reply`: separate pool + non-retrying `RotatingChatModel.invoke`
- search synthesiser: separate pool + `run_with_failover`
- page extractors: separate pool + `run_with_failover`

The observed TPM logs:

```text
[LLM] rate-limited on groq-N, cooling 60s
```

can only come from `run_with_failover`, not from `RotatingChatModel.invoke`. This explains why TPM failover was observed during search/page extraction while the extraction-stage TPD error crashed immediately.

---

# Part D — OpenRouter wiring

## Grep output

```text
app/config.py:23:    openrouter_keys_raw: str = Field("", alias="OPENROUTER_KEYS")
app/config.py:64:    def openrouter_keys(self) -> list[str]:
app/config.py:65:        return [k.strip() for k in self.openrouter_keys_raw.split(",") if k.strip()]
app/core/apis.py:16:openrouter_keys = [k.strip() for k in os.getenv("OPENROUTER_KEYS", "").split(",") if k.strip()]
app/core/apis.py:17:openrouter_api_key = os.getenv("OPENROUTER_API_KEY") or (openrouter_keys[0] if openrouter_keys else None)
app/core/apis.py:29:openrouter_model = ChatOpenAI(model="" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)
app/core/apis.py:30:openrouter_alternative = ChatOpenAI(model="google/gemma-4-31b-it:free" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)
app/core/llm_pool.py:18:    provider: str          # "groq" | "openrouter"
app/core/llm_pool.py:21:    tier: int              # 0 = primary (Groq), 1 = backup (OpenRouter)
app/core/llm_pool.py:54:    if entry.provider == "openrouter":
app/core/llm_pool.py:58:            base_url="https://openrouter.ai/api/v1",
app/core/llm_pool.py:81:    """GROQ_KEYS=key1,key2,key3  OPENROUTER_KEYS=key1,key2"""
app/core/llm_pool.py:95:    for i, k in enumerate(os.getenv("OPENROUTER_KEYS", "").split(",")):
app/core/llm_pool.py:99:                name=f"openrouter-{i+1}",
app/core/llm_pool.py:100:                provider="openrouter",
app/core/llm_pool.py:155:        elif entry.provider == "openrouter":
app/core/llm_pool.py:158:                base_url="https://openrouter.ai/api/v1", temperature=0.0,
app/core/llm_pool.py:188:        elif entry.provider == "openrouter":
app/core/llm_pool.py:191:                base_url="https://openrouter.ai/api/v1", temperature=0.0,
```

## Wiring status

**Partially wired.**

OpenRouter is:

- loaded into each `KeyPool`,
- assigned tier 1,
- constructible by both `build_model` and `_client_for`,
- reachable during `run_with_failover` when the picker selects it.

However, `RotatingChatModel.invoke` does not retry after a Groq failure, so OpenRouter is never reached as a response to that failure.

The standalone objects in `app/core/apis.py`:

```python
openrouter_model = ChatOpenAI(
    model="",
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    temperature=0.0,
)
openrouter_alternative = ChatOpenAI(
    model="google/gemma-4-31b-it:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    temperature=0.0,
)
```

do not contain selection or failover logic and are not referenced by `RotatingChatModel`.

---

# Diagnosis

The best explanation is **(iv): the crashing extraction call uses `RotatingChatModel.invoke`, which does not implement failover at all**. The exact proof is:

```python
def invoke(self, messages, **kwargs):
    entry = self._pool.pick()
    return self._client_for(entry).invoke(messages, **kwargs)
```

That method selects one Groq entry, performs one provider call, and lets `groq.RateLimitError` propagate. It does not call `_is_rate_limit`, does not mark the key cooling, does not retry another Groq key, and does not reach OpenRouter. This is why the TPD exception escaped from `RotatingChatModel.invoke` and crashed `process_turn`.

A secondary issue corresponding partly to **(iii)** is that OpenRouter is present in the pool but cannot act as post-failure fallback on the `RotatingChatModel` path. A further latent issue affects the separate `run_with_failover` path: if every entry is cooling, `_available()` returns all entries and `pick()` prioritizes tier-0 Groq rather than the soonest expiry; selecting an already-tried Groq then causes the loop to break before OpenRouter may be attempted. But that is not the primary cause of this extraction crash.

Neither **(i)** nor **(ii)** best explains this incident: there is no long-`Retry-After` rejection threshold, and the failing extraction call never entered the retry loop in the first place.
