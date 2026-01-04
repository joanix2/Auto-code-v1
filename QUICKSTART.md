# 🚀 Quick Start - AutoCode

## ✅ Prérequis

- Docker & Docker Compose installés
- Ports disponibles : 3000, 7474, 7687, 8000

## 🔧 Démarrage rapide (Développement)

```bash
# 1. Cloner le repo
git clone https://github.com/joanix2/Auto-code-v1.git
cd Auto-code-v1

# 2. Créer le fichier .env
cp .env.example .env
# Éditer .env et ajouter vos clés API

# 3. Démarrer en mode développement (sans NPM)
make start-dev

# OU directement avec Docker Compose
docker compose -f docker-compose.dev.yml up -d
```

## 🌐 Accès aux services

Une fois démarrés, accédez à :

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000/docs
- **Neo4j Browser** : http://localhost:7474
  - Username: `neo4j`
  - Password: `password`

## 📋 Commandes utiles

```bash
# Voir les logs
make logs

# Voir les logs d'un service spécifique
docker compose -f docker-compose.dev.yml logs -f backend

# Arrêter les services
make stop

# Redémarrer
make restart

# Nettoyer complètement
make clean
```

## 🔑 Configuration des clés API

Éditez le fichier `.env` et ajoutez :

```bash
# GitHub OAuth (pour l'authentification utilisateurs)
GITHUB_CLIENT_ID=votre_client_id
GITHUB_CLIENT_SECRET=votre_client_secret
GITHUB_REDIRECT_URI=http://localhost:3000/callback

# GitHub Token (pour l'agent AI)
GITHUB_TOKEN=ghp_votre_token_personnel

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-votre_cle

# Neo4j (par défaut)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# JWT
JWT_SECRET_KEY=votre_secret_genere
```

### Générer un JWT secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🎯 Premier test

1. Ouvrez http://localhost:3000
2. Connectez-vous avec GitHub OAuth
3. Créez un nouveau ticket
4. L'agent AI va traiter le ticket automatiquement

## 🐛 Problèmes courants

### Port 80 déjà utilisé

```bash
# Utiliser le mode dev qui n'utilise pas le port 80
make start-dev
```

### Backend ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker-compose.dev.yml logs backend

# Vérifier que Neo4j est démarré
docker compose -f docker-compose.dev.yml ps
```

### Erreur "anthropic version conflict"

```bash
# Le requirements.txt a été mis à jour avec anthropic==0.41.0
# Reconstruire les images
make build-dev
make start-dev
```

## 📚 Documentation complète

- [DOCKER_MODES.md](./DOCKER_MODES.md) - Modes de déploiement
- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) - Architecture
- [IaC/QUICKSTART.md](./IaC/QUICKSTART.md) - Déploiement AWS
- [.github/SECRETS.md](./.github/SECRETS.md) - Configuration CI/CD

## 🚀 Déploiement en production

Voir le guide complet : [IaC/QUICKSTART.md](./IaC/QUICKSTART.md)

```bash
# Mode production local (avec NPM)
make start

# Déploiement AWS
cd IaC
bash bash/provision.sh
```
