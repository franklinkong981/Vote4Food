"""Tests for viewing the restaurant and menu item details page, which make sure the pages viewed display the appropriate information
for the restaurant location/menu item."""

# To run these tests:
#
# FLASK_ENV=production python3 -m unittest tests/tests_details.py

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
      name = "Arby's",
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
      name = "McDonald's",
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
      restaurant_chain = "McDonald's",
      image_url = "www.mcdonalds.com/big_mac_image.jpg"
    )
    db.session.add(big_mac)

    db.session.commit()
  
  def tearDown(self):
    """After each test, revert table back to original state."""

    db.session.rollback()

  """There is one user: user_ted. There are 2 restaurants: McDonald's and Arby's. There is one menu item: Big Mac from McDonald's."""

  # Tests on restaurant details page

  def test_logged_out_restaurant_details_page(self):
    """When a logged out user tries to access a restaurant details page, are they redirected back to the homepage?"""

    arbys = Restaurant.query.filter(Restaurant.name == "Arby's").first()

    with self.client as c:
      resp = c.get(f"/restaurants/{arbys.id}")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_restaurant_details(self):
    """When a logged in user accesses a restaurant's details page, do they see the appropriate information?"""

    arbys = Restaurant.query.filter(Restaurant.name == "Arby's").first()
    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{arbys.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Add to Favorites <i class="fa-regular fa-star"></i>', html)
      self.assertIn('<h4 class="display-4">Restaurant Information</h4>', html)
      self.assertIn('<th scope="col">Sandwiches, fast food, burgers</th>', html)
      self.assertIn('<th scope="col">Good fast food place that sells burgers and sandwiches</th>', html)

      # Appropriately says there are no reviews for this restaurant.
      self.assertIn(' <p>There are no reviews currently for this restaurant.', html)
    
  def test_restaurant_details_with_hours(self):
    """When a logged in user accesses a restaurant's with hours details page, are the hours listed?"""

    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonald's").first()
    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<th scope="col">7:00AM-8:00PM</th>', html)
      self.assertIn('<th scope="col">7:00AM-5:00PM</th>', html)
    
  def test_invalid_restaurant_details(self):
    """When a logged in user accesses an invalid restaurant id's details page, are they given a 404 error and redirected back to the homepage?"""

    arbys = Restaurant.query.filter(Restaurant.name == "Arby's").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonald's").first()
    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id

        resp = c.get(f"/restaurants/restaurant_invalid")

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.location, "/")

  # Tests on menu item details page
