---
schema_version: "0.1.0"
id: "sherpa-spec-normative"
title: "SherpaMD Format Specification v0.1.0"
domain: "specification"
version: "0.1.0"
status: "active"
verification_state: "verified"
last_verified: "2026-08-21T03:26:00-05:00"
confidentiality: "public"
provenance:
  origin_task: "task-spec-001"
  author_alias: "sherpa-core"
  verifier_alias: "sherpa-core"
sources:
  - id: "src-karpathy-wiki"
    title: "Andrej Karpathy LLM Wiki Concept"
    uri: "./LLM_WIKI_GUIDELINES.md"
    type: "design_concept"
tags:
  - "sherpa-spec"
  - "schema"
  - "standard"
related_links:
  - rel: "template"
    uri: "https://github.com/sherpa-md/sherpa-kit-template"
  - rel: "kits"
    uri: "https://github.com/sherpa-md/sherpa-kits"
---

# SherpaMD Format Specification (v0.1.0)

`SHERPA.md` is the canonical file format and knowledge schema for **SherpaMD** (`sherpamd.org`). It specifies how human operators and autonomous AI agents author, maintain, verify, and cross-reference structured operational knowledge.

---

## 1. Purpose & Philosophy

SherpaMD addresses the fundamental challenge of **context rot and unstructured transcript accumulation** in multi-agent AI workflows.

Traditional AI workflows tend to either:
1. Append raw chat logs and transcripts endlessly, leading to context bloat and contradictory instructions.
2. Store ephemeral prompt instructions that lack provenance, verification history, and explicit boundaries.

**SherpaMD provides:**
- **Deterministic AI and Human Readability**: High-signal, plain Markdown format that is equally readable by human engineers and parseable by autonomous LLMs.
- **In-Place Knowledge Synthesis (Karpathy LLM-Wiki Pattern)**: Continuous distillation and in-place updating of durable facts instead of transcript dumps.
- **Auditable Provenance & Verification**: Every directive, procedure, and architecture map carries explicit verification states, test commands, and source traceability.
- **Strict Secret Hygiene**: Zero containment tolerance against committing live credentials, tokens, or sensitive system internals.

---

## 2. YAML Front Matter Schema

Every compliant `SHERPA.md` file MUST begin with a YAML front matter block enclosed between triple hyphens (`---`).

### Schema Definition (v0.1.0)

```yaml
---
schema_version: "0.1.0"
id: "sample-llm-wiki"
title: "Sample LLM Wiki & Knowledge Architecture"
domain: "knowledge-architecture"
version: "0.1.0"
status: "active"
verification_state: "verified"
last_verified: "2026-08-21T03:26:00-05:00"
confidentiality: "public"
provenance:
  origin_task: "task-spec-001"
  author_alias: "sherpa-core"
  verifier_alias: "sherpa-core"
sources:
  - id: "src-arch-protocol"
    title: "Architecture Protocol Specification"
    uri: "./sources/architecture-spec.md"
    type: "protocol_spec"
  - id: "src-karpathy-wiki"
    title: "Andrej Karpathy LLM Wiki Pattern"
    uri: "./sources/karpathy-llm-wiki-concept.md"
    type: "design_concept"
tags:
  - "architecture"
  - "llm-wiki"
  - "knowledge-graph"
  - "spec"
related_links:
  - rel: "spec"
    uri: "https://github.com/sherpa-md/sherpa-spec"
  - rel: "template"
    uri: "https://github.com/sherpa-md/sherpa-kit-template"
---
```

### Field Specifications

| Field | Type | Required | Allowed Values / Format | Description |
|---|---|---|---|---|
| `schema_version` | string | **Yes** | `"0.1.0"` | The version of the SherpaMD specification schema. |
| `id` | string | **Yes** | `^[a-z0-9-]+$` | Unique kebab-case identifier for the knowledge kit/document. |
| `title` | string | **Yes** | Text | Concise human-readable title. |
| `domain` | string | **Yes** | `^[a-z0-9-]+$` | Functional domain category (e.g. `infrastructure`, `knowledge-graph`, `operations`). |
| `version` | string | **Yes** | SemVer (e.g. `"0.1.0"`) | Semantic version of the document's contents. |
| `status` | string | **Yes** | `"draft"`, `"active"`, `"deprecated"`, `"archived"` | Lifecycle state of this knowledge document. |
| `verification_state` | string | **Yes** | `"verified"`, `"unverified"`, `"needs-retest"`, `"contradiction"` | Current factual validation state. |
| `last_verified` | string | **Yes** | ISO 8601 Timestamp | Timestamp when the contents were last validated against ground truth. |
| `confidentiality` | string | **Yes** | `"public"`, `"internal"`, `"restricted"`, `"private"` | Access tier (default for public domain kits is `"public"`). |
| `provenance` | object | **Yes** | Key-value map | Tracks `origin_task`, `author_alias`, and `verifier_alias`. |
| `sources` | list | Optional | List of source objects | Upstream inputs, references, raw data files, or design docs. |
| `tags` | list | Optional | List of strings | Keywords for search and catalog indexing. |
| `related_links` | list | Optional | List of link objects | References to related kits, external URLs, or sub-documents. |

---


### Canonical and Shareable Filenames

- The canonical entrypoint inside every kit remains `SHERPA.md`.
- A handoff intended to be sent directly MUST use `<BriefDescription>.sherpa.md`.
- `<BriefDescription>` should state the outcome before the file is opened, preserve useful acronyms, and omit dates, versions, and workflow jargon.
- Directly shareable files should be collected under a `handoffs/` directory so they can be bundled without unrelated kit internals.
- Examples: `BOMbilling.sherpa.md`, `ComputerGithubSetup.sherpa.md`, and `TokenPiggyBank.sherpa.md`.

## 3. Sources & Provenance

SherpaMD documents MUST clearly distinguish between **synthesized knowledge** and **raw source evidence**:
1. **Raw Sources**: Kept in a dedicated `sources/` subdirectory (or linked via URI). Sources include raw log excerpts, system dumps, protocol docs, or human notes.
2. **Provenance Tracking**: Each source declared in front matter MUST have a unique `id` and descriptive title.
3. **In-Body Attribution**: Statements derived from specific sources should cite the source ID (e.g. `[^src-arch-protocol]`).

---

## 4. Verification States & Lifecycle

Every claim, configuration, and procedure within a Sherpa kit MUST reflect its verification reality.

### Verification States

- `verified`: Tested and confirmed against live systems or authoritative code within the verification window. Includes explicit test commands and output proof.
- `unverified`: Proposed or synthesized content that has not yet been executed or confirmed against live infrastructure.
- `needs-retest`: Previously verified information where underlying systems, dependencies, or environment versions have changed.
- `contradiction`: Incompatible facts or instructions exist between sources or previous versions. Requires immediate reconciliation.

### Verification Command Annotation

Procedures in the Markdown body should include runnable verification snippets:
```bash
# Verify:
python3 scripts/validate_sherpa.py SHERPA.md
```

---

## 5. Related Links & Graph Relationships

SherpaMD documents form an interconnected knowledge graph. Links are expressed through:
- **Front Matter `related_links`**: Explicit relational mappings (`rel: "extends"`, `rel: "depends-on"`, `rel: "supersedes"`, `rel: "spec"`).
- **Markdown Cross-References**: Relative links to other domain kits (e.g. `[Core Fleet](../core-fleet/SHERPA.md)` or `[Template](../../sherpa-kit-template/SHERPA.md)`).
- **Section Anchors**: Deep links to specific procedural headers.

---

## 6. Contradiction Notes & Reconciliations

When multiple data sources, previous instructions, or team guidelines conflict:
1. **Do not silently overwrite or ignore the discrepancy.**
2. Add a dedicated `## Contradiction Notes & Reconciliations` section.
3. Record:
   - **Observed Conflict**: The divergent claims.
   - **Source Comparison**: Which source stated what and when.
   - **Resolution / Ground Truth**: The verified outcome and rationale.
   - **Escalation Marker**: If unresolved, mark `verification_state: "contradiction"` and issue a `NEEDS-APPROVAL` or `BLOCKED` notification to operators.

---

## 7. Editing Rules & Anti-Rot Guidance (Karpathy LLM-Wiki Pattern)

Agents and human editors MUST adhere to the following editing rules:

1. **Synthesis Over Transcript Dumps**: Never dump raw session chat logs into a Sherpa kit. Extract the distilled facts, configuration parameters, and verified scripts.
2. **In-Place Updates**: When a port, URL, or procedure changes, modify the existing section in place. Delete obsolete instructions.
3. **Strict Secret Hygiene**: NEVER commit API keys, passwords, bearer tokens, or sensitive auth files. Replace all secrets with `[REDACTED]` or environment variable names (e.g. `$API_KEY`).
4. **Inspectability**: Keep markdown plain, readable, and well-structured with GitHub Flavored Markdown (GFM). Avoid custom non-standard markup.
5. **Durable Artifacts**: Store transient runtime outputs under `./artifacts/<task-id>/` or external store and link only the durable synthesis into the kit.

---

## 8. Versioning & Evolution

- **Specification Versioning**: The SherpaMD format specification adheres to SemVer (`v0.1.0`).
- **Kit Content Versioning**: Individual kits track their own `version` in front matter (`v0.1.0` -> `v0.2.0` on major workflow changes; `v0.1.1` on patch fixes).
- **Changelog Records**: Significant structural revisions should be recorded in a concise `## Revision History` table at the end of the document.
