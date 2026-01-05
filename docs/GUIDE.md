# Description du projet

Auto-Code est une plateforme de gestion de tickets avec développement automatique assisté par IA. Elle permet de créer, organiser et développer automatiquement des tickets de développement en utilisant OpenCode AI dans un environnement Docker isolé.

# Pipeline

## Résolution d'un ticket

- **Ticket = Conversation = Branche Git**
- Les tickets sont créés et modifiés via la PWA, stockés dans Neo4j.
- Un ticket exécutable est sélectionné automatiquement (priorité + dépendances OK).
- Une branche Git et une session OpenCode sont créées.

### Boucle d’exécution

1. Message → analyse (reasoning)
2. Modification du code
3. Commit → CI/CD

- Si la CI échoue, l’erreur est ajoutée comme **message dans la conversation**.
- Le cycle recommence.

#### Limite

- Maximum **20 itérations**.
- Au-delà, l’agent s’arrête et **crée un nouveau ticket de bug** expliquant le blocage.

#### Fin

- CI OK → ticket `DONE`, branche prête à merger.

# Architecture

```mermaid
flowchart TD
%% Nodes
subgraph Frontend
A[React PWA]
end

subgraph Backend
B[API Python]
C[Neo4j Database]
end

subgraph AI_Agent
D[OpenCode Microservice]
end

subgraph GitHub
G[GitHub API]
end

%% Flows
A -- "HTTP requests (tickets, status)" --> B
B -- "CRUD tickets, deps" --> C

B -- "Trigger execution\n(create job)" --> D
D -- "AI analysis & code actions" --> C

D -- "Push commits / PR" --> G
B -- "Read/Write issues & PR metadata" --> G

G -- "Issue & PR status" --> B
A -- "View ticket & job results" --> B
```

# Diagramme de flux

```mermaid
flowchart TD
    A[Démarrage] --> B{Limite itérations atteinte ?}

    B -- Oui --> C[Ticket passe à ANNULE]
    C --> D[Créer ticket de bug]
    D --> Z[Fin]

    B -- Non --> E[Ticket passe à PENDING]

    E --> F{Repo déjà cloné ?}
    F -- Non --> G[Cloner le repo]
    F -- Oui --> H[Pull le repo]

    G --> H

    H --> I{Branche du ticket existe ?}
    I -- Non --> J[Créer la branche]
    I -- Oui --> K[Checkout branche]

    J --> L[Rebase branche]
    K --> L

    L --> M[Récupérer la conversation]

    M --> N{Dernier message existe ?}
    N -- Non --> O[Créer message depuis le ticket]
    N -- Oui --> P[Récupérer dernier message]

    O --> Q[Reasoning LLM]
    P --> Q

    Q --> R[Modification du code]
    R --> S[Commit]
    S --> T[Lancer CI]

    T --> U{CI en erreur ?}
    U -- Oui --> V[Ajouter erreur comme message]
    V --> B

    U -- Non --> W[Ticket passe à VALIDATION]
    W --> X[Validation humaine]

    X -- Rejeté --> Y[Écrire message de rejet]
    Y --> AA[Ticket repasse à TODO]
    AA --> Z[Fin]

    X -- Validé --> AB[Créer Pull Request]
    AB --> AC[Ticket DONE]
    AC --> Z[Fin]
```

# Lancer la base neo4j

# Setup l'env python

# Paramètres pour créer une app GitHub et connexion en auth 2

# Lancer le serveur

# Lancer le front

# Doc open code

https://opencode.ai/docs/server/

# Screenshots de l'app

# Update mermaid

```bash
docker run --rm -u $(id -u):$(id -g) -v $(pwd):/data minlag/mermaid-cli -i flow.mmd -o flow.png
```
