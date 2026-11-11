"""Command line entry point for authenticated SherpaMD loading."""

from __future__ import annotations

import argparse
import sys

from .verify import VerificationError, load_trust_policy, load_verified


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and load one trusted SherpaMD artifact")
    parser.add_argument("--root", required=True, help="Local artifact directory")
    parser.add_argument("--policy", required=True, help="Independently trusted local JSON policy")
    parser.add_argument("--emit", action="store_true", help="Write verified Markdown bytes to stdout")
    args = parser.parse_args()
    try:
        policy = load_trust_policy(args.policy)
        artifact = load_verified(args.root, policy)
    except VerificationError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.emit:
        sys.stdout.buffer.write(artifact.content)
    else:
        print(f"VERIFIED {artifact.project_id}/{artifact.document_id} sha256:{artifact.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
