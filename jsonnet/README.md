# Jsonnet Kubernetes Manifests

This directory contains Jsonnet-based Kubernetes manifest generation using [k8s-libsonnet](https://github.com/jsonnet-libs/k8s-libsonnet).

## Why Jsonnet?

Jsonnet provides several advantages over plain YAML:

- **DRY Principle**: Reusable components and libraries
- **Type Safety**: Catch errors before deployment
- **Composability**: Mix and match components
- **Environment-specific**: Easy multi-environment management
- **Programmatic**: Use functions, variables, and logic
- **Validation**: Built-in syntax checking

## Directory Structure

```
jsonnet/
├── jsonnetfile.json           # Dependency management
├── Makefile                   # Build automation
├── components/                # Reusable components
│   └── resume.libsonnet       # Resume application component
├── environments/              # Environment-specific configs
│   ├── dev/
│   │   └── main.jsonnet      # Dev configuration
│   └── prod/
│       └── main.jsonnet      # Prod configuration
├── lib/                       # Custom libraries (optional)
└── output/                    # Generated YAML (gitignored)
    ├── dev/
    └── prod/
```

## Prerequisites

Install required tools:

```bash
# Install Go (required for jsonnet tools)
# On Ubuntu/Debian:
sudo apt install golang-go

# On macOS:
brew install go

# Install jsonnet and jsonnet-bundler
go install -a github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest
go install github.com/google/go-jsonnet/cmd/jsonnet@latest
go install github.com/google/go-jsonnet/cmd/jsonnetfmt@latest

# Add Go bin to PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

## Quick Start

### 1. Install Dependencies

```bash
cd jsonnet
make install
```

This will:
- Install k8s-libsonnet via jsonnet-bundler
- Download dependencies to `vendor/`

### 2. Build Manifests

```bash
# Build dev environment
make dev

# Build prod environment
make prod

# Build both
make all
```

Generated YAML files will be in `output/dev/` and `output/prod/`.

### 3. Apply to Cluster

```bash
# Apply dev manifests
make apply-dev

# Apply prod manifests
make apply-prod
```

## Component: Resume Application

The resume application component (`components/resume.libsonnet`) creates:

- **Namespace**: Isolated namespace for the app
- **Deployment**: Pod deployment with:
  - Main container (resume app)
  - Sidecar container (nginx-prometheus-exporter)
  - Health checks (liveness, readiness, startup)
  - Resource limits
- **Service**: ClusterIP service with HTTP and metrics ports
- **Ingress**: HTTPS ingress with cert-manager
- **ServiceMonitor**: Prometheus metrics collection

### Usage in Environment

```jsonnet
local resume = import '../../components/resume.libsonnet';

local app = resume.new(
  name='resume',
  namespace='resume',
  image='acrk3sdev.azurecr.io/resume:latest',
  replicas=2
);

{
  'deployment.yaml': app.deployment,
  'service.yaml': app.service,
  // ...
}
```

## Customization

### Modify Resources

Edit `components/resume.libsonnet` to change default resources:

```jsonnet
resources: {
  requests: {
    memory: '128Mi',  // Changed from 64Mi
    cpu: '200m',      // Changed from 100m
  },
  limits: {
    memory: '256Mi',
    cpu: '400m',
  },
},
```

### Add New Component

Create `components/myapp.libsonnet`:

```jsonnet
local k = import 'k.libsonnet';

{
  new(name, namespace, image):: {
    deployment: k.apps.v1.deployment.new(
      name=name,
      replicas=2,
      containers=[
        k.core.v1.container.new('myapp', image),
      ]
    ),
  },
}
```

Use in environment:

```jsonnet
local myapp = import '../../components/myapp.libsonnet';

local app = myapp.new('myapp', 'default', 'myimage:latest');

{
  'deployment.yaml': app.deployment,
}
```

## Environment-Specific Configuration

### Development (dev)

```jsonnet
local config = {
  namespace: 'resume',
  image: 'acrk3sdev.azurecr.io/resume:latest',
  replicas: 2,
};
```

### Production (prod)

```jsonnet
local config = {
  namespace: 'resume',
  image: 'acrk3sprod.azurecr.io/resume:latest',
  replicas: 3,  // More replicas
};
```

## Validation

### Pre-deployment Validation

```bash
# Validate dev manifests
make validate-dev

# Validate prod manifests
make validate-prod
```

### Show Diff

```bash
# Show what would change in dev
make diff-dev

# Show what would change in prod
make diff-prod
```

## Formatting and Linting

```bash
# Format all jsonnet files
make fmt

# Lint all jsonnet files
make lint
```

## Integration with GitOps

### Option 1: Generate and Commit

```bash
# Generate manifests
make dev

# Commit to gitops repo
cp output/dev/* ../gitops/applications/dev/
git add ../gitops/applications/dev/
git commit -m "Update dev manifests from jsonnet"
```

### Option 2: CI/CD Pipeline

```yaml
# .github/workflows/jsonnet.yml
name: Build Jsonnet

on:
  push:
    paths:
      - 'jsonnet/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Install jsonnet tools
        run: |
          go install github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest
          go install github.com/google/go-jsonnet/cmd/jsonnet@latest

      - name: Build manifests
        run: |
          cd jsonnet
          make dev prod

      - name: Update gitops repo
        run: |
          cp jsonnet/output/dev/* gitops/applications/dev/
          git config user.name "github-actions[bot]"
          git add gitops/applications/dev/
          git commit -m "Update manifests from jsonnet"
          git push
```

## Advanced Usage

### Using k8s-libsonnet Features

```jsonnet
local k = import 'k.libsonnet';

// Create deployment
local deployment = k.apps.v1.deployment.new(...)
  + k.apps.v1.deployment.metadata.withLabels({app: 'myapp'})
  + k.apps.v1.deployment.spec.template.spec.withNodeSelector({
      'kubernetes.io/arch': 'amd64'
    });

// Create ConfigMap
local configMap = k.core.v1.configMap.new('myconfig')
  + k.core.v1.configMap.withData({
      'config.json': std.manifestJsonEx({
        key: 'value'
      }, '  ')
    });
```

### Mixins and Overlays

Create overlays for common modifications:

```jsonnet
// lib/mixins.libsonnet
{
  withMonitoring:: {
    metadata+: {
      labels+: {
        monitoring: 'enabled'
      }
    }
  },

  withHighAvailability(replicas=3):: {
    spec+: {
      replicas: replicas
    }
  }
}

// Use in component
local mixins = import '../lib/mixins.libsonnet';

deployment
  + mixins.withMonitoring
  + mixins.withHighAvailability(5)
```

## Troubleshooting

### Dependency Issues

```bash
# Reinstall dependencies
rm -rf vendor/
make install
```

### Syntax Errors

```bash
# Check syntax
jsonnet environments/dev/main.jsonnet

# Format and fix
make fmt
```

### Generated YAML Issues

```bash
# Validate against cluster
kubectl apply --dry-run=client -f output/dev/

# Use kubectl diff
kubectl diff -f output/dev/
```

## Benefits Over Plain YAML

| Feature | YAML | Jsonnet |
|---------|------|---------|
| **Reusability** | Copy-paste | Functions & libraries |
| **Type Safety** | None | Compile-time checks |
| **DRY** | Repetitive | Composable |
| **Environments** | Multiple files | Single source |
| **Validation** | kubectl | Built-in + kubectl |
| **Refactoring** | Manual | Automated |
| **Testing** | Limited | Unit testable |

## Migration from YAML

To migrate existing YAML to Jsonnet:

1. Create component in `components/`
2. Define fields as parameters
3. Use k8s-libsonnet builders
4. Create environment-specific configs
5. Generate and compare YAML

Example:

```bash
# Generate from jsonnet
make dev

# Compare with existing YAML
diff output/dev/deployment.yaml gitops/applications/dev/resume-deployment.yaml
```

## Best Practices

1. **One component per file** in `components/`
2. **Environment-specific** only in `environments/`
3. **Shared logic** in `lib/`
4. **Always format** before committing (`make fmt`)
5. **Validate** before applying (`make validate-dev`)
6. **Use semantic versioning** for k8s-libsonnet
7. **Document** component parameters
8. **Test** generated YAML in dev first

## Resources

- [Jsonnet Tutorial](https://jsonnet.org/learning/tutorial.html)
- [k8s-libsonnet Docs](https://jsonnet-libs.github.io/k8s-libsonnet/)
- [Jsonnet Bundler](https://github.com/jsonnet-bundler/jsonnet-bundler)
- [Jsonnet Style Guide](https://jsonnet.org/learning/getting_started.html)

## Next Steps

1. Install jsonnet tools: `make install`
2. Build manifests: `make dev`
3. Validate output: `make validate-dev`
4. Apply to cluster: `make apply-dev`
5. Create new components as needed

---

**Managed by**: Jsonnet + k8s-libsonnet
**Kubernetes Version**: 1.28
