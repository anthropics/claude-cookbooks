# Docker Registry Kubernetes Configuration

## Overview

This directory contains Kubernetes manifests for running a Docker Registry with automated garbage collection.

## Components

### 1. Registry ConfigMap (`registry-configmap.yaml`)
Contains the registry configuration including:
- Storage configuration
- Delete enabled (required for garbage collection)
- HTTP server settings
- Health check configuration

### 2. Garbage Collection CronJob (`registry-garbage-collect-cronjob.yaml`)
Automated weekly job that:
- Runs every Sunday at 2 AM
- Mounts both ConfigMap and PVC
- Executes registry garbage collection
- Includes resource limits and logging

## Quick Start

### Apply configurations:
```bash
# Create ConfigMap
kubectl apply -f registry-configmap.yaml

# Create CronJob
kubectl apply -f registry-garbage-collect-cronjob.yaml
```

### Using the automated fix script:
```bash
# Run with defaults
./scripts/fix-registry-gc.sh

# Run with custom configuration
NAMESPACE=registry-system \
PVC_NAME=my-registry-pvc \
./scripts/fix-registry-gc.sh
```

## Manual Testing

### Test garbage collection manually:
```bash
# Create a one-time job from the CronJob
kubectl create job --from=cronjob/registry-garbage-collect manual-gc-test

# Watch logs
kubectl logs -f job/manual-gc-test
```

## Troubleshooting

### Check CronJob status:
```bash
kubectl get cronjob registry-garbage-collect
kubectl describe cronjob registry-garbage-collect
```

### View recent job history:
```bash
kubectl get jobs -l app=docker-registry
```

### Check ConfigMap:
```bash
kubectl get configmap registry-config -o yaml
```

### View logs from last run:
```bash
kubectl logs -l job-name=registry-garbage-collect --tail=100
```

## Configuration

### Environment Variables for Fix Script:
- `NAMESPACE`: Kubernetes namespace (default: `default`)
- `CONFIGMAP_NAME`: ConfigMap name (default: `registry-config`)
- `CRONJOB_NAME`: CronJob name (default: `registry-garbage-collect`)
- `PVC_NAME`: PVC name (default: `registry-pvc`)

### Schedule Customization:
Edit the CronJob's `schedule` field (cron format):
```yaml
schedule: "0 2 * * 0"  # Sunday at 2 AM
```

Common schedules:
- Daily: `"0 2 * * *"`
- Weekly: `"0 2 * * 0"`
- Monthly: `"0 2 1 * *"`
