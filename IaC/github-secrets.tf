# GitHub Secrets for CI/CD
# These secrets will be automatically configured in your GitHub repository

resource "github_actions_secret" "ssh_private_key" {
  repository      = var.github_repo_name
  secret_name     = "SSH_PRIVATE_KEY"
  plaintext_value = file(var.private_key_path)
}

resource "github_actions_secret" "ec2_public_ip" {
  repository      = var.github_repo_name
  secret_name     = "EC2_PUBLIC_IP"
  plaintext_value = aws_eip.autocode.public_ip
}

resource "github_actions_secret" "neo4j_password" {
  repository      = var.github_repo_name
  secret_name     = "NEO4J_PASSWORD"
  plaintext_value = var.neo4j_password
}

resource "github_actions_secret" "gh_token" {
  repository      = var.github_repo_name
  secret_name     = "GH_TOKEN"
  plaintext_value = var.github_token
}

resource "github_actions_secret" "anthropic_api_key" {
  repository      = var.github_repo_name
  secret_name     = "ANTHROPIC_API_KEY"
  plaintext_value = var.anthropic_api_key
}

resource "github_actions_secret" "github_client_id" {
  repository      = var.github_repo_name
  secret_name     = "GITHUB_CLIENT_ID"
  plaintext_value = var.github_client_id
}

resource "github_actions_secret" "github_client_secret" {
  repository      = var.github_repo_name
  secret_name     = "GITHUB_CLIENT_SECRET"
  plaintext_value = var.github_client_secret
}

# Output pour confirmation
output "github_secrets_configured" {
  value = {
    ssh_private_key_configured    = github_actions_secret.ssh_private_key.secret_name
    ec2_public_ip_configured      = github_actions_secret.ec2_public_ip.secret_name
    neo4j_password_configured     = github_actions_secret.neo4j_password.secret_name
    gh_token_configured           = github_actions_secret.gh_token.secret_name
    anthropic_api_key_configured  = github_actions_secret.anthropic_api_key.secret_name
    github_client_id_configured   = github_actions_secret.github_client_id.secret_name
    github_client_secret_configured = github_actions_secret.github_client_secret.secret_name
  }
  description = "GitHub Actions secrets that have been configured"
}
