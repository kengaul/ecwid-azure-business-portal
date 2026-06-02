locals {
  compact_project   = lower(replace(var.project_name, "-", ""))
  compact_env       = lower(replace(var.environment, "-", ""))
  name_prefix       = lower("${var.project_name}-${var.environment}")
  short_project     = substr(local.compact_project, 0, 10)
  short_env         = substr(local.compact_env, 0, 4)
  function_location = coalesce(var.function_app_location, var.location)

  common_tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      managed-by  = "terraform"
    },
    var.tags
  )

  storage_account_name       = substr("st${local.short_project}${local.short_env}${random_string.suffix.result}", 0, 24)
  key_vault_name             = substr("kv-${local.short_project}-${local.short_env}-${random_string.suffix.result}", 0, 24)
  ecwid_api_token_secret_uri = "https://${local.key_vault_name}.vault.azure.net/secrets/${var.ecwid_api_token_secret_name}"
}
