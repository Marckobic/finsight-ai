test:
	pytest tests/ packages/ -v --tb=short \
	  --cov=. \
	  --cov-report=term-missing \
	  --cov-fail-under=95

lint:
	ruff check packages/ tests/
	mypy packages/ --ignore-missing-imports

ci: lint test
	@echo "✅ All checks passed"
