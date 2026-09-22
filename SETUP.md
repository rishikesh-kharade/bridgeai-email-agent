Quick start:

python -m venv .venv

pip install -r requirements.txt

python run.py

git Open:
http://127.0.0.1:8000/docs

---

# Security

Do not commit:

- .env
- API keys
- Database passwords
- OAuth credentials
- Access tokens
- Refresh tokens

Use environment variables for sensitive configuration.

---

# Developer

**Rishikesh Kharade**

BridgeLabz AI Engineering Assessment

---

# 2. SETUP.md

# BridgeAI Email Agent — Setup Guide

This guide explains how to install, configure, and run the BridgeAI Email Agent locally.

---

# 1. Prerequisites

Install the following:

- Python 3.12+
- PostgreSQL
- Git

## Verify Python
```bash
python --version
````

Expected:

Python 3.12.x

## Verify Git

git --version


## Verify PostgreSQL

psql --version


---

# 2. Clone the Repository

Clone the repository:

git clone <https://github.com/rishikesh-kharade/bridgeai-email-agent>


Move into the project:
```
cd bridgeai-email-agent
```

---

# 3. Create a Virtual Environment

On Windows:
```
python -m venv .venv
```

## PowerShell
```
.venv\Scripts\Activate.ps1
```

## Command Prompt
```
.venv\Scripts\activate
```

After activation, the terminal should show:
```
(.venv)
```

---

# 4. Install Dependencies

Install the project dependencies:
```
pip install -r requirements.txt
```

---

# 5. PostgreSQL Setup

Create a PostgreSQL database.

Example:
```
CREATE DATABASE bridgeai;
```

Make sure the PostgreSQL server is running.

---

# 6. Environment Configuration

Create a `.env` file in the project root.

Example:
```
DATABASE_URL=postgresql://postgres:<PASSWORD>@localhost:5432/bridgeai

GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

Replace:

- `<PASSWORD>` with the PostgreSQL password
- `<YOUR_GEMINI_API_KEY>` with a valid Gemini API key

Do not commit `.env` to GitHub.

---

# 7. Database Configuration

The application reads the database connection from:
```
DATABASE_URL
```

Example:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/bridgeai
```

Make sure:

- PostgreSQL is running
- Database exists
- Username is correct
- Password is correct
- Port is correct
- Database name is correct

Default PostgreSQL port:
```
5432
```

---

# 8. Gemini API Configuration

BridgeAI currently uses Google Gemini for AI-powered email analysis.

Configure:
```
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

Never commit the API key to GitHub.

---

# 9. Run the Application

Activate the virtual environment.

Then run:
```
python run.py
```

The application will start at:
http://127.0.0.1:8000


---

# 10. Open Swagger

Open:

http://127.0.0.1:8000/docs


FastAPI Swagger provides an interactive interface for testing the APIs.

---

# 11. Basic Email Processing Test

The current development flow allows an email to be created and processed through the AI pipeline.

## Step 1 — Create an Email

Use:
```
POST /emails
```

Example:
```
{
  "sender": "client@example.com",
  "receiver": "support@bridgeai.com",
  "subject": "Production payment failure",
  "body": "Customers cannot complete payments in production. Investigate the Payment API 500 error and inform the technical team after identifying the issue.",
  "provider_message_id": "setup-test-email-001"
}
```

The database generates the internal email ID.

## Step 2 — Process the Email

Use:
```
POST /emails/{email_id}/process
```

The current development implementation also accepts an `assigned_to_id` for task-assignment testing.

Example:
```
POST /emails/1/process?assigned_to_id=1
```

Replace the IDs with valid IDs from the database.

---

# 12. Current AI Processing Flow
```
Email
  ↓
Gemini AI
  ↓
Structured AI Analysis
  ↓
Save Email Analysis
  ↓
Business Rules
  ↓
Task Execution
  ↓
PostgreSQL
```

The AI analysis includes:

- Summary
- Category
- Priority
- Sentiment
- Requires action
- Requires attention
- Action items

---

# 13. LangChain Agent

BridgeAI contains an initial LangChain Agent and Tool architecture.

The Agent can use tools to access backend functionality.
```
LangChain Agent
      ↓
Tool
      ↓
Service Layer
      ↓
Repository Layer
      ↓
PostgreSQL
```

The Agent does not directly contain database access logic.

---

# 14. Gmail Integration

Gmail integration is part of the planned production workflow.

The intended architecture is:
```
Gmail
  ↓
Google OAuth
  ↓
Gmail API
  ↓
BridgeAI
  ↓
Email
  ↓
AI Analysis
  ↓
Business Rules
  ↓
Tasks
```

Gmail integration is currently under development and is not required for the current local email-processing test.

---

# 15. Current Project Status

## Working

- FastAPI backend
- PostgreSQL integration
- SQLAlchemy models
- Email management
- User management foundation
- Task management foundation
- Gemini AI email analysis
- Structured AI output
- Email summarization
- Dynamic categorization
- Priority detection
- Sentiment detection
- Action-item extraction
- Business rules
- Duplicate task prevention
- AI analysis persistence layer
- Initial LangChain Agent
- LangChain Tool integration

## In Progress

- Gmail integration
- Automatic email ingestion
- Automatic task assignment
- LangGraph workflow
- LangSmith observability
- Additional testing
- Production error handling and retries

---

# 16. Troubleshooting

## PostgreSQL Connection Error

Check:
```
PostgreSQL server is running
DATABASE_URL is correct
Database exists
Username/password are correct
Port is correct
```

---

## Gemini API Error

Check:

1. `GEMINI_API_KEY` exists in `.env`
2. The API key is valid
3. The configured Gemini model is available
4. Retry temporary API/service errors

---

## Module Not Found

Make sure the virtual environment is activated:
```
.venv\Scripts\Activate.ps1
```

Then reinstall:
```
pip install -r requirements.txt
```

---

## Port 8000 Already in Use

Stop the existing process using port 8000 and run:
```
python run.py
```

again.

---

# 17. Security

Never commit the following to GitHub:

- `.env`
- API keys
- Database passwords
- OAuth credentials
- Access tokens
- Refresh tokens

Use environment variables for sensitive configuration.

---

# 18. Developer

**Rishikesh Kharade**

BridgeLabz AI Engineering Assessment