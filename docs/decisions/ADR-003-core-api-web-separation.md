# ADR-003 : Séparer core, API et web dans un monorepo

- **Date** : 2026-06-03
- **Statut** : Accepté

## Contexte

Le projet a trois zones de responsabilité distinctes :
1. **Logique métier** : modèles, graphe, validation, templates, génération
2. **Exposition HTTP** : endpoints API pour le frontend et les scripts
3. **Interface utilisateur** : visualisation et édition interactive du graphe

Ces trois zones ont des cycles de vie, des dépendances et des contraintes différentes
(Python pur pour le domaine, FastAPI pour l'API, React/TypeScript pour le front).

## Décision

Structure monorepo avec trois zones isolées :

```
semantic-graph/
  packages/
    core/          → Logique pure, zéro dépendance web
  apps/
    api/           → FastAPI, dépend de core
    web/           → React + TypeScript + Vite, communique via l'API
```

Règles :
- `packages/core` ne dépend ni de FastAPI, ni de React
- `apps/api` importe `core` comme dépendance locale
- `apps/web` ne connaît que l'API HTTP, pas `core` directement
- Toute la logique sérieuse (graphe, validation, templates, génération) est dans `core`
- Les contrôleurs API sont des couches minces qui délèguent à `core`

## Conséquences

- **Positives**
  - Core testable sans serveur, sans base, sans navigateur
  - Core réutilisable (scripts CLI, agents LLM, batch processing)
  - Équipes indépendantes : backend Python / frontend TypeScript
  - Déploiement séparé possible (API scale, web CDN)
  - Faible couplage : un changement de framework API n'impacte pas core

- **Négatives**
  - Complexité de build monorepo (gestion des dépendances locales)
  - Nécessite un outillage de workspace (npm workspaces, pip -e, uv)
  - Duplication de typage entre core (Pydantic) et web (TypeScript)

- **Risques**
  - Décalage entre les types Python et TypeScript → mitigé par génération automatique
    des types TS depuis les Pydantic models (ou contrat OpenAPI)
  - Tentation de mettre de la logique dans les contrôleurs → mitigé par les revues
    et l'ADR lui-même
