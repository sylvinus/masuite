"use client";

import { useI18n } from "@/i18n/context";
import { ArrowDown } from "lucide-react";

export default function Hero() {
  const { t } = useI18n();

  return (
    <section className="relative min-h-[50vh] flex items-center justify-center bg-gradient-to-b from-masuite-900 via-masuite-800 to-masuite-600 text-white overflow-hidden">
      {/* Subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center pt-28 pb-16">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold leading-tight tracking-tight whitespace-pre-line">
          {t("hero.title")}
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-blue-100 max-w-2xl mx-auto leading-relaxed">
          {t("hero.subtitle")}
        </p>
        <a
          href="#wizard"
          className="inline-flex items-center gap-2 mt-10 px-7 py-3.5 bg-white text-masuite-600 font-semibold rounded-full hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl"
        >
          {t("hero.cta")}
          <ArrowDown size={18} />
        </a>
      </div>
    </section>
  );
}
