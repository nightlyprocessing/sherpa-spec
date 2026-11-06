# SherpaMD Verified Loading Threat Model (v1)

## Purpose

SherpaMD files may contain operational procedures and instructions that are
passed to people or AI agents. Structural validity and a front matter value
such as `verification_state: verified` do not authenticate the author, prove
review, or establish that the file is safe.

The verified-loading reference package establishes whether the consumer has
received the exact locally approved artifact bytes from an independently
authorized signer. It returns those verified bytes in memory so a caller can
avoid reopening an unchecked path.

## Protected properties

- The exact Markdown bytes, including front matter, are bound to a SHA-256
  digest in a signed attestation.
- The attestation signature is checked against one exact signer identity and
  OIDC issuer configured by trusted local policy.
- The attestation digest is pinned by that policy, binding the artifact role,
  identity, path, and dependency list.
- Dependencies are explicit, local, separately hashed files. The verifier
  never downloads or follows arbitrary references.
- Parsing, paths, file sizes, and signature execution are bounded. Failure
  blocks loading.

## Out of scope

- A valid signature does not prove that the signer is honest, the review was
  competent, or the instructions are safe.
- This package cannot protect an agent if its host bypasses the verified
  loader, independently fetches instructions, or grants excessive tools,
  credentials, or operating-system permissions.
- A signature does not prevent denial of service, compromised hosts, a
  compromised authorized signing workflow, or malicious content in sources
  fetched later by an agent.
- A manual policy pin does not provide automatic freshness, revocation
  discovery, or rollback protection. Policy updates require an independently
  trusted channel.
- User-supplied parameters remain untrusted data and must not be promoted to
  instructions or interpolated into commands without safe, typed handling.

## Required consumer behavior

Consumers must pass only the returned immutable `VerifiedArtifact.content`
and explicitly selected verified dependency bytes into an instruction
channel. They must not reopen source paths after verification. Hosts must
prevent any alternate instruction-ingestion path from bypassing this API and
must enforce least privilege independently of file verification.
