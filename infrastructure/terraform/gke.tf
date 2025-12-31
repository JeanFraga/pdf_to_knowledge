# GKE Autopilot Cluster
# Only created in prod environment to avoid costs in dev

resource "google_container_cluster" "autopilot" {
  count = local.is_prod ? 1 : 0

  name     = "${var.project_id}-cluster"
  location = var.region

  # Autopilot mode
  enable_autopilot = true

  # Network configuration
  network    = "default"
  subnetwork = "default"

  # Release channel for automatic upgrades
  release_channel {
    channel = "REGULAR"
  }

  # Workload Identity for secure service account mapping
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Deletion protection (disable for dev, enable for prod)
  deletion_protection = local.is_prod

  depends_on = [
    google_project_service.apis["container.googleapis.com"],
    google_project_service.apis["compute.googleapis.com"],
  ]
}

output "cluster_name" {
  description = "GKE cluster name (prod only)"
  value       = local.is_prod ? google_container_cluster.autopilot[0].name : null
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint (prod only)"
  value       = local.is_prod ? google_container_cluster.autopilot[0].endpoint : null
  sensitive   = true
}
