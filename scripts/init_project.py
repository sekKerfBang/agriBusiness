"""
Script pro pour initialiser le projet en 1 commande
Usage: python scripts/init_project.py
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande avec feedback"""
    print(f"📦 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur lors de : {description}")
        print(result.stderr)
        sys.exit(1)
    print(f"✅ {description} terminé")

def main():
    BASE_DIR = Path(__file__).resolve().parent.parent
    os.chdir(BASE_DIR)  # S'assure d'être à la racine du projet

    print("🚀 Initialisation de la plateforme AgriBusiness")

    # 1. Vérifier Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ requis")
        sys.exit(1)

    # 2. Installer dépendances
    # run_command(
    #     "pip install -r requirements.txt",
    #     "Installation des dépendances"
    # )

    # 3. Créer .env si absent
    env_path = BASE_DIR / '.env'
    if not env_path.exists():
        print("🔑 Génération du SECRET_KEY...")
        secret_key = subprocess.run(
            ["python", "-c", "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"],
            capture_output=True, text=True
        ).stdout.strip()

        with open(env_path, 'w') as f:
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write("DEBUG=True\n")
            f.write("DB_NAME=agrimarket_dev\n")
            f.write("DB_USER=agrimarket_user\n")
            f.write("DB_PASSWORD=dev_password\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DEFAULT_EMAIL=noreply@agrimarket.com\n")
            f.write("CELERY_BROKER=redis://localhost:6379/0\n")
            f.write("CELERY_BACKEND=redis://localhost:6379/0\n")

        print("✅ Fichier .env créé")
    else:
        print("✅ .env déjà existant")

    # 4. Migrations (ordre important avec custom user)
    run_command(
        "python manage.py makemigrations --noinput",
        "Création des migrations"
    )

    # D'abord migrer l'app utilisateur (custom user) pour éviter les erreurs de dépendance
    run_command(
        "python manage.py migrate utilisateur --noinput",
        "Migration de l'app utilisateur (custom user)"
    )

    # Puis le reste
    run_command(
        "python manage.py migrate --noinput",
        "Application des autres migrations"
    )

    # 5. Collecter static
    run_command(
        "python manage.py collectstatic --noinput --clear",
        "Collecte des fichiers statiques"
    )

    # 6. Créer superuser si nécessaire
    marker = BASE_DIR / '.superuser_created'
    if not marker.exists():
        print("👤 Création du superuser (admin / admin123)")
        create_user_cmd = (
            'from apps.utilisateur.models import Utilisateur; '
            'Utilisateur.objects.create_superuser('
            'username="admin", '
            'email="admin@agrimarket.com", '
            'password="admin123", '
            'role="ENTREPRISE"'  # ou 'CLIENT' selon ton besoin
            ') if not Utilisateur.objects.filter(username="admin").exists() else print("Superuser déjà existant")'
        )

        subprocess.run(
            f'echo "{create_user_cmd}" | '
            'python manage.py shell',
            shell=True
        )

        marker.touch()
        print("✅ Superuser créé : admin / admin123")
    else:
        print("✅ Superuser déjà créé")

    print("\n🎉 Projet initialisé avec succès !")
    print("\n🚀 Lancement rapide :")
    print("   python manage.py runserver")
    print("   celery -A config worker --loglevel=info")
    print("   celery -A config beat --loglevel=info")
    print("\nAccès admin : http://127.0.0.1:8000/admin/")
    print("Superuser : admin / admin123")

if __name__ == "__main__":
    main()


# """
# Script pro pour initialiser le projet en 1 commande
# Usage: python scripts/init_project.py
# """

# import os
# import sys
# import subprocess
# from pathlib import Path

# def run_command(cmd, description):
#     """Exécute une commande avec feedback"""
#     print(f"📦 {description}...")
#     result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
#     if result.returncode != 0:
#         print(f"❌ Erreur: {result.stderr}")
#         sys.exit(1)
#     print(f"✅ {description} terminé")

# def main():
#     BASE_DIR = Path(__file__).resolve().parent.parent
    
#     print("🚀 Initialisation de la plateforme AgriMarket")
    
#     # Vérifier Python version
#     if sys.version_info < (3, 11):
#         print("❌ Python 3.11+ requis")
#         sys.exit(1)
    
#     # 1. Installer dépendances
#     run_command(
#         "pip install -r requirements.txt",
#         "Installation des dépendances"
#     )
    
#     # 2. Créer .env
#     if not (BASE_DIR / '.env').exists():
#         secret_key = subprocess.run(
#             "python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'",
#             shell=True, capture_output=True, text=True
#         ).stdout.strip()
        
#         with open(BASE_DIR / '.env', 'w') as f:
#             f.write(f"SECRET_KEY={secret_key}\n")
#             f.write("DEBUG=True\n")
#             f.write("DATABASE_URL=sqlite:///db.sqlite3\n")
#             f.write("CELERY_BROKER=redis://localhost:6379/0\n")
        
#         print("✅ Fichier .env créé")
    
#     # 3. Migrations
#     run_command(
#         "python manage.py makemigrations --noinput",
#         "Création des migrations"
#     )
    
#     run_command(
#         "python manage.py migrate --noinput",
#         "Application des migrations"
#     )
    
#     # 4. Collecter static
#     run_command(
#         "python manage.py collectstatic --noinput",
#         "Collecte des fichiers statiques"
#     )
    
#     # 5. Créer superuser si nécessaire
#     if not (BASE_DIR / '.superuser_created').exists():
#         print("👤 Création du superuser (admin/admin)")
#         subprocess.run(
#             'echo "from apps.users.models import User; '
#             'User.objects.create_superuser(\"admin\", \"admin@agrimarket.com\", \"admin\")" | '
#             'DJANGO_SETTINGS_MODULE=config.settings.development python manage.py shell',
#             shell=True, capture_output=True
#         )
        
#         (BASE_DIR / '.superuser_created').touch()
#         print("✅ Superuser créé: admin/admin")
    
#     print("\n🎉 Projet initialisé avec succès !")
#     print("\nLancement rapide:")
#     print("  python manage.py runserver")
#     print("  celery -A config.celery worker --loglevel=info")
#     print("  cd mobile && flet run main.py")

# if __name__ == "__main__":
#     main()