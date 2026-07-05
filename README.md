# Azure Business Tools Portal

This repository contains a small Azure-hosted portal for non-technical business users. It includes tools for Ecwid frontpage SKUs, zero-rating VAT by category, and managing the online-store Featured Products category by supplier.

## Layout

```text
apps/business-tools-api/    Python 3 Azure Functions API
apps/business-tools-web/    React/Vite frontend with tool dock navigation
infra/terraform/            Azure resources managed by Terraform
scripts/legacy/             Copies of the original one-off scripts
```

The API includes both `pyproject.toml` and `requirements.txt`. `requirements.txt` keeps Azure Functions deployment compatibility broad; generate a real `uv.lock` later with `uv lock` if you standardise on `uv`.

## Local API

Without Azure Functions Core Tools:

```bash
cd apps/business-tools-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.example.json local.settings.json
# fill in ECWID_API_TOKEN and ECWID_SHOP_ID
python dev_server.py
```

The lightweight dev server listens on `http://127.0.0.1:7071`, which matches the Vite proxy.

With Azure Functions Core Tools:

```bash
cd apps/business-tools-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
cp local.settings.example.json local.settings.json
func start
```

Set `ECWID_API_TOKEN` and `ECWID_SHOP_ID` in `local.settings.json` before calling Ecwid.

The Featured Products tool conventions are owned by the app code:

- Supplier source: Ecwid product attribute type `SUPPLIER`.
- Featured category name: `Featured Products`.

The category lookup includes disabled/hidden categories and fails if the category name is missing or duplicated. The category name can still be overridden with `FEATURED_PRODUCTS_CATEGORY_NAME` if the catalogue changes later.

## Local Web App

```bash
cd apps/business-tools-web
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:7071`.

## Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

After Terraform creates the Key Vault, add the Ecwid token without committing it or putting it in Terraform state:

```bash
az keyvault secret set --vault-name <vault-name> --name ecwid-api-token --value '<ecwid-api-token>'
```

## Local Deployment

You do not need GitHub to deploy. After Terraform has applied successfully and the Ecwid token is in Key Vault, run:

```bash
az login
az account set --subscription <subscription-id>
./scripts/deploy-local.sh
```

The script:

- Builds the React app.
- Zip-deploys the Python Function App with remote build enabled.
- Reads the Static Web App deployment token.
- Deploys the built frontend with the Azure Static Web Apps CLI.

On Apple Silicon Macs, the Static Web Apps CLI may require Rosetta because the downloaded deployment helper can be x86_64:

```bash
softwareupdate --install-rosetta --agree-to-license
```

If the script cannot resolve the Static Web App name from Terraform output, set it explicitly:

```bash
STATIC_WEB_APP_NAME=<name> ./scripts/deploy-local.sh
```

GitHub Actions is still a good next step for repeatable deployments, but it is not required for the first release.

## GitHub Deployment

If local Static Web Apps deployment fails on Apple Silicon because the downloaded `StaticSitesClient` binary requires Rosetta, use the included manual GitHub Actions workflow instead.

Set this repository variable:

```text
AZURE_FUNCTION_APP_NAME=<function-app-name>
```

Set these repository secrets:

```bash
az staticwebapp secrets list \
  --resource-group <resource-group-name> \
  --name <static-web-app-name> \
  --query "properties.apiKey" \
  --output tsv
```

Store that value as:

```text
AZURE_STATIC_WEB_APPS_API_TOKEN
```

Then get the Function App publish profile:

```bash
az functionapp deployment list-publishing-profiles \
  --resource-group <resource-group-name> \
  --name <function-app-name> \
  --xml
```

Store the full XML output as:

```text
AZURE_FUNCTIONAPP_PUBLISH_PROFILE
```

Push the repo to GitHub, open **Actions**, choose **Deploy Business Tools**, and run the workflow manually.

## Kubernetes Deployment

The app can also run outside Azure on Kubernetes. In that mode:

- `apps/business-tools-api/asgi_app.py` serves the existing business logic through FastAPI.
- `apps/business-tools-web/Dockerfile` builds the React app and serves it with nginx.
- nginx proxies `/api` to the internal `business-tools-api` service.
- Ecwid credentials are read from a Kubernetes Secret, not Terraform or committed YAML.

Build and publish both images to GHCR with the **Publish Containers** GitHub Actions workflow, or locally with:

```bash
docker build -t ghcr.io/<owner>/business-tools-api:<tag> apps/business-tools-api
docker build -t ghcr.io/<owner>/business-tools-web:<tag> apps/business-tools-web
docker push ghcr.io/<owner>/business-tools-api:<tag>
docker push ghcr.io/<owner>/business-tools-web:<tag>
```

Update image names and tags in:

```text
infra/kubernetes/overlays/local/kustomization.yaml
```

Create the runtime secret in the target cluster:

```bash
kubectl create namespace business-tools
kubectl create secret generic business-tools-api-secret \
  --namespace business-tools \
  --from-literal=ECWID_API_TOKEN='<ecwid-api-token>' \
  --from-literal=ECWID_SHOP_ID='<ecwid-shop-id>'
```

The Kubernetes ingress is protected by `oauth2-proxy` using Microsoft Entra ID / OIDC. Create an Entra app registration with this web redirect URI, replacing the hostname with your real ingress hostname:

```text
https://business-tools.local/oauth2/callback
```

Create a client secret for that Entra app, then create the auth secret in the cluster:

```bash
COOKIE_SECRET="$(openssl rand -base64 32)"
kubectl create secret generic business-tools-auth-secret \
  --namespace business-tools \
  --from-literal=OIDC_ISSUER_URL='https://login.microsoftonline.com/<tenant-id>/v2.0' \
  --from-literal=OAUTH2_PROXY_CLIENT_ID='<entra-application-client-id>' \
  --from-literal=OAUTH2_PROXY_CLIENT_SECRET='<entra-client-secret>' \
  --from-literal=OAUTH2_PROXY_COOKIE_SECRET="$COOKIE_SECRET"
```

To restrict access to assigned users/groups, set assignment required on the Entra Enterprise Application and assign the allowed users or groups. To require MFA, create a Conditional Access policy targeting the same Enterprise Application.

Edit `infra/kubernetes/overlays/local/ingress.yaml` and `infra/kubernetes/overlays/local/oauth2-proxy-ingress.yaml` for your ingress class and hostname. Also update `OAUTH2_PROXY_REDIRECT_URL` in `infra/kubernetes/base/kustomization.yaml`, or override it in your overlay. The default hostname is:

```text
business-tools.local
```

For GitOps, edit `infra/argocd/business-tools.yaml` so `repoURL` points to your repository, then apply it to the cluster where Argo CD is installed:

```bash
kubectl apply -f infra/argocd/business-tools.yaml
```

For a quick non-Argo test:

```bash
kubectl apply -k infra/kubernetes/overlays/local
kubectl -n business-tools port-forward svc/business-tools-web 8080:80
```

Then open `http://127.0.0.1:8080`.

## Security Notes

The Static Web App configuration uses a Terraform-managed Entra app registration for Microsoft login. Terraform also creates the matching Enterprise Application service principal and, by default, sets `app_role_assignment_required = true`.

To restrict access, add one or more Entra group object IDs to `authorized_group_object_ids` in `infra/terraform/terraform.tfvars`. To require MFA, create a Conditional Access policy in Entra targeting the Enterprise Application output by Terraform as `entra_service_principal_object_id`.

Custom authentication for Azure Static Web Apps requires the Standard SKU, so Terraform defaults `static_web_app_sku_tier` and `static_web_app_sku_size` to `Standard`.

Terraform creates the Static Web App Entra client secret and passes it into Static Web App application settings. That secret is sensitive in Terraform state, so use a protected remote backend before applying this outside local experimentation.

If Function App creation fails with `Operation cannot be completed without additional quota` and `Current Limit (Total VMs): 0`, that is App Service/Microsoft.Web regional quota for the Function hosting plan, not the normal VM quota page. Set `function_app_location` to another supported region or request App Service quota for the failing region.

The Function is designed to be reached through the Static Web App `/api` route. If you expose the Function App directly, add an additional access restriction layer before production use.

## Custom Domain

For a subdomain such as `tools.example.com`, create a DNS CNAME pointing to the Static Web App default hostname:

```text
tools.example.com -> <static-web-app-default-hostname>
```

Then set this in `infra/terraform/terraform.tfvars`:

```hcl
custom_domain_name            = "tools.example.com"
custom_domain_validation_type = "cname-delegation"
static_web_app_default_host_name = "<static-web-app-default-hostname>"
```

Run:

```bash
terraform plan
terraform apply
```

Terraform will add the Static Web App custom domain and add the matching Entra callback URL:

```text
https://tools.example.com/.auth/login/aad/callback
```

For an apex/root domain, use `custom_domain_validation_type = "dns-txt-token"` and follow the TXT validation token shown by:

```bash
terraform output -raw static_web_app_custom_domain_validation_token
```

## Tests

```bash
cd apps/business-tools-api
pytest
```

```bash
cd infra/terraform
terraform fmt -check
terraform validate
```
