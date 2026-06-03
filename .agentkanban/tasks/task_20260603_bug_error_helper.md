---
title: Helper gestion d'erreurs controllers
lane: done
priority: P0
created: 2026-06-03T22:35:00+02:00
updated: 2026-06-03T23:15:00+02:00
description: Créer un helper mutualisé pour la gestion des erreurs HTTP dans les controllers
---

## Description

Factoriser le pattern try/except/HTTPException actuellement dupliqué dans tous les controllers.

## Sous-tâches

- [x] Créer `backend/src/utils/error_handler.py` avec 5 helpers (handle_create/update/delete/get/operation)
- [x] Remplacer 6 blocs try/except dupliqués dans `base_controller.py` par le helper
- [x] Centraliser les messages d'erreur dans un seul fichier
- [x] 110 tests passent, mypy clean
