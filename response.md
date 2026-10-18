# Chat Session Lifecycle Diagnostic

**Date:** 17 October 2026
**Scope:** Read-only inspection of backend and frontend chat-session creation, storage, expiry, error handling, reset behavior, and visible-history behavior. No source or configuration file was modified as part of the diagnosis; only this report was written.

---

# Part A — Backend session lifecycle

## A1. Session creation endpoint

The endpoint is `POST /api/v1/chat/session`. The chat router has the `/chat` prefix, and the application mounts all v1 routes under `/api/v1`.

`backend/app/api/v1/chat.py`, lines 12 and 15–23:

```python
12  router = APIRouter(prefix="/chat", tags=["chat"])

15  @router.post(
16      "/session",
17      response_model=CreateSessionResponse,
18      status_code=status.HTTP_201_CREATED,
19  )
20  def create_session() -> CreateSessionResponse:
21      """Start a new chat session. Returns a session_id to use on subsequent calls."""
22      session_id = chat_service.create_session()
23      return CreateSessionResponse(session_id=session_id)
```

`backend/app/main.py` mounts the API router under `/api/v1`:

```python
app.include_router(api_router, prefix="/api/v1")
```

The exact successful JSON response has only one field:

```json
{
  "session_id": "<UUID>"
}
```

That shape is defined in `backend/app/schemas/chat.py`, lines 4–5:

```python
4  class CreateSessionResponse(BaseModel):
5      session_id: str = Field(..., description="Opaque session identifier. Send it back on every subsequent request.")
```

The response status is HTTP `201 Created`.

**No TTL information is returned.** The response does not contain `created_at`, `expires_at`, `ttl_seconds`, idle timeout, or maximum lifetime. The frontend creates its own local `created_at`, but that timestamp is not provided by the backend.

## A2. Session TTL rules

The backend enforces two separate limits in `backend/app/services/chat_service.py`, lines 10–11:

```python
10  _SESSION_MAX_SECONDS = 30 * 60   # hard cap from creation
11  _SESSION_IDLE_SECONDS = 10 * 60  # inactivity cap
```

Therefore:

- Maximum lifetime: 30 minutes from creation.
- Idle timeout: 10 minutes since the last successfully processed message.

Expiry is calculated in lines 16–20:

```python
16  def _is_expired(session: dict[str, Any]) -> bool:
17      now = time.time()
18      age = now - session["created_at"]
19      idle = now - session["last_activity"]
20      return age > _SESSION_MAX_SECONDS or idle > _SESSION_IDLE_SECONDS
```

The two limits are independent. A session expires when either condition is true. Activity resets only `last_activity`; it does not reset `created_at`.

That behavior is explicit in lines 59–62:

```python
59  session["history"] = updated_history
60  session["current_vehicle"] = updated_vehicle
61  session["last_activity"] = time.time()   # <- resets idle timer
62  # created_at stays fixed — that's the hard cap
```

Expired sessions are removed by `_evict_expired`, lines 23–27:

```python
23  def _evict_expired() -> None:
24      """Drop sessions that have exceeded either timeout."""
25      expired = [sid for sid, s in _sessions.items() if _is_expired(s)]
26      for sid in expired:
27          _sessions.pop(sid, None)
```

There is no background timer dedicated to chat-session expiry. Expiry is checked lazily during API/service operations:

- On session creation: `create_session()` calls `_evict_expired()` at line 33.
- On message processing: `process_message()` calls `_evict_expired()` at line 46.
- On existence checks: `session_exists()` calls `_evict_expired()` at line 72.

Relevant evidence:

```python
32  def create_session() -> str:
33      _evict_expired()
```

```python
45  def process_message(session_id: str, message: str) -> str:
46      _evict_expired()
```

```python
71  def session_exists(session_id: str) -> bool:
72      _evict_expired()
73      session = _sessions.get(session_id)
74      return session is not None and not _is_expired(session)
```

Thus expiry is checked on relevant incoming chat operations, not continuously.

## A3. Message endpoint behavior for unknown or expired sessions

The endpoint is `POST /api/v1/chat/session/{session_id}/message`.

`backend/app/api/v1/chat.py`, lines 26–39:

```python
26  @router.post(
27      "/session/{session_id}/message",
28      response_model=MessageResponse,
29  )
30  def send_message(session_id: str, payload: MessageRequest) -> MessageResponse:
31      """Send a user message and get the assistant reply."""
32      if not chat_service.session_exists(session_id):
33          raise HTTPException(
34              status_code=status.HTTP_404_NOT_FOUND,
35              detail="Session not found or expired.",
36          )
38      reply, products = chat_service.process_message(session_id, payload.message)
39      return MessageResponse(reply=reply, products=products)
```

For both an unknown session and an expired session, the endpoint returns HTTP `404 Not Found` with the FastAPI JSON body:

```json
{
  "detail": "Session not found or expired."
}
```

There is no client-visible distinction between:

- A session ID that never existed.
- A session removed after idle timeout.
- A session removed after maximum lifetime.
- A valid session lost because the backend process restarted.
- A valid session lost because another worker/process owns a different in-memory store.

The service itself also uses one combined internal error condition in `backend/app/services/chat_service.py`, lines 48–51:

```python
48  session = _sessions.get(session_id)
49  if session is None or _is_expired(session):
50      _sessions.pop(session_id, None)
51      raise KeyError(f"Unknown or expired session: {session_id}")
```

In the normal route path, `session_exists()` handles the condition first and emits the 404. There is a small race window between `session_exists()` and `process_message()`: if the session expires between those calls, `process_message()` can raise an uncaught `KeyError`, which would not be converted by this handler into the same 404. Under ordinary timing this is unlikely, but the two-step check is not atomic.

## A4. Delete endpoint

A delete endpoint exists:

```text
DELETE /api/v1/chat/session/{session_id}
```

`backend/app/api/v1/chat.py`, lines 42–49:

```python
42  @router.delete(
43      "/session/{session_id}",
44      response_model=EndSessionResponse,
45  )
46  def end_session(session_id: str) -> EndSessionResponse:
47      """End a chat session and free its history."""
48      chat_service.end_session(session_id)
49      return EndSessionResponse(ok=True)
```

The service removes the session from the in-memory dictionary, lines 67–68:

```python
67  def end_session(session_id: str) -> None:
68      _sessions.pop(session_id, None)
```

The delete is idempotent: deleting an unknown ID does not fail because `pop(..., None)` is used.

No explicit status code is set, so FastAPI returns HTTP `200 OK`. The response body is:

```json
{
  "ok": true
}
```

That response shape is defined in `backend/app/schemas/chat.py`, lines 23–24:

```python
23  class EndSessionResponse(BaseModel):
24      ok: bool = True
```

## A5. History endpoint

There is **no history endpoint**.

The only customer chat routes registered in `backend/app/api/v1/chat.py` are:

- `POST /chat/session`
- `POST /chat/session/{session_id}/message`
- `DELETE /chat/session/{session_id}`

No `GET /chat/session/{id}/messages` or `GET /chat/session/{id}` handler exists.

The backend does keep history internally, but it is not exposed. Session creation initializes it in `backend/app/services/chat_service.py`, lines 36–40:

```python
36  _sessions[session_id] = {
37      "history": [],
38      "current_vehicle": {},
39      "created_at": now,
40      "last_activity": now,
41  }
```

After each successful turn, internal history is replaced in lines 53–60:

```python
53  reply, updated_history, updated_vehicle, products = process_turn(
54      user_message=message,
55      history=session["history"],
56      current_vehicle=session["current_vehicle"],
57  )
59  session["history"] = updated_history
60  session["current_vehicle"] = updated_vehicle
```

Because there is no history endpoint, the frontend cannot restore visible messages from this backend state after a reload.

## A6. Message length limit

The message limit is defined in the request schema at `backend/app/schemas/chat.py`, lines 8–9:

```python
8  class MessageRequest(BaseModel):
9      message: str = Field(..., min_length=1, max_length=2000, description="Customer message in natural language.")
```

The accepted length is 1–2,000 characters.

When the request exceeds 2,000 characters, FastAPI/Pydantic rejects the request before the endpoint handler runs and returns HTTP `422 Unprocessable Entity` with FastAPI's standard validation-error JSON. The code does not define a custom customer-facing message for this validation error.

The response therefore exposes schema-validation structure such as location, error type, and constraint context. It is useful for developers but not intentionally translated into a friendly French customer message.

The route is also rate-limited separately in `backend/app/core/rate_limit.py`:

```python
("POST", "/api/v1/chat/session/{session_id}/message", 15, 60, "session_id"),
```

That is 15 requests per 60 seconds keyed by session ID; it is separate from the 2,000-character validation limit.

## A7. Session storage model

The chat session store is a process-local in-memory dictionary.

`backend/app/services/chat_service.py`, lines 8–13:

```python
8   # ---------- session store ----------
10  _SESSION_MAX_SECONDS = 30 * 60   # hard cap from creation
11  _SESSION_IDLE_SECONDS = 10 * 60  # inactivity cap
13  _sessions: dict[str, dict[str, Any]] = {}
```

Each session stores:

- `history`
- `current_vehicle`
- `created_at`
- `last_activity`

There is no database or Redis persistence for chat sessions.

Consequences visible from the implementation:

- All sessions disappear when the backend process restarts.
- Multiple backend worker processes do not share session state.
- A request routed to a different process can see a valid frontend session ID as unknown.

Session IDs are generated with Python UUID v4:

```python
32  def create_session() -> str:
33      _evict_expired()
34      session_id = str(uuid.uuid4())
```

The identifier is random and not sequential/guessable in the practical sense expected of UUID v4.

There is no authentication or user binding in the chat endpoints. The session ID is the only lookup key. Anyone possessing a valid session ID can send messages into that session or delete it. No account, cookie, JWT, IP binding, or ownership check is applied by the route.

---

# Part B — Frontend session state and expiry handling

## B1. Session ID storage

The session is stored only in browser `localStorage`, under this key:

`frontend/src/lib/chat.ts`, lines 25–30:

```ts
25  export type SessionRecord = {
26    session_id: string;
27    created_at: number;
28  };
30  export const SESSION_STORAGE_KEY = "autolube_chat_session_v1";
```

Read logic, lines 32–49:

```ts
32  export function loadSession(): SessionRecord | null {
33    if (typeof window === "undefined") return null;
34    try {
35      const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
36      if (!raw) return null;
37      const parsed = JSON.parse(raw);
38      if (
39        !parsed ||
40        typeof parsed.session_id !== "string" ||
41        typeof parsed.created_at !== "number"
42      ) {
43        return null;
44      }
45      return parsed;
46    } catch {
47      return null;
48    }
49  }
```

Write logic, lines 51–58:

```ts
51  export function saveSession(rec: SessionRecord): void {
52    if (typeof window === "undefined") return;
53    try {
54      window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(rec));
55    } catch {
56      // ignore
57    }
58  }
```

Clear logic, lines 60–67:

```ts
60  export function clearSession(): void {
61    if (typeof window === "undefined") return;
62    try {
63      window.localStorage.removeItem(SESSION_STORAGE_KEY);
64    } catch {
65      // ignore
66    }
67  }
```

The frontend stores both `session_id` and a local `created_at` timestamp.

That timestamp is created by the frontend after a successful session-creation request, not returned by the backend. `frontend/src/components/chat/ChatProvider.tsx`, lines 37–46:

```ts
37  async function createSession(): Promise<SessionRecord> {
38    const res = await fetch(`${API_URL}/chat/session`, { method: "POST" });
39    if (!res.ok) throw new Error(`Session creation failed: ${res.status}`);
40    const data = await res.json();
41    const rec: SessionRecord = {
42      session_id: data.session_id,
43      created_at: Date.now(),
44    };
45    saveSession(rec);
46    return rec;
47  }
```

The session record is not also held in dedicated React state. It is loaded from localStorage only when needed during send/retry operations.

## B2. Message history storage

Visible messages are held only in React state.

`frontend/src/components/chat/ChatProvider.tsx`, lines 68–73:

```ts
68  export function ChatProvider({ children }: { children: React.ReactNode }) {
69    const [isOpen, setIsOpen] = useState(false);
70    const [messages, setMessages] = useState<ChatMessage[]>([]);
71    const [isSending, setIsSending] = useState(false);
72    const [error, setError] = useState<string | null>(null);
73    const [sessionExpired, setSessionExpired] = useState(false);
```

User messages are appended at lines 102–108:

```ts
102  const userMsg: ChatMessage = {
103    id: newMessageId(),
104    role: "user",
105    text: trimmed,
106    createdAt: Date.now(),
107  };
108  setMessages((prev) => [...prev, userMsg]);
```

Assistant messages are appended at lines 120–127:

```ts
120  const assistantMsg: ChatMessage = {
121    id: newMessageId(),
122    role: "assistant",
123    text: result.reply,
124    products: result.products ?? [],
125    createdAt: Date.now(),
126  };
127  setMessages((prev) => [...prev, assistantMsg]);
```

No code stores the `messages` array in localStorage, sessionStorage, IndexedDB, cookies, or the backend through a history API. `src/lib/chat.ts` persists only `SessionRecord`.

Therefore, after a page reload:

- The visible `messages` array returns to `[]`.
- The old `session_id` remains in localStorage.
- Backend history may still exist if the session remains valid, but the frontend has no endpoint to fetch it.

Visible message history does **not** survive a page reload.

## B3. How the `sessionExpired` state is triggered

The API helper treats every HTTP 404 from the message endpoint as session expiry.

`frontend/src/components/chat/ChatProvider.tsx`, lines 49–65:

```ts
49  async function sendMessage(
50    sessionId: string,
51    text: string
52  ): Promise<{ reply: string; products: ChatProduct[] }> {
53    const res = await fetch(`${API_URL}/chat/session/${sessionId}/message`, {
54      method: "POST",
55      headers: { "Content-Type": "application/json" },
56      body: JSON.stringify({ message: text }),
57    });
58    if (res.status === 404) {
59      throw new Error("SESSION_EXPIRED");
60    }
61    if (!res.ok) {
62      const body = await res.text();
63      throw new Error(`Send failed: ${res.status} ${body}`);
64    }
65    return res.json();
66  }
```

The `send` callback catches that sentinel error and sets the flag, lines 128–140:

```ts
128  } catch (err) {
129    if (err instanceof Error && err.message === "SESSION_EXPIRED") {
130      // Session died. Do NOT retry. Surface the state so the widget
131      // can show the "start new chat" button.
132      clearSession();
133      setSessionExpired(true);
134      pendingResendRef.current = trimmed;
135    } else {
136      console.error("Chat send error:", err);
137      setError(
138        "Le service est momentanément indisponible. Veuillez réessayer."
139      );
140    }
```

When this happens:

- The stale localStorage session is removed.
- `sessionExpired` becomes `true`.
- The attempted text is saved in `pendingResendRef`.
- No new session is created automatically.
- No resend occurs automatically at this point.
- The already-added user message remains visible.

Once `sessionExpired` is true, future calls to `send` are stopped before adding a bubble or making a request, lines 95–100:

```ts
95  // If session already marked expired, don't attempt to send.
96  // Ask the user to start a new chat instead.
97  if (sessionExpired) {
98    pendingResendRef.current = trimmed;
99    return;
100 }
```

The widget also blocks its send handler and disables the input/button when expired:

`frontend/src/components/chat/ChatWidget.tsx`, lines 42–46:

```tsx
42  async function handleSend() {
43    const text = input.trim();
44    if (!text || isSending || sessionExpired) return;
45    setInput("");
46    await send(text);
47  }
```

Lines 151–164:

```tsx
151  <textarea
152    rows={1}
153    value={input}
154    onChange={(e) => setInput(e.target.value)}
155    onKeyDown={handleKeyDown}
156    disabled={isSending || sessionExpired}
157    placeholder="Écrivez votre message…"
158    className="..."
159  />
160  <button
161    type="button"
162    onClick={handleSend}
163    disabled={!input.trim() || isSending || sessionExpired}
```

## B4. Exact empty-visible-history bug scenario

Scenario:

1. The browser has an expired/stale `session_id` in localStorage.
2. The page is loaded or reloaded.
3. `ChatProvider` initializes visible messages to an empty array:

```ts
const [messages, setMessages] = useState<ChatMessage[]>([]);
```

4. Opening the chat only sets `isOpen` to true. It does not validate the local session:

```ts
79  const open = useCallback(() => setIsOpen(true), []);
```

5. Because `messages.length === 0`, the widget initially renders the welcome/example screen:

`frontend/src/components/chat/ChatWidget.tsx`, lines 99–119:

```tsx
99   {/* Body */}
100  <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
101    {messages.length === 0 ? (
102      <div className="flex flex-col items-center justify-center h-full text-center gap-4">
103        <p className="text-sm text-neutral-600">
104          Bonjour. Posez-moi une question sur votre véhicule, je vous recommande les huiles adaptées.
105        </p>
106        <div className="flex flex-col gap-2 w-full">
107          {EXAMPLES.map((ex) => (
108            <button
109              key={ex}
110              type="button"
111              onClick={() => send(ex)}
...
118      </div>
119    ) : (
```

6. The user types and sends a first visible message.
7. `send` appends the user bubble **before** checking the server session:

```ts
102  const userMsg: ChatMessage = {...};
108  setMessages((prev) => [...prev, userMsg]);
```

8. `loadSession()` returns the stale localStorage record, so no new session is created:

```ts
112  try {
113    let session = loadSession();
114    if (!session) {
115      session = await createSession();
116    }
118    const result = await sendMessage(session.session_id, trimmed);
```

9. The backend returns 404 because the ID is unknown/expired.
10. The frontend converts the 404 to `SESSION_EXPIRED`, clears localStorage, sets `sessionExpired=true`, and preserves the attempted message for resend:

```ts
129  if (err instanceof Error && err.message === "SESSION_EXPIRED") {
132    clearSession();
133    setSessionExpired(true);
134    pendingResendRef.current = trimmed;
```

11. At this point, `messages.length` is now at least 1 because the failed user message was already appended. The widget switches from the empty branch to the non-empty branch.
12. The expiry UI renders under this condition:

`frontend/src/components/chat/ChatWidget.tsx`, lines 119–140:

```tsx
119  ) : (
120    <>
121      {messages.map((m) => (
122        <ChatMessageBubble key={m.id} message={m} />
123      ))}
...
129      {sessionExpired && (
130        <div className="border border-amber-300 bg-amber-50 text-amber-900 text-xs p-3 rounded-md">
131          <p>La conversation a expiré.</p>
132          <button
133            type="button"
134            onClick={startNewChat}
...
137            Démarrer une nouvelle conversation
138          </button>
139        </div>
140      )}
```

The code does **not** distinguish “empty visible history before this first attempted message” from “an established visible conversation with context.” It uses only the generic `sessionExpired` flag after having already appended the failed first message.

There is an additional render-detail: if `sessionExpired` somehow became true while `messages.length` remained exactly zero, the current JSX would not show the expiry UI at all because that UI exists only in the non-empty `else` branch. In the observed path, the user message is appended first, so the list is no longer empty and the expiry UI appears.

## B5. Auto-resend on new session

The frontend does not auto-create/retry immediately upon detecting 404. It waits for the user to click “Démarrer une nouvelle conversation.”

When 404 occurs, the pending text is stored:

```ts
132  clearSession();
133  setSessionExpired(true);
134  pendingResendRef.current = trimmed;
```

Clicking the button calls `startNewChat`, lines 148–190:

```ts
148  const startNewChat = useCallback(async () => {
149    clearSession();
150    setSessionExpired(false);
151    setError(null);

153    const toResend = pendingResendRef.current;
154    pendingResendRef.current = null;

156    try {
157      await createSession();
158    } catch (err) {
159      console.error("New chat creation failed:", err);
160      setError(
161        "Impossible de démarrer une nouvelle conversation. Réessayez."
162      );
163      return;
164    }

166    if (toResend) {
167      // Re-send the message the user already typed. Do NOT add a new
168      // user bubble — the previous one is still visible and this is
169      // the same message.
170      setIsSending(true);
171      try {
172        const session = loadSession();
173        if (!session) throw new Error("No session after creation");
174        const result = await sendMessage(session.session_id, toResend);
175        const assistantMsg: ChatMessage = {
176          id: newMessageId(),
177          role: "assistant",
178          text: result.reply,
179          products: result.products ?? [],
180          createdAt: Date.now(),
181        };
182        setMessages((prev) => [...prev, assistantMsg]);
183      } catch (err) {
184        console.error("Resend after new chat failed:", err);
185        setError("Le service est momentanément indisponible.");
186      } finally {
187        setIsSending(false);
188      }
189    }
190  }, []);
```

Therefore, after explicit user confirmation, the frontend:

1. Creates a new backend session.
2. Loads that new session from localStorage.
3. Resends the pending message.
4. Adds only the assistant reply because the original user bubble is already visible.

## B6. Reset button behavior

The header reset button calls `reset` directly.

`frontend/src/components/chat/ChatWidget.tsx`, lines 80–86:

```tsx
80  <button
81    type="button"
82    onClick={reset}
83    aria-label="Nouvelle conversation"
84    className="..."
85  >
86    <RotateCcw size={16} />
```

`reset` is defined in `frontend/src/components/chat/ChatProvider.tsx`, lines 82–88:

```ts
82  const reset = useCallback(() => {
83    clearSession();
84    setMessages([]);
85    setError(null);
86    setSessionExpired(false);
87    pendingResendRef.current = null;
88  }, []);
```

It clears:

- The localStorage session record through `clearSession()`.
- React message state.
- React error state.
- React session-expired state.
- The pending resend reference.

It does **not** call `DELETE /chat/session/{id}`. The old server session remains in `_sessions` until it expires, is evicted during a later chat operation, the process restarts, or another caller explicitly deletes it.

The “start new chat” expiry action also calls only `clearSession()` locally before creating a new session; it does not delete the old server session. In the expiry case the old session is already unknown/expired, but in manual reset it may still be valid.

## B7. Character-limit enforcement

The textarea is in `frontend/src/components/chat/ChatWidget.tsx`, lines 151–159:

```tsx
151  <textarea
152    rows={1}
153    value={input}
154    onChange={(e) => setInput(e.target.value)}
155    onKeyDown={handleKeyDown}
156    disabled={isSending || sessionExpired}
157    placeholder="Écrivez votre message…"
158    className="..."
159  />
```

It has no `maxLength={2000}` or any other client-side maximum. There is no character counter.

The 2,000-character limit exists only in the backend Pydantic schema:

```python
message: str = Field(..., min_length=1, max_length=2000, ...)
```

The frontend does not import, derive, or hardcode that limit.

If the user sends more than 2,000 characters, the backend returns 422. The frontend treats that as a generic non-404 send failure.

## B8. Error-handling shape

The message helper distinguishes only HTTP 404 from all other non-success statuses.

```ts
58  if (res.status === 404) {
59    throw new Error("SESSION_EXPIRED");
60  }
61  if (!res.ok) {
62    const body = await res.text();
63    throw new Error(`Send failed: ${res.status} ${body}`);
64  }
```

In `send`, 404 is treated as expiry; everything else gets one generic user-facing message:

```ts
128  } catch (err) {
129    if (err instanceof Error && err.message === "SESSION_EXPIRED") {
132      clearSession();
133      setSessionExpired(true);
134      pendingResendRef.current = trimmed;
135    } else {
136      console.error("Chat send error:", err);
137      setError(
138        "Le service est momentanément indisponible. Veuillez réessayer."
139      );
140    }
```

The generic error is rendered only in the non-empty-message branch of the widget:

```tsx
141  {error && (
142    <p className="text-red-600 text-xs">{error}</p>
143  )}
```

Error handling is not typed by status or backend error category. These all look the same to the user:

- 400/422 validation errors.
- 429 request rate limits.
- 500 backend failures.
- Network failure.
- CORS/configuration failure.
- Session-creation failure during normal `send`.

The raw backend body is included in the internal thrown error and logged to the browser console, but the ordinary `send` path displays a generic French message.

The `startNewChat` flow has two other generic messages:

- Session creation failure: `Impossible de démarrer une nouvelle conversation. Réessayez.`
- Resend failure: `Le service est momentanément indisponible.`

There is no structured error class or discriminated error response handling.

---

# Part C — Session TTL check on open

## C1. Session-age check when opening chat

The frontend does not check session age when the chat opens.

Open behavior is only:

```ts
const open = useCallback(() => setIsOpen(true), []);
```

The stored `created_at` timestamp is validated as a number by `loadSession()`, but it is never compared with the current time. There is no frontend TTL constant and no idle timestamp.

Expiry is discovered only when the user sends a message and the backend responds with HTTP 404.

## C2. Proactive backend validation

There is no proactive session validation on provider mount or chat open.

The frontend makes no request equivalent to:

- `GET /chat/session/{id}`
- `GET /chat/session/{id}/messages`
- Any health/validation request tied to the stored session

The backend does not expose either of those GET endpoints anyway.

The only chat network operations in `ChatProvider.tsx` are:

```ts
POST /chat/session
POST /chat/session/{id}/message
```

The frontend also does not invoke the available backend delete endpoint.

## C3. Frontend hardcoded TTL

There is no frontend TTL constant.

The locally stored `created_at` is written here:

```ts
const rec: SessionRecord = {
  session_id: data.session_id,
  created_at: Date.now(),
};
```

It is read and type-checked here:

```ts
if (
  !parsed ||
  typeof parsed.session_id !== "string" ||
  typeof parsed.created_at !== "number"
) {
  return null;
}
```

It is never used to determine expiry. The frontend also has no `last_activity`, so it cannot independently reproduce the backend's 10-minute idle-timeout calculation.

---

# Part D — Current behavior versus desired behavior

| Item | Status | Current behavior |
|---|---|---|
| **D1. Empty visible history + expired session on open should silently re-session** | **Deviating** | Opening chat only sets `isOpen=true`. It neither checks local age nor validates the session. The stale ID remains silently present until the first send. No popup appears merely on open, but no silent re-session occurs either. |
| **D2. Empty visible history + expired session, first message should silently re-session and send** | **Deviating** | The first user bubble is appended, the stale ID receives a POST, the 404 sets `sessionExpired=true`, and the UI requires the user to click “Démarrer une nouvelle conversation.” Only after that click is the pending message resent. |
| **D3. Non-empty visible history + expired session, new message should show popup/button** | **Matching** | A 404 sets `sessionExpired=true`; because the message list is non-empty, the amber expiry block and start-new-chat button render. The pending message is retained for resend after confirmation. |
| **D4. Non-empty visible history + valid session, reload should preserve visible history** | **Deviating** | Only the session ID and local creation timestamp persist. `messages` is React state initialized to `[]`, and there is no history endpoint, so visible history disappears after reload even if the backend session remains valid. |
| **D5. Reset should clear server session too** | **Deviating** | Reset removes localStorage and React state only. It never calls the existing `DELETE /chat/session/{id}` endpoint, so a valid server-side session remains until expiry/eviction/restart. |
| **D6. Pasting 3,000 chars should be prevented client-side** | **Deviating** | The textarea has no `maxLength` and no counter. The request reaches the backend and is rejected by the 2,000-character Pydantic limit with HTTP 422, which the frontend displays as a generic service-unavailable error. |

---

# Root-cause summary

The “session expired, start new chat” UI appears after an apparently empty chat because the frontend persists the backend session ID but does not persist visible messages or validate the session on open. After a reload, `messages` is empty while a stale ID can remain in localStorage. On the first send, the frontend appends the user's message before posting to the stale session; the backend returns the same 404 for unknown and expired sessions; the frontend then sets `sessionExpired=true`. Because the just-added user bubble makes `messages.length > 0`, the widget enters its non-empty render branch and displays the expiry block and button. The code never distinguishes a first message in an otherwise empty visible conversation from a message that extends an established conversation. The complete UX deviations are: no silent re-session on open, no silent first-message recovery, no visible-history persistence across reloads, no server-side deletion on reset, and no client-side 2,000-character enforcement. The non-empty-history expiry popup behavior is the only listed desired behavior currently matched.
