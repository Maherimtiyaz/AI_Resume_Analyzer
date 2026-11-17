import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth_routes import router as auth_router
from app.api.document_auth import router as document_router
from app.api.ai_routes import router as ai_router
from app.core.database import Base, engine
from app.utils.vector_store_model import DocumentChunk  # import so table is registered


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (not at import time). If the database is
    # unreachable we log a clear message instead of crash-looping the service.
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables are ready")
    except Exception as e:
        logger.error(f"Could not connect to the database: {e}")
        logger.error(
            "Check DATABASE_URL. On Render, use the database's Internal URL and make "
            "sure the database still exists and is in the same region as this service "
            "(free Render Postgres databases are deleted ~30 days after creation)."
        )
    yield


app = FastAPI(title="Doc AI System", lifespan=lifespan)

# Build CORS origins — include Render frontend URL if set
origins = [
    "https://ai-powered-doc-frontend.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(document_router, prefix="/docs", tags=["Documents"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

@app.get("/")
def root():
    return {"message": "API is running"}

