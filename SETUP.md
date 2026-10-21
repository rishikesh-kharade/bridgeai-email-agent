# BridgeAI setup (7 steps)

Use these steps for a single person's Windows computer. Each person connects their own Google account and keeps their own local configuration.

1. **Install Python and unpack the project.** Install Python 3.12 or newer, then extract the BridgeAI ZIP or copy the source project into a local folder. Do not run it from inside the ZIP.

2. **Open PowerShell in the project folder and create a virtual environment.**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies.** The shared ZIP is a source bundle and does not contain a Python wheel. Run this from the extracted project folder:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. **Create local settings.** Run `copy .env.example .env`. In `.env`, set `PROVIDER_MODE=gmail`, `TASK_PROVIDER_MODE=google_tasks`, and the person's own `GEMINI_API_KEY`. Keep `.env` private; never send it with the project.

5. **Configure Google access.** Obtain the approved OAuth desktop client file for the BridgeAI Google Cloud project through your organization's approved channel and save it as `credentials\credentials.json`. Ensure Gmail API and Google Tasks API are enabled. This OAuth app is currently **Internal**, so the signing-in account must be permitted by its Workspace organization. Never distribute `token.json` or commit the credentials file.

6. **Start BridgeAI and open the local site.** From the extracted source project folder, run `python run.py`. Open `http://127.0.0.1:8000`. If port 8000 is busy, set `APP_PORT=8001` in `.env` and open `http://127.0.0.1:8001`. Leave the terminal open while using the app.

7. **Authorize and check it.** Complete Google's browser consent using the intended Workspace account. Confirm recent emails load, then try a summary or ask `Show my tasks`. Email content is sent to Gemini when requesting a summary, question, or analysis. Task creation is a separate explicit action and only creates an email follow-up if the deterministic rules approve it.

## Important

- Keep `.env`, `credentials\credentials.json`, and `token.json` private and out of shared archives/source control. Each person supplies their own Gemini API key and gets the OAuth client file through an approved channel.
- Gmail access is read-only. Tasks are stored in the user's Google Tasks list named **BridgeAI**.
- This is a local, single-user app. It has no API login or tenant authorization and must not be exposed publicly.
- For source-project verification, run `python -m pytest -q` and `python -m pip check`.
