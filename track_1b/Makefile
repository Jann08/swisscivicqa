.PHONY: run full test models down

IMAGE := swisscivicqa:latest

# Default target for judges: verify dataset, tests and all published numbers (no model needed).
run:
	docker build -q -t $(IMAGE) . >/dev/null
	docker run --rm $(IMAGE) verify

# Re-run inference + judging from scratch with local llama.cpp servers (CPU, ~2-4 h).
full: models
	docker compose -f docker-compose.full.yml up -d --wait llm judge
	docker build -q -t $(IMAGE) . >/dev/null
	docker run --rm --network swisscivicqa_default \
		-e MODEL_URL=http://llm:8080/v1 -e JUDGE_URL=http://judge:8080/v1 \
		-v $(CURDIR)/data/results:/app/data/results $(IMAGE) full
	docker compose -f docker-compose.full.yml down

models:
	sh scripts/download_models.sh

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

down:
	docker compose -f docker-compose.full.yml down
