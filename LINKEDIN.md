# LinkedIn post — MCP Audit launch

**Post (paste this in the box):**

I scanned 1,196 MCP servers I could find on npm, PyPI, and GitHub.

219 ship tool descriptions that I would not let through a security review.

The thing the model reads before it decides which tool to call is a short string the protocol calls "description." Your client almost never shows it to you. It is the LLM equivalent of a private note slipped to a real estate agent before they show you the house, authoritative and invisible, and the model treats it as instructions.

Invariant Labs named the class on April 1, 2025: Tool Poisoning. Trail of Bits named the pattern where instructions inside the description fire before any user invocation: Line Jumping. The MCP spec has no character-set constraints on the field, and there is no rendering guarantee that the bytes you see match the bytes the model reads.

I went looking for hidden Unicode payloads first because they are the dramatic version of the attack, and I found almost none in production. So I rebuilt the detectors against three sources that had landed since the original Invariant disclosure: OWASP's Top 10 for Agentic Applications (December 2025), the Trail of Bits Line Jumping write-up, and the Vulnerable MCP taxonomy.

The rescan, across 15,933 tool descriptions:

219 of them ship descriptions that fail the strict bar, spread across 150-plus named packages.

Another 368 carry Line Jumping imperatives written directly at the agent.

64 are canonical schema-mismatch cases, where the description claims a parameter is required and the JSON schema does not.

The dramatic version of the attack hides bytes in Unicode. The version that is shipping right now is plain English nobody had a reason to read.

I built a free scanner. Paste a tool description, see what your eyes see versus what the model reads, get a score in about four seconds. It is stateless, runs at the Cloudflare edge, and does not log. If you ship an MCP server, run it on your own descriptions. If you maintain a registry, run it across your index.

Link in the first comment.

---

**First comment (post immediately after publishing):**

mcp-audit.dev

Methodology and full source ledger at mcp-audit.dev/methodology. The scan corpus, weights, and detector source are all there.

---

**Posting notes**

- Best window per research: Tuesday or Wednesday 8-10am ET.
- No hashtags. One is fine, more than one hurts reach.
- Do not put the URL in the body of the post. The first-comment workaround still beats an in-body link in 2026, even with the recent algorithmic detection.
- If you want the document-post engagement multiplier, attach a single-page PDF labeled something like "Anatomy of a poisoned tool description" with the receipt-style screenshot from the demo page. Document posts hit ~6.6% engagement vs. ~2.0% for text-only in 2026 LinkedIn tests.
- Character count: ~1,750. Inside the 1,300-1,900 sweet spot.
