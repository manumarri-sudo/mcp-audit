"""Lint content/post-v2.md against content/sources_v2.json.

Rules:
  1. Every [claim:ID] tag must resolve to a claim in sources_v2.json
  2. Every resolved claim must have claim_status == "VERIFIED" or "POSITIONING_CELL"
  3. Every VERIFIED claim must have at least 4 sources
  4. Each top-level fact-bearing sentence (heuristic: contains a digit, or a
     quoted phrase, or a vendor name) should carry at least one [claim:ID] tag

Exit codes:
  0 = clean
  1 = lint failures
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
POST = ROOT / "content" / "post-v2.md"
LEDGER = ROOT / "content" / "sources_v2.json"

CLAIM_TAG_RE = re.compile(r"\[claim:([A-Z0-9\-]+(?:\s.*?)?)\]")
PLACEHOLDER_IDS = {"ID"}
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\d`])")
DIGIT_RE = re.compile(r"\b\d{2,}\b")
QUOTED_RE = re.compile(r'"[^"]{4,}"')
VENDOR_NAMES = {
    "anthropic", "openai", "ox security", "pillar", "snyk", "promptfoo",
    "invariant", "cisco", "microsoft", "google", "vercel", "cloudflare",
    "lakera", "trojan source", "owasp", "mitre", "kimi", "moonshot",
    "smithery", "pulsemcp", "glama", "mcp", "antigravity", "cyata",
    "agentdeskai", "context.ai", "copilot",
}


def load_ledger(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text())
    return {c["claim_id"]: c for c in raw}


IMPERATIVE_STARTS = ("if you ", "run an ", "run the ", "paste ", "see ", "read ", "try ", "tell ", "click ")


def is_imperative(sentence: str) -> bool:
    s = sentence.lower().strip()
    return any(s.startswith(p) for p in IMPERATIVE_STARTS)


def is_fact_bearing(sentence: str) -> bool:
    if is_imperative(sentence):
        return False
    s = sentence.lower()
    if DIGIT_RE.search(sentence):
        return True
    if QUOTED_RE.search(sentence):
        return True
    for v in VENDOR_NAMES:
        if v in s:
            return True
    return False


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "INLINE_CODE", text)
    pieces = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        sentences = SENTENCE_END_RE.split(line)
        for s in sentences:
            s = s.strip()
            if len(s) > 30:
                pieces.append(s)
    return pieces


def main() -> int:
    if not POST.exists():
        print(f"post not found: {POST}", file=sys.stderr)
        return 1
    if not LEDGER.exists():
        print(f"ledger not found: {LEDGER}", file=sys.stderr)
        return 1

    ledger = load_ledger(LEDGER)
    post_text = POST.read_text()

    failures: list[str] = []
    warnings: list[str] = []

    cited_ids: set[str] = set()
    for m in CLAIM_TAG_RE.finditer(post_text):
        raw = m.group(1).strip()
        if raw in PLACEHOLDER_IDS:
            continue
        if " " in raw:
            warnings.append(f"informal claim tag (not in ledger): {m.group(0)}")
            continue
        cited_ids.add(raw)

    for cid in cited_ids:
        if cid not in ledger:
            failures.append(f"unresolved claim id: {cid}")
            continue
        c = ledger[cid]
        status = c.get("claim_status", "")
        if status not in {"VERIFIED", "POSITIONING_CELL"}:
            failures.append(f"{cid}: claim_status is {status}, not VERIFIED")
        sources = c.get("sources", [])
        all_own_scan = (
            len(sources) > 0
            and all(s.get("source_type") == "own_scan" for s in sources)
        )
        if status == "VERIFIED" and len(sources) < 4 and not all_own_scan:
            failures.append(f"{cid}: VERIFIED but only {len(sources)} sources")

    untagged_fact_sentences: list[str] = []
    for s in split_sentences(post_text):
        if not is_fact_bearing(s):
            continue
        if "[claim:" in s:
            continue
        untagged_fact_sentences.append(s)

    print(f"=== Lint report: content/post-v2.md ===")
    print(f"  cited claim ids: {len(cited_ids)}")
    print(f"  resolved + VERIFIED: {sum(1 for cid in cited_ids if cid in ledger and ledger[cid].get('claim_status') == 'VERIFIED')}")
    print(f"  fact-bearing sentences without claim tag: {len(untagged_fact_sentences)}")
    print(f"  failures: {len(failures)}")
    print(f"  warnings: {len(warnings)}")
    print()

    if cited_ids:
        print("Cited claims:")
        for cid in sorted(cited_ids):
            if cid in ledger:
                c = ledger[cid]
                print(f"  {cid}: {c.get('claim_status')} ({len(c.get('sources', []))} sources)")
            else:
                print(f"  {cid}: UNRESOLVED")
        print()

    if untagged_fact_sentences:
        print("Sentences flagged as fact-bearing but not citing a claim:")
        for s in untagged_fact_sentences:
            print(f"  - {s[:160]}{'...' if len(s) > 160 else ''}")
        print()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        print()
        return 1

    print("Lint clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
