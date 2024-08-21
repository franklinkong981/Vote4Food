"""Tests for favoriting restaurants/menu items as well as viewing the logged in user's list of favorite restaurants and menu items."""

# To run these tests:
#
# FLASK_ENV=production python3 -m unittest tests/tests_favorites.py

import os
from unittest import TestCase
from app import create_app, CURRENT_USER_KEY

from models.init_db import db
from models.user import User
from models.restaurant import Restaurant, Restaurant_Favorite, Restaurant_Review
from models.item import Item, Item_Favorite, Item_Review
from models.connect import connect_db

from sqlalchemy.exc import IntegrityError

# Create another application instance that connects to the testing database (vouch4food_test) instead of the main database (vouch4food on Supabase).
app = create_app("vouch4food_test", testing=True)
connect_db(app)
app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class ProfileTestCase(TestCase):
  """Test views that have to do with viewing and updating logged in user profile info."""

  def setUp(self):
    """Before each test, delete any existing data in the tables, create test client, store sample users, restaurants, and menu items in the database."""
    
    User.query.delete()
    Restaurant.query.delete()
    Restaurant_Favorite.query.delete()
    Restaurant_Review.query.delete()
    Item.query.delete()
    Item_Favorite.query.delete()
    Item_Review.query.delete()

    self.client = app.test_client()

    # Create sample test user accounts
    user_ted = User.create_user(
      first_name = "Ted",
      last_name = "Abigail",
      email = "teddybear@gmail.com",
      user_image_url = "www.testurl1.com",
      password = "PASSWORD1"
    )
    db.session.add(user_ted)

    # Create sample restaurant
    arbys = Restaurant(
      id = "restaurant1",
      name = "Arbys",
      address = "California",
      cuisines = "Sandwiches, fast food, burgers",
      description = "Good fast food place that sells burgers and sandwiches",
      phone = "1-(858)-857-9476",
      photo_url = "www.arbysimage.jpg",
      latitude = 123.456,
      longitude = 654.321
    )

    mcdonalds = Restaurant(
      id = "restaurant2",
      name = "McDonalds",
      address = "San Diego, California, 92129",
      cuisines = "Fast food, burgers, ice cream",
      description = "Famous fast food place that sells burgers, fries, and has a value menu.",
      phone = "1-(858)-947-3866",
      photo_url = "www.mcdonaldsimage.jpg",
      latitude = 578.398,
      longitude = 857.397,
      sunday_hours = "7:00AM-8:00PM",
      monday_hours = "7:00AM-5:00PM",
      tuesday_hours = "7:00AM-5:00PM",
      wednesday_hours = "7:00AM-5:00PM",
      thursday_hours = "7:00AM-5:00PM",
      friday_hours = "7:00AM-5:00PM",
      saturday_hours = "7:00AM-8:00PM"
    )
    db.session.add_all([arbys, mcdonalds])

    # Create sample menu item

    big_mac = Item(
      title = "Big Mac",
      restaurant_chain = "McDonalds",
      image_url = "www.mcdonalds.com/big_mac_image.jpg"
    )

    roast_beef_sandwich = Item(
      title = "Roast Beef Sandwich",
      restaurant_chain = "Arbys",
      image_url = "www.arbys.com/roast_beef_sandwich_image.jpg"
    )
    db.session.add_all([big_mac, roast_beef_sandwich])
    db.session.commit()

    # Create sample favorites
    mcdonalds_favorite = Restaurant_Favorite(
      author_id = user_ted.id,
      restaurant_id = mcdonalds.id
    )

    big_mac_favorite = Item_Favorite(
      author_id = user_ted.id,
      item_id = big_mac.id
    )
    db.session.add(mcdonalds_favorite)
    db.session.add(big_mac_favorite)

    db.session.commit()
  
  def tearDown(self):
    """After each test, revert table back to original state."""

    db.session.rollback()

  """There is one user: user_ted. There are 2 restaurants: McDonald's and Arby's. Two menu items: Big Mac from McDonalds and Roast Beef Sandwich from Arbys.
  Ted has McDonalds and Big Mac as his favorites."""

  # Favoriting restaurants tests

  def test_logged_out_favoriting_restaurants(self):
    """When a logged out user tries to favorite a restaurant, are they redirected to the homepage?"""

    arbys = Restaurant.query.filter(Restaurant.name == "Arbys").first()

    with self.client as c:
      resp = c.post(f"/restaurants/{arbys.id}/favorite")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_favorite_restaurant(self):
    """When a logged in user favorites a restaurant, is it added to their list of favorite restaurants?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    arbys = Restaurant.query.filter(Restaurant.name == "Arbys").first()

    # Make sure Ted already has one favorited restaurant
    self.assertEqual(len(user_ted.favorite_restaurants), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/restaurants/{arbys.id}/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_restaurants), 2)
  
  def test_unfavorite_restaurant(self):
    """When a logged in user favorites a restaurant they already favorited, is it removed from their list of favorite restaurants?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    # Make sure Ted already has one favorited restaurant
    self.assertEqual(len(user_ted.favorite_restaurants), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/restaurants/{mcdonalds.id}/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_restaurants), 0)

  def test_favorite_invalid_restaurant(self):
    """When a logged in user favorites a restaurant that doesn't exist, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    
    # Make sure Ted already has one favorited restaurant
    self.assertEqual(len(user_ted.favorite_restaurants), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/restaurants/invalid_restaurant/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_restaurants), 1)
  
  # Favoriting menu items tests

  def test_logged_out_favoriting_items(self):
    """When a logged out user tries to favorite a menu item, are they redirected to the homepage?"""

    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    with self.client as c:
      resp = c.post(f"/items/{big_mac.id}/favorite")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_favorite_item(self):
    """When a logged in user favorites a menu item, is it added to their list of favorite menu items?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    roast_beef_sandwich = Item.query.filter(Item.title == "Roast Beef Sandwich").first()

    # Make sure Ted already has one favorited menu item
    self.assertEqual(len(user_ted.favorite_items), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/items/{roast_beef_sandwich.id}/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_items), 2)

  def test_unfavorite_item(self):
    """When a logged in user favorites a menu item they already favorited, is it removed from their list of favorite menu items?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    # Make sure Ted already has one favorited menu item
    self.assertEqual(len(user_ted.favorite_items), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/items/{big_mac.id}/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_items), 0)
  
  def test_favorite_invalid_item(self):
    """When a logged in user favorites a menu item that doesn't exist, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    roast_beef_sandwich = Item.query.filter(Item.title == "Roast Beef Sandwich").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    invalid_id = 1
    while invalid_id == roast_beef_sandwich.id or invalid_id == big_mac.id:
      invalid_id += 1
    
    # Make sure Ted already has one favorited restaurant
    self.assertEqual(len(user_ted.favorite_items), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/items/{invalid_id}/favorite")
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.favorite_items), 1)    


  # Favorites button tests

  def test_favorited_restaurant_page(self):
    """When a logged in user visits the page of a restaurant they favorited, do they see the appropriate button?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Remove from Favorites <i class="fa-solid fa-star">', html)
  
  def test_unfavorited_restaurant_page(self):
    """When a logged in user visits the page of a restaurant they haven't favorited, do they see the appropriate button?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    arbys = Restaurant.query.filter(Restaurant.name == "Arbys").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{arbys.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Add to Favorites <i class="fa-regular fa-star"></i>', html)

  def test_favorited_item_page(self):
    """When a logged in user visits the page of a menu item they favorited, do they see the appropriate button?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{big_mac.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Remove from Favorites <i class="fa-solid fa-star">', html)
  
  def test_unfavorited_item_page(self):
    """When a logged in user visits the page of a menu item they haven't favorited, do they see the appropriate button?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    roast_beef_sandwich = Item.query.filter(Item.title == "Roast Beef Sandwich").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{roast_beef_sandwich.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Add to Favorites <i class="fa-regular fa-star"></i>', html)

  # Viewing favorite restaurants tests

  def test_logged_out_favorite_restaurants_page(self):
    """When a logged out user tries to access a list of their favorite restaurants, are they redirected to the home page?"""

    with self.client as c:
      resp = c.get(f"/users/favorites/restaurants")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_favorite_restaurants_page(self):
    """When a logged in user accesses the list of their favorite restaurants, do they see the appropriate restaurants listed?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/users/favorites/restaurants")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Favorite Restaurants (1)', html)
      self.assertIn('McDonalds', html)
      self.assertNotIn('Arbys', html)

  # Viewing favorite menu items tests

  def test_logged_out_favorite_restaurants_page(self):
    """When a logged out user tries to access a list of their favorite menu items, are they redirected to the home page?"""

    with self.client as c:
      resp = c.get(f"/users/favorites/items")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_favorite_items_page(self):
    """When a logged in user accesses the list of their favorite menu items, do they see the appropriate menu items listed?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/users/favorites/items")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Favorite Menu Items (1)', html)
      self.assertIn('Big Mac', html)
      self.assertNotIn('Roast Beef Sandwich', html)
