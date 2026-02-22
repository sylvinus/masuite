# MaSuite Website

Marketing website for [MaSuite](https://github.com/sylvinus/masuite), a self-hosting solution for [LaSuite](https://lasuite.numerique.gouv.fr/) apps.

Live at **[www.masuite.fr](https://www.masuite.fr)**

## Stack

- **Next.js 15** with static export (`output: "export"`)
- **React 19** + **TypeScript**
- **Tailwind CSS 3**
- Client-side i18n (FR, EN, DE, ES, IT, NL)
- Deployed to **GitHub Pages** via GitHub Actions

## Development

Requires Docker only. No host Node.js needed.

```bash
docker compose up
```

Open [http://localhost:3000](http://localhost:3000).

Source files are hot-reloaded via volume mounts.

## Build

```bash
docker compose run --rm build
```

Static output goes to `out/`.

## Deployment

Pushes to `main` trigger the GitHub Actions workflow (`.github/workflows/deploy.yml`) which builds and deploys to GitHub Pages.

### Custom domain setup

DNS records for `masuite.fr`:

```
CNAME  www   sylvinus.github.io.

A      @     185.199.108.153
A      @     185.199.109.153
A      @     185.199.110.153
A      @     185.199.111.153
```

`www.masuite.fr` is the primary domain. The bare domain redirects to `www` via GitHub Pages.

## Project structure

```
src/
  app/
    layout.tsx        # Root layout, metadata
    page.tsx          # Single-page app entry
    globals.css       # Tailwind + custom styles
  components/
    Header.tsx        # Fixed nav bar
    Hero.tsx          # Hero section
    Wizard.tsx        # 3-step install wizard
    FAQ.tsx           # Accordion FAQ
    Footer.tsx        # Footer with credits
    Apps.tsx          # App data (icons, resources, GitHub links)
  i18n/
    translations.ts   # All translations (6 languages)
    context.tsx        # I18n React context + provider
public/
  CNAME              # GitHub Pages custom domain
  install.sh         # Installer script served at masuite.fr/install.sh
.github/
  workflows/
    deploy.yml       # GitHub Pages deployment
```
