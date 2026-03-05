# Backlog

- [ ] Générer le dépôt hub2hub et l'intégrer à la merge request
- [x] Via le playbook, permettre de définir une liste de cases à cocher qui seront ajoutées à la description de la Merge Request
- [ ] Rapport disponible au format Markdown pour les LLM (https://www.npmjs.com/package/@pointsharp/antora-llm-generator)
- [x] Interface d'administration (requirements manuels) ?
- [x] Mécanisme configurable pour ajouter du contenu à la MR (via cookiecutter ?)
- [ ] Recommandation de configuration d'import (regex)
- [ ] Démo intégration avec PowerBI (idées)
- [x] Refactor engine.py
- [x] ajouter sous-commande pour la ci gitlab
- [x] groupes pour les checklists
- [ ] docs : search
- [ ] Revoir l'organisation des rapports (stocker par digest)
- [ ] image build : signature
- [ ] image build : provenance
- [ ] image build : sbom
- [ ] gérer la notion de release line semver
- [ ] <https://www.npmjs.com/package/@antora/lunr-extension>


[mermaid]
....
graph TD
    User["User / CI Pipeline"] --> CLI["CLI Layer (Click)"]
    CLI --> Engine["Analysis Engine"]
    
    subgraph "Data Extraction"
        Engine --> A1["Skopeo Analyzer"]
        Engine --> A2["Trivy Analyzer"]
        Engine --> A3["Hadolint Analyzer"]
        Engine --> A4["Dockle Analyzer"]
        Engine --> AN["... Other Analyzers"]
    end
    
    A1 & A2 & A3 & A4 & AN --> Registry["Container Registry"]
    
    Engine --> Playbook["Playbook Engine (JSON Logic)"]
    Playbook --> Results["Consolidated Results"]
    
    Results --> HTML["HTML Report (Jinja2)"]
    Results --> JSON["JSON Report"]
    
    HTML & JSON --> Output["Output Directory"]
....