---
title: Fix Metamodel creation (id Field required)
lane: qa
priority: P0
created: 2026-06-03T23:00:00+02:00
updated: 2026-06-03T23:00:00+02:00
description: La création Metamodel échoue car des champs de MetamodelCreate sont stockés dans Neo4j et ne correspondent pas au modèle Metamodel
---

## Description

`MetamodelCreate` a des champs (`settings`, `metadata`, `type`, `documentation`, `namespace`, `tags`, `is_public`, `repository_path`) qui n'existent pas sur `Metamodel`. Ils sont passés à `prepare_neo4j_properties`, stockés dans Neo4j, et au retour `self.model(**node)` échoue car Pydantic ne trouve pas `id` (ou rejette les champs inconnus selon la config).

## Solutions

1. Filtrer `data_dict` dans `validate_create` pour n'inclure que les champs de `Metamodel` + `owner_id`
2. Ou ajouter `extra = "ignore"` dans la Config de `Metamodel`
3. Ou créer des champs supplémentaires sur `Metamodel` pour stocker settings/metadata

## Sous-tâches

- [ ] Identifier la solution (option 1 recommandée)
- [ ] Implémenter le filtre dans `MetamodelController.validate_create`
- [ ] Vérifier que POST /api/metamodels crée et retourne correctement
- [ ] Vérifier que GET /api/metamodels/{id} fonctionne
