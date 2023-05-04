# Résoudre les problèmes de connexion au serveur PostgreSQL

### > Les manipulations suivantes ne peuvent être réalisées qu'avec un compte possédant les droits suffisants sur le serveur PostgreSQL.

## 1. Vérifier que le serveur PostgreSQL est bien démarré

Dans un terminal :

``` bash
$ sudo service postgresql status
```

Si le service est 'down' :

``` bash
$ sudo service postgresql start
```

Noter que la sortie des deux commandes précédentes affiche le port de connexion.

## 2. Vérifier 'host' et 'port'

Ce projet a été testé avec PostgreSQL installé sur le même serveur, les valeurs 'localhost' ou '127.0.0.1' devraient fonctionner pour le host.
Le port peut être obtenu par la vérification précédente.

Si cependant PostgreSQL n'est pas installé sur le même serveur, il conviendra de vérifier dans le fichier de configuration de PostgreSQL les adresse et port d'écoute disponibles.

Déterminer l'emplacement du fichier de configuration :

``` bash
$ sudo -u postgres psql -c 'SHOW config_file'
               config_file
-----------------------------------------
 /etc/postgresql/15/main/postgresql.conf
(1 row)
```

Rechercher l'adresse d'écoute (remplacer le path du fichier de configuration par le votre) :

``` bash
$ grep 'listen_addresses = ' /etc/postgresql/15/main/postgresql.conf
#listen_addresses = 'localhost'         # what IP address(es) to listen on;
```

Si la ligne trouvée est en commentaire comme ici, le port d'écoute par défaut est 127.0.0.1

Rechercher le port d'écoute :
``` bash
$ grep 'port = ' /etc/postgresql/15/main/postgresql.conf
port = 5433                             # (change requires restart)
```

## 3. Vérifier le compte utilisateur de l'application

Par mesure de sécurité, il est imposé dans ce projet un compte différent de 'postgres'.

### 3.1 Tentative de connexion

Tenter de se connecter avec le compte (remplacer 'username', 'host' et 'port') :

``` bash
$ psql -U username -h host -p port -d postgres
Password for user username:
psql (15.2 (Ubuntu 15.2-1.pgdg22.04+1))
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, compression: off)
Type "help" for help.

postgres=> \q
```

Si le compte n'existe pas ou si le mot de passe du compte est erroné, c'est le même message d'erreur qui s'affiche :
``` bash
$ psql -U username -h host -p port -d postgres
Password for user username:
psql: error: connection to server at "127.0.0.1", port 5432 failed: FATAL:  password authentication failed for user "username"
```

### 3.2 Vérification de l'existence du compte et de ses droits

Connexion psql :
``` bash
 $ sudo -u postgres psql
psql (15.2 (Ubuntu 15.2-1.pgdg22.04+1))
Type "help" for help.

postgres=# 
```

Recherche du compte et du privilège 'CREATEDB' :
``` sql
postgres=# SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname='username';
 rolname  | rolcreatedb
----------+-------------
 username | t
(1 row)

postgres=# \q
```

Ici, le compte existe bien et le rôle 'CREATEDB' lui a bien été attribué.

