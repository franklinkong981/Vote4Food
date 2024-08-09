from models.init_db import db

def connect_db(app):
    """Connect the SQLAlchemy instance/database, db, to Flask application instance provided in app.py.
    That is, links the database with the models set up in this file as the database for the Vouch4Food application initialized in app.py"""
    with app.app_context():
        db.app = app
        db.init_app(app)
        db.create_all() #Create all tables specified by the models above in the database.