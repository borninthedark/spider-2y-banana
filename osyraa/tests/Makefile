# Makefile for Osyraa Test Suite

.PHONY: help test test-go test-bash test-hugo test-docker clean coverage deps install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

deps: ## Download Go dependencies
	go mod download
	go mod verify

install: deps ## Install test dependencies
	@echo "Installing dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
	@command -v go >/dev/null 2>&1 || { echo "Go is required but not installed. Aborting." >&2; exit 1; }
	@echo "All dependencies installed!"

test: test-go ## Run all tests (default: Go tests)

test-go: ## Run Go test suite
	@echo "Running Go test suite..."
	go test -v -timeout 5m

test-hugo: ## Run only Hugo tests
	@echo "Running Hugo tests..."
	go test -v -run TestHugoSuite

test-docker: ## Run only Docker tests
	@echo "Running Docker tests..."
	go test -v -run TestDockerSuite

test-bash: ## Run bash test scripts
	@echo "Running bash test suite..."
	@if [ -f test_build.sh ]; then ./test_build.sh; fi
	@if [ -f test_docker.sh ]; then ./test_docker.sh; fi

coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	go test -v -coverprofile=coverage.out -covermode=atomic
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

coverage-text: ## Show coverage in terminal
	go test -v -coverprofile=coverage.out -covermode=atomic
	go tool cover -func=coverage.out

race: ## Run tests with race detection
	@echo "Running tests with race detection..."
	go test -v -race

bench: ## Run benchmarks
	go test -v -bench=. -benchmem

clean: ## Clean up test artifacts
	rm -rf ../public ../resources ../.hugo_build.lock
	rm -f coverage.out coverage.html
	docker ps -a | grep resume:test | awk '{print $$1}' | xargs -r docker rm -f
	docker images | grep resume | awk '{print $$3}' | xargs -r docker rmi -f

watch: ## Watch for changes and run tests (requires entr)
	@command -v entr >/dev/null 2>&1 || { echo "entr is required. Install with: apt install entr" >&2; exit 1; }
	@echo "Watching for changes..."
	find . -name "*.go" | entr -c make test-go

lint: ## Run Go linters
	@command -v golangci-lint >/dev/null 2>&1 || { echo "golangci-lint not installed. See: https://golangci-lint.run/usage/install/" >&2; exit 1; }
	golangci-lint run

fmt: ## Format Go code
	go fmt ./...
	gofmt -s -w .

vet: ## Run go vet
	go vet ./...

verify: fmt vet lint test ## Run all verification steps

ci: install verify ## Run all CI checks

.DEFAULT_GOAL := help
