# 🛡️ regis Security Evidence

> Generated automatically by `regis`

Analysis performed on **{{ cookiecutter.regis.request.timestamp }}**.

## 📦 Target Details

- **Registry**: `{{ cookiecutter.regis.request.registry }}`
- **Repository**: `{{ cookiecutter.regis.request.repository }}`
- **Tag**: `{{ cookiecutter.regis.request.tag }}`

## 📊 Playbook Results: {{ cookiecutter.regis.playbook.playbook_name }}

- **Score**: `{{ cookiecutter.regis.playbook.score }}%`
- **Passed Scorecards**: `{{ cookiecutter.regis.playbook.passed_scorecards }}/{{ cookiecutter.regis.playbook.total_scorecards }}`

{% set trivy = cookiecutter.regis.results.trivy | default({}) %}
{% if trivy %}

## 🐛 Vulnerability Summary (Trivy)

- **Critical**: `{{ trivy.critical_count | default(0) }}`
- **High**: `{{ trivy.high_count | default(0) }}`
- **Total**: `{{ trivy.vulnerability_count | default(0) }}`
  {% endif %}

{% set freshness = cookiecutter.regis.results.freshness | default({}) %}
{% if freshness %}

## 📅 Image Freshness

- **Age in Days**: `{{ freshness.age_days | default('N/A') }}`
  {% endif %}
