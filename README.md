# BridgeAI Email Agent

An AI-powered Email Management System built using **Python, FastAPI, PostgreSQL, Gemini, and LangChain**.

## Project Overview

BridgeAI Email Agent is being developed as part of the **BridgeLabz AI Engineering Assessment**.

The system is designed as an agentic email-processing backend that can analyze emails, extract actionable information, apply deterministic business rules, and create tasks when required.

The project is designed to evolve into a complete Gmail-based Email Agent.

## Current Capabilities

- Store and manage emails
- Analyze emails using Google Gemini
- Generate structured AI analysis
- Summarize emails
- Dynamically classify emails
- Detect priority
- Detect sentiment
- Determine whether action is required
- Determine whether attention is required
- Extract action items
- Apply deterministic business rules
- Create tasks from approved action items
- Prevent duplicate task creation
- Persist AI analysis results
- LangChain Agent and Tool integration
- Agent tools connected to Service/Repository layers
- PostgreSQL persistence

---

# Architecture

The current email-processing architecture is:
```text
Email
  |
  v
Gemini AI
  |
  v
AI Analysis
  |
  +----------------------+
  |                      |
  v                      v
Save Analysis       Business Rules
                         |
                         v
                  Task Execution
                         |
                         v
                    Task Service
                         |
                         v
                  Task Repository
                         |
                         v
                    PostgreSQL
````

The Agent architecture is:
```
                LangChain Agent
                       |
                       v
                     Tools
                       |
                       v
                 Service Layer
                       |
                       v
               Repository Layer
                       |
                       v
                  PostgreSQL
```

---

# Technology Stack

## Backend

- Python 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Pydantic

## AI

- Google Gemini API
- Gemini structured output
- LangChain
- LangGraph (in progress)
- LangSmith (planned/in progress)

## Supporting Technologies

- Redis
- Celery
- Alembic
- HTTPX
- Python-dotenv
- Git
- GitHub

## Planned Integrations

- Gmail API
- Google OAuth 2.0
- Google Calendar
- Notifications

---

# Project Structure

The project follows a layered backend architecture:
```
bridgeai-email-agent/
│
├── app/
│   ├── agents/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── tools/
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
├── run.py
├── README.md
└── SETUP.md
```

---

# AI Email Analysis

Gemini analyzes emails and produces structured information including:

- Summary
- Category
- Priority
- Sentiment
- Requires action
- Requires attention
- Action items

Example:
```
{
  "summary": "Production payment failures are affecting customers.",
  "category": {
    "main": "Technical Issue",
    "sub_category": "Payment Failure",
    "group": "Production"
  },
  "priority": "Critical",
  "sentiment": "Negative",
  "requires_action": true,
  "requires_attention": true,
  "action_items": [
    "Investigate the Payment API error",
    "Inform the technical team"
  ]
}
```

The category is dynamically inferred from the email context instead of being restricted to a fixed hard-coded category list.

---

# Business Rules

AI analysis and business decisions are kept separate.

The AI determines:
```
What does the email mean?
```

Business logic determines:
```
What should the system do?
```

Example:
```
AI Analysis
     |
     v
Requires Action?
     |
   +---+---+
   |       |
  No      Yes
   |       |
 Finish    v
       Check Existing Task
           |
       +---+---+
       |       |
     Exists   New
       |       |
     Skip    Create
```

This prevents the AI model from directly controlling database operations.

---

# Duplicate Task Prevention

Before creating a task for an action item, the task execution logic checks whether an equivalent task already exists for the email.

This prevents duplicate tasks from being created when the same email is processed multiple times.

---

# Email Analysis Persistence

AI analysis results are stored separately from the original email.
```
Email
  |
  +---- EmailAnalysis
  |
  +---- EmailAnalysis
  |
  +---- EmailAnalysis
```

This allows an email to be analyzed again in the future while preserving previous analysis history.

---

# LangChain Agent

LangChain is used to build the Agent layer.

The current Agent can use tools to interact with backend functionality.

Example:
```
User
  |
  v
LangChain Agent
  |
  v
Tool
  |
  v
Service
  |
  v
Repository
  |
  v
PostgreSQL
```

The Agent does not directly contain database logic.

---

# LangGraph

LangGraph is being used/planned for orchestration of the larger multi-step Agent workflow.

The intended workflow is:
```
Incoming Email
      |
      v
Analyze Email
      |
      v
Save Analysis
      |
      v
Business Decision
      |
      +---- No Action ----> Finish
      |
      v
Check Existing Task
      |
      +---- Exists -------> Finish
      |
      v
Create Task
      |
      v
Finish
```

LangGraph will become more important as the workflow gains additional state, branching, approval steps, and retries.

---

# LangSmith

LangSmith is intended for Agent observability, tracing, debugging, and evaluation.

It will allow Agent execution to be inspected through traces such as:
```
Agent
 |
 +-- Gemini call
 |
 +-- Tool selection
 |
 +-- Tool execution
 |
 +-- Service call
 |
 +-- Database operation
 |
 +-- Final result
```

---

# Gmail Integration

Gmail integration is part of the planned production workflow.

The intended architecture is:
```
Gmail
  |
  v
Google OAuth 2.0
  |
  v
Gmail API
  |
  v
BridgeAI
  |
  v
Email
  |
  v
AI Analysis
  |
  v
Business Rules
  |
  v
Tasks
```

Gmail integration is still under development.

---

# Development Status

## Completed / Working

- FastAPI backend
- PostgreSQL integration
- SQLAlchemy models
- Email management foundation
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
- Agent → Service → Repository → PostgreSQL architecture
- Unit tests for business rules and task execution

## In Progress

- Complete end-to-end AI analysis persistence testing
- Gmail integration
- Automatic email ingestion
- Automatic task assignment
- LangGraph workflow
- LangSmith observability
- Additional automated tests
- Production error handling and retries

## Planned

- Gmail OAuth
- Gmail message ingestion
- Automatic email processing
- Automatic task assignment
- Calendar integration
- Notifications
- Deployment
- Final documentation


For complete installation and configuration instructions, see:

SETUP.md