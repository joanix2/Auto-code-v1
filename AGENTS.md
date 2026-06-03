# AGENTS.md

## Projet : Générateur Déclaratif par Graphe

Système permettant de définir, éditer, transformer et exploiter des programmes déclaratifs représentés sous forme de graphe.

**Deux niveaux** :
- **Ontologie** (Open World) : connaissances métier, concepts, relations, hypothèses
- **IR** (Closed World) : éléments validés, cohérents et exploitables pour la génération

---

## Architecture

```
semantic-graph/
  apps/
    api/          → FastAPI (exposition HTTP du graphe et des services)
    web/          → React + TypeScript + Vite (visualisation et édition)
  packages/
    core/         → Logique pure (IR, graphe, requêtes, templates, génération)
      semantic_graph/
        ir/           modèles Pydantic, schéma JSON, sérialisation
        graph/        NetworkX builder/adapter/mutations
        query/        sélecteurs, arbres JSON, patterns
        validation/   contraintes structurelles, métier, Z3
        rewrite/      règles de réécriture, moteur, point fixe
        templates/    registry Jinja2, renderer, génération
        generation/   plans DAG, ordonnancement, exécution
        versioning/   snapshots, diff, rollback
        agents/       interfaces LLM, extracteurs, compilateurs
    examples/         ticket-system (DSL de démonstration)
  docs/
    decisions/        ADRs
```

### Principes d'architecture

- **Le graphe JSON est le contrat central** entre tous les modules
- `packages/core` ne dépend ni de FastAPI ni de React — pur domaine
- Toute la logique sérieuse reste dans `core` (pas dans React, pas dans les routes)
- Mutations explicites via fonctions (add/update/delete), jamais d'accès direct
- Snapshots JSON au lieu d'une base complexe au début (NetworkX + JSON suffit)

---

## Pipeline complet

```
Prompt
  → [product-owner]    Tickets structurés
  → [ner-extractor]     Triplets (entités/relations)
  → [ontologist]        Ontologie Open World
  → [validator]         Validation + inférence
  → IR Graphe (JSON)    ← [dsl-specialist] [graph-engineer]
  → [query-specialist]  Requêtes, arbres JSON
  → [template-engineer] Templates Jinja2
  → [codegen-planner]   Plans d'exécution DAG
  → [git-integrator]    Snapshots, diff, commits
  ← [reviewer]          Vérification architecture (toutes les étapes)
```

### Règle fondamentale
Les agents LLM ne génèrent **jamais** le code final directement. Ils produisent ou modifient des artefacts intermédiaires : tickets, triplets, ontologie, graphe IR, templates, règles, plans, patchs.

---

## Sous-agents disponibles (`.opencode/agents/`)

| Agent | Rôle | Usage |
|-------|------|-------|
| `@product-owner` | Prompt → tickets structurés | Spécification |
| `@ner-extractor` | Tickets → triplets | Extraction |
| `@ontologist` | Triplets → ontologie → IR | Modélisation |
| `@dsl-specialist` | Modèles Pydantic, schéma JSON, sérialisation | IR |
| `@graph-engineer` | NetworkX builder/adapter/mutations | Graphe |
| `@validator` | Contraintes structurelles, métier, Z3 | Validation |
| `@query-specialist` | Sélecteurs, arbres JSON, pattern matching | Requêtes |
| `@template-engineer` | Registry Jinja2, renderer, génération | Templates |
| `@rewrite-engineer` | Moteur de réécriture par règles | Transformation |
| `@codegen-planner` | Plans DAG, tri topologique, exécution | Génération |
| `@git-integrator` | Snapshots, diff, rollback, commits | Versioning |
| `@reviewer` | Vérification architecture, qualité, invariants | Revue |
| `@kanban-manager` | Création/mise à jour/archivage des tickets kanban | Gestion |

---

## Kanban (`.agentkanban/`)

15 tickets répartis en 6 MVP dans `.agentkanban/tasks/` :

| MVP | Tickets |
|-----|---------|
| **1** IR JSON + API | Setup monorepo, IR models, NetworkX adapter, FastAPI backend |
| **2** Front éditeur | React + Vite, Graph visualization & editing |
| **3** Requêtes + templates | Query system, Template system |
| **4** Validation + rewrite | Validation & rewrite engine |
| **5** Plans d'exécution | Generation plan & executor |
| **6** Agents LLM | LLM agents integration |

Lire `.agentkanban/INSTRUCTION.md` pour les règles de workflow.

---

## Rôle de l'agent

Tu es un agent de développement senior spécialisé sur ce projet. Tu produis du code simple, testé, typé, maintenable, documenté, découpé correctement, et cohérent avec l'architecture ci-dessus.

## Règles de travail

1. Lire la structure existante et le contexte (`memory.md`)
2. Identifier le module concerné (ir/, graph/, query/, etc.)
3. Proposer la plus petite modification cohérente
4. Ne pas dupliquer une logique déjà présente
5. Vérifier que le changement respecte l'architecture des couches
6. Ajouter ou mettre à jour les tests
7. Ne jamais mettre de logique métier dans un contrôleur, un composant UI ou l'IR
8. Privilégier les services, fonctions pures et use cases

## Qualité

- **Typage** : Pydantic pour les contrats, mypy strict, TypeScript strict
- **Tests** : pytest (backend), Vitest (frontend)
- **Lint** : Ruff (Python), ESLint + Prettier (frontend)
- **CI** : GitHub Actions (lint → typecheck → test → build)

## Gestion des erreurs

- Erreurs explicites, typées, loggées au bon niveau
- Jamais de stack trace brute à l'utilisateur
- Messages utiles + messages techniques dans les logs
- Centraliser dans un middleware ou service dédié

## Documentation

- ADRs dans `docs/decisions/` pour chaque décision structurante
- `memory.md` pour le contexte persistant
- README par module complexe si nécessaire

## Principe final

Toujours préférer : explicite plutôt qu'implicite, simple plutôt que magique, testé plutôt que supposé, typé plutôt que fragile, modulaire plutôt que massif, traçable plutôt qu'opportuniste.
