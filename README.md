# Goldenline Marketing Dashboard

Le Goldenline Marketing Dashboard est un projet Python qui fournit un site web permettant au service marketing de Goldenline d'analyser les données clientèle sous forme de graphiques interactifs et faciles à comprendre.

## Table des matières

- [Goldenline Marketing Dashboard](#goldenline-marketing-dashboard)
  - [Table des matières](#table-des-matières)
  - [Introduction](#introduction)
  - [Fonctionnalités](#fonctionnalités)
  - [Technologies utilisées](#technologies-utilisées)
  - [Installation et configuration](#installation-et-configuration)
  - [Utilisation](#utilisation)

## Introduction

Ce projet a pour objectif de fournir un outil d'analyse de données pour le service marketing de Goldenline. Les utilisateurs pourront explorer et analyser les données clientèle à l'aide de divers graphiques interactifs, permettant ainsi d'améliorer la prise de décisions et l'efficacité des campagnes marketing.

## Fonctionnalités

- Visualisation des données clientèle
- Filtrage des données par période, catégories de produits, catégories socio-professionnelles
- Exportation des données
- Interface utilisateur intuitive et adaptative

## Technologies utilisées

- Python
- Flask (Framework Web)
- Pandas (Bibliothèque de manipulation et d'analyse de données)

## Installation et configuration

- Cloner le dépôt
  ``` bash
  $ git clone https://github.com/Christophe-Aballea/goldenline
  ```
- Installer les dépendances du projet
  ``` bash
  $ cd goldenline
  $ pip install -r requirements.txt
  ```
- Exécuter le projet en local
  ``` bash
  $ flask --app goldenline-be:back run
  ```

## Utilisation

Le terminal dans lequel la commande `flask` a été excécutée doit afficher le lien à ouvrir dans un navigateur. Exemple : `* Running on http://127.0.0.1:5000`.  

![Mise en production - Ecran 1](./static/img/mep0.png)  
Au premier lancement le système vérifie le statut du projet et propose sa mise en production.  

![Mise en production - Ecran 2](./static/img/mep1.png)  
La première étape consiste à vérifier la connectivité au serveur PostgreSQL et l'existence d'un utilisateur d'application avec les droits suffisants.  

![Mise en production - Ecran 1](./static/img/mep2.png)  
Lorsque les paramètres saisis sont correct, l'écran suivant propose le paramétrage des noms de base de données et schémas, ainsi que le nombre de clients et de collectes à générer. Attention, la mise en production avec le paramétrage de base (3 000 000 de clients / 40 000 000 de collectes) prend un temps certain. Sur une machine équipée de 64 Go de RAM et un processeur Core i9-9900 K 16 coeurs, 3 h 22 min ont été nécessaires.
