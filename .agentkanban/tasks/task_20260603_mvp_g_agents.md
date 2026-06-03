---
title: MVP G — Pipeline Agents LLM
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
priority: P4
description: Intégration des agents LLM dans le pipeline et Patch AST (Phases 13-17)
---

## Description

Pipeline complet piloté par agents LLM : prompt → tickets → NER → triplets → ontologie → IR → templates → code → patch → commit. Orchestrateur et dashboard de suivi.

## Sous-tâches

- [ ] Agent Product Owner : prompt utilisateur → tickets structurés + critères acceptation
- [ ] Agent NER : tickets → triplets (entités, relations) avec score de confiance
- [ ] Agent Ontologue : triplets → ontologie enrichie
- [ ] Agent Graph Engineer : ontologie → IR graphe (compilation Open World → Closed World)
- [ ] Agent Template Engineer : création/modification de templates depuis l'IR
- [ ] Agent Validator : analyse des erreurs de validation + corrections proposées
- [ ] Agent Rewrite Engineer : proposition de règles de réécriture
- [ ] Agent Codegen Planner : construction du plan d'exécution de génération
- [ ] Agent Git Integrator : patchs AST, commits, branches, PR
- [ ] Agent Reviewer : vérification que les transformations respectent l'architecture
- [ ] Implémenter le Patch AST (comparaison de versions de graphe/code, diff structurel)
- [ ] Orchestrateur d'agents (séquencement, files d'attente, reprise sur erreur)
- [ ] Dashboard de suivi des pipelines d'agents
