# Resume Application

A static resume website built with Hugo and deployed via GitOps.

## Overview

This Hugo-based static site serves as a professional resume for Princeton A. Strong, demonstrating modern web deployment practices with:

- **Hugo**: Fast static site generator
- **Podman/Buildah**: Daemonless multi-stage container builds with nginx
- **Kubernetes**: Cloud-native deployment
- **GitOps**: Automated deployment via ArgoCD
- **Monitoring**: Prometheus metrics with nginx-exporter
- **CI/CD**: GitHub Actions pipeline with Trivy security scanning

## Features

### Health Checks
- Liveness probe: Ensures container is running
- Readiness probe: Ensures container is ready to serve traffic
- Startup probe: Handles slow container startup

### Monitoring
- nginx-prometheus-exporter sidecar
- Metrics endpoint on port 9113
- ServiceMonitor for Prometheus integration
- Custom Grafana dashboard

### Security
- Security headers (X-Frame-Options, CSP, etc.)
- TLS with Let's Encrypt via cert-manager
- Non-root nginx container
- Minimal Alpine-based image

## Local Development

### Prerequisites
- Podman and Buildah (or Docker as alternative)
- Hugo (optional, for local preview)

### Build Hugo Site Locally
```bash
# Using Podman
podman run --rm -v $(pwd):/src:Z -p 1313:1313 klakegg/hugo:0.111.3-alpine server

# Or with Hugo installed
hugo server -D
```

Access at: http://localhost:1313

### Build Container Image
```bash
# Using Buildah (recommended)
buildah bud \
  --format docker \
  --layers \
  --build-arg DOMAIN_NAME=princetonstrong.online \
  -t osyraa:local \
  .

# Or using Podman
podman build \
  --build-arg DOMAIN_NAME=princetonstrong.online \
  -t osyraa:local \
  .
```

### Run Container Locally
```bash
podman run -p 8080:80 osyraa:local
```

Access at: http://localhost:8080

## Testing

### Run Build Tests
```bash
cd tests
./test_build.sh
```

Tests:
- Hugo build succeeds
- index.html is generated
- Resume content is present
- HTML structure is valid

### Run Docker Tests
```bash
cd tests
./test_docker.sh
```

Tests:
- Docker image builds
- Container starts successfully
- HTTP endpoint returns 200
- Content is accessible
- Security headers are present

## CI/CD Pipeline

### GitHub Actions Workflow

**Workflow**: `.github/workflows/build-and-push.yml`

Triggers on:
- Push to `main` branch
- Changes in `osyraa/` directory or workflow file
- Pull requests to `main` branch
- Manual workflow dispatch

Pipeline steps:
1. **Checkout**: Retrieve repository code
2. **Install Tools**: Install Podman, Buildah, and Skopeo
3. **Lint Containerfile**: Validate with Hadolint
4. **Generate Tags**: Create image tags based on event type
5. **Build with Buildah**: Build OCI-compliant container image
6. **Scan with Trivy**: Security vulnerability scanning
7. **Tag Image**: Apply all generated tags
8. **Login to GHCR**: Authenticate with GitHub Container Registry
9. **Push with Podman**: Push all image tags to GHCR
10. **Get Digest**: Retrieve image digest using Skopeo
11. **Generate Attestation**: Create build provenance (security)

### Image Tags

Automatically generated tags:
- `latest`: Latest build from main branch
- `main-<sha>`: Build from main branch with commit SHA
- `pr-<number>`: Pull request builds
- Semantic version tags (if tagged releases)

### Required Secrets

No additional secrets required! The workflow uses:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- Grants permission to push to GitHub Container Registry (GHCR)

### Registry Information

- **Registry**: GitHub Container Registry (ghcr.io)
- **Image**: `ghcr.io/borninthedark/spider-2y-banana/osyraa`
- **Visibility**: Public (can be changed in package settings)
- **Cost**: Free for public repositories

## Kubernetes Deployment

### Resources Created

- **Namespace**: `resume`
- **Deployment**: 2 replicas with resource limits
- **Service**: ClusterIP on port 80
- **Ingress**: HTTPS with cert-manager
- **ServiceMonitor**: Prometheus metrics

### Resource Requirements

Per pod:
- **Requests**: 100m CPU, 96Mi memory (app + exporter)
- **Limits**: 300m CPU, 192Mi memory

### Probes Configuration

```yaml
livenessProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 12
```

## Monitoring

### Metrics Endpoint

nginx-prometheus-exporter exposes metrics on port 9113:
```
http://<pod-ip>:9113/metrics
```

### Key Metrics

- `nginx_http_requests_total`: Total HTTP requests
- `nginx_connections_active`: Active connections
- `nginx_connections_accepted`: Accepted connections
- `nginx_connections_handled`: Handled connections

### Grafana Dashboard

Access the custom resume dashboard:
1. Navigate to Grafana: https://grafana.princetonstrong.online
2. Go to Dashboards → Resume Application Dashboard
3. View metrics:
   - HTTP request rate
   - Active connections
   - CPU/Memory usage
   - Pod availability

## Content Management

### Updating Resume Content

1. Edit content in `content/_index.md`
2. Update configuration in `config.toml`
3. Test locally with `hugo server`
4. Commit and push to trigger CI/CD

### Content Structure

```
content/
└── _index.md           # Main resume content (Markdown)

layouts/
└── index.html          # HTML template with styling

config.toml             # Hugo configuration
```

### Adding Sections

Add new sections in `content/_index.md`:

```markdown
## New Section

### Subsection Title
Content here...
```

## Troubleshooting

### Image Build Fails

```bash
# Check Hugo build
podman run --rm -v $(pwd):/src:Z klakegg/hugo:0.111.3-alpine hugo --minify

# Check Containerfile syntax with linting
wget -qO /tmp/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
chmod +x /tmp/hadolint
/tmp/hadolint Containerfile

# Build without cache for debugging
buildah bud --no-cache -t osyraa:debug .
```

### Container Won't Start

```bash
# Check logs
kubectl logs -n resume <pod-name>

# Describe pod
kubectl describe pod -n resume <pod-name>
```

### Ingress Not Working

```bash
# Check ingress
kubectl get ingress -n resume
kubectl describe ingress resume -n resume

# Check certificate
kubectl get certificate -n resume
kubectl describe certificate resume-tls -n resume

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```

### Metrics Not Showing

```bash
# Check nginx-exporter sidecar
kubectl logs -n resume <pod-name> -c nginx-exporter

# Test metrics endpoint
kubectl port-forward -n resume <pod-name> 9113:9113
curl http://localhost:9113/metrics

# Check ServiceMonitor
kubectl get servicemonitor -n resume
```

## Performance

### Build Times
- Hugo build: ~500ms
- Docker image build: ~30s (with cache)
- Container startup: <5s

### Resource Usage
- Image size: ~25MB
- Memory usage: ~40MB (nginx + app)
- CPU usage: <50m under normal load

### Optimization Tips
1. Enable Hugo caching
2. Use Docker layer caching
3. Optimize images (if any added)
4. Enable gzip compression in nginx

## Security

### Implemented Measures

1. **Security Headers**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block

2. **TLS/HTTPS**
   - Automatic certificate from Let's Encrypt
   - Force HTTPS redirect

3. **Container Security**
   - Alpine-based minimal image
   - No unnecessary packages
   - Health checks enabled

4. **Kubernetes Security**
   - Resource limits enforced
   - Non-privileged container
   - Network policies (optional)

## Future Enhancements

- [ ] Add contact form with backend API
- [ ] Implement dark mode toggle
- [ ] Add blog section with Hugo
- [ ] Integrate with CMS (e.g., Netlify CMS)
- [ ] Add A/B testing capability
- [ ] Implement analytics
- [ ] Add multi-language support

## License

MIT License - See LICENSE file for details

## Contact

**Princeton A. Strong**
- Email: info@princetonstrong.online
- Website: https://resume.princetonstrong.online
