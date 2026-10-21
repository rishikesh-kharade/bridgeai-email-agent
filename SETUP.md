# BridgeAI setup (Windows)

Follow these steps on the computer where you want to run BridgeAI. Keep the project folder on your computer; do not run the application from inside the ZIP file.

## 1. Install Python and extract the project

Install Python 3.12 or newer. During installation, enable **Add Python to PATH**. Extract the project ZIP to a folder, for example `C:\BridgeAI`.

## 2. Open PowerShell and install the dependencies

Open PowerShell in the extracted `bridgeai-email-agent` folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in that PowerShell window, then activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Create a Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com/).
2. Sign in with the Google account you want to use for Gemini.
3. Create or select a Google project and create an API key.
4. Keep the key private. Do not paste it into chat or commit it to Git.

Gemini API usage is subject to the quota and billing settings for the project associated with the key.

## 4. Create a Google Cloud project and enable APIs

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Open **APIs & Services → Library**.
4. Enable **Gmail API** and **Google Tasks API** for that project.

## 5. Configure OAuth for Gmail and Google Tasks

1. In Google Cloud Console, open **Google Auth Platform** (or **APIs & Services → OAuth consent screen**).
2. Complete the app name, support email, and developer contact details under **Branding**.
3. Under **Audience**, choose **External** to authorize a personal Google account. If the app is in **Testing**, add the Google account you will use under **Test users**.
4. Under **Data Access**, add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/tasks`
5. Open **Clients**, choose **Create client**, select **Desktop app**, and create the client.
6. Download the OAuth client JSON file.

While the OAuth app is in **Testing**, Google authorization for these scopes expires after 7 days. You will need to authorize again when it expires. For ongoing use, review the publishing status and requirements in Google's [OAuth publishing guidance](https://support.google.com/cloud/answer/15549945?hl=en).

## 6. Add your local configuration

From the project folder, create your local `.env` file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in a text editor and set `GEMINI_API_KEY` to the key created in Step 3. Keep these integration settings:

```dotenv
PROVIDER_MODE=gmail
TASK_PROVIDER_MODE=google_tasks
OAUTH_CREDENTIALS_PATH=credentials/credentials.json
OAUTH_TOKEN_PATH=token.json
```

Save the file. Do not share `.env` or add it to Git.

## 7. Add the OAuth client file

In the project folder, create a `credentials` folder and put the downloaded JSON file there, named `credentials.json`:

```powershell
New-Item -ItemType Directory -Force credentials
```

The final path must be `credentials\credentials.json`. Keep this file private. BridgeAI creates `token.json` after you authorize Google; keep that file private too.

## 8. Start BridgeAI and authorize Google

Start the app from the activated PowerShell environment:

```powershell
python run.py
```

Open `http://127.0.0.1:8000` in your browser. When you first request email or task data, a Google authorization page opens. Sign in to the Google account you added as a test user, review the requested Gmail read-only and Google Tasks access, and allow it. The authorization is saved locally in `token.json`.

Use **Refresh** to load recent email and tasks. You can also ask BridgeAI to list recent emails, summarize a selected email, or analyze an email and create an eligible task.

## Data and access notes

- Gmail access is read-only. Tasks are saved to the Google Tasks account authorized above.
- BridgeAI sends email content to Gemini when you request a summary, analysis, or email question-answering.
- `.env`, `credentials\credentials.json`, and `token.json` contain private credentials or authorization data. Do not share or commit them.
- The local app is intended to be accessed from this computer at `127.0.0.1`; do not expose it directly to the internet.
- If authorization is revoked, expired, or reports an API/scope error, check the enabled APIs and OAuth setup, then remove the local `token.json` and authorize again.
