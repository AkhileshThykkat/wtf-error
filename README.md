# WTF Error

A small incident desk for collecting redacted logs, investigating failures with Workers AI, and keeping findings tied to the evidence that supports them.

## Run locally

Install the locked JavaScript tools with `npm ci`, then apply the D1 schema to the local database and start Wrangler:

```sh
npx wrangler d1 migrations apply wtf-prod-db --local
npx wrangler dev
```

Open the local URL Wrangler prints. The page, API, and D1 binding run through the same Worker. Workers AI needs a Cloudflare account with the AI binding enabled.

For a deployed Worker, apply migrations to the remote database before deploying:

```sh
npx wrangler d1 migrations apply wtf-prod-db --remote
npx wrangler deploy
```

## How it works

- Create an incident with its symptoms and environment.
- Paste logs or command output as evidence. The server masks common credential patterns, stores the redacted text, and gives each line a stable ID.
- Ask a follow-up or investigate. The service sends the incident, redacted evidence, previous messages, and findings to Llama 3.3 on Workers AI.
- The service validates cited evidence IDs and saves the assistant response and findings in D1.

Evidence redaction covers common private-key blocks, bearer tokens, and credential assignments. It cannot identify every secret format, so review pasted content before sharing it. Put the deployed Worker behind Cloudflare Access before using it with private incident data; the app does not implement user authentication.

## API

- `GET/POST /api/incidents` and `GET /api/incidents/{id}`
- `GET/POST /api/incidents/{id}/evidence`
- `GET/POST /api/incidents/{id}/messages`
- `GET /api/incidents/{id}/findings`
- `POST /api/incidents/{id}/investigate`
- `GET /health`
