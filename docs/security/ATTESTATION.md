# SherpaMD Attestation and Trust Policy v1

## Signed attestation

The attestation is a compact UTF-8 JSON object signed as a blob with Cosign.
The verifier checks the signature over the exact serialized bytes before it
interprets them. Duplicate JSON keys and unknown fields are rejected.

```json
{
  "type": "application/vnd.sherpamd.attestation.v1+json",
  "schema_version": 1,
  "project_id": "example-project",
  "document_id": "example-runbook",
  "artifact_role": "handoff",
  "artifact_path": "handoffs/ExampleRunbook.sherpa.md",
  "artifact_sha256": "<64 lowercase hexadecimal characters>",
  "dependencies": []
}
```

Each dependency is an object containing exactly `path` and `sha256`. Paths are
relative POSIX paths beneath the artifact root. The current verifier rejects
absolute paths, traversal, symlinks, duplicate paths, and remote fetching.
Each distributed artifact, including a handoff, must have its own role and
digest.

The sidecar Sigstore bundle contains the signature material for this exact
attestation. The bundle itself is not an instruction and does not grant
trust.

## Independently provisioned trust policy

The consumer receives a local JSON policy through a channel independent of
the artifact. It pins the expected project, document, role, path, SHA-256 of
the complete attestation bytes, exact signer identity, exact OIDC issuer,
absolute Cosign executable path and digest, and bounded artifact size.
Changing the artifact or signed dependency set requires a newly reviewed
attestation and an independently approved policy-pin update.

Example shape (replace every placeholder before use):

```json
{
  "type": "application/vnd.sherpamd.trust-policy.v1+json",
  "schema_version": 1,
  "project_id": "example-project",
  "document_id": "example-runbook",
  "artifact_role": "handoff",
  "artifact_path": "handoffs/ExampleRunbook.sherpa.md",
  "attestation_path": "handoffs/ExampleRunbook.attestation.json",
  "bundle_path": "handoffs/ExampleRunbook.sigstore.json",
  "attestation_sha256": "<64 lowercase hexadecimal characters>",
  "signer_identity": "<exact authorized signer identity>",
  "oidc_issuer": "https://token.actions.githubusercontent.com",
  "cosign_path": "/absolute/path/to/cosign",
  "cosign_sha256": "<64 lowercase hexadecimal characters>",
  "max_artifact_bytes": 10485760
}
```

## Cosign verification

The reference implementation invokes `cosign verify-blob` without a shell,
using the pinned attestation snapshot, bundle snapshot, exact certificate
identity, and exact OIDC issuer. Missing Cosign, a digest mismatch, invalid
signature, identity mismatch, timeout, malformed records, or content mismatch
must block loading. Verification failure must never emit Markdown to the
consumer.

For an authorized release, sign the finalized attestation bytes with a
Sigstore bundle, for example:

```sh
cosign sign-blob attestation.json --bundle attestation.sigstore.json
```

After independent review, provision the exact attestation digest, signer
identity, issuer, and Cosign binary digest through the consumer's trusted
policy channel. Do not derive or update the policy pin from an untrusted
artifact bundle.

The current v1 record authenticates identity, artifact bytes, and explicit
dependency bytes. It does not claim that content is safe or that tests were
run; any safety review or test claims require a later, explicitly scoped
attestation extension and evidence policy.

The current reference implementation uses POSIX directory-relative opens with
no-follow flags. It fails closed on Windows until an equivalent race-resistant
platform backend is implemented.
