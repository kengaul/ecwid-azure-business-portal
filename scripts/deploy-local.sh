#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"
API_DIR="$ROOT_DIR/apps/business-tools-api"
WEB_DIR="$ROOT_DIR/apps/business-tools-web"
BUILD_DIR="$ROOT_DIR/.build"

command -v az >/dev/null || {
  echo "Azure CLI is required. Install it and run az login first." >&2
  exit 1
}

command -v terraform >/dev/null || {
  echo "Terraform is required." >&2
  exit 1
}

command -v npm >/dev/null || {
  echo "npm is required." >&2
  exit 1
}

if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
  if [[ ! -e "/Library/Apple/usr/libexec/oah/libRosettaRuntime" ]]; then
    cat >&2 <<'EOF'
Azure Static Web Apps CLI downloads a macOS deployment helper that currently
requires Rosetta on Apple Silicon.

Install Rosetta, then rerun this script:

  softwareupdate --install-rosetta --agree-to-license

EOF
    exit 1
  fi
fi

RESOURCE_GROUP="$(terraform -chdir="$TF_DIR" output -raw resource_group_name)"
FUNCTION_APP_NAME="$(terraform -chdir="$TF_DIR" output -raw function_app_name)"
STATIC_WEB_APP_HOST="$(terraform -chdir="$TF_DIR" output -raw static_web_app_default_host_name)"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-}"

if [[ -z "$STATIC_WEB_APP_NAME" ]]; then
  STATIC_WEB_APP_NAME="$(
    az staticwebapp list \
      --resource-group "$RESOURCE_GROUP" \
      --query "[?defaultHostname=='$STATIC_WEB_APP_HOST'].name | [0]" \
      --output tsv
  )"
fi

if [[ -z "$STATIC_WEB_APP_NAME" || "$STATIC_WEB_APP_NAME" == "None" ]]; then
  echo "Could not resolve Static Web App name. Set STATIC_WEB_APP_NAME and rerun." >&2
  exit 1
fi

mkdir -p "$BUILD_DIR"

echo "Building web app..."
npm --prefix "$WEB_DIR" install
npm --prefix "$WEB_DIR" run build

echo "Packaging Function App..."
API_ZIP="$BUILD_DIR/business-tools-api.zip"
rm -f "$API_ZIP"
(
  cd "$API_DIR"
  zip -qr "$API_ZIP" \
    function_app.py \
    host.json \
    requirements.txt \
    business_tools
)

echo "Deploying Function App: $FUNCTION_APP_NAME"
az functionapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP_NAME" \
  --src "$API_ZIP" \
  --build-remote true \
  --timeout 600 \
  --output none

echo "Reading Static Web App deployment token..."
SWA_DEPLOYMENT_TOKEN="$(
  az staticwebapp secrets list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$STATIC_WEB_APP_NAME" \
    --query "properties.apiKey" \
    --output tsv
)"

echo "Deploying Static Web App: $STATIC_WEB_APP_NAME"
npx --yes @azure/static-web-apps-cli@2.0.9 deploy "$WEB_DIR/dist" \
  --deployment-token "$SWA_DEPLOYMENT_TOKEN" \
  --env production

echo "Deployment complete."
echo "Static Web App: https://$STATIC_WEB_APP_HOST"
