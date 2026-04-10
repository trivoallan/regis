workspace "Regis" "Container security and policy-as-code orchestration platform. Analyzes Docker images, evaluates results against playbook rules, and generates interactive reports." {

    !identifiers hierarchical

    model {
        # ─── People ───────────────────────────────────────────────────────────
        devops = person "DevOps Engineer" "Uses Regis CLI interactively to audit container images and review HTML reports before deploying." {
            tags "Person"
        }

        ciPipeline = person "CI/CD Pipeline" "Automated pipeline (GitHub Actions, GitLab CI, etc.) that runs Regis as part of a build gate and reacts to exit codes." {
            tags "Person,Automated"
        }

        # ─── Software System ──────────────────────────────────────────────────
        regisSystem = softwareSystem "Regis" "Policy-as-code orchestration platform for Docker image security. Runs pluggable analyzers concurrently, evaluates JSON Logic playbooks, and generates JSON + HTML reports." {
            tags "Internal"

            # ── Containers ────────────────────────────────────────────────────
            regisCli = container "Regis CLI" "Python CLI application. Discovers analyzers, coordinates concurrent analysis, evaluates playbooks, and writes reports." {
                technology "Python 3.10+, Click, ThreadPoolExecutor"
                tags "Container,Python"

                # ── Application layer ─────────────────────────────────────────
                group "Application Layer" {
                    cliEntrypoint = component "CLI Entry Point" "Registers all Click commands and configures logging. Console script: regis." {
                        technology "Python, Click"
                        tags "Component,Application"
                    }

                    analyzeCmd = component "Analyze Command" "Main analysis orchestrator. Parses image URL, runs analyzers concurrently via ThreadPoolExecutor, triggers playbook evaluation, and writes output." {
                        technology "Python, Click, ThreadPoolExecutor"
                        tags "Component,Application"
                    }

                    checkCmd = component "Check Command" "CI/CD gate command. Fetches image manifest and exits with non-zero code on failure — usable as a lightweight registry health check." {
                        technology "Python, Click"
                        tags "Component,Application"
                    }

                    bootstrapCmd = component "Bootstrap Command" "Scaffolds new custom playbooks from Cookiecutter templates." {
                        technology "Python, Click, Cookiecutter"
                        tags "Component,Application"
                    }

                    archiveCmd = component "Archive Command" "Persists analysis reports to an archive directory and updates manifest.json / data.json." {
                        technology "Python, Click"
                        tags "Component,Application"
                    }
                }

                # ── Domain layer ──────────────────────────────────────────────
                group "Domain Layer" {
                    playbookEvaluator = component "Playbook Evaluator" "Orchestrates full playbook evaluation: builds context, evaluates pages/sections/scorecards/widgets, resolves tiers, badges, and links." {
                        technology "Python, json-logic-qubit"
                        tags "Component,Domain"
                    }

                    rulesEvaluator = component "Rules Evaluator" "Merges default analyzer rules with playbook overrides, evaluates JSON Logic conditions, and interpolates result messages." {
                        technology "Python, json-logic-qubit"
                        tags "Component,Domain"
                    }

                    playbookLoader = component "Playbook Loader" "Loads playbook definitions from local YAML/JSON files or remote HTTP/HTTPS URLs." {
                        technology "Python, PyYAML, requests"
                        tags "Component,Domain"
                    }

                    evalContext = component "Evaluation Context" "Flattens nested report dicts into a dot-notation context for JSON Logic. Tracks missing keys for conditional section rendering." {
                        technology "Python"
                        tags "Component,Domain"
                    }

                    reportOrchestrator = component "Report Orchestrator" "Coordinates report writing: validates against JSON Schema, renders JSON and HTML formats, triggers MR template rendering." {
                        technology "Python, jsonschema, Jinja2"
                        tags "Component,Domain"
                    }

                    gitlabIntegration = component "GitLab Integration" "Resolves playbook GitLab directives: MR labels, description checklists, MR comment templates." {
                        technology "Python, python-gitlab"
                        tags "Component,Domain"
                    }
                }

                # ── Infrastructure layer ──────────────────────────────────────
                group "Infrastructure Layer" {
                    registryClient = component "Registry Client" "Docker Registry V2 HTTP client. Handles Bearer/Basic token auth transparently; fetches manifests, blobs, tags, and digests." {
                        technology "Python, requests"
                        tags "Component,Infrastructure"
                    }

                    analyzerBase = component "Analyzer Plugin Contract" "Abstract BaseAnalyzer class defining the plugin interface: analyze(), validate(), and default_rules()." {
                        technology "Python, ABC, jsonschema"
                        tags "Component,Infrastructure"
                    }

                    analyzerDiscovery = component "Analyzer Discovery" "Loads analyzer plugins registered via Python entry_points (regis.analyzers group)." {
                        technology "Python, importlib.metadata"
                        tags "Component,Infrastructure"
                    }

                    concreteAnalyzers = component "Concrete Analyzers" "12 built-in analyzers: trivy (CVE), skopeo (metadata), hadolint (Dockerfile lint), dockle (security lint), sbom, versioning, popularity, freshness, endoflife, provenance, size, scorecarddev." {
                        technology "Python; delegates to trivy, skopeo, hadolint, dockle CLIs and external APIs"
                        tags "Component,Infrastructure"
                    }

                    docusaurusBuilder = component "Docusaurus Site Builder" "Embeds report.json into the Report Viewer static directory, runs pnpm build, and copies the output site to the destination." {
                        technology "Python, subprocess, pnpm"
                        tags "Component,Infrastructure"
                    }
                }
            }

            reportViewer = container "Report Viewer" "React/Docusaurus single-page application that renders the interactive HTML security report from report.json." {
                technology "Node.js, React, Docusaurus, Tailwind CSS"
                tags "Container,NodeJS"
            }
        }

        # ─── External Systems ─────────────────────────────────────────────────
        dockerRegistry = softwareSystem "Docker Registry" "OCI/Docker Registry V2. Serves image manifests, blobs, tags, and digest headers." {
            tags "External"
        }

        trivyCli = softwareSystem "Trivy" "Aqua Security vulnerability scanner CLI. Performs CVE scanning and SBOM generation." {
            tags "External,CLI"
        }

        skopeoCli = softwareSystem "Skopeo" "OCI image inspection CLI. Provides multi-arch metadata, layer inspection, and raw manifest access." {
            tags "External,CLI"
        }

        hadolintCli = softwareSystem "Hadolint" "Dockerfile linter CLI. Enforces Dockerfile best practices." {
            tags "External,CLI"
        }

        dockleCli = softwareSystem "Dockle" "Container image security linter CLI. Checks CIS benchmarks and security best practices." {
            tags "External,CLI"
        }

        endoflifeApi = softwareSystem "endoflife.date API" "Public REST API providing software lifecycle status and end-of-life dates for base image distributions." {
            tags "External,API"
        }

        openssfApi = softwareSystem "OpenSSF Scorecard API" "REST API that returns security scorecard metrics for open-source repositories." {
            tags "External,API"
        }

        githubApi = softwareSystem "GitHub / GitLab APIs" "Source control APIs used for provenance metadata, commit data, and GitLab MR comment integration." {
            tags "External,API"
        }

        # ─── Relationships: People → System ───────────────────────────────────
        devops -> regisSystem "Analyzes images, reviews reports" "CLI / Browser"
        ciPipeline -> regisSystem "Runs analysis and enforces policy gates" "CLI / Exit code"

        # ─── Relationships: System → External ─────────────────────────────────
        regisSystem -> dockerRegistry "Fetches manifests, blobs, tags, digests" "HTTPS / Docker Registry V2 API"
        regisSystem -> trivyCli "Delegates CVE scanning and SBOM generation" "subprocess"
        regisSystem -> skopeoCli "Delegates image metadata inspection" "subprocess"
        regisSystem -> hadolintCli "Delegates Dockerfile linting" "subprocess"
        regisSystem -> dockleCli "Delegates container security linting" "subprocess"
        regisSystem -> endoflifeApi "Queries base image lifecycle status" "HTTPS / REST"
        regisSystem -> openssfApi "Queries repository security scores" "HTTPS / REST"
        regisSystem -> githubApi "Fetches provenance data and posts MR comments" "HTTPS / REST"

        # ─── Relationships: Container → External ──────────────────────────────
        regisCli -> dockerRegistry "Fetches manifests, blobs, tags" "HTTPS / Docker Registry V2 API"
        regisCli -> trivyCli "Invokes via subprocess" "stdin/stdout"
        regisCli -> skopeoCli "Invokes via subprocess" "stdin/stdout"
        regisCli -> hadolintCli "Invokes via subprocess" "stdin/stdout"
        regisCli -> dockleCli "Invokes via subprocess" "stdin/stdout"
        regisCli -> endoflifeApi "HTTP GET lifecycle data" "HTTPS / REST"
        regisCli -> openssfApi "HTTP GET scorecard data" "HTTPS / REST"
        regisCli -> githubApi "HTTP GET provenance; HTTP POST MR comments" "HTTPS / REST"

        # ─── Relationships: Container ↔ Container ─────────────────────────────
        regisCli -> reportViewer "Embeds report.json and builds static site" "pnpm build / filesystem"
        devops -> reportViewer "Views interactive HTML report" "Browser"

        # ─── Relationships: Component (Application layer) ─────────────────────
        regisCli.cliEntrypoint -> regisCli.analyzeCmd "Registers and delegates to"
        regisCli.cliEntrypoint -> regisCli.checkCmd "Registers and delegates to"
        regisCli.cliEntrypoint -> regisCli.bootstrapCmd "Registers and delegates to"
        regisCli.cliEntrypoint -> regisCli.archiveCmd "Registers and delegates to"

        regisCli.analyzeCmd -> regisCli.analyzerDiscovery "Discovers available analyzers"
        regisCli.analyzeCmd -> regisCli.registryClient "Resolves image digest"
        regisCli.analyzeCmd -> regisCli.concreteAnalyzers "Runs concurrently via ThreadPoolExecutor"
        regisCli.analyzeCmd -> regisCli.playbookLoader "Loads playbook definitions"
        regisCli.analyzeCmd -> regisCli.reportOrchestrator "Validates and writes output"
        regisCli.analyzeCmd -> regisCli.docusaurusBuilder "Triggers HTML site build (--site flag)"

        regisCli.checkCmd -> regisCli.registryClient "Fetches image manifest"

        # ─── Relationships: Component (Domain layer) ──────────────────────────
        regisCli.playbookEvaluator -> regisCli.rulesEvaluator "Evaluates JSON Logic rules"
        regisCli.playbookEvaluator -> regisCli.evalContext "Builds dot-notation evaluation context"
        regisCli.playbookEvaluator -> regisCli.gitlabIntegration "Resolves GitLab MR directives"

        regisCli.reportOrchestrator -> regisCli.playbookLoader "Loads default and custom playbooks"
        regisCli.reportOrchestrator -> regisCli.playbookEvaluator "Runs playbook evaluation pass"
        regisCli.reportOrchestrator -> regisCli.docusaurusBuilder "Triggers HTML site build"

        # ─── Relationships: Component (Infrastructure layer) ──────────────────
        regisCli.analyzerDiscovery -> regisCli.analyzerBase "Loads classes conforming to"
        regisCli.concreteAnalyzers -> regisCli.analyzerBase "Extends"
        regisCli.concreteAnalyzers -> regisCli.registryClient "Uses for registry API calls"
        regisCli.concreteAnalyzers -> dockerRegistry "Fetches metadata via" "HTTPS"
        regisCli.concreteAnalyzers -> trivyCli "Invokes" "subprocess"
        regisCli.concreteAnalyzers -> skopeoCli "Invokes" "subprocess"
        regisCli.concreteAnalyzers -> hadolintCli "Invokes" "subprocess"
        regisCli.concreteAnalyzers -> dockleCli "Invokes" "subprocess"
        regisCli.concreteAnalyzers -> endoflifeApi "Queries" "HTTPS / REST"
        regisCli.concreteAnalyzers -> openssfApi "Queries" "HTTPS / REST"
        regisCli.concreteAnalyzers -> githubApi "Queries for provenance" "HTTPS / REST"
        regisCli.docusaurusBuilder -> reportViewer "Writes report.json to static/ and runs pnpm build" "filesystem / subprocess"
    }

    views {
        # ─── System Context ───────────────────────────────────────────────────
        systemContext regisSystem "SystemContext" {
            include *
            autoLayout lr
            title "Regis — System Context"
            description "Users and external systems that interact with Regis."
        }

        # ─── Container View ───────────────────────────────────────────────────
        container regisSystem "Containers" {
            include *
            autoLayout lr
            title "Regis — Containers"
            description "The two runtime containers and the external systems they interact with."
        }

        # ─── Component View ───────────────────────────────────────────────────
        component regisCli "Components" {
            include *
            autoLayout lr
            title "Regis CLI — Components"
            description "Internal components of the Regis CLI container, organised by Application / Domain / Infrastructure layers."
        }

        # ─── Styles ───────────────────────────────────────────────────────────
        styles {
            element "Person" {
                shape Person
                background "#1168BD"
                color "#ffffff"
                fontSize 14
            }
            element "Person,Automated" {
                shape Robot
                background "#1168BD"
                color "#ffffff"
            }
            element "Internal" {
                background "#1168BD"
                color "#ffffff"
            }
            element "External" {
                background "#999999"
                color "#ffffff"
            }
            element "External,CLI" {
                background "#6b7280"
                color "#ffffff"
                shape Component
            }
            element "External,API" {
                background "#6b7280"
                color "#ffffff"
                shape Hexagon
            }
            element "Container,Python" {
                background "#438DD5"
                color "#ffffff"
                shape Box
            }
            element "Container,NodeJS" {
                background "#3c763d"
                color "#ffffff"
                shape WebBrowser
            }
            element "Component,Application" {
                background "#85BBF0"
                color "#000000"
                shape Component
            }
            element "Component,Domain" {
                background "#a8d5a2"
                color "#000000"
                shape Component
            }
            element "Component,Infrastructure" {
                background "#f5c6a0"
                color "#000000"
                shape Component
            }
            relationship "Relationship" {
                thickness 2
                color "#707070"
                style dashed
            }
        }

        theme default
    }

}
