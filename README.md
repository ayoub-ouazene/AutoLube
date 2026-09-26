# AutoLube Oil E-Commerce API

AutoLube is a FastAPI backend for an automotive oil and lubricant store. It provides product browsing, order placement, an AI chat assistant, and admin endpoints for managing orders and inventory. The assistant uses local vehicle oil-specification and stock data, with web search as a fallback when specifications are missing.

## Features

- Public product listing and product detail endpoints with category, brand, price, size, and text filters.
- Chat sessions backed by an agent that can look up cached oil specifications and matching stock, then use DDGS/Tavily search as needed.
- Customer order creation and admin order listing, detail, confirmation, and cancellation.
- Admin inventory CRUD and optional front/back product image uploads to Cloudinary.
- JWT-protected admin endpoints, request rate limits, CORS configuration, and health endpoint.
- PostgreSQL persistence through SQLAlchemy, with Alembic migrations and development seed scripts.
- A standalone CLI chat runner for trying the assistant without the API.

## Project layout

```text
app/
  agents/       LangChain assistant, search agent, and database tools
  api/          FastAPI routers and authentication dependencies
  core/         Settings integrations, security, rate limiting, and errors
  db/           SQLAlchemy engine and models
  schemas/      API request and response schemas
  services/     Chat, product, and order business logic
alembic/        Database migration environment and revisions
scripts/        Database initialization, seed data, and password utility
tests/          Import checks, API workflow scripts, and CLI chat runner
Reports/        Project reports
alembic.ini
requirements.txt
```

## Requirements

- Python 3.10 or newer.
- PostgreSQL and a `DATABASE_URL` using the `postgresql+psycopg://` driver.
- Groq credentials for the assistant. OpenRouter keys can be configured for model failover.
- A Tavily API key for the search fallback. DDGS can be used as the initial search path.
- Cloudinary credentials are optional; image uploads require them.

## Installation

From the project root, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file at the project root. The following settings are required by the current application:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt-hash>
JWT_SECRET_KEY=<long-random-secret>
```

Generate an admin password hash with:

```powershell
python -m scripts.hash_password
```

Set the optional assistant and service settings as needed:

```env
GROQ_KEYS=groq_key_1,groq_key_2
OPENROUTER_KEYS=openrouter_key_1
GROQ_API_KEY=groq_key_1
GROQ_API_KEY2=groq_key_2
GROQ_API_KEY3=groq_key_3
OPENROUTER_API_KEY=openrouter_key_1
TAVILY_API_KEY=tavily_key
CORS_ORIGINS=http://localhost:3000,https://your-store.example
WHATSAPP_NUMBER=
JWT_EXPIRE_MINUTES=480
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

`GROQ_KEYS` and `OPENROUTER_KEYS` are comma-separated pools used by the model failover logic. Cloudinary settings may be left empty when product image upload is not needed. Keep `.env` private; it is ignored by Git.

## Database

Apply the existing migrations:

```powershell
alembic upgrade head
```

Alternatively, create tables from the current models for a development database:

```powershell
python -m scripts.init_db
```

To drop and recreate all model tables:

```powershell
python -m scripts.init_db --reset
```

Load or reset development cache and stock records:

```powershell
python -m scripts.seed_cache
python -m scripts.seed_stock
python -m scripts.seed_cache --reset
python -m scripts.seed_stock --reset
```

## Run the API

Start the development server from the project root:

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is at `/docs`, and `/health` returns the service health status.

### API routes

All application routes are prefixed with `/api/v1`.

| Area | Routes | Access |
| --- | --- | --- |
| Chat | `POST /chat/session`, `POST /chat/session/{session_id}/message`, `DELETE /chat/session/{session_id}` | Public |
| Products | `GET /products`, `GET /products/{category}/{product_id}` | Public |
| Orders | `POST /orders` | Public |
| Admin login | `POST /admin/login` | Public credentials exchange |
| Admin orders | `GET /admin/orders`, `GET /admin/orders/{order_id}`, `POST /admin/orders/{order_id}/confirm`, `POST /admin/orders/{order_id}/cancel` | Bearer JWT |
| Admin stock | `GET/POST /admin/stock`, `PATCH/DELETE /admin/stock/{category}/{product_id}` | Bearer JWT |
| Admin images | `POST /admin/stock/{category}/{product_id}/images`, `DELETE /admin/stock/{category}/{product_id}/images/{position}` | Bearer JWT |

## CLI assistant

The assistant can also run directly in a terminal:

```powershell
python -m tests.test_cli_chat
```

Enter a request at the `Customer:` prompt. Type `exit` or `quit` to stop.

## Tests and workflow scripts

Run the import smoke tests with:

```powershell
python -m unittest tests.test_imports
```

`tests/test_admin.py` and `tests/test_e2e_flow.py` are manual HTTP workflow scripts and expect the API server and configured database to be running. `tests/llm_product_extraction.py` also calls the live API and assistant. `tests/test_cli_chat.py` is the CLI runner.
