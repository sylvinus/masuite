import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MaSuite - Votre suite numérique, libre et indépendante",
  description:
    "Hébergez vos propres alternatives à Google Docs, Meet, Drive, Gmail, Trello et ChatGPT. 100% open source, 100% sous votre contrôle.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
