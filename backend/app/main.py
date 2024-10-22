from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, sessions
from .config import settings
from .database import init_db
import asyncio
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

@fast_api_app.on_event("startup")
async def startup_event():
    # await asyncio.sleep(10)
    init_db()
