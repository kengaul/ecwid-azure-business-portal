resource "azurerm_static_web_app" "web" {
  name                = "stapp-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.static_web_app_location
  sku_tier            = var.static_web_app_sku_tier
  sku_size            = var.static_web_app_sku_size
  app_settings = {
    AZURE_CLIENT_ID                      = azuread_application.static_web_app.client_id
    AZURE_CLIENT_SECRET_APP_SETTING_NAME = azuread_application_password.static_web_app.value
  }
  tags = local.common_tags

  lifecycle {
    ignore_changes = [
      repository_branch,
      repository_url,
    ]
  }
}

# Link the Static Web App to the managed Azure Function API so the UI can call /api/*.
# If your provider version does not support this resource in your environment, deploy the
# Function separately and set VITE_API_BASE_URL/CORS instead.
resource "azurerm_static_web_app_function_app_registration" "api" {
  static_web_app_id = azurerm_static_web_app.web.id
  function_app_id   = azurerm_linux_function_app.api.id
}

resource "azurerm_static_web_app_custom_domain" "web" {
  count = var.custom_domain_name == null ? 0 : 1

  static_web_app_id = azurerm_static_web_app.web.id
  domain_name       = var.custom_domain_name
  validation_type   = var.custom_domain_validation_type
}
