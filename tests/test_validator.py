import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from validate_sherpa import validate_sherpa_file

class TestSherpaValidator(unittest.TestCase):
    def test_valid_normative_spec(self):
        spec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SHERPA.md"))
        ok, msg = validate_sherpa_file(spec_path)
        self.assertTrue(ok, f"Validation failed on SHERPA.md: {msg}")

    def test_missing_field(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("---\nschema_version: '0.1.0'\n---\n# Body")
            tmp_name = f.name
        try:
            ok, msg = validate_sherpa_file(tmp_name)
            self.assertFalse(ok)
            self.assertIn("Missing required front matter field", msg)
        finally:
            os.remove(tmp_name)

    def test_secret_detection(self):
        import tempfile
        dummy_secret = "ghp_" + "A" * 36
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(f"""---
schema_version: "0.1.0"
id: "test-doc"
title: "Test"
domain: "testing"
version: "0.1.0"
status: "active"
verification_state: "verified"
last_verified: "2026-08-21T00:00:00Z"
confidentiality: "public"
provenance:
  author_alias: "tester"
---
# Test Body
Token: {dummy_secret}
""")
            tmp_name = f.name
        try:
            ok, msg = validate_sherpa_file(tmp_name)
            self.assertFalse(ok)
            self.assertIn("Security Violation", msg)
        finally:
            os.remove(tmp_name)

if __name__ == "__main__":
    unittest.main()
