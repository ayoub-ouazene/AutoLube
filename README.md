# Oil E-Commerce AI Assistant

This project is an in-progress backend/agent for AutoLube, an oil recommendation assistant. The current version runs as a CLI chat app with a main LangChain agent, a web search sub-agent, local database cache lookup, and stock lookup tools.

## What The App Does Now

- Collects vehicle details from the user in a terminal chat session.
- Looks up known engine/gearbox oil specs from the local database cache.
- Falls back to DDGS/Tavily web search when local specs are missing.
- Looks up matching oil products from local stock tables.
- Uses Groq models first, with optional OpenRouter failover keys.
- Uses SQLAlchemy models with Alembic migrations and seed scripts.

## Project Structure

```text
.
- agent/
  - main_agent.py              # Current CLI entry point
  - prompts.py                 # Main and search agent prompts
  - db_tools/                  # DB-backed spec and stock lookup tools
  - search_agent/              # Web search sub-agent and tools
- alembic/                     # Database migration environment
- config/
  - apis.py                    # Model provider instances
  - db.py                      # SQLAlchemy engine/session setup
  - llm_pool.py                # LLM key pool and failover logic
- models/
  - db.py                      # SQLAlchemy tables
  - Input_schema.py            # Pydantic tool schemas
- scripts/
  - init_db.py                 # Create/drop all tables from models
  - generate_mock_spec.py      # Seed local oil spec cache
  - generate_mock_stock.py     # Seed local stock data
- Reports/                     # Project report documents
- alembic.ini
- requirements.txt
- README.md
```

## Requirements

- Python 3.10 or newer.
- PostgreSQL database URL. Neon/Postgres works with the current `psycopg` dependency.
- At least one Groq API key, or one OpenRouter key for failover.
- Tavily API key for fallback search.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you are using Command Prompt instead of PowerShell:

```cmd
.venv\Scripts\activate.bat
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```text
.env
```

Use this shape:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database

GROQ_KEYS=groq_key_1,groq_key_2
OPENROUTER_KEYS=openrouter_key_1

GROQ_API_KEY=groq_key_1
GROQ_API_KEY2=groq_key_2
GROQ_API_KEY3=groq_key_3
OPENROUTER_API_KEY=openrouter_key_1
TAVILY_API_KEY=tavily_key
DAHL_API_KEY=dahl_key_if_used
```

`GROQ_KEYS` and `OPENROUTER_KEYS` are used by the current failover pool in `config/llm_pool.py`. The individual `GROQ_API_KEY*`, `OPENROUTER_API_KEY`, and `DAHL_API_KEY` values are still used by `config/apis.py` and search/extraction helpers.

## Database Setup

You can create tables directly from the SQLAlchemy models:

```powershell
python -m scripts.init_db
```

To reset all tables before creating them again:

```powershell
python -m scripts.init_db --reset
```

The project also includes Alembic. To apply migrations instead:

```powershell
alembic upgrade head
```

Seed development data after the tables exist:

```powershell
python -m scripts.generate_mock_spec
python -m scripts.generate_mock_stock
```

To wipe and reseed those mock rows:

```powershell
python -m scripts.generate_mock_spec --reset
python -m scripts.generate_mock_stock --reset
```

## Run The Current Version

Run the CLI assistant from the project root:

```powershell
python -m agent.main_agent
```

Type a customer request at the `Customer:` prompt. Type `exit` or `quit` to stop.

Example:

```text
Customer: I need engine oil for a 2018 Renault Clio IV K9K 646
```

## Development Notes

- The current app is a CLI workflow, not a web API yet.
- `specs_lookup` checks the local oil specification cache before web search.
- `stock_lookup` searches local stock tables after an oil spec is known.
- DDGS is the first web search path, with Tavily used as fallback/verification.
- External search results depend on network access and source availability.
