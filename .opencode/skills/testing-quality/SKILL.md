---
name: testing-quality
description: "Use when writing tests or setting up CI — TDD cycle, pytest/Vitest patterns, CI pipeline, pre-commit hooks, coverage, PR checklist."
trigger: testing
---

# Testing & Quality

## TDD

Privilégier le TDD pour : règles métier, validateurs, parsers, transformations, services critiques.

Cycle : test qui échoue → code minimal → refactor → cas limites → documentation.

Priorités de test :
- règles métier, validateurs, parsers
- transformations de données
- repositories critiques
- services applicatifs
- permissions, erreurs, cas limites
- régressions, bugs corrigés

## Tests Python (pytest)

```bash
pytest
pytest tests/unit
pytest tests/integration
pytest --cov=src --cov-report=term-missing
```

## Tests Frontend (Vitest)

```bash
vitest
vitest --coverage
vitest run  # single run (CI)
```

## CI Pipeline (GitHub Actions)

Étapes : install → lint → typecheck → test → build → security scan → deploy staging → validation → deploy production.

## Règles CI

- Aucun merge sans tests critiques
- Aucun secret dans le repo
- Les migrations doivent être versionnées
- Les scripts de déploiement reproductibles
- Rollback prévu
- Environnements séparés : local, dev, staging, prod

## Qualité

- **Backend** : Ruff check + format, mypy strict, pytest
- **Frontend** : ESLint + Prettier, TypeScript strict, Vitest
- **Pre-commit** : Ruff, mypy, ESLint, Prettier
- **Pre-push** : tests unitaires + intégration

## Checklist PR

- [ ] Code typé
- [ ] Tests ajoutés ou mis à jour
- [ ] Erreurs gérées
- [ ] Pas de duplication inutile
- [ ] Fichiers raisonnablement courts
- [ ] Documentation mise à jour si nécessaire
- [ ] CI verte
- [ ] Aucun secret exposé
