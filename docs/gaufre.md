# Gaufre v2: Runtime Configuration Status

The "Gaufre" (waffle menu) lets users navigate between apps. MaSuite generates a `gaufre-services.json` file listing all enabled apps and serves it via Caddy with CORS headers.

## Current Status

| App | Gaufre visible | Uses custom services | Mechanism |
|-----|---------------|---------------------|-----------|
| **Docs** | Yes | **Yes** | `THEME_CUSTOMIZATION_FILE_PATH` -> JSON with `waffle.apiUrl` + `waffle.widgetPath` |
| **Drive** | Yes | No | Cunningham theme tokens baked at build time |
| **Projects** | Yes | No | React bundle compiled with hardcoded URLs; Sails.js config API serves correct values but frontend ignores them |
| **Messages** | Unknown | No | `NEXT_PUBLIC_*` env vars are build-time only in Next.js |
| **Conversations** | Yes | No | All gaufre URLs hardcoded in component source |
| **Meet** | No | N/A | No gaufre integration |

## What MaSuite does

The setup wizard (`cli/setup_wizard.py`) generates:

1. **`config/homepage/gaufre-services.json`** — Services list in official Gaufre API format, served at `https://home.<domain>/gaufre-services.json` with `Access-Control-Allow-Origin: *`
2. **`config/docs-theme.json`** — Theme customization JSON for Docs backend with `waffle.apiUrl` and `waffle.widgetPath`
3. **`.env` variables** — `GAUFRE_SERVICES_URL` and `GAUFRE_SCRIPT_URL` used by compose files

## Upstream Fixes Needed

### Drive (`suitenumerique/drive`)

**Problem**: The `Gaufre.tsx` component reads `apiUrl` and `widgetPath` from Cunningham theme tokens, which are generated at build time from `cunningham.ts`. The three available themes (`default`, `dark`, `anct`) all have hardcoded URLs.

**Current code** (`src/frontend/apps/drive/src/features/ui/components/gaufre/Gaufre.tsx`):
```tsx
const widgetPath = removeQuotes(theme.components.gaufre.widgetPath);
const apiUrl = removeQuotes(theme.components.gaufre.apiUrl);
```

**Fix**: Read `apiUrl` and `widgetPath` from the backend config API (which already supports `THEME_CUSTOMIZATION_FILE_PATH`) instead of from Cunningham tokens. The backend already serves `theme_customization` via `/api/v1.0/config/`, identical to how Docs works.

```tsx
// Proposed fix
const { config } = useConfig();
const waffle = config?.theme_customization?.waffle;
const widgetPath = waffle?.widgetPath || removeQuotes(theme.components.gaufre.widgetPath);
const apiUrl = waffle?.apiUrl || removeQuotes(theme.components.gaufre.apiUrl);
```

This would allow runtime override via `THEME_CUSTOMIZATION_FILE_PATH` env var on `drive-backend`, falling back to the current build-time theme tokens. MaSuite already has the backend env var and JSON file ready — only the frontend component needs the change.

**Compose env vars ready**: `THEME_CUSTOMIZATION_FILE_PATH` on `drive-backend` (same mechanism as Docs)

---

### Projects (`suitenumerique/projects`)

**Problem**: The Sails.js backend correctly reads `LAGAUFRE_WIDGET_API_URL` and `LAGAUFRE_WIDGET_PATH` env vars and exposes them via `/api/config` (`lagaufreWidgetApiUrl`, `lagaufreWidgetPath`). However, the React frontend bundle (`main.*.js`) was compiled with `REACT_APP_LAGAUFRE_WIDGET_*` env vars at build time, and the `LaGaufreButton` component uses these compiled-in values instead of fetching from the config API.

**Evidence**: After setting `LAGAUFRE_WIDGET_API_URL`, the config API returns the correct custom URL, but network requests still go to `integration.lasuite.numerique.gouv.fr/api/v1/gaufre.js` (the build-time value).

**Fix**: The `LaGaufreButton` component should read widget URLs from the `/api/config` response (via Redux state) rather than from compile-time `process.env.REACT_APP_*` variables. The Sails.js backend already serves the correct values.

**Compose env vars ready**: `LAGAUFRE_WIDGET_API_URL` and `LAGAUFRE_WIDGET_PATH` on `projects` container

---

### Messages (`suitenumerique/messages`)

**Problem**: The frontend uses `NEXT_PUBLIC_LAGAUFRE_WIDGET_API_URL` and `NEXT_PUBLIC_LAGAUFRE_WIDGET_PATH`. In Next.js, `NEXT_PUBLIC_*` env vars are inlined at build time by webpack. Setting them as runtime env vars on the Docker container has no effect since the pre-built image already has the values (or undefined) baked into the JS bundle.

**Fix**: Either:
1. Use a runtime config mechanism (Next.js `publicRuntimeConfig`, a `/api/config` endpoint, or a startup script that patches the built JS), or
2. Follow the same pattern as Docs: have the Django backend serve gaufre config via an API endpoint, and have the frontend fetch it at runtime.

**Compose env vars ready**: `NEXT_PUBLIC_LAGAUFRE_WIDGET_API_URL` and `NEXT_PUBLIC_LAGAUFRE_WIDGET_PATH` on `messages-frontend` (will work if the image is rebuilt with them, or if a runtime config mechanism is added)

---

### Conversations (`suitenumerique/conversations`)

**Problem**: All gaufre URLs are hardcoded directly in the React component source (`src/frontend/apps/conversations/src/features/header/components/LaGaufre.tsx`).

**Fix**: Read gaufre config from the backend config API (like Docs does via `THEME_CUSTOMIZATION_FILE_PATH`), or accept env vars for the widget URL and services URL.

**Compose env vars**: Not yet added (no mechanism to configure)

---

### Meet (`suitenumerique/meet`)

**Problem**: No gaufre integration exists at all. Meet is a Vite/React app and does not include any gaufre component or the `@gouvfr-lasuite/ui-kit`.

**Fix**: Add a `LaGaufreV2` component (from `@gouvfr-lasuite/ui-kit`) to the Meet header, reading config from the backend API or env vars.

**Compose env vars**: Not yet added (no mechanism to configure)

---

## Summary

**Docs is the reference implementation.** Its pattern of `THEME_CUSTOMIZATION_FILE_PATH` -> backend serves JSON via config API -> frontend reads `theme_customization.waffle` at runtime works perfectly for self-hosted deployments. If all apps adopted this pattern, MaSuite could provide a fully customized Gaufre everywhere with zero upstream image changes needed.

The minimal upstream changes per app:
- **Drive**: 5-line frontend fix (read from config API, fall back to theme tokens)
- **Projects**: Frontend should prefer `/api/config` values over compiled-in env vars
- **Messages**: Add runtime config mechanism for gaufre URLs
- **Conversations**: Add any config mechanism (currently fully hardcoded)
- **Meet**: Add gaufre integration from scratch
