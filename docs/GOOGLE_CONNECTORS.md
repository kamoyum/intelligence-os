# Google Connectors

## Why separate OAuth is required

Connections granted to ChatGPT cannot be exported into this standalone local application. Intelligence OS must obtain its own OAuth authorization from the user.

## Modes

### `off`
No Google API access.

### `safe`
Requests:

- `calendar.events.readonly`
- `drive.file`

This deliberately avoids Gmail. `drive.file` is narrow and only gives access to files available to the app through the relevant Google access model; it is not a silent whole-Drive index.

### `personal_full`
Requests:

- `calendar.events.readonly`
- `drive.readonly`
- `gmail.readonly`

This is for private development/testing. Gmail read access and broad Drive read access are restricted Google scopes. Public distribution can require verification; storing or transmitting restricted-scope data can trigger additional security requirements.

## Setup

1. Create a Google Cloud project.
2. Enable Calendar, Drive, and Gmail APIs as required by your chosen mode.
3. Configure an OAuth consent screen.
4. Create a Web application OAuth client.
5. Add redirect URI:

```text
http://127.0.0.1:8765/oauth/google/callback
```

6. Download the client secrets file as `backend/google_client_secret.json`.
7. Set:

```bash
export INTELLIGENCE_GOOGLE_MODE=safe
```

or, only for private testing:

```bash
export INTELLIGENCE_GOOGLE_MODE=personal_full
```

8. Start Core and choose **Google接続** in Console.

## v0.2 synchronization behavior

Synchronization is manual. v0.2 can ingest:

- upcoming Calendar event metadata/descriptions
- Drive file metadata available under the granted scope
- recent Gmail headers/snippets/body text only in `personal_full`

Repeated connector records use source keys, so they update rather than endlessly duplicate.

## Distribution strategy

For a broadly distributed product, prefer narrower and contextual access rather than requesting every user's entire mailbox and Drive. Examples include per-file Drive selection, user-triggered capture, Workspace add-on surfaces, or a connector architecture where broad scopes are an explicitly premium/enterprise-compliance path.
