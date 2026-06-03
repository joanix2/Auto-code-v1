---
name: architecture-patterns
description: "Use when designing or refactoring architecture — DDD, hexagonal, MVC, repository, service layers, segmentation, and coupling rules. Provides reference patterns for clean module separation."
trigger: architecture
---

# Architecture Patterns

## Découpage recommandé

```
src/
  domain/       entités, value objects, services domaine, événements
  application/  use cases, ports, DTOs, validateurs
  infrastructure/ repositories, base de données, services externes
  interfaces/   API, CLI, web
  shared/       types, utils, config, erreurs
  tests/        unit, integration, e2e
```

## Règle Dossier > Fichiers > Objets > Fonctions

Toujours organiser selon cette hiérarchie décroissante. Un fichier ne devrait pas dépasser ~350 lignes, une fonction ~40 lignes.

## DDD (Domain Driven Design)

- **Entity** : objet métier avec identité
- **ValueObject** : objet immutable sans identité
- **Aggregate** : groupe cohérent d'entités
- **DomainService** : logique métier transverse
- **Repository** : abstraction de persistance (Protocol)
- **DomainEvent** : événement métier important
- **UseCase** : action applicative orchestrant le domaine

### Règles DDD

- Le domaine ne dépend jamais de l'infrastructure
- Les entités ne connaissent pas la base de données
- Les DTO ne deviennent pas des entités métier
- Les erreurs métier sont explicites et typées

## Architecture hexagonale

```
Domaine pur
  ↑
Application / Use cases
  ↑
Ports / Interfaces
  ↑
Adapters / Infrastructure / UI / API / DB
```

Les dépendances vont de l'extérieur vers l'intérieur. Les repositories sont des ports côté domaine, implémentés côté infrastructure.

## Services

- **DomainService** : règle métier pure
- **ApplicationService** : orchestration de cas d'usage
- **InfrastructureService** : API externe, stockage, etc.
- **ValidationService** : validation métier ou formulaire
- **AuthService** : authentification, permissions
- **ObservabilityService** : logs, traces, métriques

## Segmentation du code

Chaque feature est découpée en couches :

```
feature/
  domain/        modèles, règles, erreurs
  application/   use cases, validateurs
  infrastructure/ repositories, providers
  interfaces/    routes, handlers
  tests/
```

Ne pas mélanger : parsing, validation, accès base, appels API, logique métier, rendu UI, logs, erreurs dans un même fichier.
