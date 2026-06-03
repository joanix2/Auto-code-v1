#!/bin/bash
# Setup E2E test: crée un utilisateur test dans Neo4j + génère un JWT
set -e
cd "$(dirname "$0")/../backend"
source venv/bin/activate

echo "🔧 Création de l'utilisateur E2E dans Neo4j..."
python3 -c "
from neo4j import GraphDatabase
uri = 'bolt://localhost:7687'
driver = GraphDatabase.driver(uri, auth=('neo4j', 'testpassword'))
with driver.session() as session:
    session.run(\"\"\"
        MERGE (u:User {username: 'e2e-test'})
        SET u.id = 'user-e2e',
            u.github_token = '',
            u.avatar_url = '',
            u.is_active = true,
            u.created_at = datetime()
    \"\"\")
    print('✅ Utilisateur e2e-test créé dans Neo4j')
driver.close()
"

echo "🔑 Génération du JWT..."
python3 -c "
from src.utils.auth import create_access_token
token = create_access_token({'sub': 'e2e-test', 'username': 'e2e-test'})
with open('/tmp/e2e-token.txt', 'w') as f:
    f.write(token)
print(f'✅ Token sauvegardé: {token[:50]}...')
"

echo '🎁 Prêt ! Lance les tests avec : cd frontend && npx playwright test e2e/'
