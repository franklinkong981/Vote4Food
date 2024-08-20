"""Tests for the features of Vouch4Food that have to do with user profile information as well as updating profile information
such as first name, last name, and password."""

# To run these tests:
#
# FLASK_ENV=production python3 -m unittest tests/tests_profile.py

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
    """Before each test, delete any existing data in the tables, create test client, store sample user in users table."""
    
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

    user_tara = User.create_user(
      first_name = "Tara",
      last_name = "Gordon",
      email = "tgordon981@gmail.com",
      user_image_url = "www.testurl2.com",
      password = "PASSWORD2"
    )

    db.session.commit()
  
  def tearDown(self):
    """After each test, revert table back to original state."""

    db.session.rollback()
  
  # User profile page tests

  def test_logged_out_profile_page(self):
    """When a logged out user tries to access the logged in user profile page, are they redirected to the homepage?"""

    with self.client as c:
      resp = c.get("/users/profile")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_logged_in_profile_page(self):
    """When a logged in user accesses their profile page, do they see the correct information?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get("/users/profile")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h4 class="display-4">Account Information</h4>', html)
      # Make sure buttons to edit specific information are included.
      self.assertIn('Update Profile Information', html)
      self.assertIn('Update Password', html)
      self.assertIn('<p>You do not yet have a current location.</p>', html)
      self.assertIn('Set current location.', html)

  # Edit profile tests

  def test_logged_out_update_profile_page(self):
    """When a logged out user tries to  access the update profile page, are they redirected to the homepage?"""

    with self.client as c:
      resp = c.get("/users/profile/update")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_logged_in_update_profile_page(self):
    """When a logged in user accesses the update profile page, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get("/users/profile/update")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Edit Profile Information.</h2>', html)
      self.assertIn('<p>To confirm changes, enter your current password:</p>', html)
      self.assertIn('<button class="btn btn-success">Update Profile</button>', html)
  
  def test_update_profile(self):
    """When a user updates their profile with valid information, is their information appropriately updated?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()
    user_ted_id = user_ted.id

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/users/profile/update", data={"first_name": "Fred", "last_name": "Abigail", "email": "teddybear@gmail.com", "user_image_url": "www.testurl1.com", "current_password": "PASSWORD1"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/users/profile")

      # Was the information changed?
      user_fred = User.query.filter(User.first_name == 'Fred').first()
      self.assertEqual(user_fred.id, user_ted_id)

  # Change password tests

  def test_logged_out_update_password_page(self):
    """When a logged out user tries to  access the change password page, are they redirected to the homepage?"""

    with self.client as c:
      resp = c.get("/users/profile/update_password")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_logged_in_update_password_page(self):
    """When a logged in user accesses the update change password page, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get("/users/profile/update_password")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Change Password Below.</h2>', html)
      self.assertIn('<button class="btn btn-success">Change Password</button>', html)
  
  def test_change_password(self):
    """When a logged in user changes their password successfully, is their password updated?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/users/profile/update_password", data={"current_password": "PASSWORD1", "new_password": "CHANGED_PASSWORD"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/users/profile")

      # Was the password updated?
      self.assertFalse(User.confirm_password(user_ted.id, "PASSWORD1"))
      self.assertTrue(User.confirm_password(user_ted.id, "CHANGED_PASSWORD"))


