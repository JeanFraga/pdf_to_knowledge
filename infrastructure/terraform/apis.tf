# GCP APIs - Managed by Terraform
# Bootstrap APIs (cloudresourcemanager, serviceusage, storage, iam) enabled via setup.sh

# APIs needed for both dev and prod (Gemini/AI only)
locals {
  dev_apis = [
    "aiplatform.googleapis.com", # Vertex AI / Gemini
  ]

  # Additional APIs for prod (these can incur costs)
  prod_apis = [
    "container.googleapis.com",        # GKE
    "firestore.googleapis.com",        # Firestore
    "artifactregistry.googleapis.com", # Container Registry
    "cloudbuild.googleapis.com",       # Cloud Build
    "secretmanager.googleapis.com",    # Secret Manager
    "compute.googleapis.com",          # Compute Engine (GKE dependency)
  ]

  # Combine based on environment
  enabled_apis = local.is_prod ? concat(local.dev_apis, local.prod_apis) : local.dev_apis
}

resource "google_project_service" "apis" {
  for_each = toset(local.enabled_apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
