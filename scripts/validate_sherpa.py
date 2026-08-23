#!/usr/bin/env python3
"""
Lightweight validator / linter for SherpaMD v0.1.0 documents.
Validates YAML front matter, required fields, verification states, and source declarations.
"""

import sys
import os
import re
import yaml

REQUIRED_FIELDS = [
    "schema_version",
    "id",
    "title",
    "domain",
    "version",
    "status",
    "verification_state",
    "last_verified",
    "confidentiality",
    "provenance",
]

ALLOWED_STATUSES = ["draft", "active", "deprecated", "archived"]
ALLOWED_VERIFICATION_STATES = ["verified", "unverified", "needs-retest", "contradiction"]
ALLOWED_CONFIDENTIALITY = ["private", "internal", "restricted", "public"]

def validate_sherpa_file(filepath):
    print(f"Validating {filepath}...")
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Match YAML front matter between triple hyphens
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return False, "Missing or invalid YAML front matter block (must be enclosed between triple hyphens `---`)"

    frontmatter_raw, body_raw = match.groups()

    try:
        data = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        return False, f"YAML parsing error: {e}"

    if not isinstance(data, dict):
        return False, "Front matter must be a YAML mapping/dictionary"

    # 1. Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Missing required front matter field: `{field}`"

    # 2. Check schema_version
    if str(data.get("schema_version")) != "0.1.0":
        ver = data.get("schema_version")
        return False, f"Unsupported schema_version: `{ver}` (expected '0.1.0')"

    # 3. Check id format
    if not re.match(r"^[a-z0-9-]+$", str(data.get("id"))):
        val = data.get("id")
        return False, f"Invalid id format: `{val}` (must be kebab-case)"

    # 4. Check status
    if data.get("status") not in ALLOWED_STATUSES:
        val = data.get("status")
        return False, f"Invalid status: `{val}` (allowed: {ALLOWED_STATUSES})"

    # 5. Check verification_state
    if data.get("verification_state") not in ALLOWED_VERIFICATION_STATES:
        val = data.get("verification_state")
        return False, f"Invalid verification_state: `{val}` (allowed: {ALLOWED_VERIFICATION_STATES})"

    # 6. Check confidentiality
    if data.get("confidentiality") not in ALLOWED_CONFIDENTIALITY:
        val = data.get("confidentiality")
        return False, f"Invalid confidentiality: `{val}` (allowed: {ALLOWED_CONFIDENTIALITY})"

    # 7. Check provenance
    prov = data.get("provenance")
    if not isinstance(prov, dict) or not prov.get("author_alias"):
        return False, "Provenance must be a dict containing at least `author_alias`"

    # 8. Secret check on body and front matter
    secret_patterns = [
        r"ghp_[A-Za-z0-9_]{36}",
        r"github_pat_[A-Za-z0-9_]+",
        r"sk-[A-Za-z0-9_]{20,}",
        r"AIza[0-9A-Za-z-_]{35}",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, content):
            return False, f"Security Violation: Potential secret/token detected matching `{pattern}`"

    # 9. Markdown body check
    if not body_raw.strip():
        return False, "Markdown body is empty"

    filename = os.path.basename(filepath)
    if filename == "SHERPA.md" or not filename.endswith(".sherpa.md"):
        return False, "Filename must use <BriefDescription>.sherpa.md"

    return True, "Valid SherpaMD v0.1.0 document"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_sherpa.py <file1.md> [file2.md ...]")
        sys.exit(1)

    all_passed = True
    for path in sys.argv[1:]:
        ok, msg = validate_sherpa_file(path)
        if ok:
            print(f"  [PASS] {path}: {msg}")
        else:
            print(f"  [FAIL] {path}: {msg}")
            all_passed = False

    sys.exit(0 if all_passed else 1)
