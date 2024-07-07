"""SQLAlchemy models for the Vote4Food app."""

from datetime import datetime

from flask_bcrypt import Bcrypt #For user signup/login password hashing
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """User in the app. A user can create an account by signing up, then logging in.
    User will sign up with a unique email, unique username, password, and optional profile picture."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    user_image_url = db.Column(db.Text, default="vote4food_default")
    
    # Once logged in, users can set their address which will be converted into longitude and latitude for restaurant lookup.
    location_lat = db.Column(db.Float)
    location_long = db.Column(db.Float)

class Restaurant(db.Model):
    """Restaurant location, NOT restaurant chain. Each location of a restaurant will be a different instance of the Restaurant model.
    This is for restaurant location lookup. Contains some restaurant location data taken from the API so that locations that have
    been upvoted/downvoted, reviewed, and/or favorited by the user can be accessed quickly."""

    __tablename__ = "restaurats"

class Item(db.Model):
    """Restaurant menu item. Contains some data for a menu item taken from the API so that items that have been upvoted/downvoted,
    reviewed, and/or favorited by the user can be accessed quickly."""

    __tablename__ = "items"




def connect_db(app):
    """Connect the SQLAlchemy instance/database, db, to Flask application instance provided in app.py.
    That is, links the database with the models set up in this file as the database for the Vote4Food application initialized in app.py"""
    with app.app_context():
        db.app = app
        db.init_app()
        db.create_all() #Create all tables specified by the models above in the database.