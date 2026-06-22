---
description: "Se déclenche quand architecture_diagram.md ou un fichier source de l'architecture core est modifié. Vérifie que le diagramme Mermaid reste synchronisé avec le code."
---

# Diagram Consistency Skill

Ce skill se charge **automatiquement** quand tu édites :

- `architecture_diagram.md` — le diagramme Mermaid
- `src/models/language/` — LangGraph, LangNode, LangEdge, NodeKind, EdgeKind
- `src/services/language_manager.py` — Language, LanguageManager
- `src/models/program/` — Program
- `src/services/validation/validation_report.py` — ValidationReport
- `src/services/templates/template_registry.py` — Template
- `src/services/rewrite/rewrite_rule.py` — RewriteRule

## Que fait-il

1. **Lit** `architecture_diagram.md` et les fichiers source concernés
2. **Compare** classes, attributs, relations, enum du diagramme avec le code
3. **Propose** les mises à jour si un écart est détecté
4. **Signale** les classes du code qui ne sont pas encore dans le diagramme

## Commande manuelle

Tu peux aussi l'invoquer explicitement :

```
@arch-diagram Synchronise le diagramme avec le code
```

Le hook pre-commit (`.githooks/pre-commit`) fait une vérification rapide
automatiquement avant chaque commit. Ce skill fait une analyse plus
approfondie et propose des corrections.
