---
name: python-conventions
description: "Use when working on Python code — typing, Pydantic models, error handling patterns, project structure, linting with Ruff, type checking with mypy."
trigger: python
---

# Python Conventions

## Typage

Toute fonction publique doit avoir :
- signature claire avec types explicites
- nom compréhensible
- responsabilité unique
- docstring si comportement non trivial

Outils : `typing`, `Protocol`, `Literal`, `TypedDict`, `dataclasses`, `pydantic`

## Pydantic

Utiliser Pydantic pour :
- valider les entrées API
- typer les DTO
- valider les fichiers de configuration
- typer les résultats intermédiaires
- sécuriser les frontières entre modules
- documenter implicitement les contrats de données

Ne pas utiliser Pydantic comme remplacement du domaine métier si des entités DDD sont nécessaires.

## Gestion des erreurs

Toute erreur doit être : explicite, typée, loggée au bon niveau, compréhensible pour l'utilisateur, exploitable par les développeurs.

Types d'erreurs :
- utilisateur, validation, métier, permission
- réseau, base de données, fournisseur externe
- système, inconnue

Règles :
- ne jamais masquer silencieusement une erreur
- ne jamais afficher une stack trace brute à l'utilisateur
- toujours un message utilisateur utile + message technique dans les logs
- prévoir un fallback si possible
- centraliser dans un middleware ou service dédié

## Qualité

- Ruff : lint + format (line-length 120)
- mypy : strict mode
- pytest : autodécouverte, coverage
- pyproject.toml pour toute la config

## Structure projet type

```
src/
  app/
    domain/
    application/
    infrastructure/
    interfaces/
    shared/
  tests/
    unit/
    integration/
  scripts/
  docs/
```
