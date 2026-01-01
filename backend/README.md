# KGManager - Backend API

API FastAPI pour la gestion d'un graphe de connaissances avec Neo4j.

## Architecture

Cette API suit une architecture en couches :

- **Models** : Modèles Pydantic pour la validation des données
- **Repositories** : Couche d'accès aux données Neo4j
- **Controllers** : Routes et endpoints FastAPI

## Prérequis

- Python 3.9+
- Neo4j 5.0+

## Installation

1. Cloner le repository
2. Créer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement dans `.env`

## Lancement

```bash
python main.py
```

L'API sera accessible sur http://localhost:8000

Documentation interactive : http://localhost:8000/docs

## Endpoints

### Tags

- `GET /tags` - Liste tous les tags
- `GET /tags/{tag_id}` - Récupère un tag par ID
- `POST /tags` - Crée un nouveau tag
- `PUT /tags/{tag_id}` - Met à jour un tag
- `DELETE /tags/{tag_id}` - Supprime un tag

### Users

- `GET /users` - Liste tous les utilisateurs
- `GET /users/{user_id}` - Récupère un utilisateur par ID
- `POST /users` - Crée un nouvel utilisateur
- `PUT /users/{user_id}` - Met à jour un utilisateur
- `DELETE /users/{user_id}` - Supprime un utilisateur

### URLs

- `GET /urls` - Liste toutes les URLs
- `GET /urls/{url_id}` - Récupère une URL par ID
- `POST /urls` - Crée une nouvelle URL
- `PUT /urls/{url_id}` - Met à jour une URL
- `DELETE /urls/{url_id}` - Supprime une URL

### Files

- `GET /files` - Liste tous les fichiers
- `GET /files/{file_id}` - Récupère un fichier par ID
- `POST /files` - Crée un nouveau fichier
- `PUT /files/{file_id}` - Met à jour un fichier
- `DELETE /files/{file_id}` - Supprime un fichier
