.PHONY: website website-build website-stop website-clean

website: ## Start website dev server with hot reload on http://localhost:3000
	docker compose -f website/docker-compose.yml up dev --build

website-build: ## Build static website into website/out/
	rm -rf website/out
	docker compose -f website/docker-compose.yml run --rm build

website-stop: ## Stop website dev server
	docker compose -f website/docker-compose.yml down

website-clean: ## Remove website build output and Docker artifacts
	rm -rf website/out
	docker compose -f website/docker-compose.yml down --rmi local --volumes
