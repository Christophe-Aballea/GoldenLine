import psycopg2
from psycopg2.errors import InsufficientPrivilege


def check_postgresql_connection(host, port, user, password):
    """Vérifie la connexion au serveur PostgreSQL

    Args:
        host (str): adresse IP du serveur
        port (str): port de connexion PostgreSQL
        user (str): username
        password (str): password

    Returns:
        status (dict): {"Connection": True/False,
                        "User exists": Trus/False,
                        "User authentication": True/False,
                        "User privileges": True/False}
    """
    status = {"Connection": True,
              "User exists": True,
              "User authentication": True,
              "User privileges": True}

    try:
        # Test de la connexion à PostgreSQL
        conn = psycopg2.connect(dbname="postgres",
                                user=user,
                                password=password,
                                host=host,
                                port=port)
        cursor = conn.cursor()

        try:
            # Vérification de l'existence de l'utilisateur
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s;", (user,))
            if cursor.rowcount == 1:
                status["User exists"] = True
                try:
                    # Vérification des droits de l'utilisateur
                    cursor.execute("SELECT rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=%s;", (user,))
                    can_create_db, can_create_role = cursor.fetchone()
                    if can_create_db and can_create_role:
                        status["User privileges"] = True
                    else:
                        status["User privileges"] = False
                except:
                    status["User privileges"] = False
            else:
                status["User exists"] = False

        except psycopg2.OperationalError as error:
            status["User authentication"] = False
        except InsufficientPrivilege as e:
            status["User privileges"] = False
        finally:
            # Fermeture des connexions
            cursor.close()
            conn.close()

    except psycopg2.OperationalError as error:
        print(str(error))
        status["Connection"] = False
        if "password authentication failed" in str(error):
            status["User authentication"] = False

    return status
