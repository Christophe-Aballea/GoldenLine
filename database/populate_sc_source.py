import pathlib
import datetime
import pandas as pd
import numpy as np
import psycopg2.pool


def populate_source(params):
    # Informations de connexion
    user     = params["user"]
    password = params["password"]
    host     = params["host"]
    port     = params["port"]
    database = params["db_name"]
    schema   = params["sc_source"]

    # Détermination du dossier racine du projet
    project_root = pathlib.Path(params["project_root"]).resolve()
    source_prenoms     = project_root / 'database' / 'source' / 'prenom.csv'
    source_noms        = project_root / 'database' / 'source' / 'patronymes.csv'
    source_communes    = project_root / 'database' / 'source' / 'laposte_hexasmal.csv'

    # Quantités de données à générer
    nb_rows_collecte = params["nb_collectes"]
    nb_rows_client   = params["nb_clients"]
    batch_size       = 100_000

    ##########################
    # GENERATION DES CLIENTS
    ##########################
    print("GENERATION DES CLIENTS")
    print("Préparation des données : ", end='', flush=True)
    df_client = pd.DataFrame(columns = ['id_client',
                                        'nom',
                                        'prenom',
                                        'telephone',
                                        'email',
                                        'code_postal',
                                        'ville',
                                        'csp',
                                        'nb_enfants'])

    # nom
    source = pd.read_csv(source_noms)
    noms = source[source['count'] > 100].reset_index(drop=True)
    noms_index = np.random.choice(len(noms), size=nb_rows_client, p=(noms['count'] / noms['count'].sum()))
    df_client['nom'] = noms.iloc[noms_index]['patronyme'].values
    print("nom", end='', flush=True)

    # prenom
    source = pd.read_csv(source_prenoms)
    prenoms = source[source['sum'] > 100].reset_index(drop=True)
    prenoms_index = np.random.choice(len(prenoms), size=nb_rows_client, p=(prenoms['sum'] / prenoms['sum'].sum()))
    df_client['prenom'] = prenoms.iloc[prenoms_index]['prenom'].values
    df_client['prenom'] = df_client['prenom'].apply(lambda x: x.capitalize())
    print(", prenom", end='', flush=True)

    # telephone
    numeros = np.random.choice(np.arange(100000000, 800000000), size=nb_rows_client, replace=False)
    def format_phone_number(number):
        string = f"0{number}"
        return f"{string[:2]} {string[2:4]} {string[4:6]} {string[6:8]} {string[8:]}"
    df_client['telephone'] = [format_phone_number(numero) for numero in numeros]
    print(", telephone", end='', flush=True)

    # email
    choices = ["@orange.fr", "@sfr.fr", "@wanadoo.fr", "@gmail.com", "@hotmail.fr", "@hotmail.com", "@voila.fr", "@yahoo.fr"]
    providers = np.random.choice(choices, size=nb_rows_client)
    df_client['email'] = df_client.apply(lambda row: row['prenom'][0].lower() + '.' + row['nom'].replace(' ', '').lower() + providers[row.name], axis=1)
    print(", email", end='', flush=True)

    # code postal et ville
    source = pd.read_csv(source_communes, sep=';')
    communes = source[source['code_postal'] < 97000].reset_index(drop=True)
    communes_index = np.random.randint(len(communes), size=nb_rows_client)
    df_client['code_postal'] = communes['code_postal'][communes_index].values
    print(", code_postal", end='', flush=True)
    df_client['ville'] = communes['nom_de_la_commune'][communes_index].values
    print(", ville", end='', flush=True)

    # csp
    # Répartition (source INSEE : https://www.insee.fr/fr/statistiques/2011101?geo=METRO-1)
    # Agriculteurs exploitant                           :  0.8 %
    # Artisants, commercants, chefs d'entreprise        :  3.5 %
    # Cadres et professions intellectuelles supérieures :  9.6 %
    # Professions intermédiaires                        : 14.2 %
    # Employés                                          : 16.0 %
    # Ouvriers                                          : 12.1 %
    # Retraités                                         : 27.2 %
    # Sans activité professionnelle                     : 16.6 %
    choices = ["Agriculteurs exploitants",
            "Artisants, commercants, chefs d'entreprise",
            "Cadres et professions intellectuelles supérieures",
            "Professions intermédiaires",
            "Employés",
            "Ouvriers",
            "Retraités",
            "Sans activité professionnelle"]
    weights = [0.008, 0.035, 0.096, 0.142, 0.16, 0.121, 0.272, 0.166]
    df_client['csp'] = np.random.choice(choices, size=nb_rows_client, p=weights)
    print(", csp", end='', flush=True)

    # nb_enfants
    # Répartition estimative
    choices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    weights = [0.22, 0.32, 0.22, 0.1, 0.035, 0.03, 0.025, 0.02, 0.015, 0.01, 0.005]
    df_client['nb_enfants'] = np.random.choice(choices, size=nb_rows_client, p=weights)
    print(", nb_enfants", flush=True)

    # Libération des variables
    source         = None
    noms           = None
    noms_index     = None
    prenoms        = None
    prenoms_index  = None
    numeros        = None
    choices        = None
    providers      = None
    communes       = None
    communes_index = None

    # Définir la requête SQL pour insérer les données
    insert_query = '''
    INSERT INTO client (nom, prenom, telephone, email, code_postal, ville, csp, nb_enfants)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''

    print("Enregistrement des données : ", end='', flush=True)

    for start_index in range(0, nb_rows_client, batch_size):
        end_index = start_index + batch_size
        
        # Création d'un pool de connexions
        pool = psycopg2.pool.SimpleConnectionPool(1, 80,
            user=user,
            password=password,
            host=host,
            port=port,
            database=database)
        
        # Se connecter à la base de données et insérer les données
        with pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {schema};")
                # Itérer sur chaque ligne de la dataframe et exécuter la requête d'insertion
                for row in df_client[start_index:end_index].itertuples(index=False):
                    cur.execute(insert_query, (
                        row.nom,
                        row.prenom,
                        row.telephone,
                        row.email,
                        row.code_postal,
                        row.ville,
                        row.csp,
                        row.nb_enfants
                    ))

                # Valider la transaction
                conn.commit()

        # Fermer toutes les connexions
        pool.closeall()
        print("🟩", end='', flush=True)

    print()

    # Correction des codes postaux avec un zéro de début manquant
    update_query = '''
    UPDATE client
    SET code_postal = LPAD(code_postal, 5, '0')
    WHERE LENGTH(code_postal) < 5;
    '''

    conn = psycopg2.connect(dbname=database,
                            user=user,
                            password=password,
                            host=host,
                            port=port)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO {schema};")
    cursor.execute(update_query)
    cursor.close()
    conn.close()
    print("Champ code_postal corrigé")

    # Libération mémoire
    df_client = None


    #################################
    # GENERATION DES COLLECTES
    #################################

    print("GENERATION DES COLLECTES")
    print("Préparation des données : ", end='', flush=True)

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date.today() - datetime.timedelta(days=1)

    # Liste de toutes les dates valides de la périodes
    dates = [single_date.date() for single_date in  pd.date_range(start_date, end_date, freq='C')]

    # Génération de toutes les dates et heures
    # Choix aléatoire de nb_rows_collecte dans la liste des dates valides
    # Génération aléatoire de nb_rows_collecte heure / minutes / secondes entre 9h00 et 20h59 (horaires d'ouverture)
    dates_array = np.random.choice(dates, size=nb_rows_collecte)
    hours = np.random.randint(9, 21, size=nb_rows_collecte)
    minutes = np.random.randint(0, 60, size=nb_rows_collecte)
    seconds = np.random.randint(0, 60, size=nb_rows_collecte)

    # Création des timestamp
    all_dates_heures = [
        datetime.datetime.combine(dates_array[i], datetime.time(hours[i], minutes[i], seconds[i])).strftime('%Y-%m-%d %H:%M:%S')
        for i in range(nb_rows_collecte)
    ]

    # Tri all_dates_heures en ordre croissant
    # Pour simuler l'ordre chrnologique des collectes
    all_dates_heures.sort()
    print("date_heure_passage", end='', flush=True)


    # Génération aléatoire de nb_rows_collecte id_client parmi nb_rows_client
    #all_id_clients = np.random.randint(1, nb_rows_client + 1, size=nb_rows_collecte)
    all_id_clients = np.random.choice(np.arange(1, nb_rows_client + 1), size=nb_rows_collecte, replace=True)
    print(", id_client")


    # Création des collectes et enregistrement en BD par lots de taille batch_size
    batch_number = 0
    print("Génération des montants et enegistrement des données : ", end='', flush=True)

    while nb_rows_collecte:
        # Info du lot
        nb_rows = min(batch_size, nb_rows_collecte)
        start_index = batch_size * batch_number
        end_index = start_index + nb_rows
        dates_heures = all_dates_heures[start_index:end_index]
        id_clients = all_id_clients[start_index:end_index]

        # Définition des paramètres du montant total d'une collecte
        # Distribution selon une loi normale de moyenne 75 €, écart-type de 45 €
        min_value = 0
        mean = 75
        std_dev = 45

        # Liste vide pour stocker les données
        data = []

        # Boucler sur chaque entier de 1 à batch_size pour créer chaque ligne de la dataframe
        for id_collecte in range(1, nb_rows + 1):
            # Tirage au sort d'un montant total aléatoire, suivant une loi de distribution normale
            # avec un minimum de 1.5, on suppose qu'aucun article ne coûte moins de 1.5 € chez Goldenline
            total = max(abs(np.random.normal(loc=mean, scale=std_dev)), 1.5)

            # Tirage au sort du nombre de catégories à renseigner
            # On suppose que :
            # 35 % du temps une collecte correspond à 2 catégories
            # 30 % du temps à 3 catégories
            # 20 % du temps à 1 catégorie
            # 15 % du temps aux 4 catégories
            nb_category = np.random.choice([1, 2, 3, 4], p=[0.2, 0.35, 0.3, 0.15])

            # Tirage au sort des catégories à renseigner
            choices = [0, 1, 2, 3]
            weights = [0.1, 0.35, 0.35, 0.2]
            categories = np.random.choice(choices, size=nb_category, p=weights, replace=False)

            # Répartition aléatoire du total dans les catégories
            alpha = np.ones(nb_category)
            percents = np.random.dirichlet(alpha, size=1)
            montants = [0, 0, 0, 0]
            for i, c in enumerate(categories):
                montants[c] = max(total * percents[0][i], 1.5)

            # Création d'une ligne de données
            row = {
                'date_heure_passage': dates_heures[id_collecte - 1],
                'montant_dph': montants[0],
                'montant_alimentaire': montants[1],
                'montant_textile': montants[2],
                'montant_multimedia': montants[3],
                'id_client': id_clients[id_collecte - 1]
            }

            # Ajout de la ligne de données générée
            data.append(row)

        # Création d'une dataframe à partir de la liste de données
        df_collecte = pd.DataFrame(data)

        # Arrondi de tous les montants à 2 chiffres après la virgule
        df_collecte = df_collecte.round({'montant_dph': 2, 'montant_alimentaire': 2, 'montant_textile': 2, 'montant_multimedia': 2})

        # Création d'un pool de connexions
        pool = psycopg2.pool.SimpleConnectionPool(1, 80,
            user=user,
            password=password,
            host=host,
            port=port,
            database=database)
        
        # Requête SQL d'insertion des données
        insert_query = '''
        INSERT INTO collecte (date_heure_passage, montant_dph, montant_alimentaire, montant_textile, montant_multimedia, id_client)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        # Connection à la base de données et insértion des données
        with pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {schema};")
                # Itérer sur chaque ligne de la dataframe et exécuter la requête d'insertion
                for row in df_collecte.itertuples(index=False):
                    cur.execute(insert_query, (
                        row.date_heure_passage,
                        row.montant_dph,
                        row.montant_alimentaire,
                        row.montant_textile,
                        row.montant_multimedia,
                        row.id_client
                    ))

                # Valider la transaction
                conn.commit()

        # Fermeture des connexions
        pool.closeall()

        nb_rows_collecte -= nb_rows
        batch_number += 1
        print("🟩", end='', flush=True)

    print()
