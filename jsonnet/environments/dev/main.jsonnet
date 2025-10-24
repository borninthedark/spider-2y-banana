// Development environment configuration
local resume = import '../../components/resume.libsonnet';

// Get domain from environment variable, with fallback
local baseDomain = if std.extVar('DOMAIN_NAME') != '' then std.extVar('DOMAIN_NAME') else 'princetonstrong.online';

local config = {
  namespace: 'resume',
  image: 'acrk3sdev.azurecr.io/resume:latest',
  replicas: 2,
  domain: 'resume.' + baseDomain,
};

// Create resume application
local app = resume.new(
  name='resume',
  namespace=config.namespace,
  image=config.image,
  replicas=config.replicas,
  domain=config.domain
);

// Export all resources
{
  'namespace.yaml': app.namespace,
  'deployment.yaml': app.deployment,
  'service.yaml': app.service,
  'ingress.yaml': app.ingress,
  'servicemonitor.yaml': app.serviceMonitor,
}
