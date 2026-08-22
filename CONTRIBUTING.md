# Contributing to SherpaMD Specification

Thank you for contributing to **SherpaMD**! This repository hosts the normative format specifications, schemas, guidelines, and reference validator tooling for the **SherpaMD** standard.

---

## Scope of Contributions

We welcome contributions in the following areas:
- **Specification Enhancements**: Clarifying schema requirements, lifecycle states, and provenance definitions.
- **Tooling & Validation**: Improving `scripts/validate_sherpa.py` or adding multi-language validator implementations.
- **Guidelines & Documentation**: Refining anti-rot practices, LLM-wiki curation patterns, and human+AI dual usability.

---

## Contribution Workflow

1. **Fork and Branch**: Create a feature branch from `main` (e.g. `feat/schema-enhancement`).
2. **Adhere to Schema Norms**: Any updates to front matter schemas must maintain backward compatibility or follow SemVer conventions.
3. **Run Validators**: Verify that all documentation and reference files pass the validator:
   ```bash
   python3 scripts/validate_sherpa.py SHERPA.md
   ```
4. **Security & Sanitization**: Ensure changes contain:
   - Zero hardcoded credentials, live API tokens, or session secrets.
   - Zero local user paths (e.g., `/home/<username>/`).
   - Zero private network identifiers or internal infrastructure topology.
5. **Submit Pull Request**: Open a PR with a clear summary of changes, rationale, and validation test output.

---

## Code & Markdown Style

- Use standard GitHub Flavored Markdown (GFM).
- Keep descriptions dense, actionable, and unambiguous for both human engineers and autonomous agents.
- Follow Python PEP 8 standards for scripts and validators.
