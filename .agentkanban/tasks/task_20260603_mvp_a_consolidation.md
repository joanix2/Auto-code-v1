---
title: MVP A — Consolidation IR/API/Frontend
lane: qa
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
priority: P1
description: Aligner l'existant (phases 1-3) avec le format IR cible de la roadmap
---

## Description

Audit et refactor de l'existant pour coller au format IR JSON standardisé. Ajout des endpoints manquants, d'un JSON schema formel, et garantie d'indépendance des couches.

## Sous-tâches

- [x] Auditer les modèles existants vs le format IR cible
- [x] Ajouter le support du format IR JSON natif (endpoints `/ir/save`, `/ir/load`, `/ir/files`)
- [x] Définir et valider un JSON schema formel pour l'IR (`backend/src/models/graph/schema.py`)
- [x] Garantir l'indépendance de l'IR vis-à-vis du frontend/backend
- [x] Ajouter les endpoints manquants (PATCH/DELETE edges, GET /graph complet)
- [x] Tests de roundtrip (30 tests dans `test_ir_roundtrip.py`)
