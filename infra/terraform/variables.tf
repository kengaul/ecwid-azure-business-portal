variable "project_name" {
  description = "Short name used in Azure resource names."
  type        = string
  default     = "business-tools"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "uksouth"
}

variable "azure_subscription_id" {
  description = "Azure subscription ID used by the AzureRM provider."
  type        = string
}

variable "azure_tenant_id" {
  description = "Microsoft Entra tenant ID used by the AzureRM and AzureAD providers."
  type        = string
}

variable "static_web_app_location" {
  description = "Azure Static Web Apps region. This is separate because Static Web Apps are available in fewer regions than Function Apps."
  type        = string
  default     = "westeurope"
}

variable "function_app_location" {
  description = "Azure region for the Function App service plan. Keep separate because Microsoft.Web consumption quota can differ by region."
  type        = string
  default     = null
}

variable "ecwid_shop_id" {
  description = "Ecwid shop/store ID."
  type        = string
}

variable "frontpage_max_skus" {
  description = "Maximum number of submitted SKUs processed in one request."
  type        = number
  default     = 200
}

variable "ecwid_api_token_secret_name" {
  description = "Name of the Key Vault secret containing the Ecwid API token. Create the secret outside Terraform to keep it out of state."
  type        = string
  default     = "ecwid-api-token"
}

variable "static_web_app_sku_tier" {
  description = "Static Web App SKU tier."
  type        = string
  default     = "Standard"
}

variable "static_web_app_sku_size" {
  description = "Static Web App SKU size."
  type        = string
  default     = "Standard"
}

variable "entra_app_secret_years" {
  description = "Validity period for the Static Web App Entra application client secret."
  type        = number
  default     = 1
}

variable "require_entra_assignment" {
  description = "Require users or groups to be explicitly assigned to the Enterprise Application before they can sign in."
  type        = bool
  default     = true
}

variable "authorized_group_object_ids" {
  description = "Optional Entra group object IDs assigned to the Enterprise Application when require_entra_assignment is true."
  type        = set(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to Azure resources."
  type        = map(string)
  default     = {}
}
