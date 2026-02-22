"use client";

import { useI18n } from "@/i18n/context";
import { Github, Heart } from "lucide-react";

export default function Footer() {
  const { t } = useI18n();

  return (
    <footer className="py-12 bg-slate-900 text-slate-400">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex flex-col gap-2 text-center sm:text-left">
            <p className="text-xs text-slate-500">
              <a href="#" className="text-slate-400 hover:text-white">MaSuite</a>
              {" "}{t("footer.disclaimer")}{" "}
              <a
                href="https://lasuite.numerique.gouv.fr/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white"
              >
                LaSuite
              </a>
              {t("footer.disclaimerPost")}
            </p>
            <p className="text-xs text-slate-500">
              {t("footer.reportIssues")}{" "}
              <a
                href="https://github.com/sylvinus/masuite/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white"
              >
                GitHub
              </a>
              {t("footer.bestEffort")}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm flex items-center gap-1">
              {t("footer.madeWith")}{" "}
              <Heart size={12} className="text-red-400" />{" "}
              {t("footer.by")}{" "}
              <a
                href="https://sylvainzimmer.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white hover:underline"
              >
                Sylvain Zimmer
              </a>
            </span>
            <a
              href="https://github.com/sylvinus/masuite"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-white transition-colors"
            >
              <Github size={20} />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
