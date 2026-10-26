# BridgeAI Email Agent setup

Choose the instructions for your operating system. Keep the extracted project folder on your computer; do not run the application from inside the ZIP file.

## Windows

## 1. Install Python and extract the project

Install Python 3.12 or newer. During Python installation, enable **Add Python to PATH**. Extract the project ZIP to a folder, for example `C:\BridgeAI`. The ZIP includes the built interface, so Node.js is not needed to run the app; install Node.js LTS only if you plan to change and rebuild the interface.

## 2. Open PowerShell and install the dependencies

Open PowerShell in the extracted `bridgeai-email-agent` folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you edit the React interface, rebuild it from the `frontend` folder with `npm.cmd ci` and `npm.cmd run build` before starting BridgeAI.

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
4. Enable **Gmail API** and **Google Tasks API** for that project. Enable **Google Calendar API** only if you want meeting features.

## 5. Configure OAuth for Gmail, Google Tasks, and Google Calendar

1. In Google Cloud Console, open **Google Auth Platform** (or **APIs & Services → OAuth consent screen**).
2. Complete the app name, support email, and developer contact details under **Branding**.
3. Under **Audience**, choose **External** to authorize a personal Google account. If the app is in **Testing**, add the Google account you will use under **Test users**.
4. Under **Data Access**, add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/tasks`
   - Optional: `https://www.googleapis.com/auth/calendar.events.readonly`
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
OAUTH_CREDENTIALS_PATH=credentials/credentials.json
OAUTH_TOKEN_PATH=token.json
CALENDAR_ENABLED=false
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

Open `http://127.0.0.1:8000` in your browser. The first request for email or task data opens Google authorization. Sign in to the Google account configured in your OAuth project and allow Gmail read-only and Google Tasks access. If you enabled Calendar, allow its event read-only scope as well. The authorization is saved locally in `token.json`.

Use the chat filters or ask for recent email, tasks, or upcoming meetings in your own words. You can also search by sender or topic, for example “Is there any email from HOPR?” Open an email card to read the full message; choose **Review email** for a summary and action assessment, or **Create eligible task** to evaluate whether a task should be created. You may give an eligible task a custom title in chat.

## macOS

Follow these steps on a Mac. The Google AI Studio and Google Cloud steps are the same as on Windows; the commands below use macOS Terminal.

### 1. Install Python and extract the project

Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/macos/) or with a package manager such as Homebrew. Extract the project ZIP in Finder, then open Terminal and change to the extracted `bridgeai-email-agent` folder. The ZIP includes the built interface, so Node.js is needed only if you plan to change and rebuild the interface. For example:

```bash
cd ~/Downloads/bridgeai-email-agent
```

Use the actual folder path if you extracted it somewhere else.

### 2. Create the virtual environment and install dependencies

Check that Python 3.12 or newer is available, then run:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you edit the React interface, install Node.js LTS and rebuild it from the `frontend` folder with `npm ci` and `npm run build` before starting BridgeAI.

Keep using this Terminal window with `(.venv)` active when running BridgeAI.

### 3. Create a Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com/).
2. Sign in with the Google account you want to use for Gemini.
3. Create or select a Google project and create an API key.
4. Keep the key private. Do not paste it into chat or commit it to Git.

Gemini API usage is subject to the quota and billing settings for the project associated with the key.

### 4. Create a Google Cloud project and enable APIs

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Open **APIs & Services → Library**.
4. Enable **Gmail API** and **Google Tasks API** for that project. Enable **Google Calendar API** only if you want meeting features.

### 5. Configure OAuth for Gmail, Google Tasks, and Google Calendar

1. In Google Cloud Console, open **Google Auth Platform** (or **APIs & Services → OAuth consent screen**).
2. Complete the app name, support email, and developer contact details under **Branding**.
3. Under **Audience**, choose **External** to authorize a personal Google account. If the app is in **Testing**, add the Google account you will use under **Test users**.
4. Under **Data Access**, add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/tasks`
   - Optional: `https://www.googleapis.com/auth/calendar.events.readonly`
5. Open **Clients**, choose **Create client**, select **Desktop app**, and create the client.
6. Download the OAuth client JSON file.

While the OAuth app is in **Testing**, Google authorization for these scopes expires after 7 days. You will need to authorize again when it expires. For ongoing use, review the publishing status and requirements in Google's [OAuth publishing guidance](https://support.google.com/cloud/answer/15549945?hl=en).

### 6. Add your local configuration

In Terminal, from the project folder, create `.env`:

```bash
cp .env.example .env
```

Open `.env` in a text editor and set `GEMINI_API_KEY` to the key created in Step 3. Keep these integration settings:

```dotenv
OAUTH_CREDENTIALS_PATH=credentials/credentials.json
OAUTH_TOKEN_PATH=token.json
CALENDAR_ENABLED=false
```

Save the file. Do not share `.env` or add it to Git.

### 7. Add the OAuth client file

In Terminal, create a `credentials` folder:

```bash
mkdir -p credentials
```

Move the downloaded OAuth client JSON file into that folder and name it `credentials.json`. The final path must be `credentials/credentials.json`. Keep this file private. BridgeAI creates `token.json` after you authorize Google; keep that file private too.

### 8. Start BridgeAI and authorize Google

With `(.venv)` active, start the app:

```bash
python run.py
```

Open `http://127.0.0.1:8000` in your browser. The first request for email or task data opens Google authorization. Sign in to the Google account configured in your OAuth project and allow Gmail read-only and Google Tasks access. If you enabled Calendar, allow its event read-only scope as well. The authorization is saved locally in `token.json`.

Use the chat filters or type a request to list emails, view tasks, or show upcoming meetings. Open an email card to read the full message; choose **Review email** for a summary and action assessment, or **Create eligible task** to evaluate whether a task should be created. You may give an eligible task a custom title in chat.

## Chat filters

- **Unread important** reviews up to 20 recent unread messages with Gemini and shows only those rated High or Critical, including their summaries. This is an AI urgency estimate and does not depend on Gmail's IMPORTANT label.
- **Escalated emails** and **Customer emails** are classified by Gemini from short excerpts of up to 20 recent unread messages; Gmail labels are not required. Escalated means an unresolved issue appears to be raised for higher-level help. Customer is inferred from the message and sender context because the app has no customer directory, so either filter can make mistakes. The general attention request reviews up to 10 recent unread messages. Chat requests and these excerpts are sent to Gemini for AI processing.
- **Tasks assigned to me** lists tasks in the connected Google Tasks account. Tasks are personal to that account; BridgeAI does not assign tasks to other people.
- **My meetings** lists events on the primary Google Calendar for the next 14 days. Calendar access is read-only.
- Custom filters save a name and instruction in this browser's local storage. They are shortcuts for Email Agent prompts, not Gmail labels or a separate server-side filter database.

## Data and access notes

- The terminal and rotating log file record workflow steps, tool/provider operations, outcomes, safe error types, and durations. They do not record chat prompts or email bodies. On Windows the default log is `%LOCALAPPDATA%\BridgeAI Email Agent\logs\bridgeai.log`; on macOS it is `~/Library/Logs/BridgeAI Email Agent/logs/bridgeai.log`; on Linux it is `$XDG_STATE_HOME/BridgeAI Email Agent/logs/bridgeai.log` (or `~/.local/state/...` when `XDG_STATE_HOME` is unset). Set `LOG_FILE_PATH` to use a different file.

- Gmail access is read-only. Tasks are saved to the Google Tasks account authorized above.
- BridgeAI sends email content to Gemini when you request a summary, analysis, or email question-answering.
- `.env`, `credentials\credentials.json`, and `token.json` contain private credentials or authorization data. Do not share or commit them.
- The local app is intended to be accessed from this computer at `127.0.0.1`; do not expose it directly to the internet.
- If authorization is revoked, expired, or reports an API/scope error, check the enabled APIs and OAuth setup, then remove the local `token.json` and authorize again.
