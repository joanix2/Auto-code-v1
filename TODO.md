✅ repos dans l'ordre des plus récent
✅ delete RABBITMQ
✅ bug à la connexion (deux chargement)
✅ bug de redirection à la supression d'un repo

✅ a coté du bouton de supression dans la card d'un repo on veut un bouton pour editer le repos qui nous redirige vers la page detail en mode édition (je veux pouvoir modifier le nom et la description et que ca se synchronise avec github, ne modifie pas la base neo4j avant d'avoir modifier le repo et pense à utiliser les services dédier)

✅ afficher la date de création et celle du dernier commit dans la card

✅ liste des issues

✅ ajouter supprimer et modifier en haut à gauche
✅ popup de suppression
✅ créer une issus
✅ corriger la card des issues
✅ corriger l'édition
✅ supprimer une issue

✅ syncro des issues

✅ bouton pour lancer la codage automatique d'une issue

✅ afficher le nom du repo en haut de la liste des issues

✅ filtrer les issues en fonction du status

✅ classe abstraite de la page détail

✅ corriger le style de la popup de dev auto + enlever l'alerte

✅ afficher le profile

✅ numéro de l'issue

✅ créer un drawer

helper pour la gestion des erreur dans le controller

bug fix : les ticket en attente de validation passent en open (même chose pour en cours)

✅ suppression de l'onglet home (gadre juste les repos et home)

plus de relations en base

les controller doivent avoir un double héritage, sychro github et base controller

deployement et url

# Infra

deployer sur un vps cloud : https://www.hetzner.com/cloud/

ajout d'une CI

build les images sur un registery avec tag de la branch

créer des sous domaine dev, test, prod

deployer l'image d'une branche

# Messages

liste des messages de la pr (utilisation automatique de @copilote)

ajouter un message à la pr

modifier les messages ??

injection des erreurs de la CI dans le chat

# Améliroration de la logique métier

ecriture automatique du code de teste

review des issues via IA (reformulation du ticker)

merge automatique

DAG de ticker: ajouter des dépendances entre les tickets (savoir quels sont les prochains les quels peuvent être parallèliser)

# Partie Scaffolding MDE

**Objectif** : instancier un template avec une API, un front, une infra, une CI, une doc spec kit

✅ créer un composant générique capable d'afficher des graphe avec d3.js garde en tête que nous somme en mobile first

✅ créer la page detail d'un metamodel qui affiche le meta model avec ce composant

✅ on veux pouvoir visualiser les noeuds et les arrêtes sous la forme d'un graphe orienté avec de la physique entre les noeuds

✅ créer les classes :

- metamodel.py
- attribute.py
- concept.py
- relationship.py

✅ créer les controllers

✅ ajouter un champ pour le type du noeud

✅ modifier un noeud (fix refresh)

✅ supprimer un noeud

✅ supprimer concept source / concept cible (remplacé par système de liens génériques)

✅ ajouter les type de lien possible entre les noeuds (ex: domain [Relation -> Concept], range [Relation -> Concept])

✅ metamodel controller renvoie les liens possibles avec les contraintes

✅ c'est interprété par graphe view

✅ bouton pour passer en mode création de lien

✅ créer un lien entre deux noeuds en cliquant sur un noeud source puis un noeud cible

✅ popup pour choisir le type du lien avec plusieurs options disponibles

🔄 Plus necessaire dans la graphe view
INFO: 127.0.0.1:59484 - "GET /api/metamodels/98047745-c4e0-40a0-8541-93ce2415d7f7 HTTP/1.1" 200 OK

🔄 récupérer les propriétés d'une node
🔄 À faire : Créer les edges DOMAIN/RANGE via le système click-to-click
🔄 À faire : Implémenter la persistance en base des edges créés via GraphViewer

ajouter la possiblité de calculé le nom

créer l'interface de création de meta-model

- model.py
- individual.py
- templates.py

on veux pour selectionner un type de noeud et créer des noeuds de se type
on veux pouvoir supprimer les noeuds

on veux pouvoir afficher les propriété du noeud dans le panneau latéral
on veux pouvoir créer des propriétés
modifier des propriétés
supprimer des propriétés

on veux pouvoir selectionner un type de relation et créer des relation entres les noeuds
on veux pouvoir supprimer des relation entre les noeuds

créer des converstion avec un ensemble de message chainer les un aux autres

On veux pouvoir poser des question à un LLM dans une bar de chat et qu'il nous réponde en fonction des information contenu dans le graphe

on veux pouvoir définir le prompte systhème de l'agent

on veut donner des tools à l'agent, il est capble de géréer des noeuds, des propriétés et des relations en prennant en compte les types de noeuds et les types de relations

versionner le graphe

créer des contraintes sur le graphe
-> ontologique
-> SMT
-> bi-simulation
-> flot

créer des metamodel

créer des templates

faire du scaffolding

# Future

ajout des KG

ajout des ontologies

règles sur le graphe

ajouter la commande vocal

liée des fichiers tickets

liée des images tickets

workflow multi agent

gestion des tags liée aux tickets

utilisation de spec kit

chatbot pour créer des tickets

# Gestion de projet

Liste des projets liées à github

kanban

graphe de dépendance entre les tâches

Gatt

estimation de temps

cf docs/GESTION-DE-PROJET-STEPPER.md

# Analyse du besoin

avatar client

liste des besoins

liste des solutions techniques

graphe de relation entre

CRM (liste des client lié à leur avatar)

# Marketing

Analyse des tendances
Tunnel d’acquisition
Techniques de storytelling
Stratégie de contenu
Social Media Management
SEO
Pilotage via KPIs
Gestion des publicités Google
Gestion des publicités Facebook
Email marketing
CRM et relation client
Construction de personas
Branding et positionnement
Analyse SWOT
Analyse PESTEL
Analyse du besoin

# Génération de videos

créer le script

créer un story bord

créer générer les audio

créer la video

valider et modifier la video

uploader la video
