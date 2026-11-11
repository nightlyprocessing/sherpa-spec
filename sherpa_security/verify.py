"""Verify a pinned Cosign-signed SherpaMD attestation before returning bytes.

This module authenticates an exact artifact and its explicitly declared local
dependencies. It does not determine whether authenticated instructions are
benign or constrain what a consuming agent can do with them.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Any

import yaml


POLICY_TYPE = "application/vnd.sherpamd.trust-policy.v1+json"
ATTESTATION_TYPE = "application/vnd.sherpamd.attestation.v1+json"
MAX_POLICY_BYTES = 64 * 1024
MAX_ATTESTATION_BYTES = 1024 * 1024
MAX_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_FRONT_MATTER_BYTES = 64 * 1024
MAX_DEPENDENCIES = 128
MAX_PATH_LENGTH = 1024
COSIGN_TIMEOUT_SECONDS = 30
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class VerificationError(Exception):
    """A bounded, fail-closed verification error suitable for a CLI message."""


@dataclass(frozen=True)
class TrustPolicy:
    project_id: str
    document_id: str
    artifact_role: str
    artifact_path: str
    attestation_path: str
    bundle_path: str
    attestation_sha256: str
    signer_identity: str
    oidc_issuer: str
    cosign_path: str
    cosign_sha256: str
    max_artifact_bytes: int = 10 * 1024 * 1024


@dataclass(frozen=True)
class VerifiedArtifact:
    """Immutable byte snapshots that passed the configured trust checks."""

    project_id: str
    document_id: str
    artifact_role: str
    artifact_path: str
    sha256: str
    content: bytes
    dependencies: tuple[tuple[str, str, bytes], ...]

    @property
    def text(self) -> str:
        """Return strict UTF-8 text from the already verified byte snapshot."""
        try:
            return self.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise VerificationError("Verified artifact is not valid UTF-8") from exc


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_reject_duplicate_json_keys)
    except VerificationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must be a JSON object")
    return value


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_LENGTH:
        raise VerificationError(f"{field} must be a nonempty relative path")
    if "\\" in value or value.startswith("/") or "\x00" in value:
        raise VerificationError(f"{field} must use a normalized relative POSIX path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise VerificationError(f"{field} contains an unsafe path component")
    return value


def _require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise VerificationError(f"{field} is invalid")
    return value


def _require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX_SHA256.fullmatch(value):
        raise VerificationError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _secure_read(root: Path, relative_path: str, limit: int) -> bytes:
    """Read a regular file beneath root without following any symlink.

    Requires POSIX directory-relative opens. Unsupported platforms fail closed
    until an equivalent race-resistant implementation is available.
    """
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise VerificationError("Secure local loading currently requires POSIX no-follow file opens")
    relative_path = _safe_relative_path(relative_path, "path")
    root_path = Path(os.path.abspath(root))
    root_fd = None
    current_fd = None
    opened_fds: list[int] = []
    try:
        root_fd = os.open(root_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        current_fd = root_fd
        parts = relative_path.split("/")
        for component in parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current_fd)
            opened_fds.append(next_fd)
            current_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current_fd)
        opened_fds.append(file_fd)
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise VerificationError(f"Not a regular file: {relative_path}")
        if metadata.st_size > limit:
            raise VerificationError(f"File exceeds the size limit: {relative_path}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(file_fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise VerificationError(f"File exceeds the size limit: {relative_path}")
        return b"".join(chunks)
    except VerificationError:
        raise
    except OSError as exc:
        raise VerificationError(f"Unable to safely read {relative_path}") from exc
    finally:
        for fd in reversed(opened_fds):
            os.close(fd)
        if root_fd is not None:
            os.close(root_fd)


def _load_yaml_front_matter(raw: bytes, expected_document_id: str) -> None:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerificationError("Artifact is not valid UTF-8") from exc
    if not text.startswith("---\n"):
        raise VerificationError("Artifact must begin with YAML front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise VerificationError("Artifact has no closing YAML front matter delimiter")
    if end > MAX_FRONT_MATTER_BYTES:
        raise VerificationError("YAML front matter exceeds the size limit")

    class UniqueKeyLoader(yaml.SafeLoader):
        def __init__(self, stream: str) -> None:
            super().__init__(stream)
            self._nesting = 0

        def compose_node(self, parent: Any, index: Any) -> yaml.Node:
            if self.check_event(yaml.AliasEvent):
                raise VerificationError("YAML aliases are not allowed in secure mode")
            self._nesting += 1
            try:
                if self._nesting > 64:
                    raise VerificationError("YAML nesting exceeds the supported limit")
                return super().compose_node(parent, index)
            finally:
                self._nesting -= 1

    def construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise VerificationError(f"Duplicate YAML front matter key: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        metadata = yaml.load(text[4:end], Loader=UniqueKeyLoader)
    except VerificationError:
        raise
    except (yaml.YAMLError, TypeError, ValueError) as exc:
        raise VerificationError("Invalid YAML front matter") from exc
    if not isinstance(metadata, dict):
        raise VerificationError("YAML front matter must be a mapping")
    if metadata.get("schema_version") != "0.1.0":
        raise VerificationError("Unsupported SherpaMD schema_version")
    if metadata.get("id") != expected_document_id:
        raise VerificationError("SherpaMD front matter id does not match trusted policy")


def _parse_policy(raw: bytes) -> TrustPolicy:
    data = _parse_json(raw, "Trust policy")
    required = {
        "type", "schema_version", "project_id", "document_id", "artifact_role",
        "artifact_path", "attestation_path", "bundle_path", "attestation_sha256",
        "signer_identity", "oidc_issuer", "cosign_path", "cosign_sha256",
    }
    allowed = required | {"max_artifact_bytes"}
    if set(data) - allowed or required - set(data):
        raise VerificationError("Trust policy has missing or unsupported fields")
    if data["type"] != POLICY_TYPE or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise VerificationError("Unsupported trust-policy type or schema version")
    project_id = _require_identifier(data["project_id"], "project_id")
    document_id = _require_identifier(data["document_id"], "document_id")
    artifact_role = _require_identifier(data["artifact_role"], "artifact_role")
    artifact_path = _safe_relative_path(data["artifact_path"], "artifact_path")
    attestation_path = _safe_relative_path(data["attestation_path"], "attestation_path")
    bundle_path = _safe_relative_path(data["bundle_path"], "bundle_path")
    if len({artifact_path, attestation_path, bundle_path}) != 3:
        raise VerificationError("Artifact, attestation, and bundle paths must be distinct")
    signer_identity = data["signer_identity"]
    oidc_issuer = data["oidc_issuer"]
    if not isinstance(signer_identity, str) or not signer_identity or len(signer_identity) > 2048:
        raise VerificationError("signer_identity is invalid")
    if not isinstance(oidc_issuer, str) or not oidc_issuer.startswith("https://") or len(oidc_issuer) > 2048:
        raise VerificationError("oidc_issuer must be an exact HTTPS issuer")
    cosign_path = data["cosign_path"]
    if not isinstance(cosign_path, str) or not os.path.isabs(cosign_path):
        raise VerificationError("cosign_path must be an absolute executable path")
    max_artifact_bytes = data.get("max_artifact_bytes", 10 * 1024 * 1024)
    if type(max_artifact_bytes) is not int or not 1 <= max_artifact_bytes <= 100 * 1024 * 1024:
        raise VerificationError("max_artifact_bytes is outside the supported bound")
    return TrustPolicy(
        project_id=project_id,
        document_id=document_id,
        artifact_role=artifact_role,
        artifact_path=artifact_path,
        attestation_path=attestation_path,
        bundle_path=bundle_path,
        attestation_sha256=_require_digest(data["attestation_sha256"], "attestation_sha256"),
        signer_identity=signer_identity,
        oidc_issuer=oidc_issuer,
        cosign_path=cosign_path,
        cosign_sha256=_require_digest(data["cosign_sha256"], "cosign_sha256"),
        max_artifact_bytes=max_artifact_bytes,
    )


def load_trust_policy(path: str | os.PathLike[str]) -> TrustPolicy:
    """Load a small policy file; its location and integrity are host responsibilities."""
    policy_path = Path(path)
    try:
        if policy_path.is_symlink() or not policy_path.is_file() or policy_path.stat().st_size > MAX_POLICY_BYTES:
            raise VerificationError("Trust policy must be a bounded regular file, not a symlink")
        raw = policy_path.read_bytes()
    except VerificationError:
        raise
    except OSError as exc:
        raise VerificationError("Unable to read trust policy") from exc
    if len(raw) > MAX_POLICY_BYTES:
        raise VerificationError("Trust policy exceeds the size limit")
    return _parse_policy(raw)


def _parse_attestation(raw: bytes) -> dict[str, Any]:
    data = _parse_json(raw, "Attestation")
    required = {
        "type", "schema_version", "project_id", "document_id", "artifact_role",
        "artifact_path", "artifact_sha256", "dependencies",
    }
    if set(data) != required:
        raise VerificationError("Attestation has missing or unsupported fields")
    if data["type"] != ATTESTATION_TYPE or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise VerificationError("Unsupported attestation type or schema version")
    for field in ("project_id", "document_id", "artifact_role"):
        _require_identifier(data[field], field)
    _safe_relative_path(data["artifact_path"], "artifact_path")
    _require_digest(data["artifact_sha256"], "artifact_sha256")
    dependencies = data["dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
        raise VerificationError("Attestation dependencies must be a bounded array")
    seen: set[str] = set()
    for dependency in dependencies:
        if not isinstance(dependency, dict) or set(dependency) != {"path", "sha256"}:
            raise VerificationError("Each dependency must contain only path and sha256")
        path = _safe_relative_path(dependency["path"], "dependency path")
        _require_digest(dependency["sha256"], "dependency sha256")
        if path in seen or path == data["artifact_path"]:
            raise VerificationError("Attestation contains a duplicate or self-referential dependency")
        seen.add(path)
    return data


def _verify_cosign(attestation: bytes, bundle: bytes, policy: TrustPolicy) -> None:
    executable = Path(policy.cosign_path)
    try:
        if executable.is_symlink() or not executable.is_file():
            raise VerificationError("Configured Cosign executable is not a regular file")
        digest = hashlib.sha256()
        with executable.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        executable_digest = digest.hexdigest()
    except VerificationError:
        raise
    except OSError as exc:
        raise VerificationError("Unable to read configured Cosign executable") from exc
    if executable_digest != policy.cosign_sha256:
        raise VerificationError("Configured Cosign executable digest does not match policy")

    with tempfile.TemporaryDirectory(prefix="sherpa-verify-") as temp_dir:
        attestation_file = Path(temp_dir) / "attestation.json"
        bundle_file = Path(temp_dir) / "bundle.json"
        isolated_home = Path(temp_dir) / "home"
        isolated_home.mkdir()
        attestation_file.write_bytes(attestation)
        bundle_file.write_bytes(bundle)
        command = [
            str(executable), "verify-blob", str(attestation_file),
            "--bundle", str(bundle_file),
            "--certificate-identity", policy.signer_identity,
            "--certificate-oidc-issuer", policy.oidc_issuer,
        ]
        try:
            result = subprocess.run(
                command, shell=False, check=False, capture_output=True,
                timeout=COSIGN_TIMEOUT_SECONDS, text=False,
                env={"PATH": str(executable.parent), "HOME": str(isolated_home)},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VerificationError("Cosign could not complete within the configured limit") from exc
        if result.returncode != 0:
            raise VerificationError("Cosign signature or signer identity verification failed")


def load_verified(root: str | os.PathLike[str], policy: TrustPolicy) -> VerifiedArtifact:
    """Verify signature, signer, pin, identity, and bytes before returning content."""
    root_path = Path(root)
    try:
        if root_path.is_symlink() or not root_path.is_dir():
            raise VerificationError("Artifact root must be a directory, not a symlink")
    except OSError as exc:
        raise VerificationError("Unable to access artifact root") from exc

    attestation_bytes = _secure_read(root_path, policy.attestation_path, MAX_ATTESTATION_BYTES)
    bundle_bytes = _secure_read(root_path, policy.bundle_path, MAX_BUNDLE_BYTES)
    if hashlib.sha256(attestation_bytes).hexdigest() != policy.attestation_sha256:
        raise VerificationError("Attestation digest does not match the independently pinned policy")
    _verify_cosign(attestation_bytes, bundle_bytes, policy)

    attestation = _parse_attestation(attestation_bytes)
    expected_identity = {
        "project_id": policy.project_id,
        "document_id": policy.document_id,
        "artifact_role": policy.artifact_role,
        "artifact_path": policy.artifact_path,
    }
    if any(attestation[key] != value for key, value in expected_identity.items()):
        raise VerificationError("Signed attestation identity does not match trusted policy")

    content = _secure_read(root_path, policy.artifact_path, policy.max_artifact_bytes)
    content_sha256 = hashlib.sha256(content).hexdigest()
    if content_sha256 != attestation["artifact_sha256"]:
        raise VerificationError("Artifact bytes do not match the signed attestation")
    _load_yaml_front_matter(content, policy.document_id)

    dependencies: list[tuple[str, str, bytes]] = []
    for dependency in attestation["dependencies"]:
        if dependency["path"] in {policy.artifact_path, policy.attestation_path, policy.bundle_path}:
            raise VerificationError("A declared dependency collides with an artifact sidecar path")
        dependency_bytes = _secure_read(root_path, dependency["path"], policy.max_artifact_bytes)
        dependency_sha256 = hashlib.sha256(dependency_bytes).hexdigest()
        if dependency_sha256 != dependency["sha256"]:
            raise VerificationError(f"Dependency bytes do not match attestation: {dependency['path']}")
        dependencies.append((dependency["path"], dependency_sha256, dependency_bytes))

    return VerifiedArtifact(
        project_id=policy.project_id,
        document_id=policy.document_id,
        artifact_role=policy.artifact_role,
        artifact_path=policy.artifact_path,
        sha256=content_sha256,
        content=content,
        dependencies=tuple(dependencies),
    )
