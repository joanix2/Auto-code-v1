# ADR-001 : Utiliser JSON comme format d'IR central

- **Date** : 2026-06-03
- **Statut** : Accepté

## Contexte

Le projet manipule un graphe de connaissances à deux niveaux (Ontologie Open World, IR Closed
World). Ce graphe est le contrat central entre tous les modules : extraction, validation,
requêtes, templates, génération. Il doit pouvoir être :

- **Portable** : échangeable entre processus, services, langages
- **Versionné** : traçable dans le temps, snapshots, rollbacks
- **Validable** : structure connue et vérifiable automatiquement
- **Sérialisable** : stockage fichier, transmission HTTP, diffusion Git

## Décision

Le graphe est représenté en **JSON** avec un schéma défini par des modèles **Pydantic** en
Python. Le JSON inclut un champ `schema_version` (semver) pour gérer l'évolution du format.

Le schema est produit une seule fois par version de `packages/core` et sert de contrat pour
tous les consommateurs (API, frontend, agents LLM, scripts).

Un versioning sémantique est appliqué au schema :
- **MAJOR** : breaking change (structure, champs obligatoires supprimés)
- **MINOR** : ajout compatible (nouveaux champs optionnels)
- **PATCH** : correction de documentation ou contrainte

## Conséquences

- **Positives**
  - Validation native via Pydantic (deserialization = validation)
  - Sérialisation triviale (`model_dump_json()`)
  - Interopérabilité avec tout langage / outil qui lit du JSON
  - Facile à versionner dans Git, diff visibles
  - JSON Schema exportable pour génération de clients TypeScript

- **Négatives**
  - Verbosité plus grande qu'un format binaire (protobuf, msgpack)
  - Pas de query natif (contrairement à un graphe Neo4j)
  - Poids réseau plus élevé (compressible en gzip si nécessaire)

- **Risques**
  - Mutation non contrôlée du JSON → mitigé par les modèles Pydantic readonly
  - Dérive du schema sans mise à jour du versioning → mitigé par les tests
