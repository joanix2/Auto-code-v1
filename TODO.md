✅ refaire le backend propre avec des seulement objet, user, repo et tickets et des services, supprime le reste

✅ connexion

✅ liste des repo

✅ app bar commune

✅ page profile
✅ configuration du token github
✅ configuration du auth2 github
✅ tri par dernière date de modification

✅ recherche de repo par nom (distance de levenstein) avec une bar de recherche et le bouton plus à coté

✅ style boutton nouveau repo

✅ création d'un nouveau repo

✅ créer une nouvelle page qui affiche la liste des tikets lié à un repo liste des tickets par projet,
elle va beaucoup ressembler à la liste des repo, tu peut donc copier le code dans un premier temps puis créer une classe abstraite

✅ page avec des tickets de création,

✅ page edition

✅ suppression de tickets (refaire la modale)

✅ drag and drop pour l'ordre des tickets

✅ bar pour filter l'état des tickets (si on veux que les TODO par exemple)

✅ système headless de développement automatique avec Claude AI

✅ connexion à copilote git hub (évalué : Copilot Extensions nécessite interaction IDE, incompatible avec headless automation. Claude API gardé comme solution optimale.)

✅ ajout des tickets dans un projet github

✅ bug avec l'edition des status (option pending_validation manquante dans le select d'édition)

✅ garder un seul bouton "developer" mappé avec OpenCode (simplifié : un seul bouton vert "Développer automatiquement")

✅ créer un agent Claude Opus 4 avec LangGraph dans backend/src/agent/

- Structure complète du module agent
- ClaudeAgent avec workflow (analyze → generate → review)
- 3 types de workflows : standard, iterative, TDD
- API endpoint /api/agent/develop-ticket
- Documentation complète (README + QUICKSTART)
- Dépendances ajoutées : anthropic, langgraph, langchain

✅ ajout d'un objet Message pour conversation avec LLM

- Modèle Message avec role, content, step, tokens_used
- MessageRepository avec CRUD et méthodes spécialisées
- MessageController avec endpoints REST complets
- Relation HAS_MESSAGE entre Ticket et Message dans Neo4j
- Intégration dans ClaudeAgent (sauvegarde auto des messages)

✅ implémentation du workflow complet de traitement automatique (WORKFLOW.md)

- GitService : clone, pull, branches, rebase, commit, push
- CIService : pytest, npm test, make test, GitHub Actions
- TicketProcessingService : workflow principal itératif
- Gestion MAX_ITERATIONS avec création auto de bug tickets
- Boucle LLM → Code → Commit → CI → Validation
- API endpoints : /start, /validation, /status
- Ticket.iteration_count ajouté
- Flowchart Mermaid (flow.mmd)

✅ créer un digramme de flux (flow.mmd + diagramme dans WORKFLOW.md)

✅ système WebSocket pour traitement asynchrone temps réel

- ConnectionManager pour gérer les connexions WebSocket
- Endpoints WebSocket : /ws/tickets/{ticket_id} et /ws/tickets
- Background tasks pour traitement asynchrone
- Status updates en temps réel (progress 0-100%, step, logs)
- Hook React useTicketProcessing
- Composant TicketProcessingStatus avec barre de progression
- Documentation complète (WEBSOCKET_SYSTEM.md)

✅ mettre le ticket en pending (immédiatement au clic, workflow en arrière-plan)

✅ clone / pull les repo dans un workspace (structure owner/repo)

✅ gestion des branches (créer la branche / aller sur la branche)

✅ créer un agent avec langgraph (agent Claude Opus 4 créé avec 3 workflows)

✅ créer un message à partir du ticket / récupérer le dernier message

- Implémenté dans ticket_workflow.py → \_load_conversation()
- Création auto du message initial si aucun message existant
- Récupération du dernier message : state.last_message = messages[-1]
- Persistance dans Neo4j via MessageRepository

✅ reasoning, création d'un plan

- Implémenté dans ClaudeAgent → analyze_ticket()
- Analyse approfondie du ticket
- Décomposition en étapes concrètes
- Identification des fichiers à modifier
- Plan d'implémentation détaillé
- Génération de code via generate_code()
- Review via review_code()

✅ modification des fichiers

- ClaudeAgent génère le code (JSON avec path, action, content)
- FileModificationService créé avec LangChain tools
- Utilise WriteFileTool, ReadFileTool, CopyFileTool de langchain-community
- Parse JSON du LLM et applique les modifications
- Crée backups automatiques des fichiers modifiés
- Sécurité: sanitize des paths (pas de directory traversal)
- Intégré dans ticket_workflow.py → \_call_llm()
- WebSocket logs pour chaque fichier modifié

✅ commit

- Implémenté dans ticket_workflow.py → \_commit_changes()
- Vérifie si changements non commités
- Commit avec message formaté : "feat(ticket-XXX): Title"
- Inclut numéro d'itération
- Retourne commit_hash

récupérer la sortie de la CI -> nouveau message

créer un nouveau ticket de bug si limite atteinte

merge de la branche

modifier le logo et index.html

relier les tickets à un projet github

ajout d'un queue rabbit mq pour multi utilisateur

# Options

utilisation de spec kit

review des tickets par LLMs

chatbot pour créer des tickets

# Future

avoir des templates de projets avec un formulaire

IaC et CI/CD pour depoiment automatique

DAG de ticker

ajout des KG

ajout des ontologies

règles sur le graphe

# DevOps

## Docker

```
  # Nginx Proxy Manager
  nginx-proxy-manager:
    image: "jc21/nginx-proxy-manager:latest"
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      - "80:80" # HTTP
      - "443:443" # HTTPS
      - "81:81" # Interface admin NPM
    volumes:
      - npm-data:/data
      - npm-letsencrypt:/etc/letsencrypt
    networks:
      - npm-network
    environment:
      DB_SQLITE_FILE: "/data/database.sqlite"
```

## IaC

application_urls = {
"backend" = "http://13.37.9.94:8000"
"frontend" = "http://13.37.9.94:3000"
"neo4j" = "http://13.37.9.94:7474"
"npm_admin" = "http://13.37.9.94:81"
}
instance_id = "i-067522f2398c0f746"
public_dns = "ec2-13-36-176-35.eu-west-3.compute.amazonaws.com"
public_ip = "13.37.9.94"
ssh_connection = "ssh -i ~/.ssh/aws_key.pem ubuntu@13.37.9.94"
