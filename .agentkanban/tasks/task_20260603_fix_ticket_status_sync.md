---
title: Fix ticket status sync (in_progress/review → open)
lane: done
priority: P0
created: 2026-06-03T23:30:00+02:00
updated: 2026-06-03T23:30:00+02:00
description: Les tickets en attente de validation ou en cours perdaient leur statut lors de la synchronisation GitHub
---

## Description

`sync_from_github` dans `issue_service.py` écrase le statut local (`in_progress`, `review`) par `open` car GitHub n'a que les états open/closed. Le fix préserve le statut local si le GitHub state est "open" et que le statut local est personnalisé.

## Sous-tâches

- [x] Identifier la cause : `map_github_to_db` renvoie "open" pour tout ce qui est ouvert sur GitHub
- [x] Fix : préserver le statut local si GitHub state == "open" et statut local ∉ ("open", "closed")
- [x] 110 tests passent, mypy clean
