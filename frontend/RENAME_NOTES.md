# Rename Notes: AutoLube → LubriStock (frontend)

Frontend was renamed from "AutoLube" to "LubriStock" on 2026-10-22.
All user-visible text, comments, and safe internal identifiers now use
"LubriStock".

## Intentionally NOT renamed

The following strings still contain "autolube" and must NOT be
renamed without a migration:

### localStorage keys (break existing user data if changed)

- `autolube_cart_v1` — customer cart items
- `autolube_chat_session_v1` — chat session ID
- `autolube_chat_messages_v1` — persisted chat messages

## If renaming these later

Bump to `_v2` suffix, migrate old data on first read, remove `_v1`
fallback in a subsequent release. Requires careful testing of the
cart and chat flows.

## Backend

Backend code (backend/app/) was intentionally not renamed in this
phase — no user-facing impact. Docker image and container names also
unchanged. If a full rename is desired later, plan for:

- Docker image `autolube-api:dev` → `lubristock-api:dev` (compose + CI)
- Container `autolube-api` → `lubristock-api`
- Any `AUTOLUBE_*` env vars (check `.env` files first)
