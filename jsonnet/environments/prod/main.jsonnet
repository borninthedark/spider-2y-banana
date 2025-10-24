// Production environment configuration
local resume = import '../../components/resume.libsonnet';

local config = {
  namespace: 'resume',
  image: 'acrk3sprod.azurecr.io/resume:latest',
  replicas: 3,  // More replicas for production
};

// Create resume application
local app = resume.new(
  name='resume',
  namespace=config.namespace,
  image=config.image,
  replicas=config.replicas
);

// Export all resources
{
  'namespace.yaml': app.namespace,
  'deployment.yaml': app.deployment,
  'service.yaml': app.service,
  'ingress.yaml': app.ingress,
  'servicemonitor.yaml': app.serviceMonitor,
}
