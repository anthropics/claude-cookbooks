#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Registry Garbage Collection Fix Script ===${NC}\n"

# Configuration
NAMESPACE="${NAMESPACE:-default}"
CONFIGMAP_NAME="${CONFIGMAP_NAME:-registry-config}"
CRONJOB_NAME="${CRONJOB_NAME:-registry-garbage-collect}"
PVC_NAME="${PVC_NAME:-registry-pvc}"

echo "Configuration:"
echo "  Namespace: $NAMESPACE"
echo "  ConfigMap: $CONFIGMAP_NAME"
echo "  CronJob: $CRONJOB_NAME"
echo "  PVC: $PVC_NAME"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Connected to Kubernetes cluster"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}! Namespace '$NAMESPACE' not found. Creating...${NC}"
    kubectl create namespace "$NAMESPACE"
fi

# Check if ConfigMap exists
echo -e "\n${YELLOW}Checking ConfigMap...${NC}"
if kubectl get configmap "$CONFIGMAP_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ConfigMap '$CONFIGMAP_NAME' exists"
    echo "  Would you like to update it? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        kubectl apply -f k8s/registry-configmap.yaml -n "$NAMESPACE"
        echo -e "${GREEN}✓${NC} ConfigMap updated"
    fi
else
    echo -e "${YELLOW}! ConfigMap not found. Creating...${NC}"
    kubectl apply -f k8s/registry-configmap.yaml -n "$NAMESPACE"
    echo -e "${GREEN}✓${NC} ConfigMap created"
fi

# Check if PVC exists
echo -e "\n${YELLOW}Checking PVC...${NC}"
if ! kubectl get pvc "$PVC_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${RED}! PVC '$PVC_NAME' not found.${NC}"
    echo "  Please create the PVC or set the correct PVC_NAME environment variable."
    echo "  Example: export PVC_NAME=your-pvc-name"
    exit 1
fi
echo -e "${GREEN}✓${NC} PVC '$PVC_NAME' exists"

# Check if CronJob exists
echo -e "\n${YELLOW}Checking CronJob...${NC}"
if kubectl get cronjob "$CRONJOB_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${GREEN}✓${NC} CronJob '$CRONJOB_NAME' exists"
    
    # Check if ConfigMap is mounted
    if kubectl get cronjob "$CRONJOB_NAME" -n "$NAMESPACE" -o yaml | grep -q "name: registry-config"; then
        echo -e "${GREEN}✓${NC} ConfigMap is already mounted"
    else
        echo -e "${YELLOW}! ConfigMap is NOT mounted. Updating CronJob...${NC}"
        kubectl apply -f k8s/registry-garbage-collect-cronjob.yaml -n "$NAMESPACE"
        echo -e "${GREEN}✓${NC} CronJob updated with ConfigMap mount"
    fi
else
    echo -e "${YELLOW}! CronJob not found. Creating...${NC}"
    kubectl apply -f k8s/registry-garbage-collect-cronjob.yaml -n "$NAMESPACE"
    echo -e "${GREEN}✓${NC} CronJob created"
fi

# Test with a manual job
echo -e "\n${YELLOW}Would you like to test the fix with a manual job? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    TEST_JOB_NAME="test-gc-$(date +%s)"
    echo "Creating test job: $TEST_JOB_NAME"
    kubectl create job "$TEST_JOB_NAME" --from=cronjob/"$CRONJOB_NAME" -n "$NAMESPACE"
    
    echo "Waiting for job to start..."
    sleep 5
    
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l job-name="$TEST_JOB_NAME" -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$POD_NAME" ]; then
        echo -e "\n${GREEN}Streaming logs from $POD_NAME:${NC}"
        kubectl logs -f "$POD_NAME" -n "$NAMESPACE"
        
        # Check job status
        JOB_STATUS=$(kubectl get job "$TEST_JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.succeeded}')
        if [ "$JOB_STATUS" = "1" ]; then
            echo -e "\n${GREEN}✓ Test job completed successfully!${NC}"
        else
            echo -e "\n${RED}✗ Test job failed. Check logs above for details.${NC}"
        fi
        
        echo -e "\n${YELLOW}Would you like to delete the test job? (y/n)${NC}"
        read -r cleanup
        if [[ "$cleanup" =~ ^[Yy]$ ]]; then
            kubectl delete job "$TEST_JOB_NAME" -n "$NAMESPACE"
            echo -e "${GREEN}✓${NC} Test job deleted"
        fi
    else
        echo -e "${RED}Could not find pod for test job${NC}"
    fi
fi

echo -e "\n${GREEN}=== Fix Complete ===${NC}"
echo ""
echo "Summary:"
echo "  ✓ ConfigMap with registry config is in place"
echo "  ✓ CronJob is configured to mount ConfigMap"
echo "  ✓ Weekly garbage collection should now work"
echo ""
echo "Next steps:"
echo "  1. Monitor the next scheduled run"
echo "  2. Check logs: kubectl logs -l job-name=$CRONJOB_NAME -n $NAMESPACE"
echo "  3. View CronJob: kubectl get cronjob $CRONJOB_NAME -n $NAMESPACE"
