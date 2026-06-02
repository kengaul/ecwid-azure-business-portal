resource "azurerm_storage_account" "functions" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = local.function_location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.common_tags
}

resource "azurerm_service_plan" "functions" {
  name                = "asp-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.function_location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = local.common_tags
}

resource "azurerm_linux_function_app" "api" {
  name                       = "func-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = local.function_location
  service_plan_id            = azurerm_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.functions.name
  storage_account_access_key = azurerm_storage_account.functions.primary_access_key
  https_only                 = true
  tags                       = local.common_tags

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.12"
    }

    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key               = azurerm_application_insights.main.instrumentation_key

  }

  app_settings = {
    APP_ENVIRONMENT                = var.environment
    ECWID_API_TOKEN                = "@Microsoft.KeyVault(SecretUri=${local.ecwid_api_token_secret_uri})"
    ECWID_SHOP_ID                  = var.ecwid_shop_id
    FRONTPAGE_MAX_SKUS             = tostring(var.frontpage_max_skus)
    FUNCTIONS_WORKER_RUNTIME       = "python"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
  }

  lifecycle {
    ignore_changes = [
      auth_settings_v2,
      tags["hidden-link: /app-insights-resource-id"],
    ]
  }
}
