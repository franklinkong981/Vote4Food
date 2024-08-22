"""Tests for creating, reading, updating, and deleting reviews for restaurant ane menu items, as well as viewing the list of
the logged in user's reviews for restaurants and menu items.."""

# To run these tests:
#
# FLASK_ENV=production python3 -m unittest tests/tests_reviews.py

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

    user_tara = User.create_user(
      first_name = "Tara",
      last_name = "Gordon",
      email = "tgordon981@gmail.com",
      user_image_url = "www.testurl2.com",
      password = "PASSWORD2"
    )
    db.session.add_all([user_ted, user_tara])

    # Create sample restaurant
    
    mcdonalds = Restaurant(
      id = "restaurant1",
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
    db.session.add(mcdonalds)

    # Create sample menu item

    big_mac = Item(
      title = "Big Mac",
      restaurant_chain = "McDonalds",
      image_url = "www.mcdonalds.com/big_mac_image.jpg"
    )
    db.session.add(big_mac)

    db.session.commit()

    # Create sample reviews
    ted_mcdonalds_review = Restaurant_Review(
      author_id = user_ted.id,
      restaurant_id = mcdonalds.id,
      title = "My Favorite Restaurant!",
      content = "I really like this place, especially the Big Macs!"
    )

    tara_mcdonalds_review = Restaurant_Review(
      author_id = user_tara.id,
      restaurant_id = mcdonalds.id,
      title = "Meh",
      content = "They have some good items like the Filet o Fish but not a fan of the Big Mac."
    )

    ted_big_mac_review = Item_Review(
      author_id = user_ted.id,
      item_id = big_mac.id,
      title = "One of my Favorite Foods!",
      content = "Its juicy and delicious, and I really like the secret sauce!"
    )

    tara_big_mac_review  = Item_Review(
      author_id = user_tara.id,
      item_id = big_mac.id,
      title = "I Did Not Like It",
      content = "It was bland and had no taste. The lettuce got everywhere and the bun was soggy."
    )
    db.session.add_all([ted_mcdonalds_review, tara_mcdonalds_review, ted_big_mac_review, tara_big_mac_review])

    db.session.commit()
  
  def tearDown(self):
    """After each test, revert table back to original state."""

    db.session.rollback()

  """There are two users: Ted and Tara. There is one restaurant, McDonalds, and one item from McDonalds: The Big Mac. Ted and Tara both
  have one review each of McDonalds and the Big Mac."""

  # Tests for viewing reviews on details pages

  def test_view_restaurant_reviews(self):
    """When a logged in user accesses a restaurant's details page, do they see all the reviews for the restaurant?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h3 class="display-3">All Reviews (2)</h3>', html)
      self.assertIn('<h4 class="display-4">My Favorite Restaurant!</h4>', html)
      self.assertIn("<p>I really like this place, especially the Big Macs!</p>", html)
      self.assertIn('<h4 class="display-4">Meh</h4>', html)
      self.assertIn("<p>They have some good items like the Filet o Fish but not a fan of the Big Mac.</p>", html)
  
  def test_view_item_reviews(self):
    """When a logged in user accesses an item's details page, do they see all the reviews for the menu item?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{big_mac.id}")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h3 class="display-3">All Reviews (2)</h3>', html)
      self.assertIn('<h4 class="display-4">One of my Favorite Foods!</h4>', html)
      self.assertIn("<p>Its juicy and delicious, and I really like the secret sauce!</p>", html)
      self.assertIn('<h4 class="display-4">I Did Not Like It</h4>', html)
      self.assertIn("<p>It was bland and had no taste. The lettuce got everywhere and the bun was soggy.</p>", html)
  
  # Tests for adding reviews

  def test_logged_out_add_restaurant_review(self):
    """When a logged out user tries to access the add restaurant review form, are they redirected to the homepage?"""

    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    with self.client as c:
      resp = c.get(f"/restaurants/{mcdonalds.id}/reviews/create")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_add_restaurant_review_form(self):
    """When a logged in user accesses the add restaurant review form, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}/reviews/create")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Create a New Review for McDonalds.</h2>', html)
      self.assertIn('<button class="btn btn-success">Create Review</button>', html)
  
  def test_add_restaurant_review(self):
    """When a logged in user adds a new restaurant review, is this review added to the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()

    self.assertEqual(len(user_ted.restaurant_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/restaurants/{mcdonalds.id}/reviews/create", data={"title": "My 2nd Review of McDonalds", "content": "I visited this place again and it was as great as ever!"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, f"/restaurants/{mcdonalds.id}")
      self.assertEqual(len(user_ted.restaurant_reviews), 2)

  def test_logged_out_add_item_review(self):
    """When a logged out user tries to access te add menu item review form, are they redirected to the homepage?"""

    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    with self.client as c:
      resp = c.get(f"/items/{big_mac.id}/reviews/create")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

  def test_add_item_review_form(self):
    """When a logged in user accesses the add menu item review form, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{big_mac.id}/reviews/create")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Create a New Review for Big Mac from McDonalds.', html)
      self.assertIn('<button class="btn btn-success">Create Review</button>', html)

  def test_add_item_review(self):
    """When a logged in user adds a new menu item review, is this review added to the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()

    self.assertEqual(len(user_ted.item_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/items/{big_mac.id}/reviews/create", data={"title": "My 2nd Review of the Big Mac", "content": "I had it again and now I love it even more!"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, f"/items/{big_mac.id}")
      self.assertEqual(len(user_ted.item_reviews), 2)
   
  # Tests for ediitng reviews

  def test_logged_out_edit_restaurant_review_form(self):
    """When a logged out user tries to access the edit restaurant review form, are they redirected to the homepage?"""

    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    ted_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "My Favorite Restaurant!").first()

    with self.client as c:
      resp = c.get(f"/restaurants/{mcdonalds.id}/reviews/{ted_mcdonalds_review.id}/update")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_edit__restaurant_review_form(self):
    """When a logged in user accesses the edit restaurant review form for one of their own restaurant reviews, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    ted_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "My Favorite Restaurant!").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}/reviews/{ted_mcdonalds_review.id}/update")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('Edit Your Review for McDonalds.', html)
      self.assertIn('<button class="btn btn-success">Edit Review</button>', html)

  def test_edit_unauthorized_restaurant_review_form(self):
    """When a logged in user tries to access the edit restaurant review form for a restaurant review they didn't write, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    tara_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "Meh").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/restaurants/{mcdonalds.id}/reviews/{tara_mcdonalds_review.id}/update")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

  def test_edit_restaurant_review(self):
    """When a logged in user successfully updates a restaurant review created by them, is the review sucessfully updated in the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    ted_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "My Favorite Restaurant!").first()

    self.assertEqual(len(user_ted.restaurant_reviews), 1)
    self.assertEqual(ted_mcdonalds_review.title, "My Favorite Restaurant!")

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/restaurants/{mcdonalds.id}/reviews/{ted_mcdonalds_review.id}/update", data={"title": "Still My Favorite Restaurant!", "content": "It's so good!"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, f"/restaurants/{mcdonalds.id}")
      self.assertEqual(len(user_ted.restaurant_reviews), 1)
      self.assertEqual(ted_mcdonalds_review.title, "Still My Favorite Restaurant!")
      self.assertEqual(ted_mcdonalds_review.content, "It's so good!")
  
  def test_logged_out_edit_item_review_form(self):
    """When a logged out user tries to taccess the edit menu item review form, are they redirected to the homepage?"""

    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    ted_big_mac_review = Item_Review.query.filter(Item_Review.title == "One of my Favorite Foods!").first()

    with self.client as c:
      resp = c.get(f"/items/{big_mac.id}/reviews/{ted_big_mac_review.id}/update")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def test_edit_item_review_form(self):
    """When a logged in user accesses the edit menu item review form for one of their own menu item reviews, do they see the appropriate form?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    ted_big_mac_review = Item_Review.query.filter(Item_Review.title == "One of my Favorite Foods!").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{big_mac.id}/reviews/{ted_big_mac_review.id}/update")
      html = resp.get_data(as_text=True)

      self.assertEqual(resp.status_code, 200)
      self.assertIn('<h2 class="form-header display-2">Edit Your Review for Big Mac.</h2>', html)
      self.assertIn('<button class="btn btn-success">Edit Review</button>', html)

  def test_edit_unauthorized_itemt_review_form(self):
    """When a logged in user tries to access the edit menu item review form for a restaurant review they didn't write, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    tara_big_mac_review = Item_Review.query.filter(Item_Review.title == "I Did Not Like It").first()

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.get(f"/items/{big_mac.id}/reviews/{tara_big_mac_review.id}/update")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")

  def test_edit_item_review(self):
    """When a logged in user successfully updates a menu item review created by them, is the review sucessfully updated in the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    ted_big_mac_review = Item_Review.query.filter(Item_Review.title == "One of my Favorite Foods!").first()

    self.assertEqual(len(user_ted.item_reviews), 1)
    self.assertEqual(ted_big_mac_review.title, "One of my Favorite Foods!")

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post(f"/items/{big_mac.id}/reviews/{ted_big_mac_review.id}/update", data={"title": "I Love It!", "content": "It's so good!"})

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, f"/items/{big_mac.id}")
      self.assertEqual(len(user_ted.item_reviews), 1)
      self.assertEqual(ted_big_mac_review.title, "I Love It!")
      self.assertEqual(ted_big_mac_review.content, "It's so good!") 

  # Tests for deleting reviews

  def logged_out_delete_restaurant_review(self):
    """When a logged out user tries to delete a review for a restaurant, are they redirected to the home page?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    ted_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "My Favorite Restaurant!").first()

    with self.client as c:
      resp = c.post("/restaurants/{mcdonalds.id}/reviews/{ted_mcdonalds_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def delete_unauthorized_restaurant_review(self):
    """When a logged in user tries to delete a review for a restaurant that isn't theirs, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    user_tara = User.query.filter(User.first_name == "Tara")
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    tara_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "Meh").first()

    self.assertEqual(len(user_tara.restaurant_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/restaurants/{mcdonalds.id}/reviews/{tara_mcdonalds_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_tara.restaurant_reviews), 1)
  
  def delete_restaurant_review(self):
    """When a logged in user delets a review for a restaurant that they created, is the review successfully deleted in the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    mcdonalds = Restaurant.query.filter(Restaurant.name == "McDonalds").first()
    ted_mcdonalds_review = Restaurant_Review.query.filter(Restaurant_Review.title == "My Favorite Restaurant!").first()

    self.assertEqual(len(user_ted.restaurant_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/restaurants/{mcdonalds.id}/reviews/{ted_mcdonalds_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.restaurant_reviews), 0)

  def logged_out_delete_item_review(self):
    """When a logged out user tries to delete a review for a menu item, are they redirected to the home page?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    ted_big_mac_review = Item_Review.query.filter(Item_Review.title == "One of my Favorite Foods!").first()

    with self.client as c:
      resp = c.post("/items/{big_mac.id}/reviews/{ted_big_mac_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
  
  def delete_unauthorized_item_review(self):
    """When a logged in user tries to delete a review for a menu item that isn't theirs, are they redirected to the homepage?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    user_tara = User.query.filter(User.first_name == "Tara")
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    tara_big_mac_review = Item_Review.query.filter(Item_Review.title == "I Did Not Like It").first()

    self.assertEqual(len(user_tara.item_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/items/{big_mac.id}/reviews/{tara_big_mac_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_tara.item_reviews), 1)

  def delete_item_review(self):
    """When a logged in user delets a review for a menu item that they created, is the review successfully deleted in the database?"""

    user_ted = User.query.filter(User.first_name == "Ted").first()
    big_mac = Item.query.filter(Item.title == "Big Mac").first()
    ted_big_mac_review = Item_Review.query.filter(Item_Review.title == "One of my Favorite Foods!").first()

    self.assertEqual(len(user_ted.item_reviews), 1)

    with self.client as c:
      # simulate user_ted logging in
      with c.session_transaction() as sess:
        sess[CURRENT_USER_KEY] = user_ted.id
      
      resp = c.post("/restaurants/{big_mac.id}/reviews/{ted_big_mac_review.id}/delete")

      self.assertEqual(resp.status_code, 302)
      self.assertEqual(resp.location, "/")
      self.assertEqual(len(user_ted.item_reviews), 0)

  # Tests for viewing list of user's own reviews
