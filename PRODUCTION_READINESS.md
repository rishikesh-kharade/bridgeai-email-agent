# Local product release checklist

## Product model

BridgeAI Email Agent is installed and run on one person's computer. Each customer supplies their own Gemini API key and Google OAuth desktop client. OAuth tokens stay on that computer. The app binds to loopback and is not a hosted multi-user service. Gmail, Google Tasks, and optional Google Calendar are the only implemented integrations.

The application uses LangGraph to coordinate Gemini's bounded tool calls. Python validates tool arguments and applies deterministic safeguards before task creation. Natural language is interpreted by Gemini; routing and side-effect checks remain explicit so that the agent cannot bypass authorization or task rules.

## Before a broad customer release

| Priority | Required work | Why |
|---|---|---|
| P0 | Complete live tests on clean Windows and macOS accounts: OAuth consent, Gmail read, task create/list, optional Calendar read, token refresh/revocation, Gemini quota and outage behavior. | Current automated tests mock Google and Gemini; they do not verify a fresh customer setup. |
| P0 | Store the Gemini key and OAuth refresh token in the operating system credential store for the packaged release. | Current development setup stores them in local `.env` and `token.json` files. |
| P0 | Review local web security and keep all listeners loopback-only. Test that another computer cannot access the app. | This single-user app has no sign-in boundary. |
| P0 | Publish a clear privacy/data-flow notice and account disconnect/token removal instructions. | Email excerpts are sent to Gemini when the user requests AI help. |
| P1 | Pin Python and frontend dependencies and run automated build, test, and dependency checks. | Loose versions can change behavior during later installs. |
| P1 | Produce signed Windows and macOS installers that include the built React UI; test installation, upgrade, uninstall, and clean-machine setup. | The source ZIP and wheel are developer-oriented handoff artifacts. |
| P1 | Add reliable application update and recovery guidance, including logs that avoid message content and secrets. | Customers need a safe way to diagnose and update the local app. |
| P2 | Add another mailbox integration only if it becomes a product requirement. | This build supports Gmail only; Outlook, Yahoo, and other mail services are not currently supported. |

## Release acceptance

- A customer can install from a clean supported computer by following the setup guide.
- The UI and backend start locally, and no remote listener is exposed.
- Each customer's Gemini key, OAuth client, and token are independent and never bundled with the app.
- Real Gmail and Google Tasks flows are verified on an authorized account; Calendar is verified only if included in the release.
- Logs show workflow steps and safe errors without prompts, email bodies, keys, or tokens.
- Task writes require explicit user intent and deterministic approval; duplicates are safely controlled.
- Privacy, supported integrations, troubleshooting, and uninstall instructions match the shipped build.

Until the live-account and clean-installer checks above are complete, describe the build as a controlled pilot or release candidate, not as fully production-ready for general customers.
