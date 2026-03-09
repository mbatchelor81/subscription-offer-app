output "namespace" {
  description = "Name of the Kubernetes namespace"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "service_account_name" {
  description = "Name of the Kubernetes service account"
  value       = kubernetes_service_account.app.metadata[0].name
}
