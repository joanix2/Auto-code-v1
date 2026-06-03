---
title: Plan de Migration — Roadmap Générateur Déclaratif
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
description: Plan de migration en 6 MVP pour implémenter les 17 phases de la roadmap
---

## Plan de Migration

### Résumé

Migration du projet Auto-Code-v1 actuel vers l'architecture "Générateur Déclaratif par Graphe" décrite dans la roadmap. Le projet existant couvre déjà les phases 1-3 (IR JSON, Backend FastAPI, Frontend React). Il faut implémenter les phases 4-17.

### MVP A — Consolidation (Phases 1-3)

**Objectif** : Aligner l'existant avec la roadmap.

- [ ] Auditer les modèles existants vs le format IR cible (`graph.json` avec nodes/edges/kinds)
- [ ] Ajouter le support du format IR JSON natif (`/graph/load`, `/graph/save`)
- [ ] Définir et valider un JSON schema formel pour l'IR
- [ ] Garantir l'indépendance de l'IR vis-à-vis du frontend/backend
- [ ] Ajouter les endpoints manquants de l'API REST MVP
- [ ] Tests de roundtrip (load → modify → save → load)

### MVP B — Système de Requêtes (Phase 4)

**Objectif** : Interroger le graphe comme une base de connaissances.

- [ ] Implémenter les sélecteurs : get_nodes_by_kind, get_edges_by_kind, get_neighbors
- [ ] Implémenter get_entity_tree(root_id) → arbre JSON récursif
- [ ] Gérer les cycles dans l'extraction d'arbre (profondeur max)
- [ ] Exposer les requêtes via des endpoints API REST
- [ ] Tester les cas limites : graphe vide, nœud inexistant, profondeur max

### MVP C — Templates et Génération (Phases 5-6)

**Objectif** : Générer du code à partir du graphe via templates et plans d'exécution.

- [ ] Implémenter TemplateRegistry (enregistrement, chargement, listing)
- [ ] Implémenter TemplateRenderer (Jinja2, contexte, filtres)
- [ ] Créer des templates d'exemple : Python (Pydantic, FastAPI), TypeScript/React
- [ ] Associer un template à un type de nœud via l'IR
- [ ] Définir le format du plan de génération (GenerationPlan, GenerationStep)
- [ ] Implémenter le tri topologique avec détection de cycles
- [ ] Développer l'exécuteur de plan (séquentiel/parallèle, hooks)
- [ ] Gérer les erreurs par étape (skip, abort, retry)
- [ ] Créer des plans d'exemple pour des cas d'usage typiques

### MVP D — Validation et Réécriture (Phases 7-8)

**Objectif** : Valider et transformer le graphe automatiquement.

- [ ] Implémenter les validateurs structurels (IDs uniques, références, champs requis)
- [ ] Développer les règles métier (cardinalités, cycles interdits)
- [ ] Intégrer Z3 pour les contraintes complexes
- [ ] Produire des rapports d'erreur structurés
- [ ] Définir le format des règles de réécriture (condition + action)
- [ ] Implémenter le moteur de pattern matching dans le graphe
- [ ] Implémenter le moteur d'application (simple, chaîné, point fixe)
- [ ] Assurer la traçabilité des transformations
- [ ] Créer des règles de réécriture par défaut

### MVP E — Héritage et Composition (Phases 9-10)

**Objectif** : Graphes parent/enfant, héritage multiple, composition.

- [ ] Définir un graphe comme parent d'un autre (attribut `parent_id`)
- [ ] Hériter automatiquement des entités, relations et règles du parent
- [ ] Autoriser la surcharge d'éléments hérités
- [ ] Supporter l'héritage multiple entre graphes
- [ ] Visualiser l'origine d'un élément (local ou hérité)
- [ ] Définir des règles de résolution de conflits
- [ ] Créer des bibliothèques de graphes réutilisables

### MVP F — Ontologie et Inférence (Phases 11-12)

**Objectif** : Couche ontologique Open World et moteur d'inférence.

- [ ] Définir les modèles ontologiques (Concept, Property, SemanticRelation, Taxonomy)
- [ ] Implémenter le stockage et le chargement de l'ontologie
- [ ] Permettre les connaissances incomplètes ou hypothétiques
- [ ] Définir le format des règles d'inférence
- [ ] Implémenter le moteur d'inférence
- [ ] Distinguer faits déclarés vs inférés (score/justification)
- [ ] Implémenter la compilation Ontologie → IR (Open World → Closed World)
- [ ] Éliminer les ambiguïtés incompatibles avec l'IR
- [ ] Tester le pipeline complet : tickets → NER → triplets → ontologie → IR

### MVP G — Pipeline Agents LLM (Phases 13-17)

**Objectif** : Intégrer les agents LLM dans le pipeline de génération.

- [ ] Implémenter l'agent Product Owner (prompt → tickets structurés)
- [ ] Implémenter l'agent NER (tickets → triplets)
- [ ] Implémenter l'agent Ontologue (triplets → ontologie)
- [ ] Implémenter l'agent Graph Engineer (ontologie → IR)
- [ ] Implémenter l'agent Template Engineer (création/modification templates)
- [ ] Implémenter l'agent Validator (analyse erreurs + corrections)
- [ ] Implémenter l'agent Rewrite Engineer (proposition règles)
- [ ] Implémenter l'agent Codegen Planner (plan d'exécution)
- [ ] Implémenter l'agent Git Integrator (patchs, commits, branches)
- [ ] Implémenter l'agent Reviewer (vérification architecture)
- [ ] Implémenter le Patch AST entre versions de programmes (Phase 16)
- [ ] Orchestrateur d'agents (séquencement, files d'attente, reprise)
- [ ] Dashboard de suivi des pipelines d'agents
