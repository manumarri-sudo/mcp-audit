"""Merge the 5 research JSONs into a canonical sources_v2.json.

Reads:
  ~/.claude/projects/invisible-ink/post/research/0{1..5}-*.json

Writes:
  content/sources_v2.json
  content/sources_v2.summary.md  (counts + claim_id index)

Schema of sources_v2.json:
  [
    {
      "claim_id": "MCP-THREAT-001",
      "claim_text": "...",
      "category": "...",
      "sources": [
        { "url", "title", "publisher", "publish_date", "primary",
          "source_type", "exact_quote", "accessed_at", "verification_status" }
      ],
      "minimum_sources_met": bool,
      "claim_status": "VERIFIED" | "NEEDS_MORE" | "POSITIONING_CELL",
      "lead_with_this_claim": bool,
      "notes": "..."
    }
  ]
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESEARCH_DIR = pathlib.Path.home() / ".claude/projects/invisible-ink/post/research"
OUT_JSON = ROOT / "content" / "sources_v2.json"
OUT_MD = ROOT / "content" / "sources_v2.summary.md"

MIN_SOURCES = 4


def normalize_status(status: str | None, source_count: int | None = None) -> str:
    if status is None:
        if source_count is not None and source_count >= MIN_SOURCES:
            return "VERIFIED"
        return "NEEDS_MORE"
    s = status.upper()
    if s in {"VERIFIED", "STRONG"}:
        return "VERIFIED"
    if s == "NEEDS_MORE":
        return "NEEDS_MORE"
    if s == "POSITIONING_CELL":
        return "POSITIONING_CELL"
    return "NEEDS_MORE"


def load_flat_list(path: pathlib.Path) -> list[dict[str, Any]]:
    """Files 01, 02, 03: top-level list of claims."""
    return json.loads(path.read_text())


def load_wrapped(path: pathlib.Path) -> list[dict[str, Any]]:
    """File 05: dict with 'claims' key."""
    d = json.loads(path.read_text())
    if isinstance(d, list):
        return d
    return d.get("claims", [])


CATEGORY_BY_PREFIX = {
    "MCP-THREAT": "mcp_threat_landscape",
    "UNICODE": "unicode_attack_literature",
    "NEWS": "news_this_week",
    "STATS": "ecosystem_stats",
    "COMP": "competitor_grid",
}


def infer_category(claim_id: str) -> str:
    for prefix, category in CATEGORY_BY_PREFIX.items():
        if claim_id.startswith(prefix):
            return category
    return ""


def normalize_canonical_claim(c: dict[str, Any]) -> dict[str, Any]:
    """Normalize files 01, 02, 03, 05 which already use the canonical shape."""
    sources = c.get("sources", []) or []
    sources_norm = []
    for s in sources:
        sources_norm.append(
            {
                "url": s.get("url", ""),
                "title": s.get("title", ""),
                "publisher": s.get("publisher", ""),
                "publish_date": s.get("publish_date", ""),
                "primary": bool(s.get("primary", False)),
                "source_type": s.get("source_type", ""),
                "exact_quote": s.get("exact_quote", ""),
                "accessed_at": s.get("accessed_at", ""),
                "verification_status": s.get("verification_status", "VERIFIED"),
            }
        )
    status = normalize_status(c.get("claim_status"), len(sources_norm))
    if len(sources_norm) < MIN_SOURCES and status == "VERIFIED":
        status = "NEEDS_MORE"
    claim_id = c.get("claim_id", "")
    return {
        "claim_id": claim_id,
        "claim_text": c.get("claim_text", c.get("claim", "")),
        "category": c.get("category") or infer_category(claim_id),
        "sources": sources_norm,
        "minimum_sources_met": len(sources_norm) >= MIN_SOURCES,
        "claim_status": status,
        "lead_with_this_claim": bool(c.get("lead_with_this_claim", False)),
        "notes": c.get("notes", "") or "",
    }


def normalize_competitor_grid(c: dict[str, Any]) -> dict[str, Any]:
    """File 04: each entry is a single-source positioning-cell claim per (product, claim_type)."""
    return {
        "claim_id": c.get("claim_id", ""),
        "claim_text": c.get("claim", c.get("claim_text", "")),
        "category": "competitor_grid",
        "sources": [
            {
                "url": c.get("source_url", ""),
                "title": c.get("product", ""),
                "publisher": c.get("product", ""),
                "publish_date": "",
                "primary": bool(c.get("primary_source", True)),
                "source_type": "vendor_doc",
                "exact_quote": c.get("exact_quote_supporting_claim", ""),
                "accessed_at": c.get("accessed_at", ""),
                "verification_status": c.get("verification_status", "VERIFIED"),
            }
        ],
        "minimum_sources_met": False,
        "claim_status": "POSITIONING_CELL",
        "lead_with_this_claim": False,
        "notes": f"Cell on positioning grid: product={c.get('product', '')} claim_type={c.get('claim_type', '')} tag={c.get('tag', '')}",
    }


def extract_claims(path: pathlib.Path) -> list[dict[str, Any]]:
    """Returns the list of claim dicts regardless of wrapper shape."""
    raw = json.loads(path.read_text())
    if isinstance(raw, list):
        return [c for c in raw if isinstance(c, dict)]
    if isinstance(raw, dict):
        claims = raw.get("claims", [])
        if isinstance(claims, list):
            return [c for c in claims if isinstance(c, dict)]
    return []


def is_competitor_grid_entry(c: dict[str, Any]) -> bool:
    """Distinguish file-04 entries (flat single-source) from canonical claims."""
    return "product" in c and "sources" not in c


def main() -> int:
    if not RESEARCH_DIR.exists():
        print(f"research dir not found: {RESEARCH_DIR}", file=sys.stderr)
        return 1

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    canonical: list[dict[str, Any]] = []

    scan_claims_path = ROOT / "content" / "scan_claims.json"
    if scan_claims_path.exists():
        for c in json.loads(scan_claims_path.read_text()):
            canonical.append(c)

    for f in sorted(RESEARCH_DIR.glob("0*.json")):
        if f.name.endswith(".summary.md"):
            continue
        for c in extract_claims(f):
            if is_competitor_grid_entry(c):
                canonical.append(normalize_competitor_grid(c))
            else:
                canonical.append(normalize_canonical_claim(c))

    # Stable sort by claim_id
    canonical.sort(key=lambda x: x["claim_id"])

    OUT_JSON.write_text(json.dumps(canonical, indent=2, ensure_ascii=False))

    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    leads: list[dict[str, Any]] = []
    for c in canonical:
        by_status[c["claim_status"]] = by_status.get(c["claim_status"], 0) + 1
        by_category[c["category"]] = by_category.get(c["category"], 0) + 1
        if c["lead_with_this_claim"]:
            leads.append(c)

    md = ["# sources_v2.json — merged ledger", ""]
    md.append(f"Total claims: **{len(canonical)}**")
    md.append("")
    md.append("## By status")
    for k, v in sorted(by_status.items(), key=lambda x: -x[1]):
        md.append(f"- **{k}**: {v}")
    md.append("")
    md.append("## By category")
    for k, v in sorted(by_category.items(), key=lambda x: -x[1]):
        md.append(f"- **{k}**: {v}")
    md.append("")
    md.append(f"## Lead-with claims ({len(leads)})")
    for c in leads:
        md.append(f"- **{c['claim_id']}** [{c['claim_status']}, {len(c['sources'])} sources]")
        md.append(f"  - {c['claim_text'][:200]}{'...' if len(c['claim_text']) > 200 else ''}")
    md.append("")
    md.append("## Verified claims (the post's primary citation pool)")
    for c in canonical:
        if c["claim_status"] == "VERIFIED":
            md.append(f"- `{c['claim_id']}` ({c['category']}, {len(c['sources'])} sources): {c['claim_text'][:120]}{'...' if len(c['claim_text']) > 120 else ''}")
    OUT_MD.write_text("\n".join(md))

    print(f"merged: {len(canonical)} claims -> {OUT_JSON}")
    print(f"status counts: {by_status}")
    print(f"category counts: {by_category}")
    print(f"lead-with claims: {len(leads)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
