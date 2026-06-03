---
title: Refactoring des Controllers
lane: todo
created: 2026-06-03T19:15:00+02:00
updated: 2026-06-03T19:15:00+02:00
priority: P1
description: Refactoring de l'architecture des controllers avec double héritage
---

## Description

Refondre les controllers pour qu'ils aient un double héritage : synchronisation GitHub et Base controller. Ajouter plus de relations en base.

## Sous-tâches

- [x] Extraire `GitHubSyncMixin` dans `src/controllers/mixins/github_sync.py`
- [x] Appliquer double héritage : RepositoryController, IssueController, MessageController
- [ ] Plus de relations en base
- [x] Copier NodeType et EdgeType côté API (déjà présent dans m3_controller.py)
