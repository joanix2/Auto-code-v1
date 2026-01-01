# Guide d'Installation en Production

## Déploiement du Service Headless sur Serveur

Ce guide explique comment déployer Auto-Code en mode headless sur un serveur Linux (Ubuntu/Debian).

## Prérequis

- Serveur Linux (Ubuntu 20.04+ ou Debian 11+)
- Accès root ou sudo
- Python 3.11+
- Git
- Clé API Anthropic

## Installation

### 1. Créer un Utilisateur Dédié

```bash
# Créer l'utilisateur autocode
sudo useradd -r -s /bin/bash -d /opt/autocode -m autocode

# Créer les répertoires de logs
sudo mkdir -p /var/log/autocode
sudo chown autocode:autocode /var/log/autocode
```

### 2. Cloner le Repository

```bash
# Se connecter en tant qu'utilisateur autocode
sudo su - autocode

# Cloner le projet
cd /opt/autocode
git clone https://github.com/joanix2/Auto-code-v1.git
cd Auto-code-v1
```

### 3. Installer les Dépendances Backend

```bash
# Installer Python et pip
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip

# Créer un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances
cd backend
pip install -r requirements.txt
```

### 4. Configurer l'Environnement

```bash
# Copier le template
cp backend/.env.example backend/.env

# Éditer la configuration
nano backend/.env
```

Configurer les variables :

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
SECRET_KEY=your-secret-key-min-32-chars
ANTHROPIC_API_KEY=sk-ant-your-api-key
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_secret
```

### 5. Installer Neo4j

```bash
# Ajouter le repository Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Installer Neo4j
sudo apt update
sudo apt install -y neo4j

# Démarrer Neo4j
sudo systemctl enable neo4j
sudo systemctl start neo4j

# Configurer le mot de passe
cypher-shell -u neo4j -p neo4j
ALTER USER neo4j SET PASSWORD 'your_new_password';
:exit
```

### 6. Démarrer le Backend API

```bash
# Test manuel
cd /opt/autocode/Auto-code-v1/backend
source ../venv/bin/activate
python main.py

# Si tout fonctionne, créer un service systemd
```

### 7. Configurer le Service Systemd pour le Backend

```bash
# Créer le fichier service
sudo nano /etc/systemd/system/autocode-api.service
```

Contenu du fichier :

```ini
[Unit]
Description=Auto-Code Backend API
After=network.target neo4j.service

[Service]
Type=simple
User=autocode
Group=autocode
WorkingDirectory=/opt/autocode/Auto-code-v1/backend
Environment="PATH=/opt/autocode/Auto-code-v1/venv/bin"
EnvironmentFile=/opt/autocode/Auto-code-v1/backend/.env

ExecStart=/opt/autocode/Auto-code-v1/venv/bin/python main.py

Restart=always
RestartSec=10

StandardOutput=append:/var/log/autocode/api.log
StandardError=append:/var/log/autocode/api.error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable autocode-api
sudo systemctl start autocode-api

# Vérifier le statut
sudo systemctl status autocode-api
```

### 8. Configurer le Service Headless Development

```bash
# Copier le fichier service
sudo cp /opt/autocode/Auto-code-v1/scripts/autocode-headless.service \
    /etc/systemd/system/autocode-headless.service

# Éditer la configuration
sudo nano /etc/systemd/system/autocode-headless.service
```

Modifier les variables d'environnement :

```ini
Environment="ANTHROPIC_API_KEY=sk-ant-your-real-key"
Environment="AUTOCODE_REPO_ID=your-actual-repo-id"
Environment="AUTOCODE_USERNAME=your-username"
Environment="AUTOCODE_PASSWORD=your-password"
```

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable autocode-headless
sudo systemctl start autocode-headless

# Vérifier le statut
sudo systemctl status autocode-headless
```

### 9. Configuration Nginx (Optionnel)

Pour exposer l'API via HTTPS :

```bash
# Installer Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Créer la configuration
sudo nano /etc/nginx/sites-available/autocode
```

Contenu :

```nginx
server {
    listen 80;
    server_name autocode.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activer la configuration
sudo ln -s /etc/nginx/sites-available/autocode /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d autocode.example.com
```

## Gestion des Services

### Commandes Utiles

```bash
# Vérifier les logs du service headless
sudo journalctl -u autocode-headless -f

# Vérifier les logs du backend
sudo journalctl -u autocode-api -f

# Vérifier les fichiers de logs
tail -f /var/log/autocode/headless.log
tail -f /var/log/autocode/api.log

# Redémarrer les services
sudo systemctl restart autocode-api
sudo systemctl restart autocode-headless

# Arrêter les services
sudo systemctl stop autocode-headless
sudo systemctl stop autocode-api

# Désactiver au démarrage
sudo systemctl disable autocode-headless
```

### Monitoring

```bash
# Vérifier l'utilisation des ressources
systemctl status autocode-headless
systemctl status autocode-api

# Vérifier les processus
ps aux | grep autocode
ps aux | grep python

# Vérifier Neo4j
sudo systemctl status neo4j
```

## Mise à Jour

```bash
# Se connecter en tant qu'autocode
sudo su - autocode
cd /opt/autocode/Auto-code-v1

# Arrêter les services
sudo systemctl stop autocode-headless
sudo systemctl stop autocode-api

# Mettre à jour le code
git pull

# Mettre à jour les dépendances
source venv/bin/activate
cd backend
pip install -r requirements.txt --upgrade

# Redémarrer les services
sudo systemctl start autocode-api
sudo systemctl start autocode-headless
```

## Sauvegarde

### Backup Neo4j

```bash
# Créer un script de backup
sudo nano /opt/autocode/backup.sh
```

Contenu :

```bash
#!/bin/bash
BACKUP_DIR="/opt/autocode/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Neo4j
sudo neo4j-admin dump --database=neo4j --to=$BACKUP_DIR/neo4j_$DATE.dump

# Nettoyer les anciens backups (garder 7 jours)
find $BACKUP_DIR -name "neo4j_*.dump" -mtime +7 -delete
```

```bash
# Rendre exécutable
chmod +x /opt/autocode/backup.sh

# Ajouter au cron (tous les jours à 2h du matin)
sudo crontab -e
```

Ajouter :

```cron
0 2 * * * /opt/autocode/backup.sh >> /var/log/autocode/backup.log 2>&1
```

## Sécurité

### Firewall

```bash
# Installer ufw
sudo apt install -y ufw

# Configurer les règles
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 7687/tcp  # Neo4j (uniquement si accès distant nécessaire)

# Activer le firewall
sudo ufw enable
```

### Fail2ban

```bash
# Installer fail2ban
sudo apt install -y fail2ban

# Configurer pour Nginx
sudo nano /etc/fail2ban/jail.local
```

Contenu :

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
```

```bash
sudo systemctl restart fail2ban
```

## Troubleshooting

### Service ne démarre pas

```bash
# Vérifier les erreurs
sudo journalctl -xe -u autocode-headless

# Vérifier les permissions
ls -la /opt/autocode/Auto-code-v1
ls -la /var/log/autocode

# Vérifier la configuration
cat /etc/systemd/system/autocode-headless.service
```

### API inaccessible

```bash
# Vérifier que le service tourne
sudo systemctl status autocode-api

# Vérifier les ports
sudo netstat -tlnp | grep 8000

# Vérifier les logs
tail -f /var/log/autocode/api.log
```

### Neo4j connection failed

```bash
# Vérifier Neo4j
sudo systemctl status neo4j

# Tester la connexion
cypher-shell -u neo4j -p your_password

# Vérifier les logs
sudo journalctl -u neo4j -f
```

## Support

Pour toute question :

1. Vérifier les logs : `/var/log/autocode/`
2. Consulter la documentation : `CLAUDE_HEADLESS.md`
3. Vérifier les issues GitHub
