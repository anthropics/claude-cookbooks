# Runbook: OOMKilled / OutOfMemoryError

**Symptom:** container exits 137, `OOMKilled` in pod events, heap-exhausted
errors in application logs.

**Triage:**

1. Confirm the kill is the kubelet OOM killer (exit 137) and not an
   application-level limit.
2. Open the deployment manifest under `infra/k8s/<service>-deploy.yaml`
   and check `spec.template.spec.containers[].resources.limits.memory`.
3. If the limit is below the service's documented working set (checkout-svc
   needs ~400Mi after the pricing cache warms), raise the limit. 512Mi is
   the standard next tier.
4. Keep `requests.memory` at or below the new limit.

**Fix:** open a PR against the infra repo with the corrected limit. Do not
hot-patch the live deployment.
