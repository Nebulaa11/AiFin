from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router
from app.api.routes import router
from app.api.user_routes import router as user_router
from app.config import get_settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Personal Finance Optimizer",
    description="Financial engine + optimization + AI explanations + ML training hooks",
    version="0.1.0",
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)


@app.on_event("startup")
def bootstrap_models():
    from app.services.local_agent import LocalFinanceAgent

    LocalFinanceAgent()._ensure_model()


@app.get("/")
def root():
    return {"message": "AiFin API", "docs": "/docs"}
