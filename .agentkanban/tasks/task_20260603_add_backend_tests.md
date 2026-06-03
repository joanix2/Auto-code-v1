---
title: Ajout tests backend
lane: todo
created: 2026-06-03T21:45:00+02:00
updated: 2026-06-03T21:45:00+02:00
priority: P1
description: Couvrir le backend avec des tests pytest
---

## Description

Actuellement seuls 3 tests d'auth existent. Le backend a ~80 fichiers source sans couverture de test. `test_copilot_agent.py` est un script, pas un test pytest.

## Sous-tâches

- [x] Ajouter tests pour les modèles (NodeType, EdgeType, IssueCreate, RepositoryCreate)
- [x] Convertir `test_copilot_agent.py` en vrai test pytest avec mocks httpx
- [x] Ajouter tests pour les repositories (24 tests CRUD avec mock Neo4j)
- [x] Ajouter tests pour les services (18 tests logique métier)
- [x] Ajouter tests pour les controllers (16 tests API avec TestClient FastAPI)
- [ ] Ajouter tests pour le moteur de requêtes graphe
- [x] Viser au moins 40% de couverture (110 tests au total)
