# MaSuite

Self-host [LaSuite](https://lasuite.numerique.gouv.fr/) apps on your own server with a single command.

**Docs** (Google Docs) · **Meet** (Google Meet) · **Drive** (Google Drive) · **Messages** (Gmail) · **Projects** (Trello) · **Conversations** (ChatGPT) · **Calendars** (Google Calendar)

100% open source. 100% under your control.

WARNING: This is still ALPHA software. ARM64 doesn't work well yet. Help wanted!

## Install

```bash
git clone https://github.com/sylvinus/masuite && cd masuite && ./masuite setup
```

That's it. No dependencies to install — the CLI handles everything, including Docker.

Just bring a fresh Debian or Ubuntu server and a domain name. The setup wizard takes care of the rest: installing Docker, choosing your apps, generating config, and starting services.

## Local testing

```bash
./masuite setup --mode local --apps docs,meet,drive
./masuite start
```

Open http://localhost:9120 for the homepage.

## Commands

```bash
./masuite setup              # Interactive setup wizard
./masuite start              # Start all services
./masuite stop               # Stop all services
./masuite status             # Show running containers
./masuite logs [service]     # Tail logs
./masuite update             # Pull latest images + migrate
./masuite backup             # Backup databases
./masuite user create EMAIL  # Create a user
./masuite user list          # List users
```

## Architecture

- Single `docker-compose.yml` with all apps and infrastructure
- **Caddy** as reverse proxy (automatic HTTPS in production)
- **Keycloak** for unified SSO across all apps
- **PostgreSQL**, **Redis**, **RustFS** (S3) as shared infrastructure
- Docker Compose profiles to only start selected apps
- Pure Python CLI — zero external dependencies

See [docs/architecture.md](docs/architecture.md) for details.

## Documentation

- [Quickstart](docs/quickstart.md)
- [Architecture](docs/architecture.md)
- [CLI Reference](docs/cli.md)
- [Configuration](docs/configuration.md)
- [Apps](docs/apps.md)
- [Backup & Restore](docs/backup-and-restore.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Adding a New App](docs/new_app.md)

## Requirements

- A fresh **Debian** or **Ubuntu** server (VPS or bare metal)
- A domain name with `*.yourdomain.com` pointing to your server (production mode)
- 4 GB RAM minimum (depends on which apps you enable)

Docker is installed automatically if missing. Python 3 is pre-installed on all Debian/Ubuntu systems.

## Website

[www.masuite.fr](https://www.masuite.fr)

## License

MIT
