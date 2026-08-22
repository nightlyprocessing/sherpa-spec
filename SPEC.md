# SHERPA.md Format Quick Reference (v0.1.0)

For the full normative specification, see [`SHERPA.md`](./SHERPA.md).

## Front Matter Schema Reference

```yaml
---
schema_version: "0.1.0"
id: "<kebab-case-domain-id>"
title: "<Human Readable Title>"
domain: "<category-name>"
version: "0.1.0"
status: "active"                  # draft | active | deprecated | archived
verification_state: "verified"    # verified | unverified | needs-retest | contradiction
last_verified: "YYYY-MM-DDTHH:MM:SSZ"
confidentiality: "public"         # public | internal | restricted | private
provenance:
  origin_task: "<task-or-source-id>"
  author_alias: "<agent-alias-or-name>"
  verifier_alias: "<verifier-agent-alias>"
sources:
  - id: "<source-id>"
    title: "<Source Title>"
    uri: "<relative-or-absolute-uri>"
    type: "<source-type>"
tags:
  - "<keyword-1>"
  - "<keyword-2>"
related_links:
  - rel: "spec"
    uri: "https://github.com/sherpa-md/sherpa-spec"
---
```

## Standard Document Sections

1. `# [Title]`
2. `## 1. Purpose & Scope`
3. `## 2. Core Directives & Rules`
4. `## 3. Knowledge Graph & Architecture`
5. `## 4. Operational Procedures & Commands`
6. `## 5. Contradiction Notes & Reconciliations`
7. `## 6. Related Links & Dependencies`
8. `## 7. Verification & Audit Evidence`
9. `## 8. Revision History`


## Shareable Filename Convention

The canonical kit entrypoint is `SHERPA.md`. A handoff meant to be sent directly uses:

```text
<BriefDescription>.sherpa.md
```

The brief description states the outcome before the file is opened. Collect these files under `handoffs/` when producing a bundle.
