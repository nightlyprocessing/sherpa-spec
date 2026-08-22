# SherpaMD Case File Specification (v0.1.0)

**Standard:** `SHERPAMD-CASE-FILE-0.1.0`  
**Purpose:** Standardized schema and workflow for capturing real-world user friction, persona context, root cause analysis, kit package hypotheses, and research prompts.

---

## 1. Schema Fields & Requirements

Every SherpaMD Case File is authored in Markdown with YAML front matter enclosed between triple hyphens (`---`).

| Field | Type | Required | Description / Format |
|---|---|---|---|
| `case_id` | string | **Yes** | Unique identifier matching `^case-[0-9]{3}-[a-z0-9-]+$` |
| `schema_version` | string | **Yes** | SemVer format (e.g. `0.1.0`) |
| `title` | string | **Yes** | Descriptive title summarizing the problem |
| `observed_user_pain` | string | **Yes** | Concrete failure mode or friction experienced by user |
| `persona_job` | string | **Yes** | Target role / user archetype (e.g. Software Engineer) |
| `workflow_context` | string | **Yes** | Operational workflow, tools, and operational cadence |
| `root_cause` | string | **Yes** | Structural or technical breakdown reason |
| `desired_outcome` | string | **Yes** | Target resolved state |
| `evidence_links` | list[string] | **Yes** | List of source links (Reddit, HN, community posts) |
| `risks_private_data` | string | **Yes** | Confidentiality, NDA, or compliance boundaries |
| `proposed_kit` | string | **Yes** | Target Sherpa Kit name |
| `kit_slug` | string | Optional | Canonical kebab-case kit directory slug |
| `acceptance_test` | string | **Yes** | Falsifiable test criteria to verify problem resolution |
| `status` | enum | **Yes** | `backlog`, `hypothesis-staged`, `research-queued`, `research-in-progress`, `verified`, `rejected`, `promoted-to-kit` |
| `sources_provenance` | object | **Yes** | Map containing `curator`, `batch`, `timestamp`, `verification_state` |

---

## 2. Body Structure

The Markdown body must include:
1. **Executive Summary & Problem Breakdown**
2. **Product & Kit Hypothesis Mapping**
3. **Evidence Links & Initial Scan Citations**
4. **Implementation-Ready Research Worker Prompt**
5. **Next Steps Upon Worker Pool Activation**

---

## 3. Worker Execution Lifecycle

```
[Community Scan] 
       │
       ▼
[Case File Staged] (Status: hypothesis-staged)
       │
       ▼
[Autonomous Research Worker] (Community forum and literature scan)
       │
       ▼
[Evidence Normalized] (Stored in evidence/<case-id>/raw_findings.jsonl)
       │
       ▼
[Hypothesis Evaluation] ──► Verified ──► [Promoted to Kit in sherpa-kits]
                        └──► Rejected ──► [Archived / Closed]
```
