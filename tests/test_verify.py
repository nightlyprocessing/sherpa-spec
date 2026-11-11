"""Security regression tests for verified SherpaMD loading.

Cryptographic verifier calls are mocked here to isolate artifact and policy
validation. These tests do NOT establish that real Cosign signatures validate.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sherpa_security.verify import (
    ATTESTATION_TYPE, POLICY_TYPE, VerificationError,
    _parse_attestation, _parse_policy, _secure_read, load_verified,
    load_trust_policy,
)


def digest(value):
    return hashlib.sha256(value).hexdigest()


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.document = b'---\nschema_version: "0.1.0"\nid: "doc-1"\n---\n# Instructions\n'
        self.dependency = b"approved dependency"
        self.attestation = {
            "type": ATTESTATION_TYPE,
            "schema_version": 1,
            "project_id": "project-1",
            "document_id": "doc-1",
            "artifact_role": "handoff",
            "artifact_path": "docs/doc.sherpa.md",
            "artifact_sha256": digest(self.document),
            "dependencies": [{"path": "docs/source.txt", "sha256": digest(self.dependency)}],
        }
        (self.root / "docs").mkdir()
        (self.root / "docs/doc.sherpa.md").write_bytes(self.document)
        (self.root / "docs/source.txt").write_bytes(self.dependency)
        (self.root / "attestation.json").write_bytes(self.attestation_bytes())
        (self.root / "bundle.json").write_bytes(b"test-bundle")
        self.policy_data = {
            "type": POLICY_TYPE,
            "schema_version": 1,
            "project_id": "project-1",
            "document_id": "doc-1",
            "artifact_role": "handoff",
            "artifact_path": "docs/doc.sherpa.md",
            "attestation_path": "attestation.json",
            "bundle_path": "bundle.json",
            "attestation_sha256": digest(self.attestation_bytes()),
            "signer_identity": "release@example.org",
            "oidc_issuer": "https://issuer.example.org",
            "cosign_path": "/usr/bin/cosign",
            "cosign_sha256": "a" * 64,
        }

    def attestation_bytes(self):
        return json.dumps(self.attestation, sort_keys=True).encode()

    def policy(self):
        return _parse_policy(json.dumps(self.policy_data).encode())

    def load(self):
        # Mock only signature verification, never any digest or file read.
        with patch("sherpa_security.verify._verify_cosign"):
            return load_verified(self.root, self.policy())

    def test_verified_snapshot_contains_exact_bytes(self):
        artifact = self.load()
        self.assertEqual(artifact.content, self.document)
        self.assertEqual(artifact.dependencies, (("docs/source.txt", digest(self.dependency), self.dependency),))
        self.assertEqual(artifact.text.encode(), self.document)

    def test_artifact_mutation_fails_closed(self):
        (self.root / "docs/doc.sherpa.md").write_bytes(self.document + b"untrusted")
        with self.assertRaisesRegex(VerificationError, "Artifact bytes"):
            self.load()

    def test_dependency_mutation_fails_closed(self):
        (self.root / "docs/source.txt").write_bytes(b"tampered")
        with self.assertRaisesRegex(VerificationError, "Dependency bytes"):
            self.load()

    def test_unpinned_attestation_fails_before_cosign(self):
        (self.root / "attestation.json").write_bytes(self.attestation_bytes() + b" ")
        with patch("sherpa_security.verify._verify_cosign") as verifier:
            with self.assertRaisesRegex(VerificationError, "Attestation digest"):
                load_verified(self.root, self.policy())
            verifier.assert_not_called()

    def test_invalid_signature_fails_closed(self):
        with patch("sherpa_security.verify._verify_cosign", side_effect=VerificationError("invalid signature")):
            with self.assertRaisesRegex(VerificationError, "invalid signature"):
                load_verified(self.root, self.policy())

    def test_wrong_signed_identity_fails_closed(self):
        self.attestation["document_id"] = "different"
        (self.root / "attestation.json").write_bytes(self.attestation_bytes())
        self.policy_data["attestation_sha256"] = digest(self.attestation_bytes())
        with self.assertRaisesRegex(VerificationError, "identity"):
            self.load()

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(VerificationError, "Duplicate JSON key"):
            _parse_attestation(b'{"type":"one","type":"two"}')

    def test_unknown_attestation_fields_are_rejected(self):
        self.attestation["extra"] = "unexpected"
        with self.assertRaisesRegex(VerificationError, "unsupported fields"):
            _parse_attestation(self.attestation_bytes())

    def test_traversal_and_absolute_paths_are_rejected(self):
        for bad in ("../escape", "docs/../escape", "/etc/passwd", "docs//file", "docs/./file", "docs\\file"):
            with self.subTest(path=bad):
                data = dict(self.policy_data, artifact_path=bad)
                with self.assertRaises(VerificationError):
                    _parse_policy(json.dumps(data).encode())

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "requires POSIX secure reads")
    def test_symlink_artifact_is_rejected(self):
        target = self.root / "docs/doc.sherpa.md"
        target.unlink()
        target.symlink_to(self.root / "docs/source.txt")
        with self.assertRaises(VerificationError):
            self.load()

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "requires POSIX secure reads")
    def test_symlink_parent_directory_is_rejected(self):
        (self.root / "docs/doc.sherpa.md").rename(self.root / "doc.sherpa.md")
        (self.root / "docs/source.txt").rename(self.root / "source.txt")
        (self.root / "docs").rmdir()
        (self.root / "docs").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(VerificationError):
            self.load()

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "requires POSIX secure reads")
    def test_file_size_limit(self):
        with self.assertRaisesRegex(VerificationError, "size limit"):
            _secure_read(self.root, "docs/doc.sherpa.md", 2)

    def test_duplicate_yaml_keys_are_rejected(self):
        changed = b'---\nschema_version: "0.1.0"\nid: "doc-1"\nid: "doc-1"\n---\n'
        (self.root / "docs/doc.sherpa.md").write_bytes(changed)
        self.attestation["artifact_sha256"] = digest(changed)
        (self.root / "attestation.json").write_bytes(self.attestation_bytes())
        self.policy_data["attestation_sha256"] = digest(self.attestation_bytes())
        with self.assertRaisesRegex(VerificationError, "Duplicate YAML"):
            self.load()

    def test_policy_symlink_is_rejected(self):
        actual = self.root / "real-policy.json"
        actual.write_text(json.dumps(self.policy_data))
        link = self.root / "policy-link.json"
        link.symlink_to(actual)
        with self.assertRaises(VerificationError):
            load_trust_policy(link)

    def test_boolean_size_is_not_accepted_as_integer(self):
        data = dict(self.policy_data, max_artifact_bytes=True)
        with self.assertRaisesRegex(VerificationError, "outside the supported bound"):
            _parse_policy(json.dumps(data).encode())

    def test_dependency_collision_with_sidecar_fails_closed(self):
        self.attestation["dependencies"] = [{"path": "bundle.json", "sha256": digest(b"test-bundle")}]
        (self.root / "attestation.json").write_bytes(self.attestation_bytes())
        self.policy_data["attestation_sha256"] = digest(self.attestation_bytes())
        with self.assertRaisesRegex(VerificationError, "collides"):
            self.load()


if __name__ == "__main__":
    unittest.main()
