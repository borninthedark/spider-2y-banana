---
title: "Security Hardening Guide"
date: 2025-10-23
draft: false
description: "Comprehensive security hardening recommendations for the Spider-2y-Banana GitOps infrastructure platform"
tags: ["security", "hardening", "kubernetes", "azure", "gitops", "devops"]
categories: ["Security", "Infrastructure"]
weight: 10
---

# Security Hardening Guide

This guide provides comprehensive security hardening recommendations for the Spider-2y-Banana GitOps platform. Implement these measures to enhance the security posture of your infrastructure, Kubernetes cluster, and applications.

## Table of Contents

1. [Infrastructure Security](#infrastructure-security)
2. [Kubernetes Cluster Security](#kubernetes-cluster-security)
3. [Application Security](#application-security)
4. [Secret Management](#secret-management)
5. [Network Security](#network-security)
6. [Access Control & Authentication](#access-control--authentication)
7. [Monitoring & Logging](#monitoring--logging)
8. [GitOps Security](#gitops-security)
9. [Container Security](#container-security)
10. [Compliance & Audit](#compliance--audit)

---

## Infrastructure Security

### Azure Resource Hardening

#### 1. Enable Azure Security Center

```bash
# Enable Azure Defender for all resource types
az security pricing create \
  --name VirtualMachines \
  --tier Standard

az security pricing create \
  --name ContainerRegistry \
  --tier Standard

az security pricing create \
  --name KeyVaults \
  --tier Standard

az security pricing create \
  --name SqlServers \
  --tier Standard
```

#### 2. Implement Network Segmentation

Update Bicep templates to restrict NSG rules:

```bicep
// bicep-infrastructure/modules/network.bicep
securityRules: [
  {
    name: 'AllowSSH'
    properties: {
      priority: 100
      direction: 'Inbound'
      access: 'Allow'
      protocol: 'Tcp'
      sourcePortRange: '*'
      destinationPortRange: '22'
      sourceAddressPrefix: '<YOUR_TRUSTED_IP>/32'  // Restrict to your IP only
      destinationAddressPrefix: '*'
    }
  }
  {
    name: 'AllowHTTPS'
    properties: {
      priority: 110
      direction: 'Inbound'
      access: 'Allow'
      protocol: 'Tcp'
      sourcePortRange: '*'
      destinationPortRange: '443'
      sourceAddressPrefix: 'Internet'
      destinationAddressPrefix: '*'
    }
  }
  {
    name: 'DenyAllOther'
    properties: {
      priority: 4096
      direction: 'Inbound'
      access: 'Deny'
      protocol: '*'
      sourcePortRange: '*'
      destinationPortRange: '*'
      sourceAddressPrefix: '*'
      destinationAddressPrefix: '*'
    }
  }
]
```

#### 3. Enable Azure Key Vault Access Policies

```bash
# Disable public network access to Key Vault
az keyvault update \
  --name $KEY_VAULT_NAME \
  --public-network-access Disabled

# Enable private endpoint
az network private-endpoint create \
  --name kv-private-endpoint \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --subnet private-subnet \
  --private-connection-resource-id $(az keyvault show -n $KEY_VAULT_NAME --query id -o tsv) \
  --group-id vault \
  --connection-name kv-connection
```

#### 4. Enable VM Encryption

```bash
# Enable Azure Disk Encryption on VMs
az vm encryption enable \
  --resource-group $RESOURCE_GROUP \
  --name k3s-vm-01 \
  --disk-encryption-keyvault $KEY_VAULT_NAME
```

#### 5. Implement Azure Bastion (Recommended)

Remove direct SSH access and use Azure Bastion for secure VM access:

```bash
# Create Bastion subnet
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name AzureBastionSubnet \
  --address-prefix 10.0.3.0/27

# Create Bastion host
az network bastion create \
  --name bastion-spider-2y-banana \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --public-ip-address bastion-pip
```

---

## Kubernetes Cluster Security

### k3s Hardening

#### 1. Enable Audit Logging

Create audit policy:

```yaml
# /etc/rancher/k3s/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    omitStages:
      - "RequestReceived"
  - level: Request
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods", "services"]
    verbs: ["create", "delete", "update", "patch"]
```

Update k3s installation in Ansible:

```yaml
# ansible/roles/k3s/tasks/main.yml
- name: Configure k3s with security hardening
  shell: |
    curl -sfL https://get.k3s.io | sh -s - server \
      --write-kubeconfig-mode 644 \
      --kube-apiserver-arg audit-policy-file=/etc/rancher/k3s/audit-policy.yaml \
      --kube-apiserver-arg audit-log-path=/var/log/k3s-audit.log \
      --kube-apiserver-arg audit-log-maxage=30 \
      --kube-apiserver-arg audit-log-maxbackup=10 \
      --kube-apiserver-arg audit-log-maxsize=100 \
      --kube-apiserver-arg enable-admission-plugins=NodeRestriction,PodSecurityPolicy \
      --secrets-encryption
```

#### 2. Implement Pod Security Standards

Apply Pod Security Standards across namespaces:

```yaml
# gitops/platform/security/pod-security-standards.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: resume
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: baseline
    pod-security.kubernetes.io/warn: baseline
```

#### 3. Enable Network Policies

Install Calico or use k3s built-in network policies:

```yaml
# gitops/platform/network-policies/default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: resume
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-resume-ingress
  namespace: resume
spec:
  podSelector:
    matchLabels:
      app: resume
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-resume-egress
  namespace: resume
spec:
  podSelector:
    matchLabels:
      app: resume
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 53  # DNS
        - protocol: UDP
          port: 53
```

#### 4. Implement Resource Quotas and Limits

```yaml
# gitops/platform/resource-management/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: resume-quota
  namespace: resume
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    persistentvolumeclaims: "5"
    pods: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: resume-limits
  namespace: resume
spec:
  limits:
    - max:
        cpu: "1"
        memory: 2Gi
      min:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
      defaultRequest:
        cpu: 200m
        memory: 256Mi
      type: Container
```

#### 5. Enable RBAC with Least Privilege

```yaml
# gitops/platform/rbac/resume-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: resume-app
  namespace: resume
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: resume-role
  namespace: resume
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: resume-binding
  namespace: resume
subjects:
  - kind: ServiceAccount
    name: resume-app
    namespace: resume
roleRef:
  kind: Role
  name: resume-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Application Security

### Hugo Application Hardening

#### 1. Enhanced Security Headers

The Dockerfile already includes basic security headers. Enhance them further:

**Location:** `osyraa/Dockerfile`

```nginx
# Enhanced security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Remove server version
server_tokens off;

# Disable unnecessary HTTP methods
if ($request_method !~ ^(GET|HEAD|POST)$ ) {
    return 405;
}
```

#### 2. Application Security Context

Update Kubernetes deployment with security context:

```yaml
# gitops/applications/dev/resume-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume
  namespace: resume
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
      serviceAccountName: resume-app
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
        runAsGroup: 101
        fsGroup: 101
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: resume
          image: acrk3sdev.azurecr.io/resume:latest
          imagePullPolicy: Always
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            runAsUser: 101
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE
          ports:
            - containerPort: 80
              protocol: TCP
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: cache
              mountPath: /var/cache/nginx
            - name: run
              mountPath: /var/run
      volumes:
        - name: cache
          emptyDir: {}
        - name: run
          emptyDir: {}
```

---

## Secret Management

### External Secrets Operator Hardening

#### 1. Restrict Key Vault Access

```bash
# Create managed identity for External Secrets Operator
az identity create \
  --name mi-external-secrets \
  --resource-group $RESOURCE_GROUP

# Get identity client ID
MI_CLIENT_ID=$(az identity show -n mi-external-secrets -g $RESOURCE_GROUP --query clientId -o tsv)
MI_PRINCIPAL_ID=$(az identity show -n mi-external-secrets -g $RESOURCE_GROUP --query principalId -o tsv)

# Grant Key Vault access to managed identity
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $MI_PRINCIPAL_ID \
  --secret-permissions get list
```

#### 2. Implement Secret Rotation

```yaml
# gitops/platform/external-secrets/secret-rotation.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: resume-secrets
  namespace: resume
spec:
  refreshInterval: 1h  # Refresh every hour
  secretStoreRef:
    kind: ClusterSecretStore
    name: azure-keyvault
  target:
    name: resume-secrets
    creationPolicy: Owner
  data:
    - secretKey: db-password
      remoteRef:
        key: resume-db-password
```

#### 3. Enable Secret Audit Logging

```bash
# Enable Key Vault diagnostic settings
az monitor diagnostic-settings create \
  --name kv-audit-logs \
  --resource $(az keyvault show -n $KEY_VAULT_NAME --query id -o tsv) \
  --logs '[{"category": "AuditEvent", "enabled": true}]' \
  --workspace $(az monitor log-analytics workspace show -g $RESOURCE_GROUP -n logs-workspace --query id -o tsv)
```

---

## Network Security

### TLS/SSL Hardening

#### 1. Enforce TLS 1.2+ Only

```yaml
# gitops/platform/ingress-nginx/ingress-nginx-values.yaml
controller:
  config:
    ssl-protocols: "TLSv1.2 TLSv1.3"
    ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    ssl-prefer-server-ciphers: "on"
    hsts: "true"
    hsts-max-age: "31536000"
    hsts-include-subdomains: "true"
    hsts-preload: "true"
```

#### 2. Implement cert-manager with ACME

```yaml
# gitops/platform/cert-manager/cluster-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: info@princetonstrong.online
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

#### 3. Enable mTLS for Service-to-Service Communication

Consider implementing a service mesh like Linkerd for mTLS:

```bash
# Install Linkerd
curl -sL https://run.linkerd.io/install | sh
linkerd install | kubectl apply -f -
linkerd check

# Enable auto-injection for namespace
kubectl annotate namespace resume linkerd.io/inject=enabled
```

---

## Access Control & Authentication

### ArgoCD Hardening

#### 1. Enable SSO with Azure AD

```yaml
# gitops/platform/argocd/argocd-cm-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.princetonstrong.online
  oidc.config: |
    name: Azure AD
    issuer: https://login.microsoftonline.com/$TENANT_ID/v2.0
    clientID: $CLIENT_ID
    clientSecret: $CLIENT_SECRET
    requestedScopes:
      - openid
      - profile
      - email
```

#### 2. Implement RBAC Policies

```yaml
# gitops/platform/argocd/argocd-rbac-cm.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    # Admin role
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow

    # Developer role - read-only production, full access dev
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, *, dev/*, allow
    p, role:developer, repositories, get, *, allow

    # Assign roles to Azure AD groups
    g, "azure-ad-group-admin-id", role:admin
    g, "azure-ad-group-dev-id", role:developer
```

#### 3. Disable Default Admin Account

```bash
# Update ArgoCD admin password and disable account
kubectl patch cm argocd-cm -n argocd --type merge -p '{"data":{"admin.enabled":"false"}}'
```

---

## Monitoring & Logging

### Enhanced Observability

#### 1. Deploy Falco for Runtime Security

```yaml
# gitops/platform/security/falco.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: falco
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: falco
  namespace: kube-system
spec:
  repo: https://falcosecurity.github.io/charts
  chart: falco
  targetNamespace: falco
  valuesContent: |-
    falco:
      grpc:
        enabled: true
      grpcOutput:
        enabled: true
    falcosidekick:
      enabled: true
      webui:
        enabled: true
```

#### 2. Configure Prometheus Alerts

```yaml
# gitops/platform/monitoring/prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: security-alerts
  namespace: monitoring
spec:
  groups:
    - name: security
      interval: 30s
      rules:
        - alert: UnauthorizedAccess
          expr: rate(nginx_http_requests_total{status=~"401|403"}[5m]) > 10
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High rate of unauthorized access attempts"
            description: "{{ $value }} unauthorized requests per second"

        - alert: PodSecurityViolation
          expr: kube_pod_container_status_running{namespace!~"kube-system|kube-public"} == 1
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod running with security violations"
```

#### 3. Centralized Logging with Loki

```yaml
# gitops/platform/logging/loki-stack.yaml
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: loki-stack
  namespace: kube-system
spec:
  repo: https://grafana.github.io/helm-charts
  chart: loki-stack
  targetNamespace: logging
  valuesContent: |-
    loki:
      persistence:
        enabled: true
        size: 10Gi
      config:
        auth_enabled: false
        limits_config:
          retention_period: 744h  # 31 days
    promtail:
      enabled: true
    grafana:
      enabled: false  # Using existing Grafana
```

---

## GitOps Security

### Repository Security

#### 1. Enable Branch Protection

Configure branch protection rules via GitHub:

```bash
# Via GitHub CLI
gh api repos/borninthedark/spider-2y-banana/branches/main/protection \
  --method PUT \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_pull_request_reviews[dismiss_stale_reviews]=true \
  --field required_status_checks[strict]=true \
  --field enforce_admins=true \
  --field restrictions=null
```

#### 2. Implement Pre-commit Hooks

Already configured in `.pre-commit-config.yaml`. Ensure developers use it:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### 3. Sign Git Commits

```bash
# Generate GPG key
gpg --full-generate-key

# Get key ID
gpg --list-secret-keys --keyid-format=long

# Configure Git
git config --global user.signingkey <KEY_ID>
git config --global commit.gpgsign true

# Add to GitHub
gpg --armor --export <KEY_ID>
# Add to GitHub: Settings → SSH and GPG keys → New GPG key
```

---

## Container Security

### Image Scanning & Hardening

#### 1. Enhanced Trivy Scanning in CI/CD

The workflow already includes Trivy scanning. Enhance it to fail on critical vulnerabilities:

```yaml
# osyraa/.github/workflows/build-deploy.yml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:latest
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail build on critical/high vulnerabilities

- name: Run Trivy filesystem scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: './osyraa'
    format: 'sarif'
    output: 'trivy-fs-results.sarif'
```

#### 2. Implement Image Policy with OPA Gatekeeper

```yaml
# gitops/platform/security/gatekeeper.yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8strustedimages
spec:
  crd:
    spec:
      names:
        kind: K8sTrustedImages
      validation:
        openAPIV3Schema:
          type: object
          properties:
            repos:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8strustedimages
        violation[{"msg": msg}] {
          image := input.review.object.spec.containers[_].image
          not strings.any_prefix_match(image, input.parameters.repos)
          msg := sprintf("Image '%v' is not from trusted registry", [image])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sTrustedImages
metadata:
  name: trusted-images-only
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces:
      - resume
      - monitoring
  parameters:
    repos:
      - "acrk3sdev.azurecr.io/"
      - "docker.io/library/"
      - "ghcr.io/"
```

---

## Compliance & Audit

### CIS Benchmarks

#### 1. Run CIS Kubernetes Benchmark

```bash
# Install kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs -f job/kube-bench

# Or run directly on node
docker run --rm --pid=host -v /etc:/etc:ro -v /var:/var:ro aquasec/kube-bench:latest
```

#### 2. Azure CIS Compliance

```bash
# Run Azure Security Benchmark assessment
az security assessment list \
  --resource-group $RESOURCE_GROUP

# Enable Microsoft Cloud Security Benchmark
az security auto-provisioning-setting update \
  --name default \
  --auto-provision on
```

### Backup & Disaster Recovery

#### 1. Implement Velero for Cluster Backups

```bash
# Install Velero
velero install \
  --provider azure \
  --plugins velero/velero-plugin-for-microsoft-azure:v1.9.0 \
  --bucket velero-backups \
  --secret-file ./credentials-velero \
  --backup-location-config resourceGroup=$RESOURCE_GROUP,storageAccount=$STORAGE_ACCOUNT \
  --snapshot-location-config apiTimeout=5m,resourceGroup=$RESOURCE_GROUP

# Schedule daily backups
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --include-namespaces resume,argocd,monitoring
```

---

## Implementation Priority

### Critical (Implement Immediately)

1. ✅ Enable network segmentation and restrict NSG rules
2. ✅ Implement RBAC with least privilege
3. ✅ Enable Pod Security Standards
4. ✅ Configure security headers in applications
5. ✅ Rotate and secure all credentials
6. ✅ Enable audit logging on k3s
7. ✅ Implement network policies

### High Priority (Implement Within 1 Week)

1. Deploy Falco for runtime security monitoring
2. Implement OPA Gatekeeper for policy enforcement
3. Enable mTLS between services
4. Configure centralized logging with Loki
5. Implement automated backups with Velero
6. Enable Azure Security Center Defender

### Medium Priority (Implement Within 1 Month)

1. Migrate to Azure Bastion for VM access
2. Implement SSO for ArgoCD and Grafana
3. Enable VM disk encryption
4. Run CIS benchmarks and remediate findings
5. Implement secret rotation automation
6. Configure private endpoints for PaaS services

### Long-term Improvements

1. Implement service mesh (Istio/Linkerd)
2. Migrate to distroless container images
3. Implement zero-trust networking
4. Advanced threat detection with Azure Sentinel
5. Implement chaos engineering practices
6. SOC 2 compliance preparation

---

## Security Checklist

Use this checklist to track hardening progress:

### Infrastructure
- [ ] Network segmentation implemented
- [ ] Azure Security Center enabled
- [ ] VM encryption enabled
- [ ] Key Vault private endpoints configured
- [ ] Bastion host deployed
- [ ] NSG rules restricted to minimum required

### Kubernetes
- [ ] Audit logging enabled
- [ ] Pod Security Standards enforced
- [ ] Network policies implemented
- [ ] Resource quotas configured
- [ ] RBAC with least privilege
- [ ] Secrets encryption enabled

### Applications
- [ ] Security headers configured
- [ ] Running as non-root user
- [ ] Read-only root filesystem
- [ ] No privilege escalation
- [ ] Resource limits defined
- [ ] Health checks configured

### Access Control
- [ ] SSO/SAML configured
- [ ] MFA enforced for all users
- [ ] Default admin accounts disabled
- [ ] Regular access reviews conducted
- [ ] Audit logs reviewed monthly

### Monitoring
- [ ] Falco deployed and alerting
- [ ] Prometheus alerts configured
- [ ] Centralized logging enabled
- [ ] Security dashboard created
- [ ] On-call rotation established

### Compliance
- [ ] CIS benchmarks run and remediated
- [ ] Vulnerability scans automated
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Security training completed

---

## Security Contacts

**Security Issues:** Open a private security advisory on GitHub
**General Questions:** info@princetonstrong.online
**Emergency Contact:** [On-call rotation]

## Additional Resources

- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [Azure Security Best Practices](https://learn.microsoft.com/en-us/azure/security/)
- [Kubernetes Security Documentation](https://kubernetes.io/docs/concepts/security/)
- [OWASP Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)
- [NSA Kubernetes Hardening Guide](https://media.defense.gov/2021/Aug/03/2002820425/-1/-1/1/CTR_KUBERNETES%20HARDENING%20GUIDANCE.PDF)

---

**Last Updated:** 2025-10-23
**Version:** 1.0
**Author:** Princeton A. Strong
**Review Cycle:** Quarterly
