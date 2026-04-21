# Plan Sprint 1 — Communication & Opérations
## 19 mai → 2 juin | Fondations & Préparation Pilote

> **Principe**: Communication précise, timing, stakeholders identifiés. Chaque artefact et moment a un public et un objectif clair.

---

## Contexte

**Enjeux critiques** :
- Premier sprint avec équipes pilotes en vue (Direction Expertise Applicative + équipes projet)
- Pilote linguistique : français pour architectes (non SREs)
- Visibilité interne : l'adoption dépend de la clarté du message et de la démo expérience

**Livrables Sprint 1** :
1. Moratoire snapshots doc
2. Playbook bundle format
3. Finitions site de doc
4. Guide GitLab CI

---

## Phase 0 : Pré-Sprint (16-19 mai)

### Briefing Interne — **Lundi 16 mai, 14h**

**Quoi** : 15 min max
- Objectifs Sprint 1 en langage métier (pas technique)
- Qui fait quoi (affectations claires)
- Dépendances critiques (ex: playbook bundle avant d'écrire les 3 playbooks métier)

**Qui** : Équipe Regis + tech leads sponsorisants (Direction Expertise Applicative si présents)

**Format** : Vidéo + slide + notes partagées (notion/wiki interne)

**Action** : Confirmer availability des équipes pilotes pour les démos de fin de sprint

---

## Phase 1 : Étapes du Sprint (19 mai → 29 mai)

### Étape 1 — Playbook Bundle Format & Moratoire (J1-J4)

**Quoi** : 
- Décision sur la structure du bundle (dir `playbook.yaml` + `README.md` + `inputs.schema.json`)
- Finaliser `InputsAnalyzer`
- Prototype du playbook "validation import" V1

**Qui fait** : Tech lead Regis + architecte (co-design si Direction Expertise Applicative disponible)

**Quand communiquer** : 
- **J2 (mercredi 20 mai, midi)** : Post draft de l'ADR (architecture decision record) bundle sur Slack interne
  - Vue d'ensemble simple (1 diagramme ASCII : `playbook/ → playbook.yaml + README.md + inputs.schema.json`)
  - Pourquoi ce format (résilience, documentation, composition)
  - Invite à feedback rapide (2j max)

- **J4 (vendredi 22 mai, EOD)** : Playbook "validation import" alpha
  - Règles concrètes (30-40 rules) écrites en pseudo-code dans un PR draft
  - README expliquant la logique métier
  - Invite QA pilote à revenir lundi avec retours

### Étape 2 — Finitions Site Doc (J1-J5)

**Quoi** :
- Branding cohérent (couleurs, logo, CSS custom)
- Navigation sidebar claire (Architecture C4, Getting Started, Rules Reference)
- SEO baseline (meta tags, structured data)
- CI hardening (trivy pinning, caching)

**Qui fait** : DevX/Designer + Regis tech lead

**Quand communiquer** :
- **J2 (mercredi, 10h)** : Design brief partagé (Figma ou moodboard)
  - Palette couleurs proposée
  - Typographie
  - Icônes/badges
  - Demander retours visuels (lead Direction Expertise Applicative si intéressé)

- **J5 (lundi 26 mai, EOD)** : Site preview URL partagé sur Slack
  - "Site prêt pour la démo pilote du 29 mai"
  - QR code + lien complet dans un email de recap

### Étape 3 — Guide GitLab CI (J3-J5)

**Quoi** :
- Doc complète : intégration Regis dans pipeline GitLab
- Scenarios : multi-registres, déploiement rapport sur GitLab Pages / K8s
- Cookbook concret (YAML copié/collé)

**Qui fait** : DevOps/Platform + Regis tech lead

**Quand communiquer** :
- **J3 (jeudi 21 mai, PM)** : Tech spike summary
  - "On a étudié 3 approches — voici la préférée et pourquoi"
  - 1 diagramme (flux image → Regis → artifact → GitLab Pages)
  
- **J5 (lundi 26 mai, EOD)** : Draft doc sur Docusaurus + Gist GitHub
  - Prêt pour révision pilote
  - "Prêt pour démo live jeudi 29 mai"

---

## Phase 2 : Démo & Feedback (29 mai - 2 juin)

### Démo Pilote — **Jeudi 29 mai, 10h-12h**

**Quoi** : Live demo + feedback

**Structure** (2h) :
1. **Intro 10 min** — "Regis en 2 minutes" (one-pager exécutif)
   - Pour qui ? (architectes)
   - Quel problème résout ? (visibilité images + compliance)
   - Comment on l'utilise ? (CLI + playbooks + rapports)

2. **Playbook bundle format 15 min** — démo live
   - Créer un playbook simple avec `regis bootstrap playbook`
   - Montrer la structure (YAML, README, schema)
   - Montrer JSON Logic editor dans Docusaurus
   
3. **Playbook "validation import" 20 min** — cas d'usage réel
   - Image Harbor de DEA
   - Règles (build date, vulnérabilités critiques, taille, licences)
   - Résultat final (go/no-go)
   - **Feedback clé** : "Est-ce que les règles ont du sens pour votre use case ?"

4. **Site de doc + GitLab CI 10 min**
   - Navigation Docusaurus
   - Rules Reference (tous les analyzers)
   - Guide GitLab (les équipes peuvent copier le YAML et adapter)

5. **Q&A + Retours 25 min**
   - Pain points immédiats
   - Features manquantes
   - UX/DX first impressions

**Qui** : 
- **Présentateurs** : Tech lead Regis + Product Owner
- **Audience** : Direction Expertise Applicative (min 4-5 architectes), équipes projet, stakeholders clés
- **Observateurs** : Support/adoption (pour prendre notes)

**Retours attendus** :
- Clarté des règles "validation import"
- Usabilité CLI + Docusaurus
- Pertinence du format bundle pour leurs workflows
- Blockers avant v1

**Action post-démo** : 
- Support/adoption documente les feedback
- Tech lead priorise retours critiques (J1 post-démo)

### Recap Email — **Vendredi 30 mai, 10h**

**To** : Direction Expertise Applicative, équipes projet, tech sponsors

**Subject** : "[Regis] Démo Sprint 1 — Retours et prochaines étapes"

**Contenu** :
1. Merci pour présence + feedback
2. Synthèse feedback (3-5 items clés par catégorie : rules, UX, docs, blocking issues)
3. Plan d'action (priorités, dates)
4. Resources : 
   - Docusaurus live : [URL]
   - Draft playbook bundle : [repo URL]
   - Guide GitLab : [doc URL]
5. "Prochaine démo : [date Sprint 2]"

---

## Phase 3 : Sprint Closing (2 juin)

### Standup Final — **Lundi 2 juin, 9h**

**Quoi** : 30 min
- Résumé livrables finaux (4 items checklist)
- Retours pilote intégrés oui/non
- Dépendances pour Sprint 2 confirmées (Harbor integration, 3 playbooks métier)
- Snapshot des metrics (uptime doc site, CI green, tests coverage)

**Qui** : Équipe Regis + tech sponsor

### Internal Wiki/Notion Update — **Lundi 2 juin, 11h**

**Quoi** :
- Résumé "Sprint 1 shipped"
- One-liner de chaque item + link vers PR
- Feedback pilote synthétisé
- "Sprint 2 : 19 mai ← Harbor + 3 playbooks"

**Qui lit** : Équipe Regis, stakeholders monitoring progress

---

## Communication Channels (Mapping)

| Canal | Fréquence | Contenu | Audience |
|-------|-----------|---------|----------|
| **Slack #regis-sprint** | Daily standup 10h | "Done: X, Doing: Y, Blocked: Z" | Équipe Regis + sponsors |
| **Slack #regis-pilot** | Weekly update (Wed 14h) | "Prêt pour feedback ?" + preview link | DEA + équipes projet |
| **Email recap** | Fin étape majeure | Synthèse + next steps + actions | Stakeholders clés |
| **Docusaurus Preview** | As built | URL live mis à jour daily | DEA (feedback immédiat) |
| **Démo en direct** | J29 mai | Live walkthrough + feedback session | DEA + équipes projet |
| **Wiki/Notion** | Fin sprint | Résumé + metrics + dependencies Sprint 2 | Équipe Regis + monitoring |

---

## Risk Mitigation

| Risk | Mitigation | Qui Communicate |
|------|-----------|-----------------|
| Playbook bundle trop complexe pour DEA | Prototype tôt (J2), invite feedback rapide (J4) | Tech lead |
| "Validation import" rules ne matchent pas use case DEA | Co-design avec architecte (J1), draft early, démo J29 | Product Owner + Architecte |
| Site doc pas prêt pour démo | Preview URL live dès J2 (même rough), iterate | DevX lead |
| GitLab CI doc trop technique | YAML copy/paste + Slack walkthrough après démo | DevOps lead |
| DEA unavailable pour démo J29 | Confirmer dès J1 pré-sprint, plan B async video | Product Owner |

---

## Success Criteria

✅ **Communiqué clairet à temps** :
- Objectifs Sprint 1 partagés J1 à sponsors
- Draft bundle design circulé J2 (feedback J2-J4)
- Site doc preview live J2 (iterate J2-J5)
- GitLab guide draft prêt J5

✅ **Démo pilote J29 mai** :
- Min 4 architectes DEA présents
- Live demo playbook bundle + "validation import" + rapport
- Q&A session 25+ min
- Feedback documenté (support/adoption)

✅ **Retours intégrés rapido** :
- Email recap J30 mai (synthèse + plan d'action)
- Critical blockers = assignés J1 Sprint 2
- Non-bloquants = backlog Sprint 2

---

## Artefacts à Préparer Avant J29 mai

- [ ] One-pager Regis (exec summary 1 page)
- [ ] Draft playbook bundle ADR (architecture decision)
- [ ] Prototype playbook "validation import" v1 (30+ rules)
- [ ] Docusaurus preview URL (branding + sidebar + rules ref live)
- [ ] Draft GitLab CI guide (YAML + scenarios)
- [ ] Démo script (notes de présentation)
- [ ] Feedback template (Google Form / Notion pour DEA)

---

## Post-Sprint Deliverables (J2 juin)

| Item | Owner | Target |
|------|-------|--------|
| Playbook bundle spec | Tech lead | Shipped, docs live |
| InputsAnalyzer | Regis dev | Merged, tests green |
| Playbook "validation import" v0.1 | Product Owner + Architect | Merged, ready for Sprint 2 iteration |
| Docusaurus site (branding, nav, rules ref) | DevX | Live, indexed by search |
| GitLab CI guide | DevOps lead | Live in Docusaurus, copy/paste ready |
| Snapshot moratoire | Infra/CI lead | Release-snapshot.yml disabled |

---

## Dépendances Sprint 2

- ✅ Playbook bundle format finalisé = prerequisite pour "Intégration Harbor" (Sprint 2 I2)
- ✅ GitLab guide shipped = prerequisite pour "Déploiement K8s" (Sprint 2 post-release)
- ⚠️ Feedback DEA sur "validation import" = guide content priorities Sprint 2
- ⚠️ "Contrôle catalogue" + "Progression projet" playbooks = Depends on final bundle design

---

## Notes

- **Contexte bilingual** : Documentation technique en anglais, communication executive/interne en français. One-pager et présentations pour DEA en français.
- **Timing congés** : Démo J29 mai (avant), congés 30 avr → 17 mai (avant), Sprint 2 commence 19 mai (juste après). Confirmer availability.
- **Feedback loops serrées** : Code review interne rapide (J2-J4), feedback DEA live démo J29, action plan J30. Sprint 2 commence avec insights frais.
