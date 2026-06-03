# Méthodologie du Stepper - Création de Projet

Ce document détaille les 8 étapes du processus de création de projet, basé sur les principes SMART, la méthode agile et les bonnes pratiques de gestion de projet.

---

## 📋 Vue d'ensemble des étapes

1. **Objectifs SMART** - Définir des objectifs précis et mesurables
2. **Persona** - Identifier l'utilisateur cible
3. **Problématique** - Définir le problème à résoudre
4. **Besoins** - Lister les besoins et anti-besoins
5. **Analyse CQQCOQP** - Analyser le contexte d'utilisation
6. **User Stories** - Définir les récits utilisateurs
7. **Priorisation MoSCoW** - Prioriser les fonctionnalités
8. **Architecture Fonctionnelle** - Structurer les modules

---

## Étape 1 : 🧩 Objectifs (SMART / OKR)

**Objectif** : Définir un objectif précis et mesurable selon la méthode SMART

### Questions

#### 1. Quel est l'objectif principal ? (1 phrase) \*

- **Type** : Textarea
- **Requis** : Oui
- **Placeholder** : Décrivez votre objectif principal en une phrase claire et concise
- **Exemple** :
  - ✅ **Bon** : "Augmenter de 20% la conversion mobile en 3 mois en simplifiant le checkout pour réduire l'abandon."
  - ❌ **Mauvais** : "Améliorer mon site."

#### 2. Comment mesurer que c'est réussi ? \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Augmentation de 20% du taux de conversion

#### 3. Dans quel délai ? \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: 3 mois, 6 semaines, fin Q2 2024

#### 4. Quelle valeur cela apporte-t-il ? \*

- **Type** : Textarea (2 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Réduction du temps de traitement, augmentation du chiffre d'affaires...

#### 5. Quels sont les critères de réussite ? (max 3) \*

- **Type** : 3 inputs text
- **Requis** : Au moins 1 critère
- **Placeholder** :
  - Critère 1 (requis)
  - Critère 2 (optionnel)
  - Critère 3 (optionnel)

---

## Étape 2 : 👤 Persona

**Objectif** : Définir qui est l'utilisateur cible et comprendre ses motivations

### Questions

#### 1. Quel est son métier / rôle ? \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Responsable RH, Chef de projet, Développeur...

#### 2. Quel est son objectif dans la vie de tous les jours ? \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Réduire le temps passé sur les tâches administratives

#### 3. Qu'est-ce qui le frustre le plus aujourd'hui ? \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Passer trop de temps sur des tâches répétitives

#### 4. Donne un exemple réel : "Il/Elle dit souvent : \_\_\_" \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Je perds mes journées dans Excel

### Exemple complet

✅ **Exemple** : "Marie, responsable RH, veut réduire le temps administratif. Elle dit souvent 'Je perds mes journées dans Excel.'"

---

## Étape 3 : ❗ Problem Statement

**Objectif** : Formuler le problème selon le format : Qui + Problème + Impact

### Questions

#### 1. Qui rencontre ce problème ? \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Les responsables RH des PME

#### 2. Quel est le problème exact ? \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Difficulté à gérer les congés des employés de manière efficace

#### 3. Quel en est l'impact chiffrable ou concret ? \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Perte de 2h par jour, 15% d'erreurs dans les plannings

#### 4. Comment fait-on aujourd'hui ? Qu'est-ce qui manque ? \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Utilisation d'Excel, manque d'automatisation et de validation

---

## Étape 4 : 🎯 Besoin (macro)

**Objectif** : Identifier les fonctions essentielles et les limites du système

### Questions

#### 1. Qu'est-ce que le service doit absolument permettre ? (max 3 points) \*

- **Type** : 3 inputs text
- **Requis** : Au moins 1 fonction
- **Placeholder** :
  - Fonction 1 (requis)
  - Fonction 2 (optionnel)
  - Fonction 3 (optionnel)
- **Exemple** :
  - ✅ **Besoin** : "Permettre aux employés de poser leurs congés facilement."

#### 2. Qu'est-ce qu'il ne doit **pas** faire ? (anti-besoins)

- **Type** : 2 inputs text
- **Requis** : Non
- **Placeholder** :
  - Anti-besoin 1 (optionnel)
  - Anti-besoin 2 (optionnel)
- **Aide** : Les anti-besoins aident à clarifier les limites du projet
- **Exemple** :
  - ❌ **Anti-besoin** : "Ne pas gérer la paie."

---

## Étape 5 : 🔍 Analyse CQQCOQP

**Objectif** : Analyser le contexte d'utilisation détaillé

### Questions

#### **Où** l'utilisateur utilise-t-il le produit ? \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Bureau, mobile, domicile

#### **Quand** ? (fréquence, moment crucial) \*

- **Type** : Input text
- **Requis** : Oui
- **Placeholder** : Ex: Quotidiennement, en fin de mois, lors des réunions

#### **Comment** ? (processus en 3 étapes max) \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Étape 1 → Étape 2 → Étape 3
- **Exemple** :
  - ✅ **Bon** : "Ouvre l'app → Scanne → Valide le reçu."

#### **Pourquoi** ? (motivation profonde) \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Gagner du temps, éviter les erreurs, améliorer la satisfaction

#### **Contraintes** ? (techniques, légales, temps) \*

- **Type** : Textarea (3 rows)
- **Requis** : Oui
- **Placeholder** : Ex: Conformité RGPD, budget limité, délai court

### Signification de CQQCOQP

- **C** - Combien (non utilisé dans ce formulaire)
- **Q** - Quoi (défini dans les étapes précédentes)
- **Q** - Qui (défini dans Persona)
- **C** - Comment
- **O** - Où
- **Q** - Quand
- **P** - Pourquoi

---

## Étape 6 : 🗂️ User Stories

**Objectif** : Définir les récits utilisateurs au format standard Agile

### Format

```
En tant que [rôle]
Je veux [action/fonctionnalité]
Afin de [bénéfice/objectif]
```

### Fonctionnalités

#### Génération automatique

- Les user stories sont **auto-générées** à partir des données précédentes :
  - Rôle : récupéré du **Persona**
  - Action : récupérée des **Besoins (fonctions cœur)**
  - Bénéfice : récupéré de l'**Objectif (valeur)**

#### Actions disponibles

- **Régénérer les user stories** : Bouton pour recréer les stories automatiquement
- **Valider une story** : Checkbox "Valide" pour marquer les stories correctes
- **Modifier une story** : Édition des 3 champs (En tant que, Je veux, Afin de)
- **Supprimer une story** : Bouton "Supprimer" sur chaque carte
- **Ajouter une story** : Bouton "+ Ajouter une user story"

### Structure des champs

Pour chaque user story :

#### En tant que

- **Type** : Input text
- **Placeholder** : Ex: responsable RH

#### Je veux

- **Type** : Input text
- **Placeholder** : Ex: pouvoir gérer les congés facilement

#### Afin de

- **Type** : Input text
- **Placeholder** : Ex: gagner du temps et réduire les erreurs

### Validation

- Au moins **1 user story valide** requise
- Les 3 champs doivent être remplis pour qu'une story soit considérée valide

---

## Étape 7 : 🧮 Priorisation (MoSCoW)

**Objectif** : Classer les fonctionnalités par ordre de priorité selon la méthode MoSCoW

### Méthode MoSCoW

#### Must Have (Max 5)

- Fonctionnalités **essentielles** sans lesquelles le produit ne peut pas exister
- **Limite** : Maximum 5 fonctionnalités

#### Should Have

- **Importantes** mais le produit peut fonctionner sans

#### Could Have

- **Souhaitables** mais pas prioritaires

#### Won't Have

- **Pas pour cette version**

### Structure pour chaque fonctionnalité

#### Priorité

- **Type** : Select dropdown
- **Requis** : Oui
- **Options** :
  - Must Have (Max 5)
  - Should Have
  - Could Have
  - Won't Have

#### Nom de la fonctionnalité

- **Type** : Input text
- **Requis** : Oui (au moins 1 fonctionnalité)
- **Placeholder** : Ex: Système de gestion des congés

#### Description

- **Type** : Textarea (2 rows)
- **Requis** : Non
- **Placeholder** : Décrivez brièvement cette fonctionnalité

### Validation

- Au moins **1 fonctionnalité** requise
- Au moins **1 fonctionnalité Must-Have** requise
- Maximum **5 fonctionnalités Must-Have**
- Warning affiché si plus de 5 Must-Have sélectionnés

### Actions disponibles

- **Ajouter une fonctionnalité** : Bouton "+ Ajouter une fonctionnalité"
- **Supprimer** : Bouton "Supprimer" sur chaque carte
- **Compteur** : Affichage "Must Have: X/5"

---

## Étape 8 : 🏗️ Architecture Fonctionnelle

**Objectif** : Définir les modules principaux de l'application

### Fonctionnalités

#### Génération automatique

- Les modules sont **auto-générés** à partir des **fonctionnalités Must-Have** de l'étape précédente
- Chaque fonctionnalité Must-Have devient un module

#### Actions disponibles

- **Régénérer l'architecture** : Bouton "🌟 Régénérer l'architecture"
- **Ajouter un module** : Bouton "+ Ajouter un module"
- **Supprimer un module** : Bouton "Supprimer" sur chaque carte

### Structure pour chaque module

#### Numéro du module

- Affiché automatiquement (Module 1, Module 2, etc.)

#### Nom du module

- **Type** : Input text
- **Requis** : Oui (au moins 1 module)
- **Placeholder** : Ex: Gestion des utilisateurs

#### Description

- **Type** : Textarea (3 rows)
- **Requis** : Non
- **Placeholder** : Décrivez les responsabilités de ce module

### Validation

- Au moins **1 module** avec un nom requis

---

## 🎯 Résumé Final

Après avoir complété les 8 étapes, l'utilisateur accède à un **résumé complet** du projet qui affiche toutes les données collectées organisées par sections.

### Export JSON

Un bouton permet d'**exporter le projet** au format JSON avec toutes les données structurées.

---

## 💡 Principes méthodologiques

### SMART

Les objectifs suivent le principe SMART :

- **S**pécifique
- **M**esurable
- **A**tteignable
- **R**éaliste
- **T**emporel

### MoSCoW

La priorisation suit la méthode MoSCoW :

- **M**ust have
- **S**hould have
- **C**ould have
- **W**on't have

### User Stories (Agile)

Format standard des récits utilisateurs :

```
En tant que [utilisateur]
Je veux [fonctionnalité]
Afin de [bénéfice]
```

### CQQCOQP

Analyse contextuelle complète :

- **C**ombien
- **Q**uoi
- **Q**ui
- **C**omment
- **O**ù
- **Q**uand
- **P**ourquoi

---

## 📊 Navigation

### Boutons de navigation

- **Étape 1** : "Suivant" uniquement
- **Étapes 2-7** : "Retour" et "Suivant"
- **Étape 8** : "Retour" et "Terminer"

### Validation

- Chaque étape **valide les champs obligatoires** avant de permettre la navigation
- Les messages d'erreur s'affichent **inline** sous les champs concernés
- La validation se déclenche à la **soumission du formulaire**

---

## 🎨 UX/UI Features

### Auto-génération intelligente

- **User Stories** : Générées à partir du Persona + Besoins + Objectifs
- **Architecture** : Générée à partir des fonctionnalités Must-Have

### Exemples contextuels

- Chaque formulaire inclut des **exemples de bonnes et mauvaises pratiques**
- Format visuel : ✅ Bon exemple / ❌ Mauvais exemple

### Aide contextuelle

- Messages d'**aide** (help-text) pour clarifier les concepts
- **Info boxes** avec conseils méthodologiques

### Feedback visuel

- **Warning boxes** pour les limites dépassées (ex: > 5 Must-Have)
- **Error messages** en rouge sous les champs invalides
- Classes CSS `.error` pour les champs en erreur

---

## 📁 Structure des données (TypeScript)

```typescript
interface ProjectData {
  objective?: SmartObjective;
  persona?: Persona;
  problemStatement?: ProblemStatement;
  need?: Need;
  analysis?: CQQCOQPAnalysis;
  userStories?: UserStory[];
  features?: Feature[];
  modules?: Module[];
}
```

Voir `/src/types/project.ts` pour les définitions complètes des interfaces.
