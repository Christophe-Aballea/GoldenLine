import psycopg2
import pathlib
from database import populate_sc_source


# Contenu de la table 'csp'
libelles_csp = ["Agriculteurs exploitants",
                "Artisants, commercants, chefs d'entreprise",
                "Cadres et professions intellectuelles supérieures",
                "Professions intermédiaires",
                "Employés",
                "Ouvriers",
                "Retraités",
                "Sans activité professionnelle"]

# Initiales pour csp
def get_initials(libelle):
    words = libelle.split()
    initials = ''.join([word[0] for word in words if len(word) > 2]).upper()
    return initials


# Vérification de l'existence de la procédure stockée transfer_data()
def check_stored_procedure_exists(cursor):
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM pg_proc
            WHERE proname = 'transfer_data'
        );
    """)
    return cursor.fetchone()[0]


# Création de la procédure stockée transfer_data()
def create_stored_procedure(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS last_execution(
            id SERIAL PRIMARY KEY,
            executed_at TIMESTAMP NOT NULL
        );
    """)

    cursor.execute("""
        CREATE OR REPLACE FUNCTION hash_client_data(p_id_client INTEGER, p_email VARCHAR, p_telephone VARCHAR)
        RETURNS VARCHAR(64) AS $$
        DECLARE
            v_hash VARCHAR(64);
        BEGIN
            SELECT encode(sha256(concat(p_id_client::TEXT, p_email, p_telephone)::bytea), 'hex')
            INTO v_hash;
            RETURN v_hash;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cursor.execute("""
        CREATE OR REPLACE PROCEDURE transfer_data(sc_source TEXT, sc_marketing TEXT)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_id_csp_mapping INTEGER;
            v_last_execution TIMESTAMP;
            v_sql TEXT;
        BEGIN
            -- Récupération de la date de la dernière exécution
            EXECUTE format('
                SELECT executed_at FROM %I.last_execution ORDER BY id DESC LIMIT 1;
            ', sc_marketing) INTO v_last_execution;

            -- Transfert des données de la table client
            EXECUTE format('
                INSERT INTO %I.client (id_client, nb_enfants, id_csp)
                SELECT 
                    %I.hash_client_data(c.id_client, c.email, c.telephone),
                    c.nb_enfants,
                    %I.csp.id_csp
                FROM %I.client AS c
                JOIN %I.csp ON c.csp = %I.csp.libelle
                WHERE (%L IS NULL) OR (c.id_client > %L);
            ', sc_marketing, sc_marketing, sc_marketing, sc_source, sc_marketing, sc_marketing, v_last_execution, v_last_execution);
    
            -- Transfert des données de la table collecte
            EXECUTE format('
                INSERT INTO %I.collecte (id_collecte, id_client, date_passage)
                SELECT 
                    col.id_collecte,
                    %I.hash_client_data(c.id_client, c.email, c.telephone),
                    col.date_heure_passage::DATE
                FROM %I.collecte AS col
                JOIN %I.client AS c ON col.id_client = c.id_client
                WHERE (%L IS NULL) OR (col.date_heure_passage > %L);
            ', sc_marketing, sc_marketing, sc_source, sc_source, v_last_execution, v_last_execution);

            -- Transfert des données vers la table achat pour chaque catégorie
            FOR v_id_csp_mapping IN 1..4 LOOP
                v_sql := format('
                    INSERT INTO %I.achat (id_collecte, id_categorie, montant)
                    SELECT 
                        col.id_collecte,
                        %L::INTEGER,
                        CASE %L::INTEGER
                            WHEN 1 THEN col.montant_dph
                            WHEN 2 THEN col.montant_alimentaire
                            WHEN 3 THEN col.montant_textile
                            WHEN 4 THEN col.montant_multimedia
                        END
                    FROM %I.collecte AS col
                    WHERE 
                        ((%L IS NULL) OR (col.date_heure_passage > %L)) AND
                        CASE %L::INTEGER
                            WHEN 1 THEN col.montant_dph
                            WHEN 2 THEN col.montant_alimentaire
                            WHEN 3 THEN col.montant_textile
                            WHEN 4 THEN col.montant_multimedia
                        END > 0;
                ', sc_marketing, v_id_csp_mapping, v_id_csp_mapping, sc_source, v_last_execution, v_last_execution, v_id_csp_mapping);
                EXECUTE v_sql;
            END LOOP;

            -- Enregistrement de la date d'exécution actuelle
            EXECUTE format('
                INSERT INTO %I.last_execution (executed_at) VALUES (NOW());
            ', sc_marketing);
        END;
        $$;
    """)
    

def create_db(host, port, dba_user, dba_password, dbname):
    conn = psycopg2.connect(dbname="postgres",
                            user=dba_user,
                            password=dba_password,
                            host=host,
                            port=port)
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE {dbname} WITH OWNER {dba_user};")

    cursor.close()
    conn.close()

    conn = psycopg2.connect(dbname=dbname,
                            user=dba_user,
                            password=dba_password,
                            host=host,
                            port=port)
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    cursor.close()
    conn.close()


def create_schemas(params):
    project_root = pathlib.Path(params["project_root"]).resolve()
    host, port, user, pwd = params["host"], params["port"], params["user"], params["password"]
    db_name, sc_source, sc_marketing = params["db_name"], params["sc_source"], params["sc_marketing"]

    # Création database 'db_name'
    create_db(host, port, user, pwd, db_name)
    
    # Connexion 'db_name'
    conn = psycopg2.connect(dbname=db_name, user=user, password=pwd, host=host, port=port)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Création schema_source
    cursor.execute(f"CREATE SCHEMA {sc_source};")
    cursor.execute(f"SET search_path TO {sc_source};")
    
    with open(project_root / "database" / "sc_source.sql", "r") as sql_file:
        sql_commands = sql_file.read()
    cursor.execute(sql_commands)

    # Création schema_marketing
    cursor.execute(f"CREATE SCHEMA {sc_marketing};")
    cursor.execute(f"SET search_path TO {sc_marketing};")

    with open(project_root / "database" / "sc_marketing.sql", "r") as sql_file:
        sql_commands = sql_file.read()
    cursor.execute(sql_commands)
    
    # Création procédure stockée de transfert/anonymisation gl_source -> gl_marketing
    if not check_stored_procedure_exists(cursor):
        create_stored_procedure(cursor)
        print("Procédure stockée créée avec succès.")
    else:
        print("La procédure stockée existe déjà.")
    
    # Remplissage 'sc_source' par données aléatoires
    populate_sc_source.populate_source(params)

    # Remplissage 'sc_marketing'.csp
    for libelle in libelles_csp:
        csp = get_initials(libelle)
        cursor.execute("INSERT INTO csp (libelle, csp) VALUES (%s, %s)", (libelle, csp))
    
    # Remplissage 'sc_marketing'.categorie
    for libelle in ["DPH", "Alimentaire", "Textile", "Multimedia"]:
        cursor.execute("INSERT INTO categorie (libelle) VALUES (%s)", (libelle, ))  
    
    # Transfert avec anonymisation
    sql = """
        CALL {schema}.transfer_data(%s, %s);
    """.format(schema=sc_marketing)
    cursor.execute(sql, (sc_source, sc_marketing))

    # Déconnexion
    cursor.close()
    conn.close()
