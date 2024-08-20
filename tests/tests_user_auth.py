"""Tests for the features of Vouch4Food that have to do with user authentication such as signup, login, and logout."""

# To run these tests:
#
# FLASK_ENV=production python3 -m unittest tests/tests_user_auth.py

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

class UserAuthTestCase(TestCase):
  """Test views that have to do with user authentication (signup, login, logout)."""

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
  
  # Homepage tests

  def test_logged_out_homepage(self):
    """When a logged out user visits the homepage, do they see the proper anonymous homepage?"""

    with self.client as c:
      resp = c.get("/")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h3 class="display-3">Welcome to Vouch4Food!</h3>', html)
      self.assertIn('<h4 class="display-4">Review your favorite restaurants and menu items today!</h4>', html)
  
  def test_logged_in_homepage(self):
    """When a logged in user visits the homepage, do they see the proper homepage?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
    
      resp = c.get("/")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Log Out', html)
      self.assertIn('<h2 class="welcome-headline display-2">Welcome, Ted Abigail!</h2>', html)
      self.assertIn('<p>You do not yet have a current location.</p>', html)
  
  # Signup tests
  
  def test_logged_out_signup_page(self):
    """When a logged out user visits the signup page, do they see the signup form?"""

    with self.client as c:
      resp = c.get("/signup")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Create an account to Vouch 4 Food today.</h2>', html)
      self.assertIn('<button class="btn btn-success">Create account</button>', html)
  
  def test_logged_in_signup_page(self):
    """When a logged in user visits the signup page, are they redirected to the home page?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id

      resp = c.get("/signup")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_create_account(self):
    """Can a new user create a new account?"""

    with self.client as c:
      all_users = User.query.all()
      self.assertEqual(len(all_users), 2)

      resp = c.post("/signup", data={"first_name": "Franklin", "last_name": "Kong", "email": "franklinkong981@gmail.com", "user_image_url": "www.testurl3.com", "password": "PASSWORD3"})
      
      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/login")

      # Is the new user added to the database?
      all_users = User.query.all()
      self.assertEqual(len(all_users), 3)
  
  # Login 
  
  def test_logged_out_login_page(self):
    """When a logged out user visits the login page, do they see the login form?"""

    with self.client as c:
      resp = c.get("/login")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Login to start Vouching 4 Food</h2>', html)
      self.assertIn('<button class="btn btn-success">Log In</button>', html)
  
  def test_logged_in_login_page(self):
    """When a logged in user tries to visit the login page, are they redirected back to the home page?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id

      resp = c.get("/login")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

  def test_login_user(self):
    """Can a user successfully log in?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      resp = c.post("/login", data={"email": "teddybear@gmail.com", "password": "PASSWORD1"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

      # Is the logged in user's id added to the session?
      with c.session_transaction() as sess:
        self.assertEqual(sess[CURRENT_USER_KEY], user_ted.id)

  # Logout tests

  def test_logged_out_logout(self):
    """If a logged out user tries log out, are they redirected back to the home page?"""

    with self.client as c:
      resp = c.get("/logout")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_logout(self):
    """When a logged in user tries to log out, are they redirected back to the home page?"""

    user_ted = User.query.filter(User.first_name == 'Ted').first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get("/logout")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

      # Is user_ted's id removed from the session?
      with c.session_transaction() as sess:
        self.assertNotIn(CURRENT_USER_KEY, sess)
      

  


