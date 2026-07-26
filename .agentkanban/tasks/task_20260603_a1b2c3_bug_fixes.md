---
title: Bug Fixes
lane: todo
created: 2026-06-03T19:15:00+02:00
updated: 2026-06-03T19:15:00+02:00
priority: P0
description: Résolution des bugs restants identifiés dans le TODO
---

## Description

Correction des bugs et problèmes identifiés dans le TODO.md.

## Sous-tâches

Sous-tickets (segmentation) :
- `bug_error_helper` — Helper gestion d'erreurs controllers
- `bug_relation_update` — Fix mise à jour des relations
- `bug_graph_mobile` — Fix bugs graph visualization (drag mobile, attraction, flèches, logs)

Bugs restants :
- [ ] Tickets en attente de validation passent en open (idem pour en cours)

### user

fait le bug fix P0

### agent

Correctif terminé. Les permissions de `.opencode/agents/arch-diagram.md`
utilisent désormais `allow` au lieu de `true`. `opencode --help` et
`opencode agent list` terminent avec un code de sortie 0 ; la configuration et
la liste complète des agents sont donc chargées sans erreur de schéma.

La convention a été consignée dans `TECHNICAL.md` et l'itération correspondante
du TODO est entièrement cochée. La modification préexistante de
`.opencode/agents/commit-agent.md` n'a pas été touchée.

### user
