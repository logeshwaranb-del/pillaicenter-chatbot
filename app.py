"""
app.py - Main FastAPI Application 
(Updated with Email OTP Verification Feature)
"""
import logging
import os
import json
import random
import smtplib
from email.mime.text import MIMEText
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from config import LOG_LEVEL, LOG_FORMAT
from chatbot import generate_answer, build_or_load_index
from scheduler import start_scheduler
from scraper import full_scrape_and_save
from vector_store import build_or_load_index as vs_build

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger("app")

# ==================== OTP Storage ====================
otp_storage = {}   # Temporary storage for OTPs

# ==================== Pydantic Models ====================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list = []
    error: Optional[str] = None

class RefreshResponse(BaseModel):
    status: str
    message: str

class SendOTPRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

# ==================== Lifespan ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PillaiCenter Chatbot API...")
    try:
        build_or_load_index()
        logger.info("Vector index loaded successfully.")
    except Exception as e:
        logger.warning(f"Index loading issue: {e}")

    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    yield

    logger.info("Shutting down...")
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)


# ==================== FastAPI App ====================
app = FastAPI(
    title="PillaiCenter Customer Support Chatbot",
    description="RAG-based AI Chatbot for pillaicenter.com and academy.pillaicenter.com",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==================== Favicon Fix ====================
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"detail": "No favicon"}


# ==================== Chrome DevTools Fix ====================
@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools():
    return {}


# ==================== Routes ====================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pillai Center Assistant</title>
        <link rel="stylesheet" href="/static/chatbot.css">
        <style>
            body {
                margin: 0;
                padding: 0;
                background: #0a1625;
                height: 100vh;
                overflow: hidden;
                position: relative;
            }

            .night-sky {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(to bottom, #0a1625 0%, #111827 100%);
                z-index: 1;
            }

            .stars {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    radial-gradient(white 1px, transparent 1.5px),
                    radial-gradient(white 1.2px, transparent 2px);
                background-size: 180px 180px, 320px 320px;
                background-position: 0 0, 40px 60px;
                opacity: 0.9;
                z-index: 2;
            }

            .moon {
                position: absolute;
                top: 60px;
                right: 80px;
                width: 110px;
                height: 110px;
                background: #f4f1e9;
                border-radius: 50%;
                box-shadow: 
                    0 0 30px #f4f1e9,
                    0 0 60px #e8d9a0;
                z-index: 3;
            }

            .moon::before {
                content: '';
                position: absolute;
                top: 20px;
                left: 25px;
                width: 18px;
                height: 18px;
                background: #d4c9a8;
                border-radius: 50%;
                box-shadow: 
                    35px 15px 0 #d4c9a8,
                    15px 45px 0 #d4c9a8,
                    50px 40px 0 #d4c9a8;
            }
        </style>
    </head>
    <body>

        <!-- Night Sky + Moon Background -->
        <div class="night-sky"></div>
        <div class="stars"></div>
        <div class="moon"></div>

        <!-- Chatbot Widget will load here automatically -->
        <script src="/static/chatbot.js"></script>

    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "pillaicenter-chatbot",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not req.message or len(req.message.strip()) < 2:
        raise HTTPException(status_code=400, detail="Message is too short")
    result = generate_answer(req.message.strip(), session_id=req.session_id)
    return ChatResponse(**result)


@app.post("/refresh-data", response_model=RefreshResponse)
async def refresh_data(background_tasks: BackgroundTasks):
    def _do_refresh():
        try:
            logger.info("Starting full data refresh...")
            full_scrape_and_save()
            vs_build(force_rebuild=True)
            logger.info("Full refresh completed.")
        except Exception as e:
            logger.error(f"Refresh failed: {e}")

    background_tasks.add_task(_do_refresh)
    return RefreshResponse(
        status="accepted",
        message="Full refresh started in background."
    )


# ==================== Save User Details in MySQL ====================
@app.post("/save-user")
async def save_user(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()

        if not name or not email or not phone:
            return {"status": "error", "message": "Name, Email and Phone are required"}

        import mysql.connector

        db = mysql.connector.connect(
            host="localhost",                  
            user="root",                       
            password="pillaicenter@001",     
            database="chatbot_user_data"            
        )

        cursor = db.cursor()

        sql = "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)"
        values = (name, email, phone)

        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()

        print(f"✅ User saved in MySQL: {name} | {email} | {phone}")
        return {"status": "success", "message": "User saved successfully in MySQL"}

    except Exception as e:
        print(f"❌ Error saving user in MySQL: {e}")
        return {"status": "error", "message": str(e)}


# ==================== End Chat ====================
@app.post("/end-chat")
async def end_chat(request: Request):
    try:
        data = await request.json()
        session_id = data.get("session_id", "unknown")
        print(f"✅ Chat ended for session: {session_id}")
        return {"status": "success", "message": "Chat ended successfully"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== NEW: Send OTP ====================
@app.post("/send-otp")
async def send_otp(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()

        if not email:
            return {"status": "error", "message": "Email is required"}

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(seconds=60)

        otp_storage[email] = {"otp": otp, "expiry": expiry}

        # Send Email using Gmail
        sender_email = "pillaicentertester@gmail.com"          # ← Change this
        sender_password = "ynub vtwa gkaq toyv"          # ← Change this (Gmail App Password)

        msg = MIMEText(f"Your verification code is: {otp}\n\nThis code will expire in 10 minutes.")
        msg["Subject"] = "Pillai Center Chatbot - Verification Code"
        msg["From"] = sender_email
        msg["To"] = email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()

        return {"status": "success", "message": "Verification code sent successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Failed to send OTP: {str(e)}"}


# ==================== NEW: Verify OTP ====================
@app.post("/verify-otp")
async def verify_otp(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        entered_otp = data.get("otp", "").strip()

        if email not in otp_storage:
            return {"status": "error", "message": "No OTP found. Please request again."}

        stored = otp_storage[email]

        if datetime.now() > stored["expiry"]:
            del otp_storage[email]
            return {"status": "error", "message": "OTP expired. Please request a new one."}

        if entered_otp == stored["otp"]:
            del otp_storage[email]
            return {"status": "success", "message": "Email verified successfully"}
        else:
            return {"status": "error", "message": "Invalid OTP"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)