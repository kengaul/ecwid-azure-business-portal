resource "azuread_application" "static_web_app" {
  display_name     = "${local.name_prefix}-static-web-app"
  sign_in_audience = "AzureADMyOrg"
  owners           = [data.azurerm_client_config.current.object_id]
}

resource "azuread_application_redirect_uris" "static_web_app" {
  application_id = azuread_application.static_web_app.id
  type           = "Web"
  redirect_uris = concat(
    [
      "https://${azurerm_static_web_app.web.default_host_name}/.auth/login/aad/callback"
    ],
    var.custom_domain_name == null ? [] : [
      "https://${var.custom_domain_name}/.auth/login/aad/callback"
    ]
  )
}

resource "azuread_service_principal" "static_web_app" {
  client_id                    = azuread_application.static_web_app.client_id
  app_role_assignment_required = var.require_entra_assignment
  owners                       = [data.azurerm_client_config.current.object_id]
}

resource "azuread_application_password" "static_web_app" {
  application_id = azuread_application.static_web_app.id
  display_name   = "static-web-app-auth"
  end_date       = timeadd(timestamp(), "${var.entra_app_secret_years * 8760}h")

  lifecycle {
    ignore_changes = [end_date]
  }
}

resource "azuread_app_role_assignment" "authorized_groups" {
  for_each = var.require_entra_assignment ? var.authorized_group_object_ids : []

  app_role_id         = "00000000-0000-0000-0000-000000000000"
  principal_object_id = each.value
  resource_object_id  = azuread_service_principal.static_web_app.object_id
}
