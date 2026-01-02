```
Sélectionner le prochain ticket exécutable

Si le dépôt n’est pas encore présent :
    cloner le repository

pull le repo

Créer une branche associée au ticket
Initialiser la conversation avec le premier message du ticket

Tant que le ticket n’est pas validé :
    message → reasoning → modification du code
    commit des changements
    lancer la CI

    Si la limite d’itérations est atteinte :
        créer un nouveau ticket de bug
        arrêter le traitement du ticket courant

    Si la CI retourne une erreur :
        ajouter l’erreur comme nouveau message
        continuer l’itération

    Sinon (CI validée) :
        créer une Pull Request
        marquer le ticket comme A VALIDER
        sortir de la boucle
```
