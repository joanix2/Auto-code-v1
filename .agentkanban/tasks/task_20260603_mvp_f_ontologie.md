---
title: MVP F — Ontologie et Inférence
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
description: Couche ontologique Open World, règles d'inférence, compilation vers l'IR (Phases 11-12, 15)
---

## Description

Couche ontologique indépendante de l'IR. Logique Open World (l'absence d'info ≠ info fausse). Moteur d'inférence. Compilation Ontologie → IR (Open World → Closed World).

## Sous-tâches

- [ ] Définir les modèles ontologiques (Concept, Property, SemanticRelation, Taxonomy)
- [ ] Implémenter le stockage et le chargement de l'ontologie (JSON)
- [ ] Permettre les connaissances incomplètes ou hypothétiques
- [ ] Définir des taxonomies, équivalences et spécialisations
- [ ] Définir le format des règles d'inférence (condition + conclusion + score)
- [ ] Implémenter le moteur d'inférence
- [ ] Distinguer faits déclarés vs faits inférés (score/justification)
- [ ] Implémenter la compilation Ontologie → IR (transformer concepts en nœuds, relations en arêtes)
- [ ] Éliminer les ambiguïtés incompatibles avec l'IR (hypothèses non validées restent dans l'ontologie)
- [ ] Tester le pipeline complet : tickets → NER → triplets → ontologie → IR
