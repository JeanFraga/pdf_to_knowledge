variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "pdf-to-knowledge"
}

variable "region" {
  description = "Default GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment: dev (default, no costs) or prod (deploys GKE)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

locals {
  is_prod = var.environment == "prod"
}
