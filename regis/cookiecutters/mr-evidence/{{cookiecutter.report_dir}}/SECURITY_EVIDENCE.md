# 🛡️ regis Security Evidence

> Generated automatically by `regis`

Analysis performed on **{{ cookiecutter.regis.request.timestamp }}**.

## 📦 Target Details

- **Registry**: `{{ cookiecutter.regis.request.registry }}`
- **Repository**: `{{ cookiecutter.regis.request.repository }}`
- **Tag**: `{{ cookiecutter.regis.request.tag }}`

## 📊 Playbook Results: {{ cookiecutter.regis.playbook.playbook_name }}

- **Score**: `{{ cookiecutter.regis.playbook.score }}%`
{% set tier = cookiecutter.regis.playbook.tier | default(None) %}
{% if tier %}- **Tier**: `{{ tier }}`
{% endif %}

{% set cve = cookiecutter.regis.results.cve | default({}) %}
{% if cve %}

## 🐛 Vulnerability Summary (grype)

- **Critical**: `{{ cve.critical_count | default(0) }}`
- **High**: `{{ cve.high_count | default(0) }}`
- **Medium**: `{{ cve.medium_count | default(0) }}`
- **Low**: `{{ cve.low_count | default(0) }}`
- **Total**: `{{ cve.vulnerability_count | default(0) }}`
  {% endif %}

{% set freshness = cookiecutter.regis.results.freshness | default({}) %}
{% if freshness %}

## 📅 Image Freshness

- **Age in Days**: `{{ freshness.age_days | default('N/A') }}`
  {% endif %}
