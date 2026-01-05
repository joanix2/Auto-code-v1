terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "github" {
  token = var.github_token
  owner = var.github_repo_owner
}

# Variables
variable "aws_region" {
  description = "AWS Region"
  default     = "eu-west-3"
}

variable "github_token" {
  description = "GitHub Personal Access Token with repo and admin:repo_hook scopes"
  type        = string
  sensitive   = true
}

variable "github_repo_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "Auto-code-v1"
}

variable "neo4j_password" {
  description = "Neo4j database password"
  type        = string
  sensitive   = true
  default     = "autocode_neo4j_2026"
}

variable "anthropic_api_key" {
  description = "Anthropic API Key for Claude"
  type        = string
  sensitive   = true
}

variable "github_client_id" {
  description = "GitHub OAuth Client ID"
  type        = string
  sensitive   = true
}

variable "github_client_secret" {
  description = "GitHub OAuth Client Secret"
  type        = string
  sensitive   = true
}

variable "public_key_path" {
  description = "Path to SSH public key"
  default     = "~/.ssh/aws_key.pem.pub"
}

variable "private_key_path" {
  description = "Path to SSH private key"
  default     = "~/.ssh/aws_key.pem"
}

variable "project_name" {
  description = "Name of the project"
  default     = "autocode"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

# SSH Key Pair
resource "aws_key_pair" "autocode" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.public_key_path)
}
