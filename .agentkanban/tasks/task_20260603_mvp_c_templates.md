---
title: MVP C — Templates et Génération
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
priority: P3
description: Système de templates Jinja2 et plans de génération (Phases 5-6)
---

## Description

Pipeline complet : Graphe → Requête (arbre JSON) → Template → Fichier généré. Ajout du métaprogramme de génération avec plan DAG et exécuteur.

## Sous-tâches

- [ ] Implémenter TemplateRegistry (enregistrement, chargement depuis dossier, listing)
- [ ] Implémenter TemplateRenderer (Jinja2, contexte enrichi, filtres personnalisés)
- [ ] Créer des templates d'exemple : Python (Pydantic, FastAPI), SQL, TypeScript/React
- [ ] Associer un template à un type de nœud via l'IR
- [ ] Permettre la génération multi-fichiers depuis une même entité
- [ ] Définir le format du plan de génération (GenerationPlan, GenerationStep)
- [ ] Implémenter le tri topologique avec détection de cycles
- [ ] Développer l'exécuteur de plan (séquentiel/parallèle, hooks before/after/error)
- [ ] Gérer les erreurs par étape (skip, abort, retry avec politique configurable)
- [ ] Créer des plans d'exemple pour des cas d'usage typiques
