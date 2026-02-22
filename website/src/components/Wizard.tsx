"use client";

import { useState } from "react";
import { useI18n } from "@/i18n/context";
import { APPS, DEFAULT_APPS, formatMB, BASE_RAM, BASE_VCPU, BASE_DISK, VPS_PROVIDERS } from "./Apps";
import {
  Check,
  Monitor,
  Server,
  ExternalLink,
  Copy,
  Globe,
  Terminal,
  Rocket,
  ChevronRight,
  ChevronLeft,
  Github,
  Users,
  Layers,
} from "lucide-react";

type Target = "local" | "vps";

export default function Wizard() {
  const { t } = useI18n();
  const [step, setStep] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(DEFAULT_APPS);
  const [target, setTarget] = useState<Target>("vps");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [cmdTab, setCmdTab] = useState<"curl" | "git">("curl");
  const [concurrentUsers, setConcurrentUsers] = useState(1);

  const selectedApps = APPS.filter((a) => selected.has(a.id));
  const appRam = selectedApps.reduce((s, a) => s + a.ram, 0);
  const appVcpu = selectedApps.reduce((s, a) => s + a.vcpu, 0);
  const appDisk = selectedApps.reduce((s, a) => s + a.disk, 0);

  const scaleFactor = 1 + (concurrentUsers - 1) * 9 / 99;

  const totalRam = Math.ceil((BASE_RAM + appRam) * scaleFactor / 1024);
  const totalVcpu = Math.ceil((BASE_VCPU + appVcpu) * scaleFactor * 2) / 2;
  const totalDisk = Math.ceil((BASE_DISK + appDisk) / 1024);

  const appsArg = [...selected].sort().join(",");

  const curlCmd =
    target === "vps"
      ? `curl -sSL masuite.fr/install.sh | bash -s -- --apps ${appsArg}`
      : `curl -sSL masuite.fr/install.sh | bash -s -- --apps ${appsArg} --mode local`;

  const gitCmd =
    target === "vps"
      ? `git clone https://github.com/sylvinus/masuite\ncd masuite\npython3 -m cli setup --apps ${appsArg}`
      : `git clone https://github.com/sylvinus/masuite\ncd masuite\npython3 -m cli setup --apps ${appsArg} --mode local`;

  function toggleApp(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  }

  function selectAll() {
    if (selected.size === APPS.length) setSelected(new Set());
    else setSelected(new Set(APPS.map((a) => a.id)));
  }

  function copyToClipboard(text: string, idx: number) {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  }

  const steps = [t("wizard.step1"), t("wizard.step2"), t("wizard.step3")];

  return (
    <section id="wizard" className="py-16 bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900">
            {t("wizard.title")}
          </h2>
          <p className="mt-4 text-lg text-slate-500">
            {t("wizard.subtitle")}
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {steps.map((label, i) => (
            <div key={i} className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (i <= step || selected.size > 0) setStep(i);
                }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  i === step
                    ? "bg-masuite-600 text-white"
                    : i < step
                    ? "bg-masuite-600/10 text-masuite-600 cursor-pointer"
                    : "bg-slate-200 text-slate-400"
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs">
                  {i < step ? <Check size={12} /> : i + 1}
                </span>
                <span className="hidden sm:inline">{label}</span>
              </button>
              {i < steps.length - 1 && (
                <div className="w-8 h-px bg-slate-300" />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
          {/* Step 0: App selection (merged from Apps section) */}
          {step === 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-slate-900">
                  {t("wizard.selectApps")}
                </h3>
                <button
                  onClick={selectAll}
                  className="text-sm text-masuite-600 hover:underline"
                >
                  {selected.size === APPS.length
                    ? t("wizard.deselectAll")
                    : t("wizard.selectAll")}
                </button>
              </div>
              <p className="text-sm text-slate-500 mb-6">
                {t("wizard.appsSubtitle")}{" "}
                <a
                  href="https://lasuite.numerique.gouv.fr/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-masuite-600 hover:underline"
                >
                  LaSuite
                </a>
                {t("wizard.appsSubtitlePost")}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {/* Base system card (always included) */}
                <div className="rounded-lg border-2 border-masuite-600 bg-masuite-600/5 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="p-1 rounded-md bg-slate-200 text-slate-500">
                      <Layers size={14} />
                    </div>
                    <span className="font-medium text-sm text-slate-700">{t("apps.base.name")}</span>
                  </div>
                  <div className="text-xs text-slate-500 leading-relaxed">{t("apps.base.desc")}</div>
                  <div className="mt-1.5 flex flex-wrap gap-x-2 text-xs text-slate-400">
                    <span>{formatMB(BASE_RAM)} RAM</span>
                    <span>{BASE_VCPU} vCPU</span>
                    <span>{formatMB(BASE_DISK)} {t("apps.disk")}</span>
                  </div>
                </div>

                {APPS.map((app) => {
                  const Icon = app.icon;
                  const isSelected = selected.has(app.id);
                  return (
                    <div
                      key={app.id}
                      className={`relative rounded-lg border-2 transition-all ${
                        isSelected
                          ? "border-masuite-600 bg-masuite-600/5"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <button
                        onClick={() => toggleApp(app.id)}
                        className="w-full p-3 text-left"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <div className={`p-1 rounded-md flex-shrink-0 ${app.color}`}>
                            <Icon size={14} />
                          </div>
                          <span className="font-medium text-sm text-slate-900 flex-1">
                              {t(`apps.${app.id}.name`)}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 leading-relaxed pr-6">
                          {t(`apps.${app.id}.desc`)}
                        </div>
                        <div className="mt-1.5 flex flex-wrap gap-x-2 text-xs text-slate-400">
                          <span>{formatMB(app.ram)} RAM</span>
                          <span>{app.vcpu} vCPU</span>
                          <span>{formatMB(app.disk)} {t("apps.disk")}</span>
                        </div>
                      </button>
                      <a
                        href={app.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="absolute top-2.5 right-2.5 p-1 rounded-md text-slate-300 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                        title="GitHub"
                      >
                        <Github size={12} />
                      </a>
                    </div>
                  );
                })}
              </div>

              {/* Resource summary + Concurrent users slider */}
              <div className="mt-6 p-4 bg-slate-50 rounded-xl">
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-700 mb-2">
                      {t("wizard.resources")}
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
                      <span>
                        RAM: <strong>{totalRam} GB</strong>
                      </span>
                      <span>
                        vCPU: <strong>{totalVcpu}</strong>
                      </span>
                      <span>
                        {t("apps.disk")}:{" "}
                        <strong>{totalDisk} GB</strong>{" "}
                        <span className="font-normal text-slate-400">+ {t("wizard.yourUsage")}</span>
                      </span>
                    </div>
                  </div>
                  <div className="sm:w-48 flex-shrink-0">
                    <label className="flex items-center gap-1.5 text-xs font-medium text-slate-500 mb-1.5">
                      <Users size={12} />
                      {t("wizard.concurrentUsers")}:{" "}
                      <span className="text-masuite-600 font-bold">
                        {concurrentUsers}
                      </span>
                    </label>
                    <input
                      type="range"
                      min={1}
                      max={100}
                      value={concurrentUsers}
                      onChange={(e) =>
                        setConcurrentUsers(Number(e.target.value))
                      }
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#000091]"
                    />
                    <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                      <span>1</span>
                      <span>100</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setStep(1)}
                  disabled={selected.size === 0}
                  className="flex items-center gap-2 px-5 py-2.5 bg-masuite-600 text-white rounded-lg hover:bg-masuite-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
                >
                  {t("wizard.next")}
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Step 1: Target selection */}
          {step === 1 && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-6">
                {t("wizard.target")}
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  onClick={() => setTarget("vps")}
                  className={`flex flex-col items-center gap-3 p-6 rounded-xl border-2 text-center transition-all ${
                    target === "vps"
                      ? "border-masuite-600 bg-masuite-600/5"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Server size={32} className="text-slate-600" />
                  <div>
                    <div className="font-semibold text-slate-900">
                      {t("wizard.vpsTitle")}
                    </div>
                    <div className="text-sm text-slate-500 mt-1">
                      {t("wizard.vpsDesc")}
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => setTarget("local")}
                  className={`flex flex-col items-center gap-3 p-6 rounded-xl border-2 text-center transition-all ${
                    target === "local"
                      ? "border-masuite-600 bg-masuite-600/5"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Monitor size={32} className="text-slate-600" />
                  <div>
                    <div className="font-semibold text-slate-900">
                      {t("wizard.localTitle")}
                    </div>
                    <div className="text-sm text-slate-500 mt-1">
                      {t("wizard.localDesc")}
                    </div>
                  </div>
                </button>
              </div>

              {/* Local requirements */}
              {target === "local" && (
                <div className="mt-6">
                  <p className="text-sm text-slate-500">
                    {t("wizard.localNote", {
                      ram: totalRam.toString(),
                      vcpu: totalVcpu.toString(),
                      disk: totalDisk.toString(),
                    })}
                  </p>
                </div>
              )}

              {/* VPS Recommendations */}
              {target === "vps" && (
                <div className="mt-6">
                  <p className="text-sm text-slate-500 mb-4">
                    {t("wizard.vpsNote", {
                      ram: totalRam.toString(),
                      vcpu: totalVcpu.toString(),
                      disk: totalDisk.toString(),
                    })}
                  </p>
                  <h4 className="text-sm font-semibold text-slate-700 mb-3">
                    {t("wizard.recommendedVPS")}
                  </h4>
                  <div className="space-y-3">
                    {VPS_PROVIDERS.map((provider) => {
                      const suitable = provider.tiers.filter(
                        (tier) =>
                          tier.ram >= totalRam &&
                          tier.vcpu >= Math.ceil(totalVcpu)
                      );
                      const recommended =
                        suitable[0] ||
                        provider.tiers[provider.tiers.length - 1];
                      return (
                        <a
                          key={provider.name}
                          href={provider.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:border-masuite-600/30 hover:shadow-sm transition-all"
                        >
                          <div>
                            <div className="font-medium text-slate-900">
                              {provider.name}{" "}
                              <span className="text-masuite-600">
                                {recommended.name}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5">
                              {recommended.ram} GB RAM &middot;{" "}
                              {recommended.vcpu} vCPU &middot;{" "}
                              {recommended.disk} GB {t("apps.disk")}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-700">
                              ~&euro;{recommended.price}
                              {t("wizard.perMonth")}
                            </span>
                            <ExternalLink
                              size={14}
                              className="text-slate-400"
                            />
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex justify-between mt-6">
                <button
                  onClick={() => setStep(0)}
                  className="flex items-center gap-2 px-5 py-2.5 text-slate-600 rounded-lg hover:bg-slate-100 transition-colors font-medium text-sm"
                >
                  <ChevronLeft size={16} />
                  {t("wizard.back")}
                </button>
                <button
                  onClick={() => setStep(2)}
                  className="flex items-center gap-2 px-5 py-2.5 bg-masuite-600 text-white rounded-lg hover:bg-masuite-700 transition-colors font-medium text-sm"
                >
                  {t("wizard.next")}
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Installation */}
          {step === 2 && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-8">
                {t("wizard.installTitle")}
              </h3>

              <div className="space-y-8">
                {/* Step 1: Server + domain (or Docker) */}
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-masuite-600 text-white flex items-center justify-center font-bold">
                    <Globe size={18} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900">
                      {target === "vps"
                        ? t("wizard.installStep1title")
                        : t("wizard.installStep1titleLocal")}
                    </h4>
                    <p className="text-sm text-slate-500 mt-1">
                      {target === "vps"
                        ? t("wizard.installStep1desc")
                        : t("wizard.installStep1descLocal")}
                    </p>
                  </div>
                </div>

                {/* Step 2: Run command */}
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-masuite-600 text-white flex items-center justify-center font-bold">
                    <Terminal size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-slate-900">
                      {t("wizard.installStep2title")}
                    </h4>
                    <p className="text-sm text-slate-500 mt-1 mb-4">
                      {target === "vps"
                        ? t("wizard.installStep2desc")
                        : t("wizard.installStep2descLocal")}
                    </p>

                    {/* Tabs */}
                    <div className="flex gap-1 mb-3">
                      <button
                        onClick={() => setCmdTab("curl")}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                          cmdTab === "curl"
                            ? "bg-slate-900 text-white"
                            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                        }`}
                      >
                        {t("wizard.tabCurl")}
                      </button>
                      <button
                        onClick={() => setCmdTab("git")}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                          cmdTab === "git"
                            ? "bg-slate-900 text-white"
                            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                        }`}
                      >
                        {t("wizard.tabGit")}
                      </button>
                    </div>

                    <p className="text-xs text-slate-400 mb-2">
                      {cmdTab === "curl"
                        ? t("wizard.tabCurlDesc")
                        : t("wizard.tabGitDesc")}
                    </p>

                    <div className="relative group">
                      <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap break-all">
                        {cmdTab === "curl" ? curlCmd : gitCmd}
                      </pre>
                      <button
                        onClick={() =>
                          copyToClipboard(
                            cmdTab === "curl" ? curlCmd : gitCmd,
                            cmdTab === "curl" ? 0 : 1
                          )
                        }
                        className="absolute top-2 right-2 p-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                        title="Copy"
                      >
                        {copiedIdx === (cmdTab === "curl" ? 0 : 1) ? (
                          <Check size={14} />
                        ) : (
                          <Copy size={14} />
                        )}
                      </button>
                    </div>

                  </div>
                </div>

                {/* Step 3: Done */}
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-masuite-600 text-white flex items-center justify-center font-bold">
                    <Rocket size={18} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900">
                      {t("wizard.installStep3title")}
                    </h4>
                    <p className="text-sm text-slate-500 mt-1">
                      {target === "vps"
                        ? t("wizard.installStep3desc")
                        : t("wizard.installStep3descLocal")}
                    </p>
                    <p className="text-xs text-amber-600 mt-2">
                      {t("wizard.alphaWarning")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-8 pt-6 border-t border-slate-100">
                <button
                  onClick={() => setStep(1)}
                  className="flex items-center gap-2 px-5 py-2.5 text-slate-600 rounded-lg hover:bg-slate-100 transition-colors font-medium text-sm"
                >
                  <ChevronLeft size={16} />
                  {t("wizard.back")}
                </button>
                <a
                  href="https://github.com/sylvinus/masuite"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <Github size={14} />
                  GitHub
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
