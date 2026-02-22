import {
  FileText,
  Video,
  HardDrive,
  Mail,
  Kanban,
  MessageSquare,
  CalendarDays,
} from "lucide-react";

import appsData from "../data/apps.json";
import vpsProviders from "../data/vps-providers.json";
import infraData from "../data/infra.json";

// ── UI-specific icon/color mapping ──────────────────────────────
const APP_UI: Record<string, { icon: typeof FileText; color: string }> = {
  docs: { icon: FileText, color: "bg-blue-50 text-blue-600" },
  meet: { icon: Video, color: "bg-violet-50 text-violet-600" },
  drive: { icon: HardDrive, color: "bg-amber-50 text-amber-600" },
  messages: { icon: Mail, color: "bg-emerald-50 text-emerald-600" },
  projects: { icon: Kanban, color: "bg-rose-50 text-rose-600" },
  conversations: { icon: MessageSquare, color: "bg-cyan-50 text-cyan-600" },
  calendars: { icon: CalendarDays, color: "bg-orange-50 text-orange-600" },
};

// ── LaSuite apps (JSON data + UI fields) ────────────────────────
export const APPS = appsData.map((app) => ({
  ...app,
  icon: APP_UI[app.id].icon,
  color: APP_UI[app.id].color,
}));

export const DEFAULT_APPS = new Set(
  appsData.filter((a) => a.default_enabled).map((a) => a.id)
);

// ── Base infrastructure (PostgreSQL, Keycloak, Redis, Caddy, RustFS) ──
export const BASE_RAM = infraData.base_ram;    // MB
export const BASE_VCPU = infraData.base_vcpu;
export const BASE_DISK = infraData.base_disk;  // MB

// ── VPS providers ─────────────────────────────────────────────
export const VPS_PROVIDERS = vpsProviders;

// ── Helpers ───────────────────────────────────────────────────
export function formatMB(mb: number) {
  return mb >= 1024 ? `${(mb / 1024).toFixed(1).replace(/\.0$/, "")}\u00a0GB` : `${mb}\u00a0MB`;
}
