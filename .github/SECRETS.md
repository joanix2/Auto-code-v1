# GitHub Secrets Configuration for AutoCode

Pour configurer le déploiement automatique, vous devez ajouter les secrets suivants dans votre repository GitHub :

## Secrets requis

Allez dans : `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### 1. SSH_PRIVATE_KEY

La clé privée SSH pour se connecter à l'instance EC2.

```bash
# Générer la clé si elle n'existe pas
ssh-keygen -t rsa -b 4096 -f ~/.ssh/aws_key.pem -N ""

# Copier le contenu de la clé privée
cat ~/.ssh/aws_key.pem
```

Copiez tout le contenu (y compris `-----BEGIN RSA PRIVATE KEY-----` et `-----END RSA PRIVATE KEY-----`)

### 2. EC2_PUBLIC_IP

L'adresse IP publique de votre instance EC2.

```bash
# Obtenir l'IP depuis Terraform
cd IaC
terraform output -raw public_ip
```

### 3. NEO4J_PASSWORD

Le mot de passe Neo4j (par défaut : `password`, mais changez-le !)

```
password
```

### 4. GH_TOKEN

Un Personal Access Token GitHub pour l'agent AI (pas pour OAuth2 utilisateur).

**Important** : Ce token est différent de l'OAuth2 des utilisateurs !

- OAuth2 : Authentifie les utilisateurs dans l'interface web
- GH_TOKEN : Permet à l'agent AI de cloner/modifier les repos pendant le traitement des tickets

1. Allez sur GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Cochez : `repo` (Full control of private repositories)
4. Générez et copiez le token

**Recommandation** : Créez un compte GitHub de service dédié (ex: `autocode-bot`) plutôt que d'utiliser votre token personnel

### 5. ANTHROPIC_API_KEY

Votre clé API Anthropic pour Claude.

1. Allez sur https://console.anthropic.com/
2. Créez une clé API
3. Copiez la clé

## Vérification

Après avoir ajouté tous les secrets, votre liste devrait ressembler à :

- ✅ SSH_PRIVATE_KEY
- ✅ EC2_PUBLIC_IP
- ✅ NEO4J_PASSWORD
- ✅ GH_TOKEN
- ✅ ANTHROPIC_API_KEY

## Test du workflow

1. Faites un commit et push sur la branche `main`
2. Allez dans l'onglet `Actions` de votre repository
3. Vérifiez que le workflow `Deploy AutoCode to AWS EC2` s'exécute correctement

## Déploiement manuel

Vous pouvez aussi déclencher le déploiement manuellement :

1. Allez dans `Actions`
2. Sélectionnez `Deploy AutoCode to AWS EC2`
3. Cliquez sur `Run workflow`
4. Sélectionnez la branche `main`
5. Cliquez sur `Run workflow`
