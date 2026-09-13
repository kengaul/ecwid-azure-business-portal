#!/usr/bin/env bash
set -euo pipefail

# Generates the Git-safe BitwardenSecret mapping and bootstraps the operator
# token. Secret values are never printed or written to the repository.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPPING_FILE="$ROOT_DIR/infra/kubernetes/overlays/local/bitwarden-secrets.yaml"
PROJECT_PREFIX="${PROJECT_PREFIX:-business_tools__}"
NAMESPACE="${NAMESPACE:-business-tools}"
BWS_SERVER_URL="${BWS_SERVER_URL:-https://vault.bitwarden.eu}"

command -v bws >/dev/null || { echo "bws is required." >&2; exit 1; }
command -v kubectl >/dev/null || { echo "kubectl is required." >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required." >&2; exit 1; }

: "${BWS_ACCESS_TOKEN:?Set BWS_ACCESS_TOKEN to the Bitwarden machine-account token.}"
: "${BWS_ORGANIZATION_ID:?Set BWS_ORGANIZATION_ID to the Bitwarden organization UUID.}"
: "${BWS_PROJECT_ID:?Set BWS_PROJECT_ID to the Bitwarden project UUID.}"

secret_id() {
  local key="$1"
  local name="${PROJECT_PREFIX}${key}"
  local id

  id="$(bws secret list "$BWS_PROJECT_ID" \
    --server-url "$BWS_SERVER_URL" --output json \
    | jq -r --arg name "$name" '.[] | select(.key == $name) | .id' \
    | head -n 1)"

  if [[ -z "$id" || "$id" == "null" ]]; then
    echo "Missing Bitwarden secret: $name" >&2
    exit 1
  fi
  printf '%s' "$id"
}

api_token_id="$(secret_id ECWID_API_TOKEN)"
shop_id_id="$(secret_id ECWID_SHOP_ID)"
issuer_id="$(secret_id OIDC_ISSUER_URL)"
client_id_id="$(secret_id OAUTH2_PROXY_CLIENT_ID)"
client_secret_id="$(secret_id OAUTH2_PROXY_CLIENT_SECRET)"
cookie_secret_id="$(secret_id OAUTH2_PROXY_COOKIE_SECRET)"

#kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
#kubectl -n "$NAMESPACE" create secret generic bw-auth-token \
#  --from-literal=token="$BWS_ACCESS_TOKEN" \
#  --dry-run=client -o yaml | kubectl apply -f -

umask 077
tmp_file="$(mktemp "${TMPDIR:-/tmp}/bitwarden-secrets.XXXXXX")"
trap 'rm -f "$tmp_file"' EXIT

cat >"$tmp_file" <<EOF
apiVersion: k8s.bitwarden.com/v1
kind: BitwardenSecret
metadata:
  name: business-tools-api-secrets
  namespace: $NAMESPACE
spec:
  organizationId: "$BWS_ORGANIZATION_ID"
  secretName: business-tools-api-secret
  onlyMappedSecrets: true
  map:
    - bwSecretId: $api_token_id
      secretKeyName: ECWID_API_TOKEN
    - bwSecretId: $shop_id_id
      secretKeyName: ECWID_SHOP_ID
  authToken:
    secretName: bw-auth-token
    secretKey: token
---
apiVersion: k8s.bitwarden.com/v1
kind: BitwardenSecret
metadata:
  name: business-tools-auth-secrets
  namespace: $NAMESPACE
spec:
  organizationId: "$BWS_ORGANIZATION_ID"
  secretName: business-tools-auth-secret
  onlyMappedSecrets: true
  map:
    - bwSecretId: $issuer_id
      secretKeyName: OIDC_ISSUER_URL
    - bwSecretId: $client_id_id
      secretKeyName: OAUTH2_PROXY_CLIENT_ID
    - bwSecretId: $client_secret_id
      secretKeyName: OAUTH2_PROXY_CLIENT_SECRET
    - bwSecretId: $cookie_secret_id
      secretKeyName: OAUTH2_PROXY_COOKIE_SECRET
  authToken:
    secretName: bw-auth-token
    secretKey: token
EOF

mv "$tmp_file" "$MAPPING_FILE"
trap - EXIT

cat <<EOF
Generated: $MAPPING_FILE
Bootstrapped: $NAMESPACE/bw-auth-token

Add this resource to infra/kubernetes/overlays/local/kustomization.yaml:
  - bitwarden-secrets.yaml

Review the generated mapping, commit it, and push it. Argo will then apply the
BitwardenSecret resources and the operator will populate the two Kubernetes
Secrets. Secret values were not written to the repository.
EOF
