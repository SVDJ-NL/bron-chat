from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, sessions, feedback
from .config import settings
from .database import init_db
import asyncio
import sentry_sdk


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

fast_api_app = FastAPI()

# Configure CORS
fast_api_app.add_middleware(
    CORSMiddleware,    
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
fast_api_app.include_router(chat.router)
fast_api_app.include_router(sessions.router)
fast_api_app.include_router(feedback.router)

@fast_api_app.on_event("startup")
async def startup_event():
    # await asyncio.sleep(10)
    init_db()

@fast_api_app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@fast_api_app.get("/health")
async def health_check():
    return {"status": "healthy"}
