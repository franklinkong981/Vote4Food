"""This file contains all the models that have to do with restaurants."""

from models.init_db import db
from datetime import datetime, timezone

class Restaurant(db.Model):
    """Restaurant location, NOT restaurant chain. Each location of a restaurant will be a different instance of the Restaurant model.
    This is for restaurant location lookup. Contains some restaurant location data taken from the API so that locations that have
    been reviewed and/or favorited by the user can be accessed quickly."""

    __tablename__ = "restaurants"

    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text)
    cuisines = db.Column(db.Text)
    description = db.Column(db.Text)
    phone = db.Column(db.Text)
    photo_url = db.Column(db.Text, default="/static/images/default-restaurant-image.jpg")

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    sunday_hours = db.Column(db.Text)
    monday_hours = db.Column(db.Text)
    tuesday_hours = db.Column(db.Text)
    wednesday_hours = db.Column(db.Text)
    thursday_hours = db.Column(db.Text)
    friday_hours = db.Column(db.Text)
    saturday_hours = db.Column(db.Text)

    @classmethod
    def create_restaurant(cls, restaurant):
        """Adds a new restaurant to the database through a pre-filled restaurant object."""

        new_restaurant = Restaurant(
            id = restaurant['id'],
            name = restaurant['name'],
            address = restaurant['address'],
            cuisines = restaurant['cuisines'],
            description = restaurant['description'],
            phone = restaurant['phone'],
            photo_url = restaurant['photo_url'],
            latitude = restaurant['latitude'],
            longitude = restaurant['longitude'],
            sunday_hours = restaurant['hours']['Sunday'],
            monday_hours = restaurant['hours']['Monday'],
            tuesday_hours = restaurant['hours']['Tuesday'],
            wednesday_hours = restaurant['hours']['Wednesday'],
            thursday_hours = restaurant['hours']['Thursday'],
            friday_hours = restaurant['hours']['Friday'],
            saturday_hours = restaurant['hours']['Saturday']
        )
        db.session.add(new_restaurant)
    
    def update_restaurant(self, restaurant):
        """Updates an existing restaurant in the database by comparing its information to the information in the restaurant object,
        which contains updated information about that restaurant from the Spoonacualr API."""

        # Only id is guaranteed to be the same, the rest might change.

        if self.name != restaurant['name']: self.name = restaurant['name']
        if self.address != restaurant['address']: self.address = restaurant['address']
        if self.cuisines != restaurant['cuisines']: self.cuisines = restaurant['cuisines']
        if self.description != restaurant['description']: self.description = restaurant['description']
        if self.phone != restaurant['phone']: self.phone = restaurant['phone']
        if self.photo_url != restaurant['photo_url']: self.photo_url = restaurant['photo_url']
        if self.latitude != restaurant['latitude']: self.latitude = restaurant['latitude']
        if self.longitude != restaurant['longitude']: self.longitude = restaurant['longitude']

        if self.sunday_hours != restaurant['hours']['Sunday']: self.sunday_house = restaurant['hours']['Sunday']
        if self.monday_hours != restaurant['hours']['Monday']: self.monday_hours = restaurant['hours']['Monday']
        if self.tuesday_hours != restaurant['hours']['Tuesday']: self.tuesday_hours = restaurant['hours']['Tuesday']
        if self.wednesday_hours != restaurant['hours']['Wednesday']: self.wednesday_hours = restaurant['hours']['Wednesday']
        if self.thursday_hours != restaurant['hours']['Thursday']: self.thursday_hours = restaurant['hours']['Thursday']
        if self.friday_hours != restaurant['hours']['Friday']: self.friday_hours = restaurant['hours']['Friday']
        if self.saturday_hours != restaurant['hours']['Saturday']: self.saturday_hours = restaurant['hours']['Saturday']

    # Relationships to link a restaurant location to the list of reviews and favorites for it.
    reviews = db.relationship('Restaurant_Review', cascade='all, delete', backref='restaurant')
    favorites = db.relationship('Restaurant_Favorite', cascade='all, delete', backref='restaurant')

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

    def format_created_at(self):
        """Turn the datetime created_at attribute into a more readable string."""
        return self.created_at.strftime("%A, %m/%d/%Y at %I:%M%p")

class Restaurant_Favorite(db.Model):
    """A user can mark a specific restaurant location as a favorite and will be able to view a list of their favorite restaurant
    locations on the top navbar."""

    __tablename__ = "restaurant_favorites"

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    restaurant_id = db.Column(db.Text, db.ForeignKey('restaurants.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
