---
title: MVP D — Validation et Réécriture
lane: todo
created: 2026-06-03T21:30:00+02:00
updated: 2026-06-03T21:30:00+02:00
description: Validation de contraintes et moteur de réécriture du graphe (Phases 7-8)
---

## Description

Deux moteurs complémentaires : validation (structurelle, métier, Z3) et réécriture (pattern matching, transformation, point fixe). Garantit la cohérence du graphe.

## Sous-tâches

- [ ] Implémenter les validateurs structurels (IDs uniques, références valides, kinds déclarés)
- [ ] Développer les règles métier (cardinalités, cycles interdits, règles de domaine)
- [ ] Intégrer Z3 pour les contraintes complexes (résolution de conflits, satisfaction)
- [ ] Produire des rapports d'erreur structurés (code, message, sévérité, emplacement)
- [ ] Suggérer des corrections automatiques pour chaque erreur
- [ ] Définir le format des règles de réécriture (RewriteRule : condition + action)
- [ ] Implémenter le moteur de pattern matching dans le graphe
- [ ] Implémenter l'application des règles (simple, chaîné, point fixe)
- [ ] Assurer la traçabilité : chaque transformation enregistrée avec justification
- [ ] Créer des règles de réécriture par défaut (normalisation, inférence)
