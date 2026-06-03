---
name: security-rgpd
description: "Use when handling data, authentication, or configuration — security rules, RGPD compliance, secrets management, auth patterns, logging rules."
trigger: security
---

# Security & RGPD

## Sécurité minimale

- validation de toutes les entrées
- échappement des sorties si nécessaire
- protection CSRF si cookies
- protection XSS
- protection injection SQL
- rate limiting sur routes sensibles
- permissions explicites
- secrets hors repo
- dépendances mises à jour
- audit de sécurité régulier
- headers HTTP de sécurité
- logs de sécurité

## RGPD

- minimisation des données
- consentement explicite si nécessaire
- finalité claire
- durée de conservation définie
- droit d'accès, rectification, suppression
- export des données si pertinent
- logs sans données sensibles inutiles
- chiffrement des données sensibles
- politique de confidentialité claire
- cookies gérés proprement
- traçabilité des traitements

### Ne jamais stocker inutilement

- mots de passe en clair
- tokens non chiffrés
- documents sensibles sans justification
- données personnelles dans les logs
- infos de paiement hors prestataire

## Authentification & Autorisation

- **Authn** : qui est l'utilisateur ?
- **Authz** : qu'a-t-il le droit de faire ?
- **Session** : comment garde-t-on l'état connecté ?
- OAuth2/OIDC si possible
- mots de passe hashés (algorithme robuste)
- expiration et rotation des tokens
- rôles et permissions explicites
- routes sensibles protégées
- événements de sécurité journalisés

## Observabilité

- logs structurés avec niveaux
- traces et métriques
- corrélation par request id
- monitoring des erreurs et performances
- alerting sur erreurs critiques

### À logger
- démarrage de service
- erreurs applicatives et infrastructure
- appels externes critiques
- temps de traitement longs
- échecs d'authentification
- actions métier importantes

### À ne pas logger
- mots de passe, tokens, secrets
- données personnelles inutiles
- documents clients complets
