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
	git diff --exit-code -- docs/reference || { echo "docs/reference est périmé : lancer 'make reference' et commiter."; exit 1; }
	! git ls-files -- 'docs/superpowers/plans/**' '**/search-index.json' | grep .

reference: ## Régénère la référence des règles et des schémas
	uv run regis rules list -f markdown -D docs/reference/rules
	for cat in $$(cd regis/schemas && ls -d */ | tr -d /); do \
	  uv run generate-schema-doc --config-file docs/json-schema-for-humans.config.json \
	    regis/schemas/$$cat docs/reference/schemas/$$cat; \
	done

test: ## Tests et couverture de branches (90 %)
	uv run python -m pytest

security: ## pip-audit, bloquant à partir de HIGH (commande identique dans les trois dépôts)
	@d=$$(mktemp -d) && \
	uv export --frozen --no-dev --no-emit-project --no-hashes -o $$d/req.txt && \
	{ uvx pip-audit -r $$d/req.txt --no-deps --disable-pip --progress-spinner off --format=json --output $$d/audit.json || true; } && \
	test -s $$d/audit.json && \
	python3 .github/pip-audit-gate.py $$d/audit.json --min-severity HIGH

image: ## Construit et teste les deux variantes
	docker build --build-arg VARIANT=slim -t $(CI_IMAGE) .
	$(MAKE) smoke CI_IMAGE=$(CI_IMAGE)
	docker build --build-arg VARIANT=full -t $(CI_IMAGE)-full .
	$(MAKE) smoke CI_IMAGE=$(CI_IMAGE)-full

smoke: ## Vérifie qu'une image démarre : make smoke CI_IMAGE=<ref>
	docker run --rm $(CI_IMAGE) version

settings: ## Applique .github/settings.json au dépôt
	.github/apply-settings.sh
