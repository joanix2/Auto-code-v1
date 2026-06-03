---
title: Fix bugs graph visualization
lane: todo
priority: P0
created: 2026-06-03T22:35:00+02:00
updated: 2026-06-03T22:35:00+02:00
description: Corriger les bugs du GraphViewer (drag mobile, attraction, flèches, logs)
---

## Description

Bugs frontend D3.js :
- Le drag ne marche pas en mobile
- Pas d'attraction entre les noeuds
- Style de la flèche ne doit pas partir du centre
- Si un noeud est modifié, les edges doivent continuer de pointer vers le noeud
- Si deux liaisons, pas deux fois le même noeud
- Dessin de la flèche doit partir de la bordure
- Supprimer les logs de debug

## Sous-tâches

- [ ] Fix drag mobile (touch events)
- [ ] Fix attraction physics (force parameters)
- [ ] Fix arrow style (start from border, not center)
- [ ] Fix edge target after node name change
- [ ] Fix duplicate node when multiple edges
- [ ] Supprimer les logs de debug du GraphViewer
