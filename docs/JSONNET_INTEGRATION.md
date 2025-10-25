# Jsonnet Integration Guide

## Overview

Spider-2y-Banana now includes **Kubernetes libsonnet** (jsonnet) for programmatic Kubernetes manifest generation, providing a type-safe, composable alternative to plain YAML.

## What Was Added

### 📁 New Directory Structure

```
spider-2y-banana/
└── jsonnet/                          # NEW! Jsonnet manifest generation
    ├── jsonnetfile.json              # Dependency management
    ├── Makefile                      # Build automation
    ├── README.md                     # Comprehensive guide
    ├── .gitignore                    # Ignore vendor/ and output/
    ├── components/                   # Reusable components
    │   └── resume.libsonnet          # Resume app component
    ├── environments/                 # Environment configs
    │   ├── dev/
    │   │   └── main.jsonnet         # Dev configuration
    │   └── prod/
    │       └── main.jsonnet         # Prod configuration
    └── lib/                          # Custom libraries (optional)
```

## Benefits of Jsonnet

### vs. Plain YAML

| Feature | YAML | Jsonnet |
|---------|------|---------|
| Reusability | ❌ Copy-paste | ✅ Functions & libraries |
| Type Safety | ❌ None | ✅ Compile-time checks |
| DRY Principle | ❌ Repetitive | ✅ Composable |
| Multi-env | ❌ Multiple files | ✅ Single source |
| Validation | ⚠️ kubectl only | ✅ Built-in + kubectl |
| Refactoring | ❌ Manual | ✅ Automated |
| Testing | ⚠️ Limited | ✅ Unit testable |

### vs. Helm

| Feature | Helm | Jsonnet |
|---------|------|---------|
| Learning Curve | Moderate | Steep |
| Templating | Go templates | Full language |
| Packaging | ✅ Charts | ❌ No built-in |
| Type Safety | ❌ Runtime | ✅ Compile-time |
| Dependencies | ✅ Chart repos | ✅ jsonnet-bundler |
| Complexity | Moderate | Low (for simple) |

### vs. Kustomize

| Feature | Kustomize | Jsonnet |
|---------|-----------|---------|
| Approach | Overlay patches | Programmatic |
| Logic | ❌ Limited | ✅ Full programming |
| Validation | kubectl | Built-in + kubectl |
| Reusability | Bases | Libraries |
| Native k8s | ✅ Built-in | ⚠️ External tool |

## Quick Start

### 1. Install Prerequisites

```bash
# Install Go (if not already installed)
sudo apt install golang-go  # Ubuntu/Debian
brew install go             # macOS

# Install jsonnet tools
go install github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest
go install github.com/google/go-jsonnet/cmd/jsonnet@latest
go install github.com/google/go-jsonnet/cmd/jsonnetfmt@latest

# Add to PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

### 2. Install Dependencies

```bash
cd jsonnet
make install
```

This downloads k8s-libsonnet to `vendor/`.

### 3. Generate Manifests

```bash
# Generate dev environment
make dev

# Generate prod environment
make prod

# Check output
ls output/dev/
# namespace.yaml  deployment.yaml  service.yaml  ingress.yaml  servicemonitor.yaml
```

### 4. Apply to Cluster

```bash
# Validate first
make validate-dev

# Show diff
make diff-dev

# Apply
make apply-dev
```

## Component Architecture

### Resume Component

The `components/resume.libsonnet` defines a reusable resume application:

```jsonnet
local resume = import 'components/resume.libsonnet';

local app = resume.new(
  name='resume',
  namespace='resume',
  image='acrk3sdev.azurecr.io/resume:latest',
  replicas=2
);
```

**What it creates:**
- ✅ Namespace
- ✅ Deployment (with health checks)
- ✅ Service (HTTP + metrics)
- ✅ Ingress (HTTPS with cert-manager)
- ✅ ServiceMonitor (Prometheus)

**Features:**
- Type-safe configuration
- Default resource limits
- Health check probes
- Metrics exporter sidecar
- Environment-specific overrides

## Integration with GitOps

### Workflow Options

#### Option 1: Generate → Commit → ArgoCD

```bash
# Generate manifests
cd jsonnet
make dev

# Copy to gitops repo
cp output/dev/*.yaml ../gitops/applications/dev/

# Commit
git add ../gitops/applications/dev/
git commit -m "Update from jsonnet"
git push

# ArgoCD syncs automatically
```

#### Option 2: CI/CD Pipeline

```yaml
# .github/workflows/jsonnet.yml
name: Generate Manifests

on:
  push:
    paths: ['jsonnet/**']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v4

      - name: Install jsonnet
        run: |
          go install github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest
          go install github.com/google/go-jsonnet/cmd/jsonnet@latest

      - name: Generate manifests
        run: |
          cd jsonnet
          make dev prod

      - name: Update gitops
        run: |
          cp jsonnet/output/dev/* gitops/applications/dev/
          git add gitops/applications/dev/
          git commit -m "Update from jsonnet [skip ci]"
          git push
```

#### Option 3: ArgoCD Native (Future)

ArgoCD can potentially use jsonnet directly:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: resume
spec:
  source:
    repoURL: https://github.com/borninthedark/spider-2y-banana
    path: jsonnet/environments/dev
    jsonnet: {}
```

## Creating New Components

### 1. Create Component File

```jsonnet
// components/myapp.libsonnet
local k = import 'k.libsonnet';

{
  new(name, namespace, image, replicas=2):: {
    local this = self,

    config:: {
      name: name,
      namespace: namespace,
      image: image,
      replicas: replicas,
    },

    deployment:
      k.apps.v1.deployment.new(
        name=this.config.name,
        replicas=this.config.replicas,
        containers=[
          k.core.v1.container.new('myapp', this.config.image)
          + k.core.v1.container.withPorts([
              k.core.v1.containerPort.new('http', 8080),
            ]),
        ]
      )
      + k.apps.v1.deployment.metadata.withNamespace(this.config.namespace),

    service:
      k.core.v1.service.new(
        this.config.name,
        { app: this.config.name },
        [k.core.v1.servicePort.newNamed('http', 80, 8080)]
      )
      + k.core.v1.service.metadata.withNamespace(this.config.namespace),
  },
}
```

### 2. Use in Environment

```jsonnet
// environments/dev/myapp.jsonnet
local myapp = import '../../components/myapp.libsonnet';

local app = myapp.new(
  name='myapp',
  namespace='default',
  image='myimage:latest',
  replicas=2
);

{
  'deployment.yaml': app.deployment,
  'service.yaml': app.service,
}
```

### 3. Build and Apply

```bash
cd jsonnet
jsonnet -J vendor -m output/dev environments/dev/myapp.jsonnet
kubectl apply -f output/dev/
```

## Advanced Usage

### Mixins for Common Patterns

```jsonnet
// lib/mixins.libsonnet
{
  // Add monitoring labels
  withMonitoring:: {
    metadata+: {
      labels+: { monitoring: 'enabled' }
    }
  },

  // Configure HA
  withHA(replicas=3):: {
    spec+: { replicas: replicas }
  },

  // Add node affinity
  withNodeAffinity(key, value):: {
    spec+: {
      template+: {
        spec+: {
          affinity: {
            nodeAffinity: {
              requiredDuringSchedulingIgnoredDuringExecution: {
                nodeSelectorTerms: [{
                  matchExpressions: [{
                    key: key,
                    operator: 'In',
                    values: [value],
                  }],
                }],
              },
            },
          },
        },
      },
    },
  },
}

// Use mixins
local mixins = import '../lib/mixins.libsonnet';

deployment
  + mixins.withMonitoring
  + mixins.withHA(5)
  + mixins.withNodeAffinity('kubernetes.io/arch', 'amd64')
```

### Environment Inheritance

```jsonnet
// lib/base.libsonnet
{
  defaults:: {
    replicas: 2,
    resources: {
      requests: { memory: '64Mi', cpu: '100m' },
      limits: { memory: '128Mi', cpu: '200m' },
    },
  },
}

// environments/prod/main.jsonnet
local base = import '../../lib/base.libsonnet';

local config = base.defaults {
  replicas: 3,  // Override for prod
  resources+: {
    limits+: {
      memory: '256Mi',  // Increase for prod
    },
  },
};
```

## Testing Jsonnet

### Unit Tests

```jsonnet
// components/resume_test.jsonnet
local resume = import 'resume.libsonnet';

local app = resume.new('test', 'test-ns', 'image:test', 2);

// Test assertions
assert app.deployment.metadata.name == 'test';
assert app.deployment.spec.replicas == 2;
assert app.service.spec.ports[0].port == 80;

'Tests passed'
```

Run tests:
```bash
jsonnet -J vendor components/resume_test.jsonnet
```

## Comparison: YAML vs Jsonnet

### Original YAML (109 lines)

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: resume
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume
  namespace: resume
  labels:
    app: resume
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resume
  template:
    metadata:
      labels:
        app: resume
    spec:
      containers:
        - name: resume
          image: acrk3sdev.azurecr.io/resume:latest
          ports:
            - containerPort: 80
              name: http
# ... 80+ more lines ...
```

### Jsonnet (15 lines)

```jsonnet
local resume = import '../../components/resume.libsonnet';

local app = resume.new(
  name='resume',
  namespace='resume',
  image='acrk3sdev.azurecr.io/resume:latest',
  replicas=2
);

{
  'namespace.yaml': app.namespace,
  'deployment.yaml': app.deployment,
  'service.yaml': app.service,
  'ingress.yaml': app.ingress,
  'servicemonitor.yaml': app.serviceMonitor,
}
```

**Reduction**: 109 lines → 15 lines (86% reduction)

## Best Practices

1. **Keep components generic** - Use parameters for all variants
2. **Environment-specific** only in `environments/`
3. **Shared logic** goes in `lib/`
4. **Always format** before committing (`make fmt`)
5. **Validate** before applying (`make validate-dev`)
6. **Document** component parameters and usage
7. **Test** with unit tests
8. **Version** k8s-libsonnet in `jsonnetfile.json`

## Troubleshooting

### Jsonnet Not Found

```bash
# Ensure Go bin is in PATH
export PATH=$PATH:$(go env GOPATH)/bin

# Reinstall
go install github.com/google/go-jsonnet/cmd/jsonnet@latest
```

### k8s-libsonnet Not Found

```bash
# Reinstall dependencies
cd jsonnet
rm -rf vendor/
jb install
```

### Syntax Errors

```bash
# Check syntax
jsonnet environments/dev/main.jsonnet

# Format all files
make fmt
```

### Generated YAML Issues

```bash
# Validate against cluster
kubectl apply --dry-run=client -f output/dev/

# Compare with kubectl
kubectl diff -f output/dev/
```

## Migration Path

### From Existing YAML

1. Keep existing YAML in `gitops/`
2. Create jsonnet components
3. Generate and compare: `diff output/dev/ gitops/applications/dev/`
4. Gradually replace YAML with jsonnet
5. Eventually: jsonnet becomes source of truth

### Incremental Adoption

- ✅ Start with one component (resume)
- ✅ Test in dev environment
- ✅ Compare generated vs existing
- ✅ Apply and verify
- ✅ Add more components as needed
- ✅ Keep YAML as backup during transition

## Resources

- [Jsonnet Tutorial](https://jsonnet.org/learning/tutorial.html)
- [k8s-libsonnet Documentation](https://jsonnet-libs.github.io/k8s-libsonnet/)
- [Jsonnet Bundler](https://github.com/jsonnet-bundler/jsonnet-bundler)
- [Jsonnet Best Practices](https://jsonnet.org/learning/getting_started.html)
- [ArgoCD Jsonnet Support](https://argo-cd.readthedocs.io/en/stable/user-guide/jsonnet/)

## Next Steps

1. ✅ Install jsonnet tools
2. ✅ Run `make install` to get dependencies
3. ✅ Generate manifests with `make dev`
4. ✅ Review generated YAML in `output/dev/`
5. ✅ Apply to cluster with `make apply-dev`
6. ✅ Create additional components as needed
7. ✅ Integrate with CI/CD pipeline

---

**Spider-2y-Banana** now supports three manifest management approaches:
1. **Plain YAML** (in `gitops/`)
2. **Jsonnet** (in `jsonnet/`) - **NEW!**
3. **Crossplane** (for infrastructure)

Choose the approach that best fits your workflow!
