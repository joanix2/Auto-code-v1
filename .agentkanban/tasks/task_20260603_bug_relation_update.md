---
title: Fix mise à jour des relations
lane: done
priority: P0
created: 2026-06-03T22:35:00+02:00
updated: 2026-06-03T22:35:00+02:00
description: Corriger le problème de mise à jour des relations dans le graphe
---

## Description

Les relations ne se mettent pas à jour correctement après modification.

## Corrections

1. `get_by_source_concept` et `get_by_target_concept` manquants dans `RelationshipRepository` → ajoutés
2. `BaseRepository.update` filtrait les valeurs `None` → changé pour filtrer uniquement les champs internes `_`
3. `issue_service.py` écrasait le statut local pendant le sync GitHub → préservation si statut personnalisé
