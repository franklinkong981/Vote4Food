"""SQLAlchemy models for the Vouch4Food app."""

from datetime import datetime, timezone

from flask_bcrypt import Bcrypt #For user signup/login password hashing
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """User in the app. A user can create an account by signing up, then logging in.
    User will sign up with a first name, last name, unique email address, password, and optional profile picture."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    user_image_url = db.Column(db.Text, default="vote4food_default")
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Once logged in, users can set their address which will be converted into longitude and latitude for restaurant lookup.
    address_street = db.Column(db.Text)
    address_city = db.Column(db.Text)
    address_state = db.Column(db.String(2))
    address_zip = db.Column(db.String(5))
    location_lat = db.Column(db.Float)
    location_long = db.Column(db.Float)

    # Relationships to link a user to their list of restaurant/menu item reviews and favorites.
    restaurant_reviews = db.relationship('Restaurant_Review', cascade='all, delete', backref='author')
    restaurant_favorites = db.relationship('Restaurant_Favorite', cascade='all, delete', backref='author')
    item_reviews = db.relationship('Item_Review', cascade='all, delete', backref='author')
    item_favorites = db.relationship('Item_Favorite', cascade='all, delete', backref='author')

    # Relationships to link a user to the list of restaurants and menu items they favorited so information about them can be
    # easily accessed via the navbar.
    favorite_restaurants = db.relationship('Restaurant', secondary='restaurant_favorites', backref='favorite_users')
    favorite_items = db.relationship('Item', secondary='item_favorites', backref='favorite_users')

class Restaurant(db.Model):
    """Restaurant location, NOT restaurant chain. Each location of a restaurant will be a different instance of the Restaurant model.
    This is for restaurant location lookup. Contains some restaurant location data taken from the API so that locations that have
    been reviewed and/or favorited by the user can be accessed quickly."""

    __tablename__ = "restaurants"

    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text)
    description = db.Column(db.Text)
    cuisines = db.Column(db.Text)
    store_photo_url = db.Column(db.Text)
    logo_photo_url = db.Column(db.Text, default="vote4food_default")

    # Relationships to link a restaurant location to the list of reviews and favorites for it.
    reviews = db.relationship('Restaurant_Review', cascade='all, delete', backref='restaurant')
    favorites = db.relationship('Restaurant_Favorite', cascade='all, delete', backref='restaurant')

class Item(db.Model):
    """Restaurant menu item. Contains some data for a menu item taken from the API so that items that have been reviewed 
    and/or favorited by the user can be accessed quickly."""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    restaurant_chain = db.Column(db.Text)
    image_url = db.Column(db.Text, default="vote4food_default")

    # Relationships to link a menu item to the list of reviews and favorites for it.
    reviews = db.relationship('Item_Review', cascade='all, delete', backref='item')
    favorites = db.relationship('Item_Favorite', cascade='all, delete', backref='item')

class Restaurant_Review(db.Model):
    """A user can create a review for a specific restaurant location. Each restaurant review only has one author, and a user can create
    multiple reviews for the same restaurant location. Users can also update and delete the restaurant reviews they created."""

    __tablename__ = "restaurant_reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Text, db.ForeignKey('restaurants.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Item_Review(db.Model):
    """A user can create a review for a restaurant chain's menu item. Each item review only has one author, and a user can create 
    multiple reviews for the same menu item. Users can also update and delete the menu item reviews they created."""

    __tablename__ = "item_reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Restaurant_Favorite(db.Model):
    """A user can mark a specific restaurant location as a favorite and will be able to view a list of their favorite restaurant
    locations on the top navbar."""

    __tablename__ = "restaurant_favorites"

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    restaurant_id = db.Column(db.Text, db.ForeignKey('restaurants.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Item_Favorite(db.Model):
    """A user can mark a specific menu item from a chain restaurant as a favorite and will be able to view a list 
    of their favorite menu items on the top navbar."""

    __tablename__ = "item_favorites"

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))



def connect_db(app):
    """Connect the SQLAlchemy instance/database, db, to Flask application instance provided in app.py.
    That is, links the database with the models set up in this file as the database for the Vouch4Food application initialized in app.py"""
    with app.app_context():
        db.app = app
        db.init_app(app)
        db.create_all() #Create all tables specified by the models above in the database.