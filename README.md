# BridgeAI Email Agent

BridgeAI Email Agent is a local, single-user email assistant. It connects to the user's Gmail, Google Tasks, and (optionally) primary Google Calendar. The React interface is built into the local FastAPI app. This repository contains the Email Agent only; the wider AI.DO platform is a later product phase.

Gmail is the only implemented email provider. Yahoo Mail, Outlook/Microsoft 365, and other providers require their own adapter and authorization flow before they can be used.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the simple application flow and [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for the prioritized launch checklist.

## How it works

```text
React UI → FastAPI → LangGraph → Gemini tool choice → validated Python tool
                                                     ├── Gmail (read-only)
                                                     ├── deterministic rules → personal Google Tasks
                                                     └── Google Calendar (event read-only)
```

The app binds to `127.0.0.1`; it is for one local user and must not be exposed publicly. Gmail and Calendar access are read-only. Task creation happens only when requested and approved by deterministic priority/action rules. Tasks are created in a dedicated `BridgeAI` task list. Calendar events are only listed; the app does not create or change them. Chat messages are not persisted; the process keeps only the current email ID per thread in memory for follow-up questions. User-created chat filter shortcuts are stored in that browser's local storage.

## Install and run

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Each person supplies their own Gemini API key in the ignored `.env` file. Never put API keys or OAuth tokens in chat or commit them. Set these Google integration paths in `.env`:

```dotenv
OAUTH_CREDENTIALS_PATH=credentials/credentials.json
OAUTH_TOKEN_PATH=token.json
CALENDAR_ENABLED=false
```

Each person uses their own Gemini key and Google Cloud OAuth client. Enable Gmail and Google Tasks APIs, create a Desktop app OAuth client, and place that person's downloaded OAuth client JSON at the ignored `credentials/credentials.json`. The first Gmail or Tasks request opens Google consent and saves authorization in the ignored local `token.json`. Follow [SETUP.md](SETUP.md) for the complete setup. Calendar access is optional; enable the Calendar API, add its read-only scope, and set `CALENDAR_ENABLED=true` only if needed. Run:

```powershell
python run.py
```

Open `http://127.0.0.1:<APP_PORT>` (default `8000`). The first email/task request opens the local browser OAuth flow for Gmail read-only and Google Tasks permissions. Each person configures the OAuth audience in their own Cloud project for their account type and saves the resulting token locally. See [SETUP.md](SETUP.md) for details and Google's current testing and verification limits.

## Distribute to colleagues

For a source handoff, use `dist/bridgeai-project-source-2.0.0.zip`. It contains the project, setup guide, frontend source, and built React UI, but excludes local secrets, virtual environments, frontend dependencies, and build caches. The ZIP is a source bundle; it does not contain a wheel. See [SETUP.md](SETUP.md) for Windows or macOS instructions. Node.js is needed only when rebuilding the frontend.

A wheel is a separate optional package artifact. It can be built with `python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .`; it is not included in the source ZIP or published to PyPI.

## Use

- Ask “Show the last five emails” or choose an unread mail filter. Open an email card to read its full message; choose **Review email** for a summary and action assessment together, or **Create eligible task** when you want the agent to evaluate task eligibility.
- Search by sender or subject/topic in your own words, for example “Is there any email from HOPR?” The agent searches matching messages and reports when there are none; it does not replace that search with a recent-email list.
- You can also request a task in chat and give it a title, for example “Create a task for this email and name it Follow up on the assessment.” Task creation still requires a validated action item and approval by deterministic priority/action rules. Low priority or no-action analyses never create tasks.
- Every free-form chat request goes to Gemini. Gemini can answer directly or request one of the application's validated tools; Python then performs the provider operation and returns its bounded result to Gemini. There is no fixed chat-intent enum or keyword parser. Inbox triage and unread filters use Gemini to classify bounded excerpts from recent unread messages. The **Unread important** filter checks up to the configured scan limit and shows only emails rated High or Critical, with summaries on the cards; it does not rely on Gmail's IMPORTANT label. The Escalated filter looks for an unresolved issue being raised for higher-level help; the Customer filter cautiously infers customer-related correspondence because no customer directory is configured. These are AI estimates.

### Logs

The app writes structured JSON operational logs to the terminal and a rotating local log file. The default file is under the signed-in user's application data/logs directory (Windows: `%LOCALAPPDATA%\BridgeAI Email Agent\logs\bridgeai.log`; macOS: `~/Library/Logs/BridgeAI Email Agent/logs/bridgeai.log`; Linux: `$XDG_STATE_HOME/BridgeAI Email Agent/logs/bridgeai.log`, or `~/.local/state/...` when unset). Set `LOG_FILE_PATH` to choose another location. Logs include workflow steps, tool/provider operations, outcomes, safe error types, and durations; they do not include prompts, email bodies, OAuth tokens, or API keys. File logs rotate automatically.
- Add personal chat filters as saved prompt shortcuts. They are stored only in the current browser.
- Google Tasks has no priority field; BridgeAI records the analyzed priority in task notes.
- Google Calendar access is read-only and limited in the UI to upcoming events in the next 14 days. Google Tasks due dates are not currently extracted from email.

## Verification

```powershell
python -m pytest -q
python -m pip check
```

Install test dependencies first with `python -m pip install -r requirements-dev.txt`.

Unit/integration adapter tests use mocked Google/Gemini behavior. Live Gmail, Google Tasks, and Calendar verification requires the local OAuth browser flow. `/health` only confirms the app process is running.

## Limits

- This release is a single-user local app with no API login or tenant controls. The supported launcher binds to loopback (`127.0.0.1`); do not expose it to a network or host it as a shared service.
- `ENVIRONMENT=production` requires `GEMINI_API_KEY`. Gmail and Google Tasks are the built-in integrations; OAuth remains per installation and is initialized only when the user first accesses a Google service.
- Each installation's OAuth audience and Google verification status determine which accounts can authorize it. This guide assumes the buyer configures and uses their own project for personal use.
- An OAuth token file grants the configured access to the signed-in person's account; keep it private.
- No tasks are assigned to other people; the Google Tasks integration is for the local user's own tasks.
