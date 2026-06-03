---
title: MVP B — Système de Requêtes
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
description: Implémenter le système de requêtes sur le graphe (Phase 4)
---

## Description

Permettre d'interroger le graphe comme une base de connaissances : sélecteurs par type, arbre JSON récursif, pattern matching, exposition via API REST.

## Sous-tâches

- [ ] Implémenter get_nodes_by_kind(kind) et get_edges_by_kind(kind)
- [ ] Implémenter get_neighbors(node_id) et get_incident_edges(node_id)
- [ ] Implémenter get_entity_tree(root_id, max_depth) → arbre JSON récursif
- [ ] Gérer les cycles dans l'extraction d'arbre (profondeur max, détection cycles)
- [ ] Exposer les requêtes via des endpoints API REST dédiés
- [ ] Implémenter le pattern matching (recherche de sous-graphes par motif)
- [ ] Tester les cas limites : graphe vide, nœud inexistant, profondeur max
