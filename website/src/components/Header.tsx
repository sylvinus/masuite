"use client";

import { useI18n } from "@/i18n/context";
import { LANGUAGES, LANGUAGE_LABELS, type Language } from "@/i18n/translations";
import { Github, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export default function Header() {
  const { lang, setLang, t } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <a href="#" className="text-lg font-bold text-masuite-600 tracking-tight">
          MaSuite
        </a>

        <nav className="flex items-center gap-4 sm:gap-6 text-sm">
          <a
            href="#wizard"
            className="hidden sm:inline text-slate-600 hover:text-slate-900 transition-colors"
          >
            {t("nav.getStarted")}
          </a>
          <a
            href="#faq"
            className="hidden sm:inline text-slate-600 hover:text-slate-900 transition-colors"
          >
            {t("nav.faq")}
          </a>
          <a
            href="https://github.com/sylvinus/masuite"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-600 hover:text-slate-900 transition-colors"
          >
            <Github size={18} />
          </a>

          <div ref={ref} className="relative">
            <button
              onClick={() => setOpen(!open)}
              className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 px-2 py-1 rounded-md hover:bg-slate-100 transition-colors uppercase font-medium tracking-wide"
            >
              {lang}
              <ChevronDown size={14} />
            </button>
            {open && (
              <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 py-1 min-w-[140px]">
                {LANGUAGES.map((l) => (
                  <button
                    key={l}
                    onClick={() => {
                      setLang(l as Language);
                      setOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 text-sm hover:bg-slate-50 transition-colors ${
                      l === lang ? "text-masuite-600 font-medium" : "text-slate-700"
                    }`}
                  >
                    {LANGUAGE_LABELS[l]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
