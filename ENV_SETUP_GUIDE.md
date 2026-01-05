# 🚀 Configuration rapide du fichier .env

## 1. Créer le fichier .env

```bash
cp .env.example .env
```

## 2. Remplir les variables obligatoires

### 🔐 GitHub OAuth (authentification utilisateurs)

1. Allez sur https://github.com/settings/developers
2. Cliquez sur "New OAuth App"
3. Remplissez :
   - **Application name** : `AutoCode`
   - **Homepage URL** : 
     - Local : `http://localhost:3000`
     - AWS : `http://35.181.22.28:3000` (remplacez par votre IP)
   - **Authorization callback URL** :
     - Local : `http://localhost:8000/api/auth/github/callback`
     - AWS : `http://35.181.22.28:8000/api/auth/github/callback`
4. Copiez le **Client ID** et générez un **Client Secret**

Dans votre `.env` :
```bash
GITHUB_CLIENT_ID=Ov23li...votre_client_id
GITHUB_CLIENT_SECRET=...votre_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback
```

### 🤖 GitHub Token (pour l'agent AI)

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur "Generate new token (classic)"
3. Cochez : `repo` (Full control of private repositories)
4. Copiez le token

Dans votre `.env` :
```bash
GITHUB_TOKEN=ghp_...votre_token
```

**💡 Recommandation** : Créez un compte bot dédié (ex: `autocode-bot`)

### 🧠 Anthropic API Key

1. Allez sur https://console.anthropic.com/
2. Créez une clé API
3. Copiez la clé

Dans votre `.env` :
```bash
ANTHROPIC_API_KEY=sk-ant-...votre_cle
```

### 🔑 JWT Secret

Générez une clé secrète aléatoire :

```bash
openssl rand -hex 32
```

Copiez le résultat dans votre `.env` :
```bash
SECRET_KEY=996320cd7d7f9a9ed6b9bf4dc66f90dc52440ebc4d9e4902437c119dfd6d348b
```

### 🗄️ Neo4j Password

Changez le mot de passe par défaut :

```bash
NEO4J_PASSWORD=VotreMotDePasseSecurise123
```

### 🌐 URLs (selon votre environnement)

**Pour développement local** :
```bash
FRONTEND_URL=http://localhost:3000
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback
ENVIRONMENT=development
```

**Pour AWS** :
```bash
FRONTEND_URL=http://35.181.22.28:3000
GITHUB_REDIRECT_URI=http://35.181.22.28:8000/api/auth/github/callback
ENVIRONMENT=production
```

## 3. Fichier .env complet (exemple)

```bash
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=MonMotDePasse123

# GitHub OAuth
GITHUB_CLIENT_ID=Ov23liAbCdEfGh123456
GITHUB_CLIENT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

# GitHub Token (AI Agent)
GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456789

# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456789

# JWT
SECRET_KEY=996320cd7d7f9a9ed6b9bf4dc66f90dc52440ebc4d9e4902437c119dfd6d348b
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://backend:8000
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=development
```

## 4. Pour AWS (avec Terraform)

Si vous déployez sur AWS, ajoutez ces variables d'environnement avant `terraform apply` :

```bash
export TF_VAR_github_token="ghp_...votre_token"
export TF_VAR_github_owner="joanix2"
export TF_VAR_github_repo="Auto-code-v1"
export TF_VAR_aws_region="eu-west-3"
export TF_VAR_project_name="autocode"
```

Terraform configurera automatiquement les secrets GitHub Actions !

## 5. Vérification

```bash
# Vérifier que le .env existe et contient les bonnes variables
cat .env | grep -E "GITHUB_CLIENT_ID|ANTHROPIC_API_KEY|SECRET_KEY"

# Démarrer les services
make start-dev
```

## 🔒 Sécurité

⚠️ **IMPORTANT** : 
- Ne commitez JAMAIS le fichier `.env` sur Git
- Le `.env` est déjà dans le `.gitignore`
- Utilisez des mots de passe forts pour la production
- Changez tous les secrets par défaut

## 🆘 Problèmes courants

### "OAuth callback mismatch"
➡️ Vérifiez que `GITHUB_REDIRECT_URI` correspond exactement à l'URL de callback dans votre OAuth App

### "Invalid API key"
➡️ Vérifiez que votre clé Anthropic est valide et n'a pas expiré

### "Connection refused Neo4j"
➡️ Lancez `make start-dev` pour démarrer Neo4j
