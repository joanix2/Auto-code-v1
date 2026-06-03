"""
Test Playwright : création d'un métamodèle sans erreur.

Stratégie : on utilise MockNeo4jDB comme les tests pytest,
on préconfigure les résultats pour chaque appel Neo4j.
"""

import sys, os, json
_backend = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, _backend)
os.chdir(_backend)
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from main import app
from src.models.oauth.user import User
from src.utils.auth import get_current_user
from src.database import get_db
from tests.conftest import MockNeo4jDB

MOCK_USER = User(id="user-test", username="testuser", github_token="", avatar_url="")
db = MockNeo4jDB()

# Ordre des requêtes Neo4j :
# 1. get_by_name("ModeleTest") → MATCH (m:Metamodel {name: $name}) RETURN m → pas de metamodel existant
db.add_result([])
# 2. MetamodelRepository.create :
#    CREATE (m:Metamodel $props) SET m.created_at = datetime()
#    WITH m MATCH (u:User {username: $owner_id}) CREATE (u)-[r:OWNS]->(m) RETURN m
db.add_result([{"m": {"id": "mm-test-1", "name": "ModeleTest", "version": "1.0", "status": "draft", "description": "", "owner_id": "user-test", "node_count": 0, "edge_count": 0, "graph_id": "mm-test-1", "x_position": None, "y_position": None, "created_at": "2026-06-03T00:00:00Z", "updated_at": None}}])

app.dependency_overrides[get_current_user] = lambda: MOCK_USER
app.dependency_overrides[get_db] = lambda: db

client = TestClient(app)


def test_create_metamodel():
    payload = {"name": "ModeleTest", "version": "1.0"}
    resp = client.post("/api/metamodels/", json=payload)
    print(f"POST /api/metamodels/ → {resp.status_code}")

    if resp.status_code != 201:
        print(f"❌ Erreur: {resp.text}")
        assert False, f"Expected 201, got {resp.status_code}"

    body = resp.json()
    print(f"✅ Metamodel créé: {json.dumps(body, indent=2, default=str)}")
    assert "id" in body, f"Missing 'id' in response: {body}"
    assert body["name"] == payload["name"]
    return body


if __name__ == "__main__":
    try:
        test_create_metamodel()
        print("\n🎉 Test réussi !")
    finally:
        app.dependency_overrides.clear()
