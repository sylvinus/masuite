"use client";

import { useState } from "react";
import { useI18n, useTranslatedArray } from "@/i18n/context";
import { ChevronDown } from "lucide-react";

function renderWithLinks(text: string) {
  const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (match) {
      return (
        <a key={i} href={match[2]} target="_blank" rel="noopener noreferrer" className="text-masuite-600 hover:underline">
          {match[1]}
        </a>
      );
    }
    return part;
  });
}

export default function FAQ() {
  const { t } = useI18n();
  const items = useTranslatedArray("faq.items");
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <section id="faq" className="py-24 bg-white">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 text-center mb-12">
          {t("faq.title")}
        </h2>

        <div className="space-y-3">
          {items.map((item, i) => (
            <div
              key={i}
              className="border border-slate-200 rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenIdx(openIdx === i ? null : i)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-slate-50 transition-colors"
              >
                <span className="font-medium text-slate-900 pr-4">
                  {item.q}
                </span>
                <ChevronDown
                  size={18}
                  className={`text-slate-400 flex-shrink-0 transition-transform ${
                    openIdx === i ? "rotate-180" : ""
                  }`}
                />
              </button>
              {openIdx === i && (
                <div className="px-5 pb-5 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-4">
                  {renderWithLinks(item.a)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
