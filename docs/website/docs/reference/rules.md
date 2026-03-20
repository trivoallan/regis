# Standard Rules

:::info
For more information on how rules work and how to customize them, see the [Rules](../concepts/rules.md).
:::

| Provider  | Slug                     | Title                                                      | Level    | Tags          | Parameters                                                            |
| :-------- | :----------------------- | :--------------------------------------------------------- | :------- | :------------ | :-------------------------------------------------------------------- |
| dockle    | `dockle-max-warnings`    | Too many Dockle warnings found.                            | warning  | security      | `max_count=5`                                                         |
| dockle    | `dockle-no-fatal`        | No FATAL issues found by Dockle.                           | critical | security      | `max_count=0`                                                         |
| freshness | `freshness-age`          | Image should be less than expected days old.               | warning  | freshness     | `max_days=30`                                                         |
| skopeo    | `skopeo-exposed-ports`   | Image exposes permitted ports.                             | warning  | security      | `allowed_ports=['80', '443']`                                         |
| skopeo    | `skopeo-forbidden-env`   | Image must not contain forbidden environment variables.    | critical | security      | `keys=['DEBUG', 'SECRET_KEY']`                                        |
| skopeo    | `skopeo-max-layers`      | Image has an acceptable number of layers.                  | warning  | performance   | `max_layers=30`                                                       |
| skopeo    | `skopeo-max-size`        | Image size is within limits.                               | warning  | hygiene       | `max_mb=1000`                                                         |
| skopeo    | `skopeo-multi-arch`      | Image should support multiple platforms.                   | info     | compatibility | `min_platforms=2`                                                     |
| skopeo    | `skopeo-no-root`         | Image must not run as root.                                | critical | security      | `forbidden_user=root`                                                 |
| skopeo    | `skopeo-required-labels` | Image must have required OCI labels.                       | warning  | metadata      | `labels=['org.opencontainers.image.source']`                          |
| skopeo    | `skopeo-tag-not-latest`  | Image tag should not be 'latest'.                          | warning  | lifecycle     |                                                                       |
| trivy     | `trivy-fix-available`    | All vulnerabilities should be fixed if a patch exists.     | warning  | security      | `max_count=0`                                                         |
| trivy     | `trivy-no-critical`      | No CRITICAL vulnerabilities found by Trivy.                | critical | security      | `max_count=0`                                                         |
| trivy     | `trivy-no-high`          | No HIGH vulnerabilities found by Trivy.                    | warning  | security      | `max_count=0`                                                         |
| trivy     | `trivy-secret-scan`      | No secrets or credentials should be embedded in the image. | critical | security      | `max_count=0`                                                         |
| core      | `trusted-domain`         | Image must originate from a trusted domain.                | critical | security      | `domains=['docker.io', 'registry-1.docker.io', 'quay.io', 'ghcr.io']` |
