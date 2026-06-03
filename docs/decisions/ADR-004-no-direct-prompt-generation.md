# ADR-004 : Les agents LLM ne génèrent jamais le code final directement

- **Date** : 2026-06-03
- **Statut** : Accepté

## Contexte

Le pipeline utilise des agents LLM à plusieurs étapes (product-owner, ner-extractor,
ontologist, dsl-specialist, graph-engineer, template-engineer, …). Ces agents sont
sollicités pour produire des artefacts intermédiaires.

Si un agent LLM produit directement du code exécutable (Python, TypeScript, SQL,
templates Jinja2), cela pose plusieurs problèmes :
- **Fiabilité** : le code généré peut être incorrect, dangereux ou incohérent
- **Traçabilité** : on ne sait pas quelles décisions ont mené à ce code
- **Validation** : un code final est difficile à valider sans son contexte
- **Révision** : la relecture humaine est inefficace sur du code généré en boîte noire

## Décision

**Aucun agent LLM ne produit de code final directement.**

Chaque agent produit uniquement des **artefacts intermédiaires** typés et validables :

| Agent | Artefact produit |
|-------|-----------------|
| `@product-owner` | Tickets structurés |
| `@ner-extractor` | Triplets (entités / relations) |
| `@ontologist` | Ontologie Open World (JSON) |
| `@dsl-specialist` | Modèles Pydantic, schéma JSON |
| `@graph-engineer` | Graphe IR (JSON + mutations NetworkX) |
| `@validator` | Contraintes, règles de validation |
| `@query-specialist` | Requêtes, arbres JSON, patterns |
| `@template-engineer` | Templates Jinja2 |
| `@rewrite-engineer` | Règles de réécriture |
| `@codegen-planner` | Plans DAG, ordonnancement |
| `@git-integrator` | Snapshots, diff, patchs |
| `@reviewer` | Rapports de vérification |

Le code final est produit par des **transformations déterministes** (réécriture, templates,
compilation, génération) à partir de ces artefacts.

## Conséquences

- **Positives**
  - Traçabilité : chaque étape produit un artefact visible et versionné
  - Validation possible à chaque étape (contraintes, tests, revue)
  - Révision humaine facilitée (artefacts lisibles et structurés)
  - Réexécution déterministe : les transformations vérifiées sont reproductibles
  - les LLM restent dans leur rôle : génération de spécifications, pas de code

- **Négatives**
  - Pipeline plus long (artefacts intermédiaires = étapes supplémentaires)
  - Coût LLM plus élevé (plus d'appels, plus de tokens)
  - Complexité d'orchestration (coordination des agents)

- **Risques**
  - Contournement de la règle par pression de productivité → mitigé par revue
    systématique et CI qui vérifie qu'aucun code final n'est produit par un agent
  - Artefacts intermédiaires trop volumineux → mitigé par une taille de graphe limitée
    et un versioning Git efficace
