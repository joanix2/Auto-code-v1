# Architecture Decision Records (ADR)

Ce dossier contient les décisions d'architecture du projet **Générateur Déclaratif par Graphe**.

## Format

Chaque ADR suit le format MADR (Markdown Architectural Decision Records) :

```markdown
# Titre

- **Date** : YYYY-MM-DD
- **Statut** : [Proposé | Accepté | Déprécié | Remplacé]
- **Décideurs** : (optionnel)

## Contexte

## Décision

## Conséquences
```

## Numérotation

Les ADR sont numérotés séquentiellement : `ADR-NNN-titre-kebab-case.md`.

- `NNN` : numéro à 3 chiffres (001, 002, …)
- Le titre est en kebab-case, anglais de préférence

## Statuts

| Statut | Signification |
|--------|--------------|
| **Proposé** | Proposition en cours de discussion |
| **Accepté** | Décision validée et appliquée |
| **Déprécié** | Plus valide mais conservé pour historique |
| **Remplacé** | Remplacé par un autre ADR (le lien est précisé) |

## Règles

1. Une décision structurante = un ADR
2. Ne pas créer d'ADR pour des détails d'implémentation triviaux
3. Si un ADR est remplacé, le nouveau mentionne l'ancien et vice-versa
4. Les ADR acceptés ne sont pas modifiés ; on crée un nouvel ADR si le contexte change
