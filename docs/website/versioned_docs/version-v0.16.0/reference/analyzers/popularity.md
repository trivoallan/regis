# popularity

The `popularity` analyzer provides community adoption metrics from public registries.

## Overview

- **Analyzer Name**: `popularity`
- **External API**: `https://hub.docker.com/v2/repositories` (Docker Hub)
- **Output Schema**: [`popularity.schema.json`](pathname:///regis-cli/schemas/analyzer/popularity.schema.json)

## Functionality

This analyzer fetches metadata from the Docker Hub API to determine the image's community standing:

- **Pull Count**: Total number of downloads.
- **Star Count**: Number of stars given by users.
- **Is Official**: Whether the image is part of the Docker Hub "Official Images" program.
- **Last Updated**: The date the repository was last updated.
