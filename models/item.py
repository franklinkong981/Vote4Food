"""This file contains all the models that have to do with menu items."""

from models.init_db import db
from datetime import datetime, timezone

class Item(db.Model):
    """Restaurant menu item. Contains some data for a menu item taken from the API so that items that have been reviewed 
    and/or favorited by the user can be accessed quickly."""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    restaurant_chain = db.Column(db.Text)
    image_url = db.Column(db.Text, default="/static/images/default-menu-item-image.jpg")

    @classmethod
    def create_item(cls, item):
        """Adds a new menu item to the database through a pre-filled item object."""

        new_item = Item(
            id = item['id'],
            title = item['title'],
            restaurant_chain = item['restaurant_chain'],
            image_url = item['image_url'],
        )
        db.session.add(new_item)
    
    def update_item(self, item):
        """Updates an existing Item in the database by comparing its information to the information in the item object,
        which contains updated information about that menu item from the Spoonacualr API."""

        # Only id is guaranteed to be the same, the rest might change.

        if self.title != item['title']: self.title = item['title']
        if self.restaurant_chain != item['restaurant_chain']: self.restaurant_chain = item['restaurant_chain']
        if self.image_url != item['image_url']: self.image_url = item['image_url']

    # Relationships to link a menu item to the list of reviews and favorites for it.
    reviews = db.relationship('Item_Review', cascade='all, delete', backref='item')
    favorites = db.relationship('Item_Favorite', cascade='all, delete', backref='item')

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

    def format_created_at(self):
        """Turn the datetime created_at attribute into a more readable string."""
        return self.created_at.strftime("%A, %m/%d/%Y at %I:%M%p")

class Item_Favorite(db.Model):
    """A user can mark a specific menu item from a chain restaurant as a favorite and will be able to view a list 
    of their favorite menu items on the top navbar."""

    __tablename__ = "item_favorites"

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
