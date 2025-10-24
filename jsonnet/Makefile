# Makefile for building Kubernetes manifests from Jsonnet

.PHONY: all clean install dev prod fmt lint

# Default target
all: dev

# Install dependencies
install:
	@echo "Installing jsonnet-bundler and jsonnet..."
	@command -v jb >/dev/null 2>&1 || { echo "Installing jb..."; go install -a github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest; }
	@command -v jsonnet >/dev/null 2>&1 || { echo "Installing jsonnet..."; go install github.com/google/go-jsonnet/cmd/jsonnet@latest; }
	@echo "Installing dependencies..."
	jb install

# Build dev environment
dev: install
	@echo "Building dev environment manifests..."
	@mkdir -p output/dev
	jsonnet -J vendor -m output/dev --ext-str DOMAIN_NAME="${DOMAIN_NAME:-princetonstrong.online}" environments/dev/main.jsonnet

# Build prod environment
prod: install
	@echo "Building prod environment manifests..."
	@mkdir -p output/prod
	jsonnet -J vendor -m output/prod --ext-str DOMAIN_NAME="${DOMAIN_NAME:-princetonstrong.online}" environments/prod/main.jsonnet

# Format jsonnet files
fmt:
	@echo "Formatting jsonnet files..."
	@find . -name '*.jsonnet' -o -name '*.libsonnet' | xargs jsonnetfmt -i

# Lint jsonnet files
lint:
	@echo "Linting jsonnet files..."
	@find . -name '*.jsonnet' -o -name '*.libsonnet' | xargs jsonnet-lint

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf output/
	rm -rf vendor/

# Apply dev manifests
apply-dev: dev
	kubectl apply -f output/dev/

# Apply prod manifests
apply-prod: prod
	kubectl apply -f output/prod/

# Show diff for dev
diff-dev: dev
	kubectl diff -f output/dev/ || true

# Show diff for prod
diff-prod: prod
	kubectl diff -f output/prod/ || true

# Validate generated manifests
validate-dev: dev
	@echo "Validating dev manifests..."
	@for file in output/dev/*.yaml; do \
		echo "Validating $$file..."; \
		kubectl apply --dry-run=client -f $$file; \
	done

validate-prod: prod
	@echo "Validating prod manifests..."
	@for file in output/prod/*.yaml; do \
		echo "Validating $$file..."; \
		kubectl apply --dry-run=client -f $$file; \
	done

# Help
help:
	@echo "Available targets:"
	@echo "  install      - Install jsonnet-bundler and dependencies"
	@echo "  dev          - Build dev environment manifests"
	@echo "  prod         - Build prod environment manifests"
	@echo "  fmt          - Format jsonnet files"
	@echo "  lint         - Lint jsonnet files"
	@echo "  clean        - Clean generated files"
	@echo "  apply-dev    - Apply dev manifests to cluster"
	@echo "  apply-prod   - Apply prod manifests to cluster"
	@echo "  diff-dev     - Show diff for dev environment"
	@echo "  diff-prod    - Show diff for prod environment"
	@echo "  validate-dev - Validate dev manifests"
	@echo "  validate-prod - Validate prod manifests"
