# Configuration automatique des secrets GitHub avec Terraform

Cette configuration Terraform configure automatiquement les secrets GitHub Actions nécessaires au déploiement CI/CD.

## Prérequis

1. **GitHub Personal Access Token** avec les scopes :

   - `repo` (Full control of private repositories)
   - `admin:repo_hook` (Full control of repository hooks)
   - `workflow` (Update GitHub Action workflows)

   Créez-le sur : https://github.com/settings/tokens

2. **Clés API** :
   - Anthropic API Key
   - GitHub OAuth Client ID & Secret

## Configuration

### 1. Créer le fichier terraform.tfvars

```bash
cd IaC
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Remplissez avec vos vraies valeurs :

```hcl
# GitHub Configuration
github_token      = "ghp_votre_token_ici"
github_repo_owner = "joanix2"
github_repo_name  = "Auto-code-v1"

# GitHub OAuth
github_client_id     = "Ov23li..."
github_client_secret = "votre_secret"

# Anthropic
anthropic_api_key = "sk-ant-..."

# Neo4j
neo4j_password = "mot_de_passe_securise"
```

### 2. Initialiser Terraform

```bash
terraform init
```

### 3. Appliquer la configuration

```bash
terraform apply
```

Terraform va :

1. ✅ Créer l'infrastructure AWS (EC2, Security Group, Elastic IP)
2. ✅ Configurer automatiquement **tous les secrets GitHub Actions** :
   - `SSH_PRIVATE_KEY`
   - `EC2_PUBLIC_IP`
   - `NEO4J_PASSWORD`
   - `GH_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `GITHUB_CLIENT_ID`
   - `GITHUB_CLIENT_SECRET`

## Secrets configurés automatiquement

| Secret                 | Description                  | Source               |
| ---------------------- | ---------------------------- | -------------------- |
| `SSH_PRIVATE_KEY`      | Clé privée SSH               | `~/.ssh/aws_key.pem` |
| `EC2_PUBLIC_IP`        | IP publique EC2              | AWS Elastic IP       |
| `NEO4J_PASSWORD`       | Mot de passe Neo4j           | `terraform.tfvars`   |
| `GH_TOKEN`             | Token GitHub pour l'agent AI | `terraform.tfvars`   |
| `ANTHROPIC_API_KEY`    | Clé API Anthropic Claude     | `terraform.tfvars`   |
| `GITHUB_CLIENT_ID`     | OAuth Client ID              | `terraform.tfvars`   |
| `GITHUB_CLIENT_SECRET` | OAuth Client Secret          | `terraform.tfvars`   |

## Vérification

Après `terraform apply`, vérifiez que les secrets sont configurés :

```bash
# Via l'output Terraform
terraform output github_secrets_configured

# Ou sur GitHub
# Allez sur : https://github.com/joanix2/Auto-code-v1/settings/secrets/actions
```

## Déploiement automatique

Une fois les secrets configurés, le déploiement CI/CD est automatique :

```bash
git push origin main
```

GitHub Actions va :

1. Détecter le push
2. Utiliser les secrets configurés
3. Déployer sur EC2 automatiquement

## Mise à jour des secrets

Si vous changez l'IP EC2 ou un secret :

```bash
# Mettre à jour terraform.tfvars si nécessaire
nano terraform.tfvars

# Réappliquer
terraform apply
```

Les secrets GitHub seront automatiquement mis à jour !

## Sécurité

⚠️ **Important** :

- Ne commitez JAMAIS `terraform.tfvars` (déjà dans `.gitignore`)
- Gardez votre GitHub token en sécurité
- Utilisez des mots de passe forts pour Neo4j

## Dépannage

### Erreur "404 Not Found"

- Vérifiez que le `github_token` a les bons scopes
- Vérifiez que `github_repo_owner` et `github_repo_name` sont corrects

### Erreur "403 Forbidden"

- Le token GitHub n'a pas les permissions `admin:repo_hook`
- Recréez un token avec les bons scopes

### Secrets non visibles sur GitHub

- Attendez quelques secondes et rafraîchissez la page
- Vérifiez les outputs Terraform : `terraform output github_secrets_configured`
