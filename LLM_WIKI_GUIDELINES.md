# LLM Wiki Synthesis & Anti-Rot Guidelines (v0.1.0)

Inspired by Andrej Karpathy's LLM Wiki concept, knowledge in **SherpaMD** is maintained as a curated, continuously synthesized graph of durable concepts rather than an append-only log of raw chat transcripts.

---

## 1. Synthesis over Transcript Dumps
- **Do Not**: Dump multi-thousand line terminal logs, raw JSON responses, or entire chat transcripts into knowledge kits.
- **Do**: Read raw evidence, extract verified facts, architectural decisions, and operational commands, and synthesize them directly into the relevant section of the knowledge base.
- **Rule**: If raw source data must be retained, place it in the kit's `sources/` folder and link to it via a source descriptor in the YAML front matter.

---

## 2. In-Place Updates & Aggressive Pruning
- **In-Place Mutation**: When a system configuration, IP address, port, command syntax, or API endpoint changes, update the existing entry in-place.
- **Prune Obsolete Directives**: Immediately remove superseded instructions or deprecated rules rather than leaving stale advice alongside newer contradictory advice.
- **Context Density**: Keep documents concise and high-signal so agents can load the entire relevant domain within minimal context tokens.

---

## 3. Verifiable Technical Claims
- Every technical directive and operational workflow must include an actionable verification step.
- Include executable verification snippets:
  ```bash
  # Verify:
  systemctl --user is-active my-service.service
  ```
- Track the verification status in the front matter (`verification_state: "verified"`).

---

## 4. Contradiction Management & Reconciliation
- When sources or instructions diverge, do not guess or silently overwrite without explanation.
- Add an entry under `## Contradiction Notes & Reconciliations` comparing the conflicting sources and documenting the verified resolution.
- If the conflict requires human or orchestrator decision, mark `verification_state: "contradiction"` and issue a `NEEDS-APPROVAL` notification on the agent coordination bus / task tracker.

---

## 5. Absolute Secret Containment
- NEVER commit API keys, authentication tokens, passwords, private keys, or session cookies into Sherpa kits or source files.
- Replace all sensitive tokens with `[REDACTED]` or standard environment variable references (e.g. `$GITHUB_TOKEN`).
