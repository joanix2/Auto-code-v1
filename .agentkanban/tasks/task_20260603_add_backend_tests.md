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

- [ ] Convertir `test_copilot_agent.py` en vrai test pytest avec mocks GitHub API
- [ ] Ajouter tests pour les modèles (Node, Edge, Graph, Metamodel, Concept, Attribute, Relationship)
- [ ] Ajouter tests pour les repositories (CRUD de base)
- [ ] Ajouter tests pour les services (logique métier)
- [ ] Ajouter tests pour les controllers (endpoints API avec TestClient FastAPI)
- [ ] Ajouter tests pour le moteur de requêtes graphe
- [ ] Viser au moins 40% de couverture
