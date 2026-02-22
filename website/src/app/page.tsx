"use client";

import { I18nProvider } from "@/i18n/context";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Wizard from "@/components/Wizard";
import FAQ from "@/components/FAQ";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <I18nProvider>
      <Header />
      <main>
        <Hero />
        <Wizard />
        <FAQ />
      </main>
      <Footer />
    </I18nProvider>
  );
}
