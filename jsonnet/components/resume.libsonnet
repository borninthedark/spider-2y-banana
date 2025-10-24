// Resume application component using k8s-libsonnet
local k = import 'k.libsonnet';
local deployment = k.apps.v1.deployment;
local container = k.core.v1.container;
local port = k.core.v1.containerPort;
local service = k.core.v1.service;
local ingress = k.networking.v1.ingress;
local serviceMonitor = k.monitoring.coreos.com.v1.serviceMonitor;

{
  new(name, namespace, image, replicas=2, domain='resume.princetonstrong.online'):: {
    local this = self,

    config:: {
      name: name,
      namespace: namespace,
      image: image,
      replicas: replicas,
      domain: domain,
      resources: {
        requests: {
          memory: '64Mi',
          cpu: '100m',
        },
        limits: {
          memory: '128Mi',
          cpu: '200m',
        },
      },
      exporterResources: {
        requests: {
          memory: '32Mi',
          cpu: '50m',
        },
        limits: {
          memory: '64Mi',
          cpu: '100m',
        },
      },
    },

    namespace: k.core.v1.namespace.new(this.config.namespace),

    deployment:
      deployment.new(
        name=this.config.name,
        replicas=this.config.replicas,
        containers=[
          container.new('resume', this.config.image)
          + container.withPorts([
              port.new('http', 80),
            ])
          + container.resources.withRequests(this.config.resources.requests)
          + container.resources.withLimits(this.config.resources.limits)
          + container.livenessProbe.httpGet.withPath('/')
          + container.livenessProbe.httpGet.withPort('http')
          + container.livenessProbe.withInitialDelaySeconds(10)
          + container.livenessProbe.withPeriodSeconds(10)
          + container.livenessProbe.withTimeoutSeconds(3)
          + container.livenessProbe.withFailureThreshold(3)
          + container.readinessProbe.httpGet.withPath('/')
          + container.readinessProbe.httpGet.withPort('http')
          + container.readinessProbe.withInitialDelaySeconds(5)
          + container.readinessProbe.withPeriodSeconds(5)
          + container.readinessProbe.withTimeoutSeconds(3)
          + container.readinessProbe.withFailureThreshold(3)
          + container.startupProbe.httpGet.withPath('/')
          + container.startupProbe.httpGet.withPort('http')
          + container.startupProbe.withInitialDelaySeconds(0)
          + container.startupProbe.withPeriodSeconds(5)
          + container.startupProbe.withTimeoutSeconds(3)
          + container.startupProbe.withFailureThreshold(12),

          container.new('nginx-exporter', 'nginx/nginx-prometheus-exporter:0.11.0')
          + container.withArgs(['-nginx.scrape-uri=http://localhost:80/nginx_status'])
          + container.withPorts([
              port.new('metrics', 9113),
            ])
          + container.resources.withRequests(this.config.exporterResources.requests)
          + container.resources.withLimits(this.config.exporterResources.limits),
        ]
      )
      + deployment.metadata.withNamespace(this.config.namespace)
      + deployment.metadata.withLabels({ app: this.config.name }),

    service:
      service.new(
        this.config.name,
        { app: this.config.name },
        [
          k.core.v1.servicePort.newNamed('http', 80, 'http'),
          k.core.v1.servicePort.newNamed('metrics', 9113, 'metrics'),
        ]
      )
      + service.metadata.withNamespace(this.config.namespace)
      + service.metadata.withLabels({ app: this.config.name })
      + service.spec.withType('ClusterIP'),

    ingress:
      ingress.new(this.config.name)
      + ingress.metadata.withNamespace(this.config.namespace)
      + ingress.metadata.withAnnotations({
        'cert-manager.io/cluster-issuer': 'letsencrypt-prod',
        'nginx.ingress.kubernetes.io/force-ssl-redirect': 'true',
      })
      + ingress.spec.withIngressClassName('nginx')
      + ingress.spec.withTls([
          {
            hosts: [this.config.domain],
            secretName: this.config.name + '-tls',
          },
        ])
      + ingress.spec.withRules([
          {
            host: this.config.domain,
            http: {
              paths: [
                {
                  path: '/',
                  pathType: 'Prefix',
                  backend: {
                    service: {
                      name: this.config.name,
                      port: {
                        number: 80,
                      },
                    },
                  },
                },
              ],
            },
          },
        ]),

    serviceMonitor:
      {
        apiVersion: 'monitoring.coreos.com/v1',
        kind: 'ServiceMonitor',
        metadata: {
          name: this.config.name,
          namespace: this.config.namespace,
          labels: {
            app: this.config.name,
            release: 'kube-prometheus-stack',
          },
        },
        spec: {
          selector: {
            matchLabels: {
              app: this.config.name,
            },
          },
          endpoints: [
            {
              port: 'metrics',
              interval: '30s',
              path: '/metrics',
            },
          ],
        },
      },
  },
}
