---
title: MVP A — Consolidation IR/API/Frontend
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
description: Aligner l'existant (phases 1-3) avec le format IR cible de la roadmap
---

## Description

Audit et refactor de l'existant pour coller au format IR JSON standardisé. Ajout des endpoints manquants, d'un JSON schema formel, et garantie d'indépendance des couches.

## Sous-tâches

- [ ] Auditer les modèles existants vs le format IR cible (`graph.json` avec nodes/edges/kinds)
- [ ] Ajouter le support du format IR JSON natif (endpoints `/graph/load`, `/graph/save`)
- [ ] Définir et valider un JSON schema formel pour l'IR
- [ ] Garantir l'indépendance de l'IR vis-à-vis du frontend/backend
- [ ] Ajouter les endpoints manquants (PATCH/DELETE edges, GET /graph)
- [ ] Tests de roundtrip (load → modify → save → load)
