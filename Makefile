.PHONY: test test-go test-python fmt docker-up docker-down

test: test-go test-python

test-go:
	cd src/go-agent && go test ./...

test-python:
	pytest tests\python

fmt:
	cd src/go-agent && gofmt -w ./cmd ./internal
	cd src/orchestrator && python -m compileall src

docker-up:
	docker compose up --build

docker-down:
	docker compose down
