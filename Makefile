test:
	pytest tests/ packages/ -v --tb=short \
	  --cov=. \
	  --cov-report=term-missing \
	  --cov-fail-under=95

lint:
	ruff check packages/ tests/ evals/ apps/
	mypy packages/ --ignore-missing-imports

# AI-layer evaluation. Mock mode: free, offline, deterministic — safe for CI.
eval:
	FINSIGHT_FORCE_MOCK=1 python evals/run.py --mock

# Live mode spends money. Latency numbers are only meaningful from this run.
eval-live:
	python evals/run.py --live

ci: lint test eval
	@echo "✅ All checks passed"

.PHONY: test lint eval eval-live ci
