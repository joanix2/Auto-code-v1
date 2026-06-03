# Architecture du Générateur Déclaratif par Graphe

## Vue d'ensemble

Le système transforme des prompts utilisateur en code généré via un pipeline en plusieurs
étapes, où chaque étape produit un artefact structuré. Le coeur est un **graphe de
connaissances** à deux niveaux :

```
┌─────────────────────────────────────────────────────────┐
│                    Ontologie (Open World)                 │
│  Concepts, relations, hypothèses — connaissances métier  │
│  Validée et inférée →                                   │
│                                                         │
│                    IR (Closed World)                      │
│  Éléments validés, cohérents, exploitables              │
│  Requêté, transformé, templatisé →                      │
│                                                         │
│                    Code généré                            │
│  Fichiers, projet, documentation                        │
└─────────────────────────────────────────────────────────┘
```

### Niveaux

1. **Ontologie** (monde ouvert) : connaissances métier, concepts, relations, hypothèses.
   Peut contenir des contradictions, des incomplétudes. C'est le résultat brut de
   l'extraction et de la modélisation.

2. **IR — Intermediate Representation** (monde fermé) : sous-ensemble validé, cohérent
   et exploitable. C'est le graphe qui sert de source unique de vérité pour la génération.

## Structure du monorepo

```
semantic-graph/
├── apps/
│   ├── api/                  → FastAPI — exposition HTTP
│   │   ├── routes/           → Endpoints (graphe, query, templates, generation)
│   │   ├── dependencies/     → Injection de dépendances
│   │   └── main.py
│   └── web/                  → React + TypeScript + Vite — UI
│       ├── src/
│       │   ├── components/   → React components
│       │   ├── hooks/        → Custom hooks
│       │   ├── services/     → API client
│       │   └── types/        → Typescript types (générés depuis Pydantic)
│       └── package.json
├── packages/
│   └── core/                 → Python — logique pure
│       └── semantic_graph/
│           ├── ir/           → Modèles Pydantic, schéma JSON, sérialisation
│           ├── graph/        → NetworkX builder/adapter/mutations
│           ├── query/        → Sélecteurs, arbres JSON, patterns
│           ├── validation/   → Contraintes structurelles, métier, Z3
│           ├── rewrite/      → Règles de réécriture, moteur, point fixe
│           ├── templates/    → Registry Jinja2, renderer, génération
│           ├── generation/   → Plans DAG, ordonnancement, exécution
│           ├── versioning/   → Snapshots, diff, rollback
│           └── agents/       → Interfaces LLM, extracteurs, compilateurs
├── docs/
│   ├── decisions/            → Architecture Decision Records
│   └── dsl.json              → Spécification du DSL de démonstration
└── .agentkanban/             → Kanban des tickets MVP
```

## Pipeline complet

```
Prompt Utilisateur
    │
    ▼
┌──────────────────┐
│  @product-owner  │  → Tickets structurés
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @ner-extractor  │  → Triplets (entités / relations)
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @ontologist     │  → Ontologie Open World (JSON)
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @validator      │  → Validation + inférence → IR
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @dsl-specialist │  → Modèles Pydantic, schéma JSON (IR)
│  @graph-engineer │  → Graphe IR (NetworkX)
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @query-spe.     │  → Requêtes, arbres JSON, patterns
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @template-eng.  │  → Templates Jinja2
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @codegen-planner│  → Plans DAG, ordonnancement
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  @git-integrator │  → Snapshots, diff, commits
└──────────────────┘
    │
    ▼
Code généré
```

### Règle fondamentale

Les agents LLM ne génèrent **jamais** le code final directement. Ils produisent ou
modifient des artefacts intermédiaires : tickets, triplets, ontologie, graphe IR,
templates, règles, plans, patchs. Voir [ADR-004](../decisions/ADR-004-no-direct-prompt-generation.md).

## Rôles des agents LLM

| Agent | Rôle | Artefact produit |
|-------|------|-----------------|
| `@product-owner` | Analyser le prompt, produire des spécifications structurées | Tickets |
| `@ner-extractor` | Extraire entités et relations du texte | Triplets |
| `@ontologist` | Modéliser l'ontologie à partir des triplets | Ontologie JSON |
| `@validator` | Valider structure, cohérence, contraintes métier | Rapports, IR validé |
| `@dsl-specialist` | Définir les modèles et le schéma de l'IR | Modèles Pydantic, JSON Schema |
| `@graph-engineer` | Construire et muter le graphe NetworkX | Graphe IR JSON |
| `@query-specialist` | Formuler des requêtes et patterns | Arbres JSON, sélecteurs |
| `@template-engineer` | Créer et maintenir les templates Jinja2 | Templates |
| `@rewrite-engineer` | Définir des règles de transformation | Règles de réécriture |
| `@codegen-planner` | Planifier l'exécution de la génération | Plans DAG |
| `@git-integrator` | Gérer snapshots, diff, rollback | Commits, patchs |
| `@reviewer` | Vérifier la qualité et les invariants | Rapports de revue |

## Principes d'architecture

1. **Le graphe JSON est le contrat central** entre tous les modules
2. **`packages/core` ne dépend ni de FastAPI ni de React** — pur domaine
3. **Toute la logique sérieuse reste dans `core`** (pas dans React, pas dans les routes)
4. **Mutations explicites** via fonctions (add/update/delete), jamais d'accès direct
5. **Snapshots JSON** au lieu d'une base complexe au début (NetworkX + JSON suffit)
6. **Versioning** : le schema IR est versionné (semver), les snapshots aussi
