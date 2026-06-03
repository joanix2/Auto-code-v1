# ADR-002 : Utiliser NetworkX comme moteur graphe backend

- **Date** : 2026-06-03
- **Statut** : Accepté

## Contexte

Le coeur du projet est un graphe orienté typé (noeuds = entités, arêtes = relations). Il doit
supporter :
- Des mutations fréquentes (ajout/suppression de noeuds et arêtes)
- Des algorithmes de parcours (topologique, descendants, ascendants)
- De l'inférence de clôture transitive
- La sérialisation vers/depuis le JSON de l'IR

Plusieurs solutions existent : Neo4j, ArangoDB, NetworkX, iGraph, graphe fait main.

## Décision

Utiliser **NetworkX** comme backend graphe en mémoire, sans base de données graphe dédiée
dans un premier temps.

Architecture :
- Un `GraphBuilder` construit le graphe NetworkX à partir du JSON IR
- Un `GraphAdapter` expose les mutations (add/update/delete noeuds et arêtes)
- La sérialisation se fait via le format JSON natif de NetworkX, transformé en IR Pydantic

Le module `semantic_graph/graph/` contient toute la logique d'adaptation.

## Conséquences

- **Positives**
  - Léger (pas de serveur, pas de dépendance lourde)
  - Algorithmes intégrés (DFS, BFS, Dijkstra, tri topologique, composantes connexes)
  - Facile à tester en mémoire sans infrastructure
  - Migration simple vers une base dédiée si nécessaire (l'IR JSON reste l'interface)

- **Négatives**
  - Pas de persistence native (sauvegarde manuelle vers JSON)
  - Pas de requêtes déclaratives (Cypher, SPARQL)
  - Performance limitée pour des graphes très volumineux (>1M noeuds)
  - Pas de concurrence d'accès (mono-process)

- **Risques**
  - Le choix NetworkX devient un goulet d'étranglement → mitigé par l'isolation derrière
    l'interface `GraphAdapter`, remplaçable par iGraph ou autre
  - On réimplémente des fonctionnalités de base de données → mitigé : le cas d'usage est
    un graphe de taille modérée (< 50k noeuds) pour un projet de génération déclarative
