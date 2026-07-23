# Kubernetes Deployment Guide

This guide describes how to deploy the HIR Platform to a production Kubernetes cluster.

## Prerequisites
- A running K8s cluster (EKS, GKE, or AKS)
- `kubectl` configured
- Access to the container registry (`ghcr.io/your-org`)

## Deployment Steps

1. **Apply Secrets and ConfigMaps**
   You must first create the required secrets (DB passwords, LLM API keys) before applying deployments.
   ```bash
   kubectl create secret generic hir-backend-secrets --from-env-file=.env.production -n hir-production
   kubectl create secret generic hir-ai-secrets --from-env-file=.env.ai -n hir-production
   ```

2. **Deploy the Services**
   Apply the manifests found in the `kubernetes/` directory:
   ```bash
   kubectl apply -f kubernetes/backend-deployment.yaml
   kubectl apply -f kubernetes/frontend-deployment.yaml
   kubectl apply -f kubernetes/ai-worker-deployment.yaml
   ```

3. **Verify Deployment**
   ```bash
   kubectl get pods -n hir-production
   ```
   Ensure all pods are in `Running` state.

## Monitoring
A `docker-compose.monitoring.yml` is provided for a quick Prometheus/Grafana stack, but for production K8s, it is recommended to use the `kube-prometheus-stack` Helm chart. 
The backend exposes metrics at `/metrics`.
