# provenance

The `provenance` analyzer checks for SLSA (Supply-chain Levels for Software Artifacts) provenance and build attestations.

## Overview

- **Analyzer Name**: `provenance`
- **Output Schema**: [`provenance.schema.json`](pathname:///regis-cli/schemas/analyzer/provenance.schema.json)

## Functionality

This analyzer searches for evidence of secure software supply chain practices:

1.  **OCI Labels**: Looks for standard OCI labels such as `org.opencontainers.image.source` and `org.opencontainers.image.revision`.
2.  **BuildKit Metadata**: Detects build-time information embedded by Docker BuildKit.
3.  **Cosign Signatures**: Attempts to find [cosign](https://github.com/sigstore/cosign) signatures in the registry associated with the image digest.
4.  **Attestation Detection**: Identifies `in-toto` or `dsse` envelopes that might contain build attestations.
