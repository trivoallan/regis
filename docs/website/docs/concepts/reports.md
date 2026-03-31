---
tags:
  - reports
---

# Reports

One of the core missions of `regis` is to bridge the gap between automated tools and human review through **Visual Excellence**.

## The Reporting Engine

`regis` uses a modern **Single Page Application (SPA)** architecture for its reports. Instead of static, server-side rendered pages, every report is a fully-featured, client-side application built with **React** and **Docusaurus**.

The following diagram illustrates the relationship between the CLI and the generated report:

```mermaid
C4Component
    title Component Diagram — Report Viewer

    Person(user, "User / Security Reviewer", "Reviews security findings in a browser.")

    Container_Boundary(cli_boundary, "regis (CLI)") {
        Component(engine, "Analysis Engine", "Python", "Orchestrates analyzers and playbooks; produces consolidated results.")
        Component(reporter, "Docusaurus Reporter", "Python", "Injects analysis data into the SPA and triggers the static build.")
    }

    Container_Boundary(spa_boundary, "Report Viewer (SPA)") {
        Component(react_app, "React Application", "React / Docusaurus", "Interactive dashboard for browsing security findings.")
        Component(json_data, "report.json", "JSON", "Static data file bundled with the SPA at build time.")
    }

    Rel(engine, reporter, "Passes analysis results", "In-process")
    Rel(reporter, json_data, "Writes", "File system")
    Rel(reporter, react_app, "Triggers build & deploy", "Subprocess / File system")
    Rel(react_app, json_data, "Fetches at runtime", "HTTP / Static")
    Rel(user, react_app, "Browses findings", "Browser")

    UpdateElementStyle(user, $fontColor="white", $bgColor="#08427B", $borderColor="#052E56")
    UpdateElementStyle(engine, $fontColor="white", $bgColor="#1A8C4E", $borderColor="#136B3B")
    UpdateElementStyle(reporter, $fontColor="white", $bgColor="#1168BD", $borderColor="#0B4A87")
    UpdateElementStyle(react_app, $fontColor="white", $bgColor="#7B2D8B", $borderColor="#5C2168")
    UpdateElementStyle(json_data, $fontColor="white", $bgColor="#B7770D", $borderColor="#8C5B0A")
    UpdateRelStyle(engine, reporter, $textColor="#1168BD", $lineColor="#1168BD")
    UpdateRelStyle(reporter, json_data, $textColor="#B7770D", $lineColor="#B7770D")
    UpdateRelStyle(reporter, react_app, $textColor="#7B2D8B", $lineColor="#7B2D8B")
    UpdateRelStyle(react_app, json_data, $textColor="#B7770D", $lineColor="#B7770D")
    UpdateRelStyle(user, react_app, $textColor="#7B2D8B", $lineColor="#7B2D8B")
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="2")
```

This architecture allows for:

- **Rich Interactivity**: Instant filtering, sorting, and searching across thousands of vulnerability findings.
- **Unified Viewing Experience**: A consistent UI across different report types, with a polished, professional aesthetic.
- **Self-Contained Portability**: Each report is bundled into a single directory, ready to be served from any static host or viewed as a CI/CD artifact.

## Philosophy: Visual Excellence

We believe that security reports should be easy to read and aesthetically pleasing. A well-designed report:

1. **Reduces Cognitive Load**: Highlighting the most important issues first through clear categorization and visual cues.
2. **Encourages Adoption**: Teams are more likely to engage with security when given clear, actionable, and professional feedback.
3. **Facilitates Decision Making**: Using color-coded risk levels and intuitive navigation to distinguish between minor warnings and critical blockers.

## Hybrid Reporting

`regis` follows a "hybrid" reporting strategy:

- **JSON Report**: The source of truth. A machine-readable document containing all analysis and evaluation data, perfect for automated processing.
- **SPA Viewer**: A human-friendly dashboard that consumes the JSON report to provide a rich, interactive experience.

```bash
# Generate both JSON and interactive HTML site
regis analyze <image-url> --site
```

:::tip
Check our [Usage Guide](../usage/configuration.md) to learn how to set default themes for your project.
:::
