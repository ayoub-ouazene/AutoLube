# AutoLube

Monorepo for the AutoLube oil and lubricant shop.

- `backend/` — FastAPI backend and AI assistant
- `frontend/` — customer-facing web app (scaffold)
- `Reports/` — project documentation and notes

## Project structure

```text
.
├── backend/
│   ├── app/          FastAPI application, services, and AI agent
│   ├── alembic/      Database migrations
│   ├── scripts/      Database setup, seed data, and password utility
│   ├── tests/        Import checks and API workflow scripts
│   ├── .env          Local configuration (create this file)
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/         Customer-facing app scaffold
├── Reports/          Project reports
└── README.md
```

## Backend overview

The backend provides product browsing, customer orders, an AI chat assistant, and admin endpoints for orders and inventory. The assistant checks local vehicle oil-specification and stock data, then can use DDGS and Tavily web search when specifications are missing. Product image uploads can use Cloudinary.

The API includes:

- Public product listing and product detail endpoints with category, brand, price, size, and text filters.
- Chat sessions that return assistant replies and matching products.
- Customer order creation.
- JWT-protected admin order and inventory management.
- Optional product image upload and deletion through Cloudinary.
- Request rate limits, configurable CORS, and a health endpoint.

## Requirements

- Python 3.10 or newer.
- PostgreSQL, configured with a `postgresql+psycopg://` database URL.
- Groq credentials for the assistant. OpenRouter keys can be configured for model failover.
- Tavily API key for search fallback; DDGS is also used as a search provider.
- Cloudinary credentials are optional and only needed for image uploads.

## Install

Create and activate a virtual environment from the repository root, then install the backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

For macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

## Configure the backend

Create `backend/.env`. These settings are required by the current application:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt-hash>
JWT_SECRET_KEY=<long-random-secret>
```

Generate an admin password hash from the `backend/` directory:

```powershell
python -m scripts.hash_password
```

Optional assistant and service settings:

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

`GROQ_KEYS` and `OPENROUTER_KEYS` are comma-separated key pools used by model failover. Keep `backend/.env` private; it is ignored by Git.

## Database setup

Run these commands from `backend/`. Apply migrations with:

```powershell
alembic upgrade head
```

For a development database, tables can instead be created from the current models:

```powershell
python -m scripts.init_db
```

To drop and recreate all model tables:

```powershell
python -m scripts.init_db --reset
```

Seed or reset development cache and stock data:

```powershell
python -m scripts.seed_cache
python -m scripts.seed_stock
python -m scripts.seed_cache --reset
python -m scripts.seed_stock --reset
```

## Run the API

From `backend/`, start the development server:

```powershell
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. OpenAPI documentation is available at `/docs`; `/health` returns the health status.

All application routes are prefixed with `/api/v1`:

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

From `backend/`, run the assistant in a terminal:

```powershell
python -m tests.test_cli_chat
```

Enter a request at the `Customer:` prompt. Type `exit` or `quit` to stop.

## Tests and workflow scripts

Run the import smoke tests from `backend/`:

```powershell
python -m unittest tests.test_imports
```

`tests/test_admin.py` and `tests/test_e2e_flow.py` are manual HTTP workflows that expect the API server and configured database to be running. `tests/llm_product_extraction.py` also calls the live API and assistant. `tests/test_cli_chat.py` is the CLI runner.