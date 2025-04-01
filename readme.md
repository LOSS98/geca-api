# GECA API - Messaging Service with Queuing System

GECA API is a messaging service that provides an API for sending emails and SMS with managed queues. The API ensures orderly processing with controlled delays between each send operation (1 second for emails, 6 seconds for SMS).

## Key Features

- ✉️ **Email Queue** - Sends emails with a 1-second delay between each send
- 📱 **SMS Queue** - Sends SMS via TextMeBot with a 6-second delay between each send
- 🔐 **Code Verification** - Generates and verifies security codes for email authentication
- 🔑 **API Security** - Endpoint protection via API key
- 📊 **Queue Monitoring** - Real-time queue status consultation

## Project Structure

```
geca-api/
├── .venv/                # Python virtual environment
├── .env                  # Environment variables
├── app.py                # Main FastAPI application
├── email_template.html   # HTML template for emails
├── verification.db       # SQLite database
├── verification_utils.py # Utilities for code verification
├── email_utils.py        # Utilities for email queuing
└── sms_utils.py          # Utilities for SMS queuing
```

## Prerequisites

- Python 3.7+
- SMTP account for sending emails
- TextMeBot account for sending SMS (http://textmebot.com)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/geca-api.git
   cd geca-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   API_KEY=your_custom_api_key
   EMAIL_ADDRESS=your_email@example.com
   EMAIL_PASS=your_email_password
   EMAIL_SERVER=smtp.example.com
   EMAIL_PORT=465
   TEXTMEBOT_API_KEY=your_textmebot_api_key
   MAX_DURATION=3600
   MAX_ATTEMPS=3
   ```

## Starting the Server

To start the API server:

```bash
python app.py
```

The server will start on `http://127.0.0.1:5000` by default.

## API Endpoints

### Code Verification

#### `POST /generate`
Generates a verification code and sends it via email.

**Request:**
```json
{
  "email": "user@uphf.fr"
}
```

**Response:**
```json
{
  "message": "Code will be sent",
  "email": "user@uphf.fr",
  "status": 200
}
```

#### `POST /verify`
Verifies a code received via email.

**Request:**
```json
{
  "email": "user@uphf.fr",
  "code": "ABC123XYZ"
}
```

**Response:**
```json
{
  "message": "Valid code",
  "status": 200
}
```

### Message Sending

#### `POST /send-email`
Adds an email to the queue.

**Request:**
```json
{
  "to": "recipient@example.com",
  "subject": "Email subject",
  "body": "Email content"
}
```

**Response:**
```json
{
  "message": "Email queued successfully",
  "to": "recipient@example.com",
  "queue_id": 1,
  "status": 200
}
```

#### `POST /send-sms`
Adds an SMS to the queue.

**Request:**
```json
{
  "recipient": "+33612345678",
  "message": "SMS content"
}
```

**Response:**
```json
{
  "message": "SMS queued successfully",
  "recipient": "+33612345678",
  "queue_id": 1,
  "status": 200
}
```

### Status

#### `GET /queue-status`
Returns the current state of the queues.

**Response:**
```json
{
  "email_queue_size": 2,
  "sms_queue_size": 1
}
```

## Authentication

All endpoints require API key authentication. Add the `X-API-KEY` header to each request:

```
X-API-KEY: your_custom_api_key
```

## API Documentation

Interactive documentation is available at `http://127.0.0.1:5000/docs` when the server is running.

## Email Template Customization

Emails use an HTML template. You can customize this template by modifying the `email_template.html` file. The template uses the `{{ variable }}` substitution syntax to insert dynamic values.

Example template:
```html
<html>
<body>
  <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
    <h2>Your Verification Code</h2>
    <p>Here is your code: <strong>{{ code }}</strong></p>
  </div>
</body>
</html>
```

## Error Handling

The API returns standard HTTP error codes:

- `400 Bad Request` - Invalid request (e.g., incorrect email format)
- `403 Forbidden` - Incorrect API key
- `404 Not Found` - Resource not found
- `410 Gone` - Code expired
- `429 Too Many Requests` - Too many attempts
- `500 Internal Server Error` - Server internal error

## Development

### Auto-reload

For development, you can enable auto-reload:

```bash
uvicorn app:app --reload --port 5000
```

### Required Dependencies

Create a `requirements.txt` file with the following dependencies:

```
fastapi==0.95.1
uvicorn==0.22.0
pydantic==1.10.7
python-dotenv==1.0.0
requests==2.28.2
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributors

- Your Name - Lead Developer

## Support

For questions or issues, please open an issue on the GitHub repository.