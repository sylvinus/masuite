// Generates website/public/data/apps.json and infra.json from services/*/metadata.json.
// Run automatically via `npm run prebuild` or manually with `node scripts/sync-apps.js`.
const fs = require("fs");
const path = require("path");

const servicesDir = path.resolve(__dirname, "../../services");
const outDir = path.resolve(__dirname, "../public/data");

fs.mkdirSync(outDir, { recursive: true });

const apps = [];

for (const entry of fs.readdirSync(servicesDir)) {
  const metaPath = path.join(servicesDir, entry, "metadata.json");
  if (!fs.existsSync(metaPath)) continue;

  const meta = JSON.parse(fs.readFileSync(metaPath, "utf-8"));

  // _base is infrastructure, not an app
  if (meta.is_infrastructure) {
    const infraFile = path.join(outDir, "infra.json");
    fs.writeFileSync(infraFile, JSON.stringify({
      base_ram: meta.ram,
      base_vcpu: meta.vcpu,
      base_disk: meta.disk,
    }, null, 2) + "\n");
    console.log(`Generated ${path.relative(process.cwd(), infraFile)}`);
    continue;
  }

  apps.push({
    id: entry,
    ram: meta.ram,
    vcpu: meta.vcpu,
    disk: meta.disk,
    github: meta.github,
    default_enabled: meta.default_enabled,
    port: meta.port,
  });
}

// Sort by port number (encodes display order: 9121=docs, 9122=meet, etc.)
apps.sort((a, b) => a.port - b.port);
apps.forEach((a) => delete a.port);

const appsFile = path.join(outDir, "apps.json");
fs.writeFileSync(appsFile, JSON.stringify(apps, null, 2) + "\n");
console.log(`Generated ${path.relative(process.cwd(), appsFile)} (${apps.length} apps)`);
