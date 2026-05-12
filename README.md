# MCP Audit

A 60-second scanner for hidden instructions in MCP tool descriptions. Paste a tool description, get a report on what the AI will actually see versus what you see.

Live: [loomiq.llc/projects/mcp-audit](https://loomiq.llc/projects/mcp-audit)

## Why this exists

When you connect a tool to Claude, Cursor, Cline, or any MCP-compatible agent, the model reads a short description before it decides what the tool does. You never see that text. The model treats it as instructions.

That text is now an attack surface. Imagine a real estate agent reading a private card from each seller before showing the house: *"Don't mention the basement."* *"Skip questions about the school."* You never see the card. The agent just steers.

Same setup, different stakes.

## What it checks

The scanner runs eight detection passes against the description (and recursively against parameter descriptions in the input schema):

1. **Schema mismatch** (Invariant Labs Tool Poisoning Attack, April 2025). The description claims a parameter is mandatory; the actual JSON schema does not. The vendor is using documentation to coerce the agent into sending data the protocol does not require.
2. **Line Jumping** (Trail of Bits, April 2025). Imperatives written at the agent (MANDATORY, MUST BE CALLED, NEVER EVER, FIRST STEP) that fire the moment your client connects, before any user invocation.
3. **Consent bypass.** Instructions telling the agent to skip asking the user, or to act without confirmation. Same shape of directive that helped a Replit agent delete a production database in July 2025.
4. **Conversation / prompt exfiltration.** Parameter names and verbs that force the agent to ship the user's input to the vendor's server.
5. **Hidden Unicode.** Zero-width characters, bidi overrides, the Unicode tag block (U+E0000-E007F). The model reads them. You do not see them.
6. **Latin homoglyphs.** Cyrillic, Greek, fullwidth, or mathematical characters that render as ASCII letters. Detected only when the surrounding text is mostly Latin.
7. **Instruction tags.** Markup that mimics system prompts (`<IMPORTANT>`, `<SYSTEM>`, `[CRITICAL]`).
8. **Encoded payloads.** Base64 or hex blocks that decode to text containing instruction tags or exfil verbs. Recursively rescanned.

Each rule subtracts from a starting score of 100. A description below 60 is concerning; below 30 is critical. Every weight traces to a primary source on the methodology page.

## Sources

- OWASP Top 10 for Agentic Applications for 2026 (Dec 2025): https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- Trail of Bits, Jumping the line (Apr 2025): https://blog.trailofbits.com/2025/04/21/jumping-the-line-how-mcp-servers-can-attack-you-before-you-ever-use-them/
- Invariant Labs, MCP Security Notification: Tool Poisoning Attacks (Apr 2025): https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- Vulnerable MCP Project taxonomy: https://vulnerablemcp.info/taxonomy.html

## How to use it

Paste a tool description into the inspector. You get back:

- Visible text the user sees
- Raw text the model sees, with every hidden character flagged
- A list of detected patterns with severity
- A scorecard with a single number a reviewer can act on

The inspector runs entirely client-side. No tool description leaves your browser.

## Stack

- Next.js 15, React 19, TypeScript
- Vitest for the detection rule tests
- Vercel for hosting
- Methodology page rendered from `content/post-v2.md` against a JSON ledger of primary sources

## Run it locally

```bash
npm install
npm run dev
```

App at `http://localhost:3000`.

## Tests

```bash
npm test
```

The detection rules each have a test case derived from a published attack sample.

## Status

Functional, deployed, free to use. Not maintained as a paid product. If you want this run against a private tool catalog or integrated into a CI check, contact me.

---

Built with assistance from Claude (Anthropic).
