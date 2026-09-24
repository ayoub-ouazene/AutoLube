from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.session import engine
from fastapi.responses import RedirectResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    print("[startup] AutoLube API starting up")

    print(f"swagger documentation : http://127.0.0.1:8000/docs ")
   
    # engine is a module-level SQLAlchemy Engine; it connects lazily on first use,
    # so there's nothing to warm here beyond importing it (which we already did).
    # If you ever add a key-pool warmup or a cache warmup, do it below.
    yield
    # ---- shutdown ----
    print("[shutdown] Disposing DB engine")
    engine.dispose()


app = FastAPI(
    title="AutoLube API",
    description="Automotive oil & lubricant recommendation assistant.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
def root() :
    
    return RedirectResponse(url="/docs")