from fastapi import FastAPI, Depends, HTTPException
from starlette import status

from app.core.config import settings
from app.core.logger import logger
from sqlalchemy import text
from app.db.database import engine, Base, get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.exc import IntegrityError
from app.api.routes import users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI-powered Email Management System"
)

app.include_router(users.router)

logger.info("Application started successfully")

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
except Exception as e:
    logger.error(f"Database connection failed: {e}")


Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    import logging
    #print("HOME FUNCTION EXECUTED")
    #logger.info("Home endpoint accessed")
    logging.info("ROOT LOGGER WORKING")
    logger.info("CUSTOM LOGGER WORKING")
    return {
        "message": f"Welcome to {settings.app_name} "
    }

@app.get("/health")
def health():
    print("HEALTH FUNCTION EXECUTED")
    logger.info("Health endpoint accessed")
    return {
        "status": "healthy",
        "debug": settings.debug,
        "version": settings.app_version
    }


