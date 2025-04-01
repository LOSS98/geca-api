# GECA API Endpoint Documentation

## Overview

GECA Messaging API is a robust Python-based messaging service providing secure email and SMS verification with an intelligent queuing system. Built using FastAPI, this service offers comprehensive communication utilities for authentication and messaging.

## Technology Stack

- **Language**: Python 3.11.0
- **Web Framework**: FastAPI
- **Database**: SQLite
- **Email**: SMTP
- **SMS**: TextMeBot API

## Key Features

- 📧 **Email Verification**
  - Generate and validate secure verification codes
  - Custom HTML email templates
  - Queue-based email sending

- 📱 **SMS Messaging**
  - Send SMS through TextMeBot API
  - Intelligent queuing with controlled sending intervals

- 🔐 **API Security**
  - Endpoint protection via API key authentication
  - Secure environment variable management

- 📊 **Queue Management**
  - Real-time queue status monitoring
  - Configurable send rates and attempt limits

## Project Structure

```
geca-api/
├── .venv/                # Python virtual environment
├── .env                  # Environment variables
├── app.py                # Main FastAPI application
├── email_template.html   # HTML email template
├── verification.db       # SQLite database
├── verification_utils.py # Code verification utilities
├── email_utils.py        # Email queuing utilities
└── sms_utils.py          # SMS queuing utilities
```

## Prerequisites

- Python 3.11.0
- pip package manager
- SMTP account for email sending
- TextMeBot account for SMS services

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/geca-api.git
   cd geca-api
   ```

2. Create and activate a virtual environment:
   ```bash
   # Ensure you have Python 3.11.0 installed
   python3.11 -m venv .venv
   
   # Activate the virtual environment
   # On Windows
   .venv\Scripts\activate
   # On Linux/macOS
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment Variables
   Create a `.env` file with the following configuration:
   ```
   API_KEY=your_secure_api_key
   EMAIL_ADDRESS=your_smtp_email@example.com
   EMAIL_PASS=your_smtp_password
   EMAIL_SERVER=smtp.gmail.com
   EMAIL_PORT=465
   TEXTMEBOT_API_KEY=your_textmebot_api_key
   MAX_DURATION=3600
   MAX_ATTEMPS=3
   ```

## Authentication

### API Key Requirements
- All endpoints require an API key
- Pass the API key in the `X-API-KEY` header
- If no valid API key is provided, you'll receive a 403 Forbidden error

## Verification Endpoints

### 1. Generate Verification Code
- **Endpoint**: `POST /generate`
- **Purpose**: Generate a verification code and send it to an email address

#### Request
```json
{
  "email": "user@uphf.fr"
}
```

#### Successful Response
```json
{
  "message": "Code will be sent",
  "email": "user@uphf.fr",
  "status": 200
}
```

#### Possible Errors
- `400 Bad Request`: Invalid email format
- `500 Internal Server Error`: System error during code generation

#### Python Request Example
```python
import requests

url = "http://localhost:5000/generate"
headers = {"X-API-KEY": "your_api_key"}
data = {"email": "user@example.com"}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 2. Verify Verification Code
- **Endpoint**: `POST /verify`
- **Purpose**: Validate a verification code sent to an email

#### Request
```json
{
  "email": "user@uphf.fr",
  "code": "ABC123"
}
```

#### Successful Response
```json
{
  "message": "Valid code",
  "status": 200
}
```

#### Possible Errors
- `400 Bad Request`: Invalid code
- `429 Too Many Attempts`: Exceeded maximum verification attempts
- `410 Gone`: Code has expired
- `404 Not Found`: Email not found in verification system

#### Python Request Example
```python
import requests

url = "http://localhost:5000/verify"
headers = {"X-API-KEY": "your_api_key"}
data = {
  "email": "user@example.com",
  "code": "123456"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 3. Send Custom Code
- **Endpoint**: `POST /send-custom-code`
- **Purpose**: Send a custom verification code via email

#### Request
```json
{
  "email": "user@uphf.fr",
  "code": "CUSTOM123",
  "subject": "Optional Custom Subject"
}
```

#### Successful Response
```json
{
  "message": "Custom code will be sent",
  "email": "user@uphf.fr",
  "queue_id": 1,
  "status": 200
}
```

#### Possible Errors
- `500 Internal Server Error`: Failed to queue email

## Messaging Endpoints

### 4. Send Email
- **Endpoint**: `POST /send-email`
- **Purpose**: Send a custom email to a specific address

#### Request
```json
{
  "to": "recipient@example.com",
  "subject": "Important Message",
  "body": "This is the email content in HTML format"
}
```

#### Successful Response
```json
{
  "message": "Email queued successfully",
  "to": "recipient@example.com",
  "queue_id": 2,
  "status": 200
}
```

#### Possible Errors
- `500 Internal Server Error`: Failed to queue email

#### Python Request Example
```python
import requests

url = "http://localhost:5000/send-email"
headers = {"X-API-KEY": "your_api_key"}
data = {
  "to": "recipient@example.com",
  "subject": "Hello",
  "body": "<html><body><h1>Welcome!</h1></body></html>"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 5. Send SMS
- **Endpoint**: `POST /send-sms`
- **Purpose**: Send an SMS to a specific phone number

#### Request
```json
{
  "recipient": "+33612345678",
  "message": "Your SMS message here"
}
```

#### Successful Response
```json
{
  "message": "SMS queued successfully",
  "recipient": "+33612345678",
  "queue_id": 1,
  "status": 200
}
```

#### Requirements
- Phone number MUST start with a country code (e.g., +33 for France)

#### Possible Errors
- `400 Bad Request`: Invalid phone number format
- `500 Internal Server Error`: Failed to queue SMS

#### Python Request Example
```python
import requests

url = "http://localhost:5000/send-sms"
headers = {"X-API-KEY": "your_api_key"}
data = {
  "recipient": "+33612345678",
  "message": "Your verification code is 123456"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## Status Endpoint

### 6. Queue Status
- **Endpoint**: `GET /queue-status`
- **Purpose**: Check the current status of email and SMS queues

#### Successful Response
```json
{
  "email_queue_size": 2,
  "sms_queue_size": 1
}
```

#### Python Request Example
```python
import requests

url = "http://localhost:5000/queue-status"
headers = {"X-API-KEY": "your_api_key"}

response = requests.get(url, headers=headers)
print(response.json())
```

## Common Error Responses

### Authentication Errors
- `403 Forbidden`: Invalid or missing API key

### Validation Errors
- `400 Bad Request`: 
  - Invalid email format
  - Missing required fields
  - Incorrect phone number format

### System Errors
- `500 Internal Server Error`: 
  - Database connection issues
  - Email/SMS sending failures
  - Unexpected system errors