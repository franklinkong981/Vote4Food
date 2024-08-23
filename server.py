"""Main deployment/launch file that creates an instance of the Vouch4Food app, connects the database, and launches the app."""

from app import create_app
from models.connect import connect_db

app = create_app("vouch4food")
connect_db(app)