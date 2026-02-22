# Quickstart

## Requirements

- A **Debian** or **Ubuntu** server (VPS or bare metal) with at least 4 GB RAM
- For production: a domain name with a wildcard DNS record (`*.yourdomain.com`) pointing to your server

That's all. Docker and all dependencies are installed automatically.

## Install

```bash
git clone https://github.com/sylvinus/masuite && cd masuite && ./masuite setup
```

Single command, zero dependencies. On a fresh server, the CLI will detect that Docker is missing, install it, then launch the interactive setup wizard.

The wizard will ask you to:
1. Choose a mode (local or production)
2. Enter your domain and email (production only)
3. Select which apps to enable
4. Configure optional services (LLM for Conversations, SMTP for Messages)

Then start everything:

```bash
./masuite start
```

## Local mode

For testing on your machine:

```bash
./masuite setup --mode local --apps docs,meet,drive
./masuite start
```

Open `http://localhost:9120` for the homepage, or go directly to any app:
- Docs: `http://localhost:9121`
- Meet: `http://localhost:9122`
- Drive: `http://localhost:9123`
- Messages: `http://localhost:9124`
- Projects: `http://localhost:9125`
- Conversations: `http://localhost:9126`
- Calendars: `http://localhost:9127`

Keycloak admin: `http://localhost:9200` (credentials shown after setup).

## Creating users

```bash
./masuite user create alice@example.com
```

The password is generated and printed. Users can also be managed via the Keycloak admin UI.

## Stopping

```bash
./masuite stop
```
