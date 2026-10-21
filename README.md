# BridgeAI Email Assistant

BridgeAI is a personal email assistant that each person runs on their own computer. It connects to that person's Gmail and Google Tasks. BridgeAI does not keep an organization-wide employee directory or shared email database.

## How it works

```text
Local browser UI → FastAPI → conditional LangGraph → Gmail (read-only)
                                         ├── Gemini for requested analysis
                                         └── deterministic rules → personal Google Tasks
```

The app binds to `127.0.0.1`; it is for one local user and must not be exposed publicly. Gmail access is read-only. Task creation happens only when requested and approved by the deterministic priority/action rules. Tasks are created in a dedicated `BridgeAI` task list. Calendar events are not created. Chat messages are not persisted; the process keeps only the current email ID per thread in memory for follow-up questions.

## Install and run

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Each person supplies their own Gemini API key in the ignored `.env` file. Never put API keys or OAuth tokens in chat or commit them. To use the real Google integrations, confirm these `.env` settings:

```dotenv
PROVIDER_MODE=gmail
TASK_PROVIDER_MODE=google_tasks
OAUTH_CREDENTIALS_PATH=credentials/credentials.json
OAUTH_TOKEN_PATH=token.json
```

Each person creates and owns a Google Cloud project, enables Gmail API and Google Tasks API, configures their OAuth audience and creates a Desktop app OAuth client. Place that person's downloaded OAuth client JSON at the ignored `credentials/credentials.json`. The first Gmail or Tasks request opens Google consent for that person's account and saves its authorization in the ignored local `token.json`. Follow [SETUP.md](SETUP.md) for the personal-account setup and current OAuth testing limits. Run:

```powershell
python run.py
```

Open `http://127.0.0.1:<APP_PORT>` (default `8000`). The first email/task request opens the local browser OAuth flow for Gmail read-only and Google Tasks permissions. Each person configures the OAuth audience in their own Cloud project for their account type and saves the resulting token locally. See [SETUP.md](SETUP.md) for details and Google's current testing and verification limits.

## Distribute to colleagues

For a source handoff, use `dist/bridgeai-project-source-0.1.4.zip`. It contains the project and setup guide but excludes `.env`, OAuth client credentials, `token.json`, virtual environments, and build caches. The ZIP is a source bundle; it does not contain a wheel. Follow [SETUP.md](SETUP.md) to configure Gemini, Google Cloud APIs, OAuth, and the local app.

A wheel is a separate optional package artifact. It can be built with `python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .`; it is not included in the source ZIP or published to PyPI.

## Use

- Refresh recent email, or chat with “Show the last five emails”.
- Summarize an email by choosing its button or asking “Summarize email `<ID>`”.
- To create tasks, explicitly ask to analyze an email and create eligible tasks, or use the email's **Analyze & create eligible tasks** button. The deterministic rules require action and an eligible priority. Low priority or no-action analyses never create tasks.
- Google Tasks has no priority field; BridgeAI records the analyzed priority in task notes.
- Calendar is not used. Google Tasks due dates are not currently extracted from email.

## Verification

```powershell
python -m pytest -q
python -m pip check
```

Unit/integration adapter tests use mocked Google/Gemini behavior. Live Gmail and Google Tasks verification requires the local OAuth browser flow. `/health` only confirms the app process is running.

## Limits

- This app has no API login or tenant controls; keep it bound to loopback.
- Each installation's OAuth audience and Google verification status determine which accounts can authorize it. This guide assumes the buyer configures and uses their own project for personal use.
- An OAuth token file grants the configured access to the signed-in person's account; keep it private.
- No tasks are assigned to other people; the Google Tasks integration is for the local user's own tasks.
