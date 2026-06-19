# Project Brief

## Project Name

Regis

## Description

Container Security & Policy-as-Code Orchestration. Regis provides unified container analysis, custom playbooks, and highly customizable interactive reports for production-ready CI/CD.

## Vision

Provide a single orchestration layer for container security, supply-chain evidence, and policy evaluation that works across CI/CD systems and produces both machine-readable and human-friendly reports.

## Core Requirements

- Unified container registry inspection and metadata extraction
- Pluggable analyzers for security, quality, freshness, provenance, and size
- Policy-as-code playbooks using JSON Logic
- HTML dashboards plus JSON outputs for automation
- GitHub Actions and GitLab CI support
- SBOM and provenance artifacts in release/CD workflows

## Goals

- Make container review and compliance checks repeatable
- Reduce manual security review effort
- Keep reports consumable by both engineers and automation
- Preserve compatibility with CI/CD and release pipelines

## Scope

### In Scope

- CLI commands under `regis/adapters/driving/cli/commands/`
- Analyzer plugins under `regis/core/domain/analyzers/`
- Playbook evaluation and rule logic
- Registry integrations and report generation
- Docusaurus documentation and dashboard UI
- CI/CD workflows, SBOM generation, and provenance attestation

### Out of Scope

- General-purpose container runtime management (not a replacement for Docker/Podman)
- Real-time image scanning daemon (batch/CI-oriented only)
- Multi-tenant SaaS hosting — self-hosted CI/CD integration only
- Custom analyzer authoring guide (deferred post-v1)

## Key Stakeholders

- Tristan Rivoallan
- Direction Expertise Applicative (architectes et experts sécurité) — cible pilote v1
- Équipes projet — utilisateurs playbook "progression projet"
