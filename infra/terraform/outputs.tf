output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "static_web_app_default_host_name" {
  value = azurerm_static_web_app.web.default_host_name
}

output "static_web_app_custom_domain_validation_token" {
  value     = try(azurerm_static_web_app_custom_domain.web[0].validation_token, null)
  sensitive = true
}

output "entra_application_client_id" {
  value = azuread_application.static_web_app.client_id
}

output "entra_service_principal_object_id" {
  value = azuread_service_principal.static_web_app.object_id
}

output "function_app_name" {
  value = azurerm_linux_function_app.api.name
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "ecwid_api_token_secret_command" {
  value = "az keyvault secret set --vault-name ${azurerm_key_vault.main.name} --name ${var.ecwid_api_token_secret_name} --value '<ecwid-api-token>'"
}
