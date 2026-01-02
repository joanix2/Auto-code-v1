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

créer un digramme de flux

mettre le ticket en pending

clone / pull les repo dans un workspace

gestion des branches (créer la branche / aller sur la branche)

✅ créer un agent avec langgraph (agent Claude Opus 4 créé avec 3 workflows)

créer un message à partir du ticket / récupérer le dernier message

resoning, création d'un plan

modification des fichers

commit

récupérer la sortie de la CI -> nouveau message

créer un nouveau ticket de bug si limite atteinte

merge de la branche

modifier le logo et index.html

relier les tickets à un projet github

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
