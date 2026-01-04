# 🚀 Étapes de Déploiement AWS - AutoCode

## ✅ Étapes complétées

1. ✅ Infrastructure Terraform déployée
2. ✅ Code poussé sur GitHub
3. ✅ Code tiré sur le serveur AWS
4. ✅ Fichier `.env` créé sur le serveur

## 📝 Prochaines étapes

### 1. Configurer les clés API sur le serveur

Connectez-vous au serveur :

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94
```

Éditez le fichier `.env` :

```bash
cd /home/ubuntu/app
nano .env
```

Remplacez les valeurs suivantes :

- `GITHUB_TOKEN` : Votre Personal Access Token GitHub (pour l'agent AI)
- `GITHUB_CLIENT_ID` : Client ID de votre OAuth App
- `GITHUB_CLIENT_SECRET` : Client Secret de votre OAuth App
- `ANTHROPIC_API_KEY` : Votre clé API Anthropic Claude

Sauvegardez avec `Ctrl+O`, `Enter`, puis quittez avec `Ctrl+X`.

### 2. Mettre à jour votre GitHub OAuth App

Allez sur https://github.com/settings/developers et mettez à jour :

- **Homepage URL** : `http://13.37.9.94:3000`
- **Authorization callback URL** : `http://13.37.9.94:8000/api/auth/github/callback`

### 3. Démarrer les services Docker

```bash
cd /home/ubuntu/app
docker compose up -d --build
```

### 4. Vérifier les services

```bash
# Voir le statut
docker compose ps

# Voir les logs
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f backend
```

### 5. Tester l'accès

Ouvrez dans votre navigateur :

- Frontend : http://13.37.9.94:3000
- Backend API : http://13.37.9.94:8000/docs
- Neo4j : http://13.37.9.94:7474 (neo4j / autocode_neo4j_2026)
- Nginx Proxy Manager : http://13.37.9.94:81 (admin@example.com / changeme)

## 🔧 Configuration Nginx Proxy Manager (Optionnel)

1. Accédez à http://13.37.9.94:81
2. Login : `admin@example.com` / `changeme`
3. Changez le mot de passe
4. Configurez un domaine personnalisé si vous en avez un
5. Activez SSL avec Let's Encrypt

## 🔒 Sécurisation (Important !)

### Changez le mot de passe Neo4j

```bash
docker exec -it auto-code-neo4j cypher-shell -u neo4j -p autocode_neo4j_2026
# Puis :
ALTER USER neo4j SET PASSWORD 'VotreNouveauMotDePasse';
:exit

# Mettez à jour le .env avec le nouveau mot de passe
nano .env
# Changez NEO4J_PASSWORD=VotreNouveauMotDePasse

# Redémarrez
docker compose restart backend
```

### Restreignez l'accès SSH

```bash
# Sur votre machine locale
cd /home/joan/Documents/AutoCode/Auto-code-v1/IaC

# Éditez main.tf pour restreindre SSH à votre IP
nano main.tf
# Changez la ligne :
# cidr_blocks = ["0.0.0.0/0"]
# en :
# cidr_blocks = ["VOTRE_IP/32"]

# Appliquez
terraform apply
```

## 📊 Monitoring

### Logs en temps réel

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94 "cd /home/ubuntu/app && docker compose logs -f"
```

### Statut des services

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94 "cd /home/ubuntu/app && docker compose ps"
```

### Utilisation des ressources

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94 "docker stats --no-stream"
```

## 🔄 Déploiements futurs

### Via GitHub Actions (recommandé)

1. Configurez les secrets GitHub (voir `.github/SECRETS.md`)
2. Push sur `main` → déploiement automatique

### Manuellement

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94
cd /home/ubuntu/app
git pull origin main
docker compose up -d --build
```

## 🆘 Dépannage

### Les services ne démarrent pas

```bash
# Voir les logs
docker compose logs

# Reconstruire complètement
docker compose down -v
docker compose up -d --build
```

### Erreur de connexion Neo4j

```bash
# Vérifier que Neo4j est démarré
docker compose ps neo4j

# Voir les logs Neo4j
docker compose logs neo4j
```

### Erreur OAuth GitHub

- Vérifiez que les URLs de callback sont correctes dans GitHub
- Vérifiez que `GITHUB_CLIENT_ID` et `GITHUB_CLIENT_SECRET` sont corrects dans `.env`
- Vérifiez que `FRONTEND_URL` est correct (http://13.37.9.94:3000)

## 💰 Coûts AWS

- EC2 t3.medium : ~€30/mois
- EBS 30GB : ~€2.40/mois
- Data Transfer : ~€5-10/mois
- **Total : ~€40-45/mois**

## 🛑 Arrêter/Détruire

### Arrêter l'application (garder l'infrastructure)

```bash
ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94 "cd /home/ubuntu/app && docker compose down"
```

### Détruire toute l'infrastructure AWS

```bash
cd /home/joan/Documents/AutoCode/Auto-code-v1/IaC
terraform destroy
```
