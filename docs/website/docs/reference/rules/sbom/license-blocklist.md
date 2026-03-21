---
tags:
  - compliance
  - licensing
  - rules
---

# license-blocklist

Image must not include components with licenses from the configured blocklist.

| Provider | Level    | Tags                  |
| :------- | :------- | :-------------------- |
| sbom     | Critical | compliance, licensing |

## Overview

This is a **template rule**: you instantiate it in your playbook with a custom `blocklist` parameter
listing the [SPDX license identifiers](https://spdx.org/licenses/) you want to forbid.

The rule evaluates to **pass** when none of the image's component licenses appear in the blocklist.
It relies on the [`copyleft_licenses`](../../schemas/analyzer/sbom.schema.md#copyleft_licenses)
field computed by the SBOM analyzer for its failure message.

:::tip Vacuous pass
When no SBOM is available (`has_sbom: false`), the `licenses` array is empty and this rule
passes vacuously. Use the [`has-sbom`](./has-sbom.md) rule alongside this one to ensure an SBOM
is always present.
:::

## Messages

| Type     | Message                                                              |
| :------- | :------------------------------------------------------------------- |
| **Pass** | No blocked licenses detected across `{total_components}` components. |
| **Fail** | Blocked license(s) detected: `{copyleft_licenses}`.                  |

## Playbook Example

The default playbook ships two opt-in presets. Enable one or both by setting `enable: true`,
or define your own instance with a custom blocklist:

```yaml
rules:
  # Block strong copyleft (GPL, AGPL, SSPL) — critical
  - provider: sbom
    rule: license-blocklist
    slug: no-strong-copyleft
    level: critical
    enable: true
    options:
      blocklist:
        - GPL-2.0
        - GPL-2.0-only
        - GPL-2.0-or-later
        - GPL-3.0
        - GPL-3.0-only
        - GPL-3.0-or-later
        - AGPL-3.0
        - AGPL-3.0-only
        - AGPL-3.0-or-later
        - SSPL-1.0

  # Warn on weak copyleft (LGPL, MPL, EPL, CDDL, EUPL) — warning
  - provider: sbom
    rule: license-blocklist
    slug: no-weak-copyleft
    level: warning
    enable: true
    options:
      blocklist:
        - LGPL-2.1
        - LGPL-2.1-only
        - LGPL-2.1-or-later
        - LGPL-3.0
        - LGPL-3.0-only
        - MPL-2.0
        - EPL-2.0
        - CDDL-1.0
        - EUPL-1.2
```

## Condition

```json
{
  "!": [
    {
      "intersects": [
        { "var": "results.sbom.licenses" },
        { "var": "rule.params.blocklist" }
      ]
    }
  ]
}
```

## Copyleft License Reference

The SBOM analyzer maintains a built-in reference list of copyleft SPDX identifiers, split by
category. You can use any subset as your `blocklist`.

### Strong copyleft

Require releasing the source code of **all** derivative works.

| License                                          | Notes                                                         |
| :----------------------------------------------- | :------------------------------------------------------------ |
| `GPL-2.0`, `GPL-2.0-only`, `GPL-2.0-or-later`    | GNU General Public License v2                                 |
| `GPL-3.0`, `GPL-3.0-only`, `GPL-3.0-or-later`    | GNU General Public License v3                                 |
| `AGPL-1.0`                                       | Affero GPL v1                                                 |
| `AGPL-3.0`, `AGPL-3.0-only`, `AGPL-3.0-or-later` | Affero GPL v3 — also covers network/SaaS use                  |
| `SSPL-1.0`                                       | Server Side Public License — very broad copyleft for services |

### Weak copyleft

Copyleft applies only to **modifications of the licensed component itself**, not to the broader application.

| License                                          | Notes                                       |
| :----------------------------------------------- | :------------------------------------------ |
| `LGPL-2.0`, `LGPL-2.0-only`, `LGPL-2.0-or-later` | GNU Lesser GPL v2                           |
| `LGPL-2.1`, `LGPL-2.1-only`, `LGPL-2.1-or-later` | GNU Lesser GPL v2.1                         |
| `LGPL-3.0`, `LGPL-3.0-only`, `LGPL-3.0-or-later` | GNU Lesser GPL v3                           |
| `MPL-2.0`, `MPL-2.0-no-copyleft-exception`       | Mozilla Public License 2.0                  |
| `EPL-1.0`, `EPL-2.0`                             | Eclipse Public License                      |
| `CDDL-1.0`                                       | Common Development and Distribution License |
| `EUPL-1.1`, `EUPL-1.2`                           | European Union Public License               |
