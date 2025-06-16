from app import create_app, db # Assurez-vous d'importer db

app = create_app()

# Bloc à exécuter une fois pour créer les tables manquantes
# Vous pouvez le commenter ou le supprimer après la première exécution réussie
# ATTENTION: db.create_all() ne mettra pas à jour les tables existantes si vous modifiez leur structure.
# C'est pourquoi Flask-Migrate est préférable pour les changements de schéma.
# with app.app_context():
#     db.create_all()
#     print("Tables créées (si elles n'existaient pas).")


if __name__ == '__main__':
    # Pour créer les tables au démarrage si elles n'existent pas (une seule fois)
    with app.app_context():
        db.create_all() 
        print("Tentative de création des tables manquantes effectuée.")
    app.run(debug=True)