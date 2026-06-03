---
name: frontend-conventions
description: "Use when working on the React/TypeScript frontend — component patterns, UI states, accessibility, responsive design, form validation, project structure."
trigger: frontend
---

# Frontend Conventions

## Structure projet

```
src/
  app/
  pages/
  components/  composants réutilisables
  features/    fonctionnalités découpées
  services/    appels API, logique partagée
  hooks/
  stores/
  validators/
  types/
  utils/
  tests/
```

## Création de composants

Chaque composant doit avoir :
- nom clair, props typées, responsabilité unique
- état loading, erreur, vide
- accessibilité (navigation clavier, `aria-label`, focus visible)
- test si logique importante
- pas d'appel API direct si un service existe
- pas de logique métier complexe

Structure recommandée :
```
UserCard/
  UserCard.tsx
  UserCard.test.tsx
  UserCardSkeleton.tsx
  UserCard.types.ts
  index.ts
```

## États UI obligatoires

Pour chaque écran ou composant asynchrone :
- `idle`, `loading`, `success`, `empty`, `error`, `partial`, `unauthorized`

## Formulaires

Validation côté client + serveur, messages d'erreur compréhensibles, désactivation des boutons pendant l'envoi, conservation des données en cas d'erreur.

Outils : Zod, React Hook Form, Pydantic côté backend

## Accessibilité (WCAG)

- navigation clavier
- contraste suffisant
- labels sur les champs
- focus visible
- textes alternatifs
- pas d'info transmise uniquement par la couleur

## Performance

- mesurer avant d'optimiser
- surveiller : taille bundle, temps API, mémoire, rendu mobile
- charger initial raisonnable
