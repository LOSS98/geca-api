import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY is not defined in the .env file")

try:
    from verification_utils import generate_code, verify_code, send_code_email, check_fisa
    from sms_utils import queue_sms, init_sms_db, start_sms_worker
    from email_utils import init_email_db, start_email_worker, queue_email, load_html_template
except ImportError as e:
    raise ImportError(f"Error importing utilities: {e}")

app = FastAPI(title="Messaging API", description="API for email verification and SMS sending", version="1.0")

api_key_header = APIKeyHeader(name="X-API-KEY")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

class EmailRequest(BaseModel):
    email: EmailStr

class EmailDirectRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str

class SendCodeRequest(BaseModel):
    email: EmailStr
    code: str
    subject: Optional[str] = "Los Barryachies - Ton code de code de vérification"

class SMSRequest(BaseModel):
    recipient: str
    message: str

class QueueStatusResponse(BaseModel):
    email_queue_size: int
    sms_queue_size: int

@app.get("/")
def home(api_key: str = Depends(verify_api_key)):
    return {"message": "Messaging API is running", "status": 200}

@app.post("/generate")
def generate(request: EmailRequest, api_key: str = Depends(verify_api_key)):
    try:
        code = generate_code(request.email)
        if code == -1:
            raise HTTPException(status_code=400, detail="Unauthorized email")

        send_code_email(request.email, "Los Barryachies - Ton code de code de vérification", code)
        return {"message": "Code will be sent", "email": request.email, "status": 200}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")

@app.post("/verify")
def verify(request: VerifyRequest, api_key: str = Depends(verify_api_key)):
    result = verify_code(request.email, request.code)

    if result == 1:
        return {"message": "Valid code", "status": 200}
    elif result == 0:
        raise HTTPException(status_code=400, detail="Invalid code")
    elif result == -1:
        raise HTTPException(status_code=429, detail="Too many attempts")
    elif result == -2:
        raise HTTPException(status_code=410, detail="Code expired")
    elif result == -3:
        raise HTTPException(status_code=404, detail="Email not found")
    else:
        raise HTTPException(status_code=500, detail="Unknown error")

@app.post("/send-custom-code")
def send_custom_code(request: SendCodeRequest, api_key: str = Depends(verify_api_key)):
    try:

        html_content = load_html_template({'code': request.code})

        email_id = queue_email(request.email, "Los Barryachies - Ton code de code de vérification", html_content)

        if email_id:
            return {
                "message": "Custom code will be sent",
                "email": request.email,
                "queue_id": email_id,
                "status": 200
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue email with custom code")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending custom code: {str(e)}")

@app.post("/send-email")
def send_email(request: EmailDirectRequest, api_key: str = Depends(verify_api_key)):
    try:

        email_id = queue_email(request.to, request.subject, request.body)

        if email_id:
            return {
                "message": "Email queued successfully",
                "to": request.to,
                "queue_id": email_id,
                "status": 200
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue email")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.post("/send-sms")
def send_sms(request: SMSRequest, api_key: str = Depends(verify_api_key)):
    try:

        if not request.recipient.startswith('+'):
            raise HTTPException(status_code=400, detail="Phone number must start with country code (ex: +33)")

        sms_id = queue_sms(request.recipient, request.message)

        if sms_id:
            return {
                "message": "SMS queued successfully",
                "recipient": request.recipient,
                "queue_id": sms_id,
                "status": 200
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue SMS")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending SMS: {str(e)}")

@app.get("/queue-status", response_model=QueueStatusResponse)
async def queue_status(api_key: str = Depends(verify_api_key)):
    try:

        conn = sqlite3.connect("/app/verification.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM email_queue WHERE status = 'pending'")
        email_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sms_queue WHERE status = 'pending'")
        sms_count = cursor.fetchone()[0]

        conn.close()

        return {
            "email_queue_size": email_count,
            "sms_queue_size": sms_count
        }

    except Exception as e:

        return {
            "email_queue_size": 0,
            "sms_queue_size": 0
        }

@app.on_event("startup")
async def startup_event():

    init_email_db()
    init_sms_db()

    start_email_worker()
    start_sms_worker()

    print("Messaging API started with email and SMS queues")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=False)