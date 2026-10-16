# Contrat commun à regis, knock et uske : la CI n'appelle que ces cibles.
.PHONY: ci-tools lint reference test security image smoke settings

CI_IMAGE ?= regis:ci

ci-tools: ## Rien à installer : uv suffit

lint: ## ruff, mypy, frontières hexagonales, référence à jour, gardes du dépôt
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy regis
	uv run lint-imports
	$(MAKE) reference
	test -z "$$(git status --porcelain -- docs/reference)" || { git status --short -- docs/reference; echo "docs/reference est périmé : lancer 'make reference' et commiter."; exit 1; }
	! git ls-files -- 'docs/superpowers/plans/**' | grep . || { echo "plans d'exécution commités"; exit 1; }

reference: ## Régénère la référence des règles et des schémas (README.md des règles est écrit à la main)
	rm -rf docs/reference/schemas
	mkdir -p docs/reference/rules
	find docs/reference/rules -mindepth 2 -name '*.md' -delete
	uv run regis rules list -f markdown -D docs/reference/rules
	for cat in $$(find regis/schemas -mindepth 1 -maxdepth 1 -type d ! -name __pycache__ -exec basename {} \; | sort); do \
	  mkdir -p docs/reference/schemas/$$cat && \
	  uv run generate-schema-doc --config-file docs/json-schema-for-humans.config.json \
	    regis/schemas/$$cat docs/reference/schemas/$$cat || exit 1; \
	done

test: ## Tests et couverture de branches (90 %)
	uv run python -m pytest

security: ## pip-audit, bloquant à partir de HIGH (commande identique dans les trois dépôts)
	@d="$$(mktemp -d)" && trap 'rm -rf "$$d"' EXIT && \
	uv export -q --frozen --no-dev --no-emit-project --no-hashes -o "$$d/req.txt" && \
	{ uvx pip-audit==2.10.1 -r "$$d/req.txt" --no-deps --disable-pip --progress-spinner off --format=json --output "$$d/audit.json" || true; } && \
	test -s "$$d/audit.json" && \
	python3 .github/pip-audit-gate.py "$$d/audit.json" --min-severity HIGH

image: ## Construit et teste les deux variantes (les mêmes que .github/images.json)
	docker build --build-arg VARIANT=slim -t $(CI_IMAGE) .
	$(MAKE) smoke CI_IMAGE=$(CI_IMAGE)
	docker build --build-arg VARIANT=full -t $(CI_IMAGE)-full .
	$(MAKE) smoke CI_IMAGE=$(CI_IMAGE)-full

smoke: ## Vérifie qu'une image démarre : make smoke CI_IMAGE=<ref>
	docker run --rm $(CI_IMAGE) version

settings: ## Applique .github/settings.json au dépôt
	.github/apply-settings.sh
