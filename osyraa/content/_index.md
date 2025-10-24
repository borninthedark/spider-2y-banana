---
title: "Princeton A. Strong - Professional Resume"
date: 2024-01-01
draft: false
---

## Professional Summary

Platform Engineer specializing in secure hybrid cloud & on-prem solutions by leveraging Python automation, Open Source technologies, & DevSecOps best practices.

## Experience

### Enterprise Security Architect - Staff Consultant
**Booz Allen Hamilton** | December 2020 - October 2022 | McLean, VA

- Implemented AWS infrastructure using Terraform Cloud/Enterprise with Hashicorp Sentinel; administered AWS Organizations with SCPs, consolidated billing, and cross-account IAM roles
- Managed GitHub Organization settings including SSO/SAML integration, team permissions, branch protection policies, and repository access controls
- Built immutable infrastructure using Hashicorp Packer to create standardized, security-hardened AMIs for EC2 deployments
- Orchestrated multi-container applications using docker-compose for local development environments and testing workflows
- Configured Ansible playbooks for automated configuration management, server provisioning, and compliance enforcement across hybrid cloud infrastructure
- Implemented observability solutions using SignalFx for real-time application performance monitoring, metrics collection, and distributed tracing
- Designed and implemented AWS networking architecture using VPCs, subnets, route tables, NACLs, security groups, VPC peering, and Transit Gateway for secure multi-account connectivity
- Configured Azure Virtual Networks with NSGs, route tables, VNet peering, and Azure Firewall to establish secure hybrid cloud connectivity between on-premises and cloud environments
- Configured CI/CD pipelines for SAST/DAST/SCA vulnerability scanning and created scalable automated production deployment system using Terraform for cloud native applications
- Configured, deployed, and scaled Palo Alto CORTEX XSOAR in AWS for automated security orchestration and incident response
- Designed security compliance metrics aligned with DevSecOps; developed custom Splunk queries and dashboards for real-time monitoring; used YAML to create pipeline infrastructure for deploying container images into ACR & AWS ECR
- Wrote SQL queries to extract and analyze data from AWS RDS, Aurora, DynamoDB, and Azure SQL; created data-driven reports and visualizations for stakeholders

### DevOps Engineer
**Factual Data** | December 2018 - April 2020 | Columbus, OH

- Configured pipelines for automated deploy to app servers and performed build maintenance in Jenkins and TeamCity
- Deployed and managed .NET Framework applications on Windows Server 2012/2016 using IIS; configured application pools, bindings, SSL certificates, and authentication methods
- Used Infrastructure-as-Code methodologies to automate, centralize, and scale the configuration changes made to application, database, and web frontend servers
- Constructed application configuration files that were added to version control using Bitbucket and SVN while also managing repository permissions and functionality
- Worked with development teams to implement monitoring on applications using Dynatrace and log aggregation; created Splunk queries and alerts for application performance monitoring, error tracking, and security event correlation
- Implemented health check endpoints and monitoring for .NET applications using custom APIs and IIS URL Rewrite; configured load balancer health probes in F5 Big IP
- Configured app connections to SQL databases (MS SQL Server, MariaDB, PostgreSQL) and app properties in version control; automated creation of Python BI environments using Anaconda and Pip
- Used knowledge of Python, Jinja templates and YAML to assist the team with Ansible Playbooks for multiple purposes including deployment and auditing
- Maintained a fully automated CI/CD pipeline for code deployment and state configuration using Ansible and Rundeck with Bash and PowerShell scripts
- Administered Windows Server environments using PowerShell DSC and Ansible for configuration management; automated IIS deployments and Windows service management
- Worked with Unix Admins and Networking to complete RHEL 7 migrations by configuring new RHEL 7 app and Apache or Java Tomcat web servers and adding them to the correct Big IP F5 pools
- Used PowerShell to automate logging and cleanup tasks improving disk utilization; utilized OpenJDK for migrating Java applications to open-source technologies
- Used Thycotic Secret Server to manage application secrets and grant users RBAC to application secrets

## Education

**G.E.D.** | State of Ohio

## Certifications

- **Microsoft Azure Administrator Associate**
- **Microsoft Azure DevOps Engineer Expert**
- **Microsoft Azure Solutions Architect Expert**
- **Linux Foundation Certified System Administrator** (LFCS)
- **AWS Solutions Architect Associate**
- **Certified Kubernetes Administrator** (CKA)
- **Certified Kubernetes Application Developer** (CKAD)

## Skills

### Cloud Platforms
- **AWS**: EC2, VPC, S3, RDS, Aurora, DynamoDB, Organizations, Transit Gateway, CloudWatch
- **Azure**: Virtual Networks, NSGs, Azure Firewall, SQL Database, ACR, Key Vault

### Infrastructure as Code & Configuration Management
- **IaC**: Terraform (Cloud/Enterprise), Bicep, Crossplane, Packer
- **Configuration Management**: Ansible, PowerShell DSC
- **Secrets Management**: HashiCorp Vault, Azure Key Vault, Thycotic Secret Server

### Containers & Orchestration
- **Containers**: Docker, docker-compose
- **Kubernetes**: k3s, EKS, AKS, Helm, Kustomize
- **GitOps**: ArgoCD, Flux

### DevOps & CI/CD
- **CI/CD Tools**: Jenkins, TeamCity, Azure DevOps, GitHub Actions, Rundeck
- **Version Control**: Git, GitHub, Bitbucket, SVN
- **Security**: SAST/DAST/SCA scanning, Palo Alto CORTEX XSOAR

### Programming & Scripting
- **Languages**: Python, Bash, PowerShell, SQL, YAML
- **Frameworks**: Jinja templates, .NET Framework
- **Databases**: MS SQL Server, PostgreSQL, MariaDB, AWS RDS/Aurora/DynamoDB, Azure SQL

### Monitoring & Observability
- **Monitoring**: SignalFx, Dynatrace, Splunk, Prometheus, Grafana
- **Logging**: Splunk, CloudWatch

### Networking & Security
- **Networking**: VPCs, subnets, route tables, NACLs, security groups, VNet peering, F5 Big IP
- **Security**: IAM roles, SCPs, SSO/SAML, HashiCorp Sentinel, security compliance metrics

## Projects

### Spider-2y-Banana GitOps Platform
A comprehensive GitOps demonstration showcasing modern cloud-native infrastructure:
- **Infrastructure**: Bicep for Azure resource provisioning (VMs, networking, Key Vault, ACR)
- **Automation**: Ansible for k3s cluster bootstrapping and platform component installation
- **Cloud-Native IaC**: Crossplane for Kubernetes-native Azure resource management
- **GitOps**: ArgoCD with App-of-Apps pattern for declarative infrastructure and application delivery
- **Secrets Management**: External Secrets Operator integrated with Azure Key Vault
- **Platform Services**: Ingress-nginx, cert-manager with Let's Encrypt
- **CI/CD**: GitHub Actions for automated container builds and GitOps repository updates
- **Application**: Hugo static site (this resume) with automated deployment

**Repository**: [github.com/borninthedark/spider-2y-banana](https://github.com/borninthedark/spider-2y-banana)
