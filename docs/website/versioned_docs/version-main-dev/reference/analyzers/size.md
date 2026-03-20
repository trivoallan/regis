# size

The `size` analyzer provides a detailed breakdown of an image's compressed size.

## Overview

- **Analyzer Name**: `size`
- **Tool Dependency**: `skopeo`
- **Output Schema**: [`size.schema.json`](pathname:///regis-cli/schemas/analyzer/size.schema.json)

## Functionality

Size is a critical factor for container performance and security. This analyzer reports:

- **Total Compressed Size**: Total bytes for the image manifest.
- **Layer Breakdown**: Every image layer index with its specific digest and size.
- **Multi-arch Support**: Aggregates size metrics for all supported platforms in a manifest index.
- **Config Size**: Separates the image configuration blob from the content layers.
