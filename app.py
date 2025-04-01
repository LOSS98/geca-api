import uvicorn
import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate API_KEY existence
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY is not defined in the .env file")

# Import utility functions
try:
    from verification_utils import generate_code, verify_code, send_code_email
except ImportError as e:
    raise ImportError(f"Error importing utilities: {e}")

# Initialize FastAPI app
app = FastAPI(title="Email Verification API", version="1.0")

# API key authentication
api_key_header = APIKeyHeader(name="X-API-KEY")

def verify_api_key(api_key: str = Security(api_key_header)):
    """ Validates the provided API key. """
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Request models
class EmailRequest(BaseModel):
    email: EmailStr  # Ensures valid email format

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str

# Routes
@app.get("/")
def home(api_key: str = Depends(verify_api_key)):
    """ Health check endpoint to verify if the API is running. """
    return {"message": "Hello world!", "status": 200}

@app.post("/generate")
def generate(request: EmailRequest, api_key: str = Depends(verify_api_key)):
    """ Generates a verification code and sends it via email. """
    try:
        code = generate_code(request.email)
        if code == -1:
            raise HTTPException(status_code=400, detail="Unauthorized email")

        send_code_email(request.email, "Your verification code", code)
        return {"message": "Code sent", "email": request.email, "status": 200}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")

@app.post("/verify")
def verify(request: VerifyRequest, api_key: str = Depends(verify_api_key)):
    """ Verifies if the provided code is valid. """
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

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True, log_level="info")
