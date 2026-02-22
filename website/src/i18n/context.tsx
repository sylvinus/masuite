"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { translations, LANGUAGES, type Language } from "./translations";

type I18nContextType = {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, vars?: Record<string, string>) => string;
};

const I18nContext = createContext<I18nContextType>(null!);

function getNestedValue(obj: unknown, path: string): string | unknown[] | undefined {
  let current: unknown = obj;
  for (const key of path.split(".")) {
    if (current == null || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[key];
  }
  if (typeof current === "string") return current;
  if (Array.isArray(current)) return current;
  return undefined;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>("en");

  useEffect(() => {
    const stored = localStorage.getItem("masuite-lang") as Language | null;
    if (stored && LANGUAGES.includes(stored)) {
      setLang(stored);
      return;
    }
    const browserLang = navigator.language.split("-")[0] as Language;
    if (LANGUAGES.includes(browserLang)) {
      setLang(browserLang);
    }
  }, []);

  const changeLang = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem("masuite-lang", newLang);
    document.documentElement.lang = newLang;
  };

  const t = (key: string, vars?: Record<string, string>): string => {
    let value = getNestedValue(translations[lang], key);
    if (value === undefined) {
      value = getNestedValue(translations["en"], key);
    }
    if (typeof value !== "string") return key;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        value = value.replace(`{${k}}`, v);
      }
    }
    return value;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang: changeLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

export function useTranslatedArray(key: string) {
  const { lang } = useI18n();
  const value = getNestedValue(translations[lang], key);
  if (Array.isArray(value)) return value as { q: string; a: string }[];
  const fallback = getNestedValue(translations["en"], key);
  if (Array.isArray(fallback)) return fallback as { q: string; a: string }[];
  return [];
}
