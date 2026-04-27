import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

export const metadata = {
  title: "Methodology - MCP Audit",
  description:
    "How the scanner works, what it detects, and the primary-source ledger backing every claim.",
};

interface Source {
  url: string;
  title: string;
  publisher: string;
  publish_date: string;
  exact_quote: string;
  source_type: string;
}

interface Claim {
  claim_id: string;
  claim_text: string;
  category: string;
  sources: Source[];
  claim_status: string;
}

const loadPost = (): string =>
  fs.readFileSync(path.join(process.cwd(), "content", "post-v2.md"), "utf-8");

const loadLedger = (): Record<string, Claim> => {
  const raw = fs.readFileSync(path.join(process.cwd(), "content", "sources_v2.json"), "utf-8");
  const arr: Claim[] = JSON.parse(raw);
  const out: Record<string, Claim> = {};
  for (const c of arr) out[c.claim_id] = c;
  return out;
};

const CLAIM_TAG_RE = /\[claim:([A-Z0-9\-]+)\]/g;

const renderPost = (md: string, ledger: Record<string, Claim>): string => {
  const seen = new Set<string>();
  return md.replace(CLAIM_TAG_RE, (_, id: string) => {
    if (id === "ID") return "";
    if (!ledger[id]) return ` <sup>[?${id}]</sup>`;
    seen.add(id);
    return ` <sup><a href="#claim-${id}" title="${id}">[${id}]</a></sup>`;
  });
};

const collectCitedClaims = (md: string, ledger: Record<string, Claim>): Claim[] => {
  const ids = new Set<string>();
  for (const m of md.matchAll(CLAIM_TAG_RE)) {
    if (m[1] !== "ID" && ledger[m[1]!]) ids.add(m[1]!);
  }
  return Array.from(ids)
    .sort()
    .map((id) => ledger[id]!)
    .filter(Boolean);
};

export default function MethodologyPage() {
  const md = loadPost();
  const ledger = loadLedger();
  const annotated = renderPost(md, ledger);
  const cited = collectCitedClaims(md, ledger);

  return (
    <main className="container">
      <article style={{ maxWidth: "720px" }}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          components={{
            h1: ({ children }) => <h1>{children}</h1>,
            h2: ({ children }) => <h2>{children}</h2>,
            h3: ({ children }) => <h3>{children}</h3>,
            sup: ({ children, ...props }) => (
              <sup style={{ fontSize: "0.7em", color: "var(--accent)" }} {...props}>
                {children}
              </sup>
            ),
            a: ({ href, children, ...props }) => (
              <a href={href} {...props}>
                {children}
              </a>
            ),
          }}
        >
          {annotated}
        </ReactMarkdown>

        <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "3rem 0 2rem" }} />

        <h2>Citations</h2>
        <p className="muted">
          {cited.length} claims cited in this post. Each lists its primary sources with
          publish date and exact-quote provenance. Full ledger of {Object.keys(ledger).length} claims
          (including {Object.values(ledger).filter((c) => c.category === "competitor_grid").length}{" "}
          positioning-grid cells) at{" "}
          <code>content/sources_v2.json</code>.
        </p>

        {cited.map((c) => (
          <div
            key={c.claim_id}
            id={`claim-${c.claim_id}`}
            style={{
              marginTop: "1.5rem",
              padding: "1rem 1.1rem",
              background: "#ffffff",
              border: "1px solid var(--border)",
              borderRadius: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", gap: "0.6rem", flexWrap: "wrap" }}>
              <strong style={{ fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
                {c.claim_id}
              </strong>
              <span className={`tier-badge tier-${c.claim_status === "VERIFIED" ? "clean" : "minor"}`}>
                {c.claim_status}
              </span>
              <span className="muted" style={{ fontSize: "0.85rem" }}>
                {c.sources.length} source{c.sources.length === 1 ? "" : "s"}
              </span>
            </div>
            <p style={{ marginTop: "0.5rem", fontSize: "0.95rem" }}>{c.claim_text}</p>
            {c.sources.length > 0 ? (
              <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.1rem", fontSize: "0.85rem" }}>
                {c.sources.map((s, i) => (
                  <li key={i} style={{ marginTop: "0.3rem" }}>
                    {s.url.startsWith("http") ? (
                      <a href={s.url} target="_blank" rel="noreferrer">
                        {s.publisher || s.title}
                      </a>
                    ) : (
                      <code>{s.url}</code>
                    )}
                    {s.publish_date ? (
                      <span className="muted"> ({s.publish_date})</span>
                    ) : null}
                    {s.exact_quote ? (
                      <div className="muted" style={{ fontStyle: "italic", marginLeft: "0.6rem" }}>
                        "{s.exact_quote.slice(0, 200)}{s.exact_quote.length > 200 ? "..." : ""}"
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}

        <p className="muted" style={{ marginTop: "3rem", fontSize: "0.9rem" }}>
          Run an audit on your own setup at <Link href="/">the home page</Link>, or open{" "}
          <Link href="/demo">Bytes vs Eyes</Link>.
        </p>
      </article>
    </main>
  );
}
