# Apps

MaSuite bundles 7 apps from LaSuite. Each is optional and can be enabled independently.

## Docs

Collaborative document editor (like Google Docs).

- **Upstream**: [suitenumerique/impress](https://github.com/suitenumerique/impress)
- **Stack**: Django backend + Next.js frontend + Y.js collaboration server
- **Containers**: `docs-backend`, `docs-frontend`, `docs-celery`, `docs-yprovider`
- **Resources**: ~512 MB RAM, 0.5 vCPU, 1 GB disk
- **Port**: 9121

## Meet

Video conferencing (like Google Meet).

- **Upstream**: [suitenumerique/meet](https://github.com/suitenumerique/meet)
- **Stack**: Django backend + React/Vite frontend + LiveKit
- **Containers**: `meet-backend`, `meet-frontend`, `meet-celery`, `livekit`
- **Resources**: ~1 GB RAM, 1 vCPU, 1 GB disk
- **Port**: 9122
- **Notes**: LiveKit needs ports 7880/7881/7882 exposed. In prod mode, it requires a `livekit.` subdomain.

## Drive

File storage and editing (like Google Drive).

- **Upstream**: [suitenumerique/drive](https://github.com/suitenumerique/drive)
- **Stack**: Django backend + Next.js frontend + Collabora Online
- **Containers**: `drive-backend`, `drive-frontend`, `drive-celery`, `collabora`
- **Resources**: ~1 GB RAM, 1 vCPU, 2 GB disk
- **Port**: 9123
- **Notes**: Collabora handles document editing via WOPI protocol. `amd64` only.

## Messages

Collaborative email (like Gmail).

- **Upstream**: [suitenumerique/lasuite-messages](https://github.com/suitenumerique/lasuite-messages)
- **Stack**: Django backend + Next.js frontend + SMTP (in/out) + OpenSearch + rspamd
- **Containers**: `messages-backend`, `messages-frontend`, `messages-celery`, `messages-mta-in`, `messages-mta-out`, `messages-socks-proxy`, `opensearch`, `rspamd`
- **Resources**: ~1.5 GB RAM, 0.5 vCPU, 2 GB disk
- **Port**: 9124
- **Notes**: Needs an SMTP relay if your VPS blocks port 25. Images are on GHCR (`ghcr.io/suitenumerique/messages-*`), `main` tag only, `amd64` only.

## Projects

Kanban project management (like Trello).

- **Upstream**: [suitenumerique/lasuite-projects](https://github.com/suitenumerique/lasuite-projects) (Planka fork)
- **Stack**: Sails.js / Node.js (single container)
- **Containers**: `projects`
- **Resources**: ~256 MB RAM, 0.25 vCPU, 1 GB disk
- **Port**: 9125
- **Notes**: Not Django. OIDC config uses Planka-style env vars, not Django-style. Set `OIDC_FULLNAME_ATTRIBUTES=given_name,family_name` for standard Keycloak (Planka defaults to France Connect attributes). `amd64` only.

## Conversations

AI chatbot (like ChatGPT).

- **Upstream**: [suitenumerique/lasuite-conversations](https://github.com/suitenumerique/lasuite-conversations)
- **Stack**: Django backend (ASGI/uvicorn) + Next.js frontend
- **Containers**: `conversations-backend`, `conversations-frontend`
- **Resources**: ~512 MB RAM, 0.5 vCPU, 1 GB disk
- **Port**: 9126
- **Notes**: Requires an OpenAI-compatible LLM API endpoint. `amd64` only.

## Calendars

Shared calendar with CalDAV support (like Google Calendar).

- **Upstream**: [suitenumerique/calendars](https://github.com/suitenumerique/calendars)
- **Stack**: Django backend + Next.js frontend + SabreDAV (CalDAV server)
- **Containers**: `calendars-backend`, `calendars-frontend`, `calendars-celery`, `calendars-caldav`
- **Resources**: ~512 MB RAM, 0.5 vCPU, 1 GB disk
- **Port**: 9127
- **Notes**: No S3 storage needed (uses local FileSystemStorage). The CalDAV server (SabreDAV, PHP/Apache) provides CalDAV protocol support and connects to the same PostgreSQL database. Docker images not yet published — this app is pre-release.
