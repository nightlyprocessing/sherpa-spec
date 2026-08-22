# SherpaMD Specification (`sherpa-spec`)

**SherpaMD** (`sherpamd.org`) is an open, portable, structured, human- and AI-readable knowledge format and context standard designed for deterministic agent collaboration, verified provenance, and curated operational knowledge bases.

---

## What is SherpaMD?

SherpaMD solves the problem of multi-agent **context rot**, unstructured chat log sprawl, and contradictory agent directives. It standardizes how autonomous AI agents and human operators document architectures, operating directives, and procedures.

### Core Pillars

1. **Dual Human + AI Readability**: High-density Plain Markdown parseable by LLMs and instantly readable by engineers.
2. **Deterministic Provenance & Verification**: Every directive and procedure links to verified sources and concrete test commands (`verification_state: "verified"`).
3. **In-Place Synthesis (Karpathy LLM-Wiki Pattern)**: Continuous distillation and in-place updating of knowledge graphs instead of append-only transcript dumps.
4. **Strict Secret Hygiene**: Zero containment tolerance against committing API keys, tokens, or credentials.
5. **Ecosystem Modularity**:
   - [`sherpa-spec`](https://github.com/sherpa-md/sherpa-spec): Format specification and normative schema.
   - [`sherpa-kit-template`](https://github.com/sherpa-md/sherpa-kit-template): Reusable starter scaffold for new domain kits.
   - [`sherpa-kits`](https://github.com/sherpa-md/sherpa-kits): Central repository of standard, reusable domain knowledge kits.

---

## Dual Human + AI Usage Guide

### For Human Engineers
- **Instant Domain Orientation**: Read `SHERPA.md` at the root of any domain kit for an executive briefing, system architecture, and operational procedures.
- **Auditable History**: Check `provenance` and `verification_state` before executing operational runbooks.
- **Fast Troubleshooting**: Look up `## Contradiction Notes & Reconciliations` to understand recent breaking changes and reconciled configurations.

### For Autonomous AI Agents
- **Context Loading**: Inject `SHERPA.md` directly into prompt context as the authoritative ground truth for the domain.
- **Continuous Knowledge Synthesis**: When completing tasks, update existing knowledge sections in-place rather than appending uncurated logs (see [`LLM_WIKI_GUIDELINES.md`](./LLM_WIKI_GUIDELINES.md)).
- **Verification Proof**: Run attached verification commands and update `last_verified` timestamps and `verification_state`.

---

## Repository Contents

- [`SHERPA.md`](./SHERPA.md): The normative **SherpaMD Format Specification v0.1.0** covering purpose, YAML front matter, sources/provenance, verification states, related links, contradiction notes, editing rules, and versioning.
- [`SPEC.md`](./SPEC.md): Summary reference and YAML schema quick-reference.
- [`CASE_FILE_SPEC.md`](./CASE_FILE_SPEC.md): Standardized schema and workflow for research case files and kit hypotheses.
- [`LLM_WIKI_GUIDELINES.md`](./LLM_WIKI_GUIDELINES.md): Practical anti-rot synthesis rules for autonomous LLM curators.
- [`scripts/validate_sherpa.py`](./scripts/validate_sherpa.py): Reference Python linter and validator for SherpaMD documents.

---

## Quick Example: A Minimal `SHERPA.md`

```markdown
---
schema_version: "0.1.0"
id: "sample-service"
title: "Sample Service Knowledge Kit"
domain: "infrastructure"
version: "0.1.0"
status: "active"
verification_state: "verified"
last_verified: "2026-08-21T03:26:00-05:00"
confidentiality: "public"
provenance:
  origin_task: "sample-task-001"
  author_alias: "agent-name"
  verifier_alias: "verifier-name"
sources:
  - id: "src-config"
    title: "Service Systemd Unit"
    uri: "/etc/systemd/user/sample.service"
    type: "config"
tags:
  - "sample"
  - "systemd"
related_links:
  - rel: "spec"
    uri: "https://github.com/sherpa-md/sherpa-spec"
---

# Sample Service Knowledge Kit

## 1. Purpose & Scope
High-signal overview of the service purpose and boundaries.

## 2. Core Directives
1. Always run under the user manager (`systemctl --user`).
2. Never commit live tokens or credentials.

## 3. Operational Procedures
Start or check the service:
```bash
# Verify:
systemctl --user status sample.service
```

## 4. Verification Evidence
- Verified healthy via `systemctl --user is-active sample.service` on 2026-08-21.
```

---

## Validation Tooling

SherpaMD includes a standalone validator script to lint documents and check compliance against the v0.1.0 schema:

```bash
# Validate a single file:
python3 scripts/validate_sherpa.py SHERPA.md

# Validate multiple files:
python3 scripts/validate_sherpa.py path/to/kit/SHERPA.md
```

---

## Contributing & Security

- **Contributing**: See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for contribution guidelines, schema rules, and PR workflows.
- **Security Policy**: See [`SECURITY.md`](./SECURITY.md) for vulnerability disclosure and secret containment rules.

---

## License

SherpaMD specification, schemas, and validator tooling are open source and licensed under the [MIT License](./LICENSE).
