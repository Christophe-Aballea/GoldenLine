import pathlib
import json
from flask import Flask, render_template, request, url_for, flash, redirect
from flaskext.markdown import Markdown
from database import check_db, create_db

# Détermination du dossier racine du projet
project_root = pathlib.Path(__file__).parent.resolve()

# Paramètres du projet
params_file = project_root / 'params.json'
params = {"project_root": str(project_root)}

# Déclaration de l'application Flask
back = Flask(__name__)
Markdown(back)
back.secret_key = b'eyJzdWIiOiJnb2xkZW5saW5lIiwibmFtZSI6IkNocmlzdG9waGUgQUJBTExFQSIsImlhdCI6MTUxNjIzOTAyMn0'


@back.route("/")
def index():
    return render_template("index.html")


@back.route("/error")
def error():
    return render_template("error.html")


@back.route("/db_params", methods=["GET", "POST"])
def db_params():
    if request.method == "GET":
        return render_template("db_params.html")
    else:
        form_data = request.form
        host, port = form_data["host"], form_data['port']
        username, password = form_data['user'], form_data['mdp']
        test_connection = check_db.check_postgresql_connection(host, port, username, password)
        if test_connection["Connection"] and test_connection["User exists"] and test_connection["User privileges"]:
            return redirect(url_for("db_creation", host=host, port=port, user=username, password=password))
        else:
            flash(f"Connexion refusée par le serveur", "error")
            flash(f"Causes possibles", "error")
            flash(f"Le serveur PostgreSQL n'est pas démarré", "error")
            flash(f"L'adresse de connexion {host}:{port} n'est pas valide", "error")
            flash(f"Le compte '{username}' n'existe pas", "error")
            flash(f"Erreur de saisie du mot de passe du compte '{username}'", "error")
            flash(f"Le compte '{username}' ne dispose pas des droits nécessaires", "error")
            flash(f"Accéder à la documentation", "error")
        return render_template("db_params.html", host=host, port=port, user=username, password=password)


@back.route("/db_creation", methods=["GET", "POST"])
def db_creation():
    global params
    if request.method == "GET":
        for k, v in request.args.items():
            params[k] = v
        with open(params_file, 'w') as file:
            json.dump(params, file)
        return render_template("db_creation.html")
    else:
        with open(params_file, 'r') as file:
            params = json.load(file)

        for k, v in request.form.items():
            if k.startswith('nb_'):
                v = int(v.replace(' ', ''))
            params[k] = v
        
        with open(params_file, 'w') as file:
            json.dump(params, file)
        create_db.create_schemas(params)
        return render_template("index.html")
    


@back.route("/help/db_connection")
def help_db_connection():
    with open("templates/help/db_connection.md", "r") as f:
        content = f.read()
    return render_template("help/db_connection.html", content=content)

