# Bitwarden Secrets Manager integration

This directory contains the GitOps-facing configuration for syncing runtime
secrets from Bitwarden Secrets Manager into Kubernetes.

The values are not stored in Git. The repository stores only:

- the Bitwarden secret UUIDs;
- the Kubernetes Secret names and keys to create; and
- the namespace and Bitwarden organization identifier.

The Bitwarden Secrets Manager Kubernetes Operator must be installed once per
cluster by a cluster administrator. It is intentionally separate from the
`business-tools` Argo Application because the operator is a cluster-level
dependency.

## One-time cluster setup

Install or upgrade the official operator:

```bash
helm repo add bitwarden https://charts.bitwarden.com/
helm repo update
helm upgrade --install sm-operator bitwarden/sm-operator \
  --namespace sm-operator-system \
  --create-namespace \
  --devel \
  --set settings.cloudRegion=EU \
  --set settings.bwSecretsManagerRefreshInterval=300
```

Use `US` instead of `EU` when the Bitwarden organization is hosted in the US
cloud. The operator requires a Bitwarden Secrets Manager organization and a
machine-account access token with read access to the project containing these
secrets.

## Recreate the cluster bootstrap token

The token is deliberately not managed by Argo. Set it in your current shell
without committing it or putting it in a manifest:

```bash
export BWS_ACCESS_TOKEN='...'
kubectl create namespace business-tools --dry-run=client -o yaml | kubectl apply -f -
kubectl -n business-tools create secret generic bw-auth-token \
  --from-literal=token="$BWS_ACCESS_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
unset BWS_ACCESS_TOKEN
```

The machine-account token can be stored locally in the macOS Keychain and
exported only when bootstrapping. Do not put it in Git, shell startup files,
Argo settings, or a Kubernetes manifest.

## Create the Bitwarden secrets

Create these secrets in a dedicated Bitwarden Secrets Manager project, for
example `business-tools/local`:

| Bitwarden secret | Kubernetes key | Required |
|---|---|---:|
| Ecwid API token | `ECWID_API_TOKEN` | yes |
| Ecwid shop ID | `ECWID_SHOP_ID` | yes |
| OIDC issuer URL | `OIDC_ISSUER_URL` | yes |
| OAuth client ID | `OAUTH2_PROXY_CLIENT_ID` | yes |
| OAuth client secret | `OAUTH2_PROXY_CLIENT_SECRET` | yes |
| OAuth cookie secret | `OAUTH2_PROXY_COOKIE_SECRET` | yes |
| GHCR docker config JSON | `.dockerconfigjson` | only for private images |

Generate the OAuth cookie secret as exactly 32 hexadecimal characters:

```bash
openssl rand -hex 16
```

After creating each Bitwarden secret, record its UUID. UUIDs are identifiers,
not secret values, and are suitable for the Git-managed mapping below.

## Add the mapping

The repository includes a helper which looks up UUIDs by the naming convention
and creates the Kubernetes bootstrap token without displaying secret values.
Install the Bitwarden Secrets Manager CLI (`bws`), then run:

```bash
export BWS_ACCESS_TOKEN='...'
export BWS_ORGANIZATION_ID='<organization-uuid>'
export BWS_PROJECT_ID='<project-uuid>'
scripts/bootstrap-bitwarden-business-tools.sh
unset BWS_ACCESS_TOKEN BWS_ORGANIZATION_ID BWS_PROJECT_ID
```

The helper defaults to the EU endpoint (`https://vault.bitwarden.eu`). Set
`BWS_SERVER_URL=https://vault.bitwarden.com` for a US-hosted organization.

The script expects these Bitwarden names by default:

```text
homelab__business-tools__ECWID_API_TOKEN
homelab__business-tools__ECWID_SHOP_ID
homelab__business-tools__OIDC_ISSUER_URL
homelab__business-tools__OAUTH2_PROXY_CLIENT_ID
homelab__business-tools__OAUTH2_PROXY_CLIENT_SECRET
homelab__business-tools__OAUTH2_PROXY_COOKIE_SECRET
```

If you chose another prefix, set it when running the script:

```bash
PROJECT_PREFIX='my-prefix__' scripts/bootstrap-bitwarden-business-tools.sh
```

Copy `business-tools-secrets.yaml.example` to
`../overlays/local/bitwarden-secrets.yaml`, replace the organization and
secret UUID placeholders, and commit the resulting mapping. The real file is
safe to commit because it contains only UUIDs and mappings, never secret
values.

Add the file to `infra/kubernetes/overlays/local/kustomization.yaml`:

```yaml
resources:
  - ../../base
  - ingress.yaml
  - oauth2-proxy-ingress.yaml
  - bitwarden-secrets.yaml
```

This makes the existing Argo Application manage the `BitwardenSecret` custom
resources. The `bw-auth-token` Secret remains a bootstrap secret created
outside Argo.

```bash
kubectl apply -f infra/kubernetes/overlays/local/bitwarden-secrets.yaml
kubectl -n business-tools get secret business-tools-api-secret
kubectl -n business-tools get secret business-tools-auth-secret
```

Once the generated Secrets exist, Argo can safely manage the Deployments. If a
cluster is recreated, rerun the operator install and bootstrap-token steps;
the operator will repopulate the generated Kubernetes Secrets from Bitwarden.
