import type { Metadata } from "next";
import { Inter, Source_Serif_4, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], variable: "--inter", display: "swap" });
const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--serif-font",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--mono-font",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MCP Audit - check your AI agent's tool descriptions for hidden Unicode",
  description:
    "Free 60-second audit of MCP tool descriptions. Detects hidden Unicode, agent commandeering language, homoglyph mixes, encoded payloads. Compare your setup against a 911-server reference corpus.",
  metadataBase: new URL("https://mcp-audit.dev"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>
        <nav className="nav">
          <Link href="/" className="nav-brand">
            MCP Audit
          </Link>
          <div className="nav-links">
            <Link href="/demo">Bytes vs Eyes</Link>
            <Link href="/methodology">Methodology</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
