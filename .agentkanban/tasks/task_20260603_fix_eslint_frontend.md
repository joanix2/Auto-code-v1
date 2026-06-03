---
title: Fix 2 erreurs ESLint frontend
lane: todo
created: 2026-06-03T21:45:00+02:00
updated: 2026-06-03T21:45:00+02:00
priority: P1
description: Résoudre les 2 erreurs ESLint dans le frontend React
---

## Description

2 erreurs ESLint dans les composants UI shadcn :
- `textarea.tsx` : `interface` vide équivalente à son supertype (`@typescript-eslint/no-empty-object-type`)
- 9 warnings `react-refresh/only-export-components` (non bloquant)

## Sous-tâches

- [x] Fix `textarea.tsx` : supprimer l'interface vide → type alias
- [x] Fix `command.tsx` : supprimer l'interface vide → type alias
- [ ] Examiner les 9 warnings react-refresh (fichiers qui exportent constants + composants) — non bloquant
- [x] Vérifier que `npm run lint` passe sans erreurs
