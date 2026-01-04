# AutoCode - Docker Deployment Modes

Ce projet supporte deux modes de déploiement Docker :

## 🔧 Mode Développement (sans NPM)

**Fichier** : `docker-compose.dev.yml`

**Services** :

- Neo4j (ports 7474, 7687)
- Backend (port 8000)
- Frontend (port 3000)

**Avantages** :

- ✅ Pas de conflit de port 80/443
- ✅ Plus léger (pas de NPM)
- ✅ Idéal pour le développement local
- ✅ Volumes séparés (\_dev suffix)

**Lancement** :

```bash
# Avec Make
make start-dev

# Ou directement
docker compose -f docker-compose.dev.yml up -d
```

**Accès** :

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

---

## 🌐 Mode Production (avec NPM)

**Fichier** : `docker-compose.yml`

**Services** :

- Neo4j (ports 7474, 7687)
- Backend (port 8000)
- Frontend (port 3000)
- **Nginx Proxy Manager** (ports 80, 443, 81)

**Avantages** :

- ✅ Reverse proxy pour domaines personnalisés
- ✅ Certificats SSL automatiques (Let's Encrypt)
- ✅ Interface de gestion NPM
- ✅ Production-ready

**Pré-requis** :

- Ports 80 et 443 disponibles (aucun serveur web ne doit les utiliser)
- Si Apache/Nginx tourne localement, l'arrêter :
  ```bash
  sudo systemctl stop apache2
  sudo systemctl stop nginx
  ```

**Lancement** :

```bash
# Avec Make
make start

# Ou directement
docker compose up -d
```

**Accès** :

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474
- **NPM Admin**: http://localhost:81
  - Email: `admin@example.com`
  - Password: `changeme`

---

## 📋 Commandes Make

### Développement

```bash
make start-dev        # Démarrer mode dev
make build-dev        # Builder mode dev
make restart          # Redémarrer mode dev
```

### Production

```bash
make start            # Démarrer mode prod
make build            # Builder mode prod
make restart-prod     # Redémarrer mode prod
```

### Commun

```bash
make stop             # Arrêter tous les services
make logs             # Voir les logs
make logs-backend     # Logs backend uniquement
make logs-neo4j       # Logs Neo4j uniquement
make clean            # Tout nettoyer (⚠️ supprime les volumes)
```

---

## 🔄 Basculer entre les modes

```bash
# Passer de dev à prod
make stop
make start

# Passer de prod à dev
make stop
make start-dev
```

---

## 🐛 Résolution de problèmes

### Port 80 déjà utilisé

```bash
# Vérifier quel process utilise le port 80
sudo lsof -i :80

# Arrêter Apache/Nginx
sudo systemctl stop apache2
sudo systemctl stop nginx

# Ou utiliser le mode dev qui n'utilise pas le port 80
make start-dev
```

### Nettoyer complètement

```bash
# Arrêter et supprimer tout
make clean

# Redémarrer en mode dev
make start-dev
```

---

## 💡 Recommandations

**Pour le développement local** :

- ✅ Utilisez `make start-dev`
- Évite les conflits de ports
- Plus rapide à démarrer

**Pour la production / démo** :

- ✅ Utilisez `make start`
- Configure NPM pour vos domaines
- Active SSL avec Let's Encrypt

**Pour AWS EC2** :

- ✅ Utilisez `docker-compose.yml` (mode prod)
- NPM gérera le reverse proxy
- Terraform déploie automatiquement en mode prod
