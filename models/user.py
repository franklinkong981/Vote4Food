"""This file contains the User model."""

from flask_bcrypt import Bcrypt #For user signup/login password hashing

from models.init_db import db
from datetime import datetime, timezone

bcrypt = Bcrypt()

class User(db.Model):
    """User in the app. A user can create an account by signing up, then logging in.
    User will sign up with a first name, last name, unique email address, password, and optional profile picture."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    user_image_url = db.Column(db.Text, default="/static/images/default-profile-image.jpg")
    password = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Once logged in, users can set their address which will be converted into longitude and latitude for restaurant lookup.
    address_zip = db.Column(db.Integer)
    location_lat = db.Column(db.Float)
    location_long = db.Column(db.Float)

    def get_full_name(self):
        """Get first and last name of the user"""
        return self.first_name + " " + self.last_name
    
    def format_created_at(self):
        """Turn the datetime created_at attribute into a more readable string."""
        return self.created_at.strftime("%A, %m/%d/%Y at %I:%M%p")

    @classmethod
    def create_user(cls, first_name, last_name, email, user_image_url, password, id= None):
        """Creates and returns a new user model instance out of the input parameters and hashes the password using bcrypt."""

        hashed_password = bcrypt.generate_password_hash(password).decode('UTF-8')
        new_user = User(
            first_name = first_name,
            last_name = last_name,
            email = email,
            user_image_url = user_image_url,
            password = hashed_password
        )

        db.session.add(new_user)
        return new_user
    
    
    @classmethod
    def authenticate_user(cls, email, password):
        """Attempts to find a user in the database whose email and password matches the parameter inputs. Returns the user if found,
        0 if the user with the email isn't found in the database, and 1 user is found but the hashed password doesn't match."""

        # emails are unique so we only need the first result.
        user = cls.query.filter_by(email=email).first()

        if user:
            do_passwords_match = bcrypt.check_password_hash(user.password, password)
            if do_passwords_match:
                return user
            return 1
        
        return 0
    
    @classmethod
    def confirm_password(cls, id, password):
        """Make sure that the hashed password matches the user with the specified id's current hashed password."""

        user = cls.query.get(id)

        if user:
            return bcrypt.check_password_hash(user.password, password)
        
        return False
    
    @classmethod
    def update_password(cls, id, new_password):
        """Updates the user with specific id's password by generating a new hash to new_password."""

        user = cls.query.get(id)
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode('UTF-8')
        user.password = new_hashed_password


    # Relationships to link a user to their list of restaurant/menu item reviews and favorites.
    restaurant_reviews = db.relationship('Restaurant_Review', cascade='all, delete', backref='author')
    restaurant_favorites = db.relationship('Restaurant_Favorite', cascade='all, delete', backref='author')
    item_reviews = db.relationship('Item_Review', cascade='all, delete', backref='author')
    item_favorites = db.relationship('Item_Favorite', cascade='all, delete', backref='author')

    # Relationships to link a user to the list of restaurants and menu items they favorited so information about them can be
    # easily accessed via the navbar.
    favorite_restaurants = db.relationship('Restaurant', secondary='restaurant_favorites', backref='favorite_users')
    favorite_items = db.relationship('Item', secondary='item_favorites', backref='favorite_users')