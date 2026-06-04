---
title: "MVP-H — Restructuration Graphe : Abstract → DSL → Ontologie/Architecture"
lane: todo
created: "2026-06-04T23:00:00"
updated: "2026-06-04T23:00:00"
description: "Refonte complète de l'architecture graphe sur 3 niveaux : Abstract (abstrait) → DSL (langage) → Ontologie & Architecture (domaines). Renommage Metamodel → DSL, création des couches Ontologie et Architecture, backend + frontend."
---

# MVP-H — Restructuration Graphe

## Structure cible

### Principe : Open World / Closed World

**Dans un projet :**

```
Tickets
  ↓ [ner-extractor] triplets
Ontologie (OW, par projet) — concepts extraits des tickets, libres
  ↓ mapping manuel/assisté
Architecture (CW, par projet) — modèle typé par un DSL
```

Le **DSL** (ex-Métamodèle) est un type system **réutilisable**, créé indépendamment dans l'onglet "DSLs". Il n'est PAS généré par l'ontologie — l'ontologie alimente directement l'architecture.

```
AbstractGraph (M3 — framework générique)
  ├── OntologyGraph (OW — par projet, tickets → triplets → concepts libres)
  ├── DSLGraph (M2 — réutilisable, standalone, définit les types)
  │    └── ArchitectureGraph (CW — par projet, parent_dsl_id, types = DSLConcept du parent)
  └── ...
```

### Types

```
AbstractNodeType
  ├── (utilisé directement par OntologyGraph — types libres/contexte)
  └── DSLConcept (M2 — type formel, défini dans DSLGraph)
       └── ArchitectureNode (M1 — instance d'un DSLConcept)
            ├── name: "MonAPI"
            ├── dsl_concept_id → DSLConcept "Microservice"
            └── properties: {...}
```

### Backend

```
models/abstract/                      models/dsl/                     models/ontology/              models/architecture/
  AbstractGraph                         DSLGraph extends AbstractGraph   OntologyGraph                  ArchitectureGraph
  AbstractNode                          DSLConcept extends AbstractNode   extends AbstractGraph           extends DSLGraph
  AbstractEdge                          DSLAttribute extends AbstractNode  (pas de parent DSL)           └── parent_dsl_id
  AbstractNodeType                      DSLRelation extends AbstractNode  ─── types libres              (types = DSLConcept du parent)
  AbstractEdgeType                      DSLEdge extends AbstractEdge      
                                        DSLConfig (ex-M3Config)          OntologyNode                    ArchitectureNode
                                                                         (type libre: string)            (instance de DSLConcept)
                                                                                                        └── dsl_concept_id
                                                                         OntologyEdge                    ArchitectureEdge
                                                                         (type libre)                    (instance de DSLEdge)
```

### Frontend

```
components/common/GraphViewer/        components/dsl/                   components/ontology/          components/architecture/
  AbstractGraphViewer                   DSLGraphViewer                    OntologyGraphViewer           ArchitectureGraphViewer
  AbstractNodeType                      extends AbstractGraphViewer       extends DSLGraphViewer        extends DSLGraphViewer
  AbstractEdgeType                                                           
                                        DSLNodeType (Concept/Attr/Rel)   OntologyNodeType              ArchitectureNodeType
                                        DSLEdgeType                                                       
                                                                         OntologyEdgeType              ArchitectureEdgeType
```

### Héritage

**OntologyGraph** : `extends AbstractGraph` (pas de parent DSL, pas de contrainte de types)

**ArchitectureGraph** : `extends DSLGraph` avec référence à un DSL parent
  - `parent_dsl_id: str` → le DSL dont les types sont utilisés
  - `allowed_node_types` → DSLConcept du parent (lecture seule, pas de création locale)
  - `allowed_edge_types` → DSLEdge du parent (lecture seule)

**ArchitectureNode** :
  - `dsl_concept_id: str` → référence un DSLConcept du parent
  - `name`, `properties` → instance du concept

## Renommages

| Ancien | Nouveau | Contexte |
|--------|---------|----------|
| `Graph` | `AbstractGraph` | models/graph/ |
| `Node` | `AbstractNode` | models/graph/ |
| `Edge` | `AbstractEdge` | models/graph/ |
| `NodeType` | `AbstractNodeType` | models/graph/ |
| `EdgeType` | `AbstractEdgeType` | models/graph/ |
| `Metamodel` | `DSLGraph` | Nouveau: models/dsl/ |
| `Concept` | `DSLConcept` | models/dsl/ |
| `Attribute` | `DSLAttribute` | models/dsl/ |
| `Relationship` | `DSLRelation` | models/dsl/ |
| `MetamodelEdge` | `DSLEdge` | models/dsl/ |
| `M3Config` | `DSLConfig` | models/dsl/ |
| `/api/metamodels` | `/api/dsls` | Routes |
| `MetamodelController` | `DSLController` | controllers/dsl/ |
| `MetamodelService` | `DSLService` | services/dsl/ |
| `MetamodelRepository` | `DSLRepository` | repositories/dsl/ |
| `GraphViewer` | `AbstractGraphViewer` | Frontend components/ |
| `NodeType` (front) | `AbstractNodeType` | Frontend types/ |
| `ConceptNodeType` | `DSLConceptNodeType` | Frontend |
| `AttributeNodeType` | `DSLAttributeNodeType` | Frontend |
| `RelationNodeType` | `DSLRelationNodeType` | Frontend |

## Nouveaux modèles

### Ontologie (backend) — OPEN WORLD
- `OntologyGraph extends AbstractGraph` — conteneur ontologie (pas de parent DSL)
  - `allowed_node_types` → libres, pas de contrainte M2
- `OntologyNode` — nœud ontologique (type libre, pas d'instance de DSLConcept)
  - `type` → chaîne libre (ex: "Personne", "Lieu", "Événement")
- `OntologyEdge` — lien ontologique libre
- `OntologyRepository`, `OntologyService`, `OntologyController`
- Routes: `/api/ontology`

### Architecture (backend) — CLOSED WORLD
- `ArchitectureGraph extends DSLGraph` — conteneur architecture
  - `parent_dsl_id` — référence le DSL qui contraint ses types
  - `allowed_node_types` → DSLConcept du parent (lecture seule)
- `ArchitectureNode` — composant d'architecture (instance de DSLConcept)
  - `dsl_concept_id` — référence le DSLConcept qui est son type
  - `properties` — valeurs pour les DSLAttribute du concept
- `ArchitectureEdge` — dépendance d'architecture (instance de DSLEdge)
- `ArchitectureRepository`, `ArchitectureService`, `ArchitectureController`
- Routes: `/api/architecture`

### Frontend
- `OntologyGraphViewer extends DSLGraphViewer` — rend un graphe d'ontologie
  - Nodes colorés par DSLConcept
  - Palette de types = DSLConcept du parent
- `ArchitectureGraphViewer extends DSLGraphViewer` — rend un graphe d'architecture
  - Nodes avec icône par type (composant, service, interface...)
  - Palette de types = DSLConcept du parent
- Intégration dans les sous-onglets Projet (Ontologie, Architecture)

## Phases

### Phase 1 — Nettoyage backend: Abstract → DSL
- Renommer `models/graph/` en `models/abstract/` ou garder le namespace
- Renommer Metamodel → DSL, Concept → DSLConcept, etc.
- Déplacer en `models/dsl/`, `repositories/dsl/`, `services/dsl/`, `controllers/dsl/`
- Mettre à jour `main.py`, `__init__.py`
- Mettre à jour les routes `/api/metamodels` → `/api/dsls`
- Mettre à jour les tests backend

### Phase 2 — Nettoyage frontend: Abstract → DSL
- Renommer GraphViewer → AbstractGraphViewer
- Renommer NodeType → AbstractNodeType
- Renommer ConceptNodeType → DSLConceptNodeType, etc.
- Renommer Metamodel type → DSL type
- Mettre à jour les pages, composants, navigation
- Mettre à jour les tests frontend

### Phase 3 — Création Ontologie (backend)
- Créer `models/ontology/OntologyGraph`, `OntologyNode`, `OntologyEdge`
- Créer `repositories/ontology/`, `services/ontology/`, `controllers/ontology/`
- Routes: `/api/ontology/*`
- Tests backend

### Phase 4 — Création Architecture (backend)
- Créer `models/architecture/ArchitectureGraph`, `ArchitectureNode`, `ArchitectureEdge`
- Créer `repositories/architecture/`, `services/architecture/`, `controllers/architecture/`
- Routes: `/api/architecture/*`
- Tests backend

### Phase 5 — Intégration frontend Ontologie + Architecture
- Créer `OntologyGraphViewer`, `OntologyNodeType`, `OntologyEdgeType`
- Créer `ArchitectureGraphViewer`, `ArchitectureNodeType`, `ArchitectureEdgeType`
- Intégrer dans les sous-onglets Projet (Ontologie, Architecture)
- Tests frontend + e2e

## Conversation

### user

On doit restructurer toute l'architecture graphe. La hiérarchie cible est :

```
Abstract (Graph, Node, Edge)
  └── DSL (Graph, Node, Edge)
       ├── Ontologie (Graph, Node, Edge)
       └── Architecture (Graph, Node, Edge)
```

Côté back comme côté front. Il faut :
1. Renommer l'existant (Metamodel → DSL)
2. Créer les couches Ontologie et Architecture
3. Intégrer dans les projets

### agent

J'ai créé le ticket maître MVP-H avec la structure cible complète, les renommages, et 5 phases d'exécution. Chaque phase a ses sous-tickets associés.

La stratégie :
- **Phases 1-2** : Refactor/rename de l'existant (Metamodel → DSL) — le plus gros du travail
- **Phases 3-4** : Création des nouvelles couches (Ontologie, Architecture) — relativement simple une fois la base DSL clean
- **Phase 5** : Intégration frontend dans les projets

Souhaites-tu qu'on attaque la **Phase 1** (backend : renommage Metamodel → DSL) ou tu veux d'abord valider/ajuster le plan ?
