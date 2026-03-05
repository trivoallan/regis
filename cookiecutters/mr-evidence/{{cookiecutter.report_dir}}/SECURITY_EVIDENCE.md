# 🛡️ regis-cli Security Evidence

> Generated automatically by `regis-cli`

Analysis performed on **{{ cookiecutter.regis.request.timestamp }}**.

## 📦 Target Details
- **Registry**: `{{ cookiecutter.regis.request.registry }}`
- **Repository**: `{{ cookiecutter.regis.request.repository }}`
- **Tag**: `{{ cookiecutter.regis.request.tag }}`

## 📊 Playbook Results: {{ cookiecutter.regis.playbook.playbook_name }}
- **Score**: `{{ cookiecutter.regis.playbook.score }}%`
- **Passed Scorecards**: `{{ cookiecutter.regis.playbook.passed_scorecards }}/{{ cookiecutter.regis.playbook.total_scorecards }}`

{% if cookiecutter.regis.results.trivy is defined %}
## 🐛 Vulnerability Summary (Trivy)
- **Critical**: `{{ cookiecutter.regis.results.trivy.critical_count }}`
- **High**: `{{ cookiecutter.regis.results.trivy.high_count }}`
- **Total**: `{{ cookiecutter.regis.results.trivy.vulnerability_count }}`
{% endif %}

{% if cookiecutter.regis.results.freshness is defined %}
## 📅 Image Freshness
- **Age in Days**: `{{ cookiecutter.regis.results.freshness.age_days }}`
- **Freshness Score**: `{{ cookiecutter.regis.results.freshness.score }}`
{% endif %}
