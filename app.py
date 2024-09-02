"""Main application file for the Vouch4Food application that contains all the imports, routes, and view functions wrapped up in a
create_app function to create separate instances/application contexts for development and testing."""

import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from forms.authenticate_forms import SignUpForm, LoginForm
from forms.profile_forms import EditProfileForm, ChangePasswordForm, SetLocationForm
from forms.review_forms import ReviewForm

from models.init_db import db
from models.user import User
from models.restaurant import Restaurant, Restaurant_Favorite, Restaurant_Review
from models.item import Item, Item_Favorite, Item_Review
from models.connect import connect_db

from api_helpers import get_address_info, get_restaurant_search_results, get_menu_items_json, get_menu_items_only

from helpers.restaurant_helpers import build_restaurant_address_string, build_restaurant_cuisine_string, format_restaurant_phone_number, get_restaurant_photo_url
from helpers.menu_item_helpers import does_item_belong_to_restaurant

"""This key will be in the Flask session and contain the logged in user's id once a user successfully logs in, will be removed once a user
successfully logs out."""
CURRENT_USER_KEY = "logged_in_user"
GO_BACK_URL = "back_url"

def create_app(db_name, testing=False):
    """Create an instance of the app to ensure separate production database and testing database, and that sample data inserted into
    database for unit/integration testing purposes doesn't interfere with actual database for production."""
    app = Flask(__name__)
    app.testing = testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    toolbar = DebugToolbarExtension(app)
    if app.testing:
        # Database used for testing is local, not development/production database on Supabase.
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql:///{db_name}'
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        # Get DB_URI from environ variable (useful for production/testing) or,
        # if not set there, use development local db.
        app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', f'postgresql:///{db_name}'))
        app.config['SQLALCHEMY_ECHO'] = True
    
    #Routes and view functions for the application.

    ##############################################################################
    # Functions for user authentication, aka signing up, logging in, and logging out. Also functions on g object.

    @app.before_request
    def add_user_to_g_object():
        """Before sending each request, a user is currently logged in, add the logged in user's instance to the Flask g object."""

        if CURRENT_USER_KEY in session:
            g.user = User.query.get_or_404(session[CURRENT_USER_KEY])
        else:
            g.user = None
    
    @app.before_request
    def add_back_url_to_g_object():
        """This adds the URL to the g object so that submission of the update location form takes user to the page they previously visited."""

        if GO_BACK_URL in session:
            g.back_url = session[GO_BACK_URL]
        else:
            g.back_url = None
    
    def login_user(user):
        """Add user's id to the Flask session to indicate that this user is currently logged in."""

        session[CURRENT_USER_KEY] = user.id
    
    def logout_user():
        """Remove the previously logged in user's id from the Flask session to indicate no user is currently logged in."""

        del session[CURRENT_USER_KEY]
    
    @app.route('/signup', methods=['GET', 'POST'])
    def handle_signup():
        """If GET request, display user signup form. If POST request (user has submitted signup form), create a new User model instance,
         add the new user to the database, and redirect user to login form. If errors occur (ex. email already taken by another user),
         redirect to signup form with error message."""

        # If user is already signed in, redirect to their home page.
        if g.user:
            flash("You already have an account and are signed in", "danger")
            return redirect('/')

        form = SignUpForm()

        if form.validate_on_submit():
            try:
                new_user = User.create_user(
                    first_name = form.first_name.data,
                    last_name = form.last_name.data,
                    email = form.email.data,
                    user_image_url = form.user_image_url.data or User.user_image_url.default.arg,
                    password = form.password.data
                )
                db.session.commit()

                # If user successfully signs up, redirect them to login page and prompt them to sign in.
                flash("Your account has been successfully created! Now please log in.", "success")
                return redirect('/login')
            except IntegrityError as exc:
                # Only possible error not covered by WTForms validation is uniqueness of the email.
                flash("The email you inputted already has an account associated with it", "danger")
                print(f"ERROR: {exc}")
            except:
                # Issue with connecting to SQLAlchemy database.
                flash("There was an error in connecting/accessing the database. Please try again later.", "danger")

        return render_template('users/signup.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
    def handle_login():
        """If GET request, display user login form. If POST request (user has submitted login form), attempt to login user. If successful,
        redirect to signed in homepage. If errors occur (can't find email in database or hashed password doesn't match), redirect to
        login form with error message."""
        
        # If user is already signed in, redirect to their home page.
        if g.user:
            flash("You already have an account and are signed in", "danger")
            return redirect('/')

        form = LoginForm()

        if form.validate_on_submit():
            try:
                user = User.authenticate_user(form.email.data, form.password.data)

                # user = 0 if email isn't found, 1 if email is found but password doesn't match.
                if user != 0 and user != 1:
                    login_user(user)
                    flash(f"Hello, {user.get_full_name()}!", "success")
                    return redirect("/")
                elif user == 0:
                    flash("The email you entered is not associated with any current account.", "danger")
                else:
                    # user == 1
                    flash("The password you entered is incorrect.", "danger")
            except:
                # Issue with connecting to SQLAlchemy database.
                flash("There was an error in connecting/accessing the database. Please try again later.", "danger")
        
        return render_template('users/login.html', form=form)
    
    @app.route('/logout')
    def handle_logout():
        """Sign out the user and redirect them to the signed out homepage."""

        if not g.user:
            flash("You already were not signed in", "danger")
            return redirect("/")

        logout_user()
        # Empty the nearby restaurants array so when another user signs in, their nearby restaurants will be recalculated.
        CURRENT_RESTAURANTS_NEARBY.clear()
        flash("Successfully logged out.", "success")
        return redirect("/")

    ##############################################################################
    # Routes relevant to the logged in user, such as user profile information, user's reviews, and user's favorite restaurants/menu items.

    @app.route('/users/favorites/restaurants')
    def show_favorited_restaurants():
        """Shows a list of the currently logged in user's favorited restaurant locations."""

        if not g.user:
            flash("Please sign in to view your favorited restaurants", "danger")
            return redirect("/")
        
        number_favorites = len(list(g.user.favorite_restaurants))
        return render_template("/users/favorites/restaurants.html", favorites=g.user.favorite_restaurants, number_favorites=number_favorites)
    
    @app.route('/users/favorites/items')
    def show_favorited_items():
        """Shows a list of the currently logged in user's favorited menu items."""

        if not g.user:
            flash("Please sign in to see your favorited menu items", "danger")
            return redirect("/")
        
        number_favorites = len(list(g.user.favorite_items))
        
        return render_template("/users/favorites/items.html", favorites=g.user.favorite_items, number_favorites=number_favorites)
    
    @app.route('/users/reviews/restaurants')
    def show_restaurant_reviews():
        """Shows a list of the currently logged in user's reviews for restaurant locations."""

        if not g.user:
            flash("Please sign in to view your restaurant reviews", "danger")
            return redirect("/")
        
        session[GO_BACK_URL] = request.path
        
        # get all of the logged in user's restaurant reviews, newest first.
        restaurant_reviews = Restaurant_Review.query.filter(Restaurant_Review.author_id == g.user.id).order_by(desc(Restaurant_Review.created_at))

        return render_template("/users/reviews/restaurants.html", reviews=restaurant_reviews)
    
    @app.route('/users/reviews/items')
    def show_item_reviews():
        """Shows a list of the currently logged in user's reviews for menu items."""

        if not g.user:
            flash("Please sign in to view your menu item reviews", "danger")
            return redirect("/")
        
        session[GO_BACK_URL] = request.path

        # get all of the logged in user's menu item reviews, newest first.
        item_reviews = Item_Review.query.filter(Item_Review.author_id == g.user.id).order_by(desc(Item_Review.created_at))

        return render_template("/users/reviews/items.html", reviews=item_reviews)


    @app.route('/users/profile')
    def show_profile_info():
        """Shows information about the current logged in user, including the user's name, email, and location if they have one."""

        if not g.user:
            flash("Please sign in to view your profile information", "danger")
            return redirect("/")
        
        # There are multiple pages where you can access the update location form. This is to store the current url so user can easily
        # go back to the page they came from if they decide not to update their location.
        session[GO_BACK_URL] = request.path
        
        return render_template("/users/profile.html")

    @app.route('/users/profile/update', methods=['GET', 'POST'])
    def update_profile_form():
        """Show the form that allows the logged in user to edit their profile information. They must enter their current password
        for the form to submit and the changes to be saved."""

        if not g.user:
            flash("Please sign in to update your profile information", "danger")
            return redirect("/")
        
        form = EditProfileForm(obj=g.user)
        if form.validate_on_submit():
            # Need to make current password user entered matches before proceeding with editing profile information.
            if User.confirm_password(session[CURRENT_USER_KEY], form.current_password.data):
                g.user.first_name = form.first_name.data
                g.user.last_name = form.last_name.data
                g.user.email = form.email.data
                g.user_image_url = form.user_image_url.data or None

                try:
                    db.session.commit()

                    flash("Profile successfully updated", "success")
                    return redirect("/users/profile")
                except IntegrityError as exc:
                    # If IntegrityError occurs, only problem not covered by form validation is non-unique email.
                    flash("Unable to update profile, new email entered is already associated with another account", "danger")
                    print(f"ERROR: {exc}")
                except:
                    # Issue with connecting to SQLAlchemy database.
                    flash("There was an error in connecting/accessing the database. Please try again later.", "danger")  
            else:
                flash("The current password you entered does not match the current password associated with your account", "danger")

        return render_template("users/edit.html", form=form)

    @app.route('/users/profile/update_password', methods=['GET', 'POST'])
    def update_password():
        """Show the form that allows the logged in user to update their password. They must enter a new password and their current password
        for the password to be successfully updated."""

        if not g.user:
            flash("Please sign in to update your password", "danger")
            return redirect("/")

        form = ChangePasswordForm()
        if form.validate_on_submit():
            # Need to make current password user entered matches before proceeding with updating password.
            if User.confirm_password(session[CURRENT_USER_KEY], form.current_password.data):
                User.update_password(session[CURRENT_USER_KEY], form.new_password.data)

                try:
                    db.session.commit()

                    flash("Password successfully updated", "success")
                    return redirect("/users/profile")
                except:
                    # Issue with connecting to SQLAlchemy database.
                    flash("There was an error in connecting/accessing the database. Please try again later.", "danger")
            else:
                flash("The current password you entered does not match the current password associated with your account", "danger")
        
        return render_template("users/edit_password.html", form=form)
    
    ##############################################################################
    # Routes/functions relevant to setting/updating the logged in user's locations and storing a list of nearby restaurant locations.

    # Stores the list of restaurant locations near the user's set location (zip code, latitude, and longitude) that will be displayed
    # on the user's home page.
    CURRENT_RESTAURANTS_NEARBY = []

    def store_nearby_restaurants(restaurants):
        """Extract the important information about each restaurant near the user's current location such as opening hours,
        name, etc. and store them in an array."""

        CURRENT_RESTAURANTS_NEARBY.clear()
        for restaurant in restaurants:
            store_nearby_restaurant(restaurant)
        
        # If CURRENT_RESTAURANTS_NEARBY is still empty at this point, that means there are no registered restaurants near the user's
        # location. Append something to indicate this.
        if len(CURRENT_RESTAURANTS_NEARBY) == 0:
            CURRENT_RESTAURANTS_NEARBY.append("NO RESTAURANTS NEARBY")
    
    def store_nearby_restaurant(restaurant):
        """restaurant is a JSON Restaurant object returned from the Spoonacular API. This function extracts the useful data from it,
        processes them into more readable formats, and appends it to an array that stores all restaurants near the user's current location."""

        restaurant_data = {
            'id': restaurant['_id'],
            'name': restaurant['name'],
            'address': build_restaurant_address_string(restaurant['address']),
            'latitude': restaurant['address']['latitude'],
            'longitude': restaurant['address']['longitude'],
            'cuisines': build_restaurant_cuisine_string(restaurant["cuisines"]),
            'description': restaurant["description"] or None,
            'phone': restaurant["phone_number"] if "phone_number" in restaurant else None,
            'hours': restaurant['local_hours']['operational'] or None,
            'photo_url': get_restaurant_photo_url(restaurant)
        }
        CURRENT_RESTAURANTS_NEARBY.append(restaurant_data)
    
    def get_and_store_nearby_restaurants():
        """This method is called after the user either sets or updates their location by entering their current zip code on their home
        or profile information page. This calls the Spoonacular API to get a list of nearby restaurants as JSON, and stores important 
        information about each Restaurant JSON object returned into the CURRENT_RESTAURANTS_NEARBY array."""

        # get list of restaurants near the location the user just set 
        nearby_restaurants_data = get_restaurant_search_results("", g.user.location_lat, g.user.location_long)

        # Store nearby restaurants in the array.
        store_nearby_restaurants(nearby_restaurants_data)
    
    @app.route('/users/profile/update_location', methods=['GET', 'POST'])
    def update_location():
        """Show the form that allows the logged in user to update their location by entering their 5-digit zip code. The zip code will then
        be transformed into latitude and longitude coordinates. 
        The Spoonacular API will then be called to get a list of restaurants near the zip code entered, which will be displayed on the
        user's home page."""

        if not g.user:
            flash("Please sign in to update your location", "danger")
            return redirect("/")
        
        form = SetLocationForm()
        if form.validate_on_submit():
            try:
                # Use Position Stack Geolocation API to turn zip code from form into latitude and longitude.
                zip_code = form.address_zip.data
                address_coords = get_address_info(zip_code)
                
                # Update logged in user's zip code, latitude, and longitude in the database.
                g.user.address_zip = zip_code
                g.user.location_lat = address_coords['latitude']
                g.user.location_long = address_coords['longitude']
                db.session.commit()

                flash("Location successfully updated!", "success")

                # Get and save restaurants nearby the zip code the user just entered.
                get_and_store_nearby_restaurants()

                # Save/update restaurant information in the database
                add_new_restaurants_to_db(CURRENT_RESTAURANTS_NEARBY)
                db.session.commit()

                flash("Restaurants nearby generated and saved to database", "success")

                if not g.back_url:
                    return redirect("/")
                return redirect(g.back_url)
            except ValueError as exc:
                flash("Unable to update location, the zip code you entered is not a registered US postal code. Please try again.", "danger")
                print(f"ERROR: {exc}")
            except Exception as exc:
                # Issue with connecting to SQLAlchemy database or Geolocation API.
                flash("There was an error in connecting/accessing the database. Please try again later.", "danger")
                print(f"ERROR: {exc}")
        
        return render_template("users/edit_location.html", form=form)

    ##############################################################################
    # Routes relevant to searching for restaurants, mainly through the restaurant search bar in the navbar.

    # Keeps the results of the most recent restaurant search query stored so it persists across different routes/redirects.
    CURRENT_RESTAURANT_SEARCH_RESULTS = []
    
    def store_restaurant_search_results(restaurants):
        """Extract the important information about each restaurant in the most recent restaurant search results such as opening hours,
        name, etc. and store them in an array."""

        CURRENT_RESTAURANT_SEARCH_RESULTS.clear()
        for restaurant in restaurants:
            store_restaurant_search_result(restaurant)
    
    def store_restaurant_search_result(restaurant):
        """restaurant is a JSON Restaurant object returned from the Spoonacular API. This function extracts the useful data from it,
        processes them into more readable formats, and appends it to an array that stores all search results."""

        restaurant_data = {
            'id': restaurant['_id'],
            'name': restaurant['name'],
            'address': build_restaurant_address_string(restaurant['address']),
            'latitude': restaurant['address']['latitude'],
            'longitude': restaurant['address']['longitude'],
            'cuisines': build_restaurant_cuisine_string(restaurant["cuisines"]),
            'description': restaurant["description"] or None,
            'phone': format_restaurant_phone_number(restaurant["phone_number"]),
            'hours': restaurant['local_hours']['operational'] or None,
            'photo_url': get_restaurant_photo_url(restaurant)
        }
        CURRENT_RESTAURANT_SEARCH_RESULTS.append(restaurant_data)
    
    def add_new_restaurants_to_db(restaurants):
        """Add all new restaurants from search results into the Restaurant database."""
        
        for restaurant in restaurants:
            add_or_update_new_restaurant(restaurant)
    
    def add_or_update_new_restaurant(restaurant):
        """Search for the restaurant by id in the Vouch4Food Restaurant database. If not found, add it to the database.
        If found, check for information to update."""

        database_restaurant = Restaurant.query.get(restaurant['id'])

        if not database_restaurant:
            Restaurant.create_restaurant(restaurant)
        else:
            database_restaurant.update_restaurant(restaurant)


    @app.route("/restaurants/add", methods=["POST"])
    def add_restaurants_to_db():
        """This route consists of 4 steps:
        1. Calls the PositionStack API to return a longitude and latitude corresponding to the zip code the user typed in.
        2. Calls the Spoonacular API to search for all restaurants that match the search query and are located near the zip code.
        3. Extracts several pieces of useful information from each restaurant object in the JSON response and stores them for persistence.
        4. Adds each restaurant whose id isn't found in the database into the vouch4Food database as a Restaurant object.
            If the id is found, update the restaurant information if any data in the JSON for that restaurant has changed."""
        
        if not g.user:
            flash("Please sign in to search for restaurants", "danger")
            return redirect("/")
        
        try:
            # Step 1
            zip_code = request.form['zip_code']
            coords = get_address_info(zip_code)

            # Step 2
            search_term = request.form['query']
            restaurants_data = get_restaurant_search_results(search_term, coords['latitude'], coords['longitude'])

            # Step 3
            store_restaurant_search_results(restaurants_data)

            # Step 4
            add_new_restaurants_to_db(CURRENT_RESTAURANT_SEARCH_RESULTS)
            db.session.commit()

            flash("Search successful, new restaurants successfully added to database","success")
            return redirect("/restaurants")
        except ValueError as exc:
            flash("The zip code you entered is not a registered US postal code. Please try again.", "danger")
            print(f"ERROR: {exc}")
        except:
            flash("There was trouble connecting to the database and/or the PositionStack and Spoonacular APIs. Please try again later", "danger")
        
        redirect_url = request.referrer or "/"
        return redirect(redirect_url)


    @app.route("/restaurants")
    def show_restaurant_search_results():
        """Displays each restaurant in the search results each with a link to a page containing more information about that restaurant."""

        if not g.user:
            flash("Please sign in to search for restaurants", "danger")
            return redirect("/")

        return render_template('/restaurants/search.html', number_results=len(CURRENT_RESTAURANT_SEARCH_RESULTS), restaurant_results=CURRENT_RESTAURANT_SEARCH_RESULTS)

    ##############################################################################
    # Routes relevant to restaurant pages, including adding/removing a restaurant from the user's favorites and creating, editing, 
    # and deleting a review for the restaurant.

    @app.route("/restaurants/<restaurant_id>")
    def display_restaurant_page(restaurant_id):
        """Displays detailed restaurant information of a restaurant with a particular id. This restaurant should be one that has already
        come up in a previous search result by any user. The page should display detailed information like the restaurant's opening hours
        and have a button for the user to add the restaurant to their list of favorite restaurants. It should also list all reviews
        of the restaurant with most recent first, and have links for the user to create, edit, and delete their own reviews.
        Finally, there will be a link to take the user to a list of the restaurant's menu items."""

        if not g.user:
            flash("Please sign in to see details for a restaurant", "danger")
            return redirect("/")
        
        session[GO_BACK_URL] = request.path
        
        # returns a 404 error if the restaurant isn't found in the database.
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        # Get all reviews for this restaurant location, newest first.
        restaurant_reviews = Restaurant_Review.query.filter(Restaurant_Review.restaurant_id == restaurant_id).order_by(desc(Restaurant_Review.created_at))

        return render_template('/restaurants/details.html', restaurant=restaurant, restaurant_reviews=restaurant_reviews)
    
    @app.route("/restaurants/<restaurant_id>/favorite", methods=["POST"])
    def toggle_restaurant_to_favorites(restaurant_id):
        """Adds the restaurant to the list of the current logged in user's favorites or removes it if the logged in user currently
        has it in their favorites."""

        if not g.user:
            flash("Please sign in to add a restaurant to your list of favorites", "danger")
            return redirect("/")
        
        favorited_restaurant = Restaurant.query.get_or_404(restaurant_id)

        try:
            if favorited_restaurant in g.user.favorite_restaurants:
                g.user.favorite_restaurants = [restaurant for restaurant in g.user.favorite_restaurants if restaurant != favorited_restaurant]
                flash("Restaurant successfully removed from favorites!", "success")
            else:
                g.user.favorite_restaurants.append(favorited_restaurant)
                flash("Restaurant successfully added to favorites", "success")
            
            db.session.commit()
        except:
            flash("Unable to connect to/access the database. Please try again later.", "danger") 

        redirect_url = request.referrer or "/"
        return redirect(redirect_url)
    
    @app.route("/restaurants/<restaurant_id>/reviews/create", methods=["GET", "POST"])
    def create_restaurant_review(restaurant_id):
        """Creates a new review from the logged in user for the restaurant with the id of restaurant_id."""

        if not g.user:
            flash("Please sign in to review a restaurant", "danger")
            return redirect("/")
        
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        form = ReviewForm()

        if form.validate_on_submit():
            try:
                new_review = Restaurant_Review(
                    author_id = g.user.id,
                    restaurant_id = restaurant_id,
                    title = form.title.data,
                    content = form.content.data
                )
                db.session.add(new_review)
                db.session.commit()

                flash(f"New review for {restaurant.name} successfully added", "success")
                return redirect(f"/restaurants/{restaurant.id}")
            except:
                flash("Unable to add review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")
        
        return render_template("/restaurants/add_review.html", restaurant=restaurant, form=form)
    
    @app.route("/restaurants/<restaurant_id>/reviews/<int:review_id>/update", methods=["GET", "POST"])
    def update_restaurant_review(restaurant_id, review_id):
        """Updates a particular review for a particular restaurant as long as the review being updated was written by the 
        logged in user currently updating it."""

        if not g.user:
            flash("Please sign in to edit your restaurant reviews", "danger")
            return redirect("/")
        
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        review = Restaurant_Review.query.get_or_404(review_id)
        # Only allow users to edit their own restaurant reviews
        if review.author.id != g.user.id:
            flash("You can only edit reviews that you created!", "danger")
            redirect_url = request.referrer or "/"
            return redirect(redirect_url)

        form = ReviewForm(obj=review)
        if form.validate_on_submit():
            try:
                review.title = form.title.data
                review.content = form.content.data

                db.session.commit()

                flash(f"Review for {restaurant.name} successfully updated", "success")
                return redirect(f"/restaurants/{restaurant_id}")
            except:
                flash("Unable to edit review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")

        return render_template("/restaurants/edit_review.html", restaurant=restaurant, form=form)
    
    @app.route("/restaurants/<restaurant_id>/reviews/<int:review_id>/delete", methods=["POST"])
    def delete_restaurant_review(restaurant_id, review_id):
        """Deletes a restaurant review as long as it was written by the currently logged in user."""

        if not g.user:
            flash("Please sign in to delete your restaurant reviews", "danger")
            return redirect("/")
        
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        review = Restaurant_Review.query.get_or_404(review_id)
        # Only allow users to delete their own restaurant reviews
        if review.author.id != g.user.id:
            flash("You can only delete reviews that you created!", "danger")
            redirect_url = request.referrer or "/"
            return redirect(redirect_url)
        
        try:
            db.session.delete(review)
            db.session.commit()

            flash(f"Your review for {restaurant.name} was successfully deleted!", "success")
        except:
            flash("Unable to delete review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")

        redirect_url = request.referrer or "/"
        return redirect(redirect_url)
    
    ##############################################################################
    # Routes relevant to the menu item search page, which lists out the menu items belonging to a specific chain restaurant.

    # Keeps important information about menu items belonging to a particular chain restaurant so that results can easily be displayed.
    CURRENT_MENU_ITEMS = []

    def store_all_menu_items(restaurant_id):
        """Stores all menu items belonging to a certain chain restaurant into the array CURRENT_MENU_ITEMS. It gets all menu items
        as JSON objects from the Spoonacular API and then extracts important information from each object, which it stores in another
        object and adds to the CURRENT_MENU_ITEMS array."""

        CURRENT_MENU_ITEMS.clear()
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        
        # Get total number of menu items in search results to see how many offsets you need to call to get JSON for all menu items.
        initial_item_json = get_menu_items_json(restaurant.name, 0)
        total_items = initial_item_json['totalMenuItems']

        # In Spoonacular, if the first menu item in search results doesn't belong to the restaurant with restaurant_id, then
        # there are no menu items that belong to it.
        if total_items > 0 and does_item_belong_to_restaurant(initial_item_json['menuItems'][0], restaurant.name):
            store_menu_items(initial_item_json['menuItems'], restaurant.name)
            store_additional_menu_items(restaurant.name, total_items)
    
    def store_additional_menu_items(restaurant_chain, total_items):
        """When searching for menu items from a specific restaurant chain, multiple calls to the Spoonacular API may need to be made,
        since each call to return menu items from this API returns a maximum of 100 results. This function calls the API as many times
        as needed with offsets to get all menu items based on the total menu items belonging to the restaurant then stores them."""

        offset = 100
        while offset < total_items:
            menu_items_raw = get_menu_items_only(restaurant_chain, offset)
            store_menu_items(menu_items_raw, restaurant_chain)
            offset += 100
    
    def store_menu_items(raw_menu_items_list, restaurant_name):
        """Extracts important information like name, etc. from each menu item (which is represented in JSON) in the raw_menu_items_list
        and stores it in the CURRENT_MENU_ITEMS array."""

        for item in raw_menu_items_list:
            store_menu_item(item, restaurant_name)
    
    def store_menu_item(item, restaurant_name):
        """Item is an object that contains attributes of a specific menu item. If the item belongs to the chain restaurant restaurant_name, 
        this function extracts the id of the item, its name, the restaurant chain it belongs to, and the url for a photo of it. 
        It wraps these attributes into an object and appendsthe object to the CURRENT_MENU_ITEMS array."""

        if item['restaurantChain'] == restaurant_name:
            menu_item_data = {
            'id': item['id'],
            'title': item['title'],
            'restaurant_chain': item['restaurantChain'] or None,
            'image_url': item['image'] or None
            }
            CURRENT_MENU_ITEMS.append(menu_item_data)
    
    def add_new_menu_items_to_db(menu_items):
        """Add all new menu items from search results into the Item database."""
        
        for menu_item in menu_items:
            add_or_update_new_item(menu_item)
    
    def add_or_update_new_item(item):
        """Search for the item by id in the Vouch4Food Item database. If not found, add it to the database.
        If found, check for information to update."""

        database_item = Item.query.get(item['id'])

        if not database_item:
            Item.create_item(item)
        else:
            database_item.update_item(item)

    @app.route("/restaurants/<restaurant_id>/items/add", methods=["POST"])
    def add_menu_items_to_db(restaurant_id):
        """This route is triggered after the user clicks on the button to list out menu items belonging to a particular chain restaurant.
        It does the following steps:
        1. Get all menu items from the particular chain restaurant by calling the menu item search route in Spoonacular API. Since the API
        returns a maximum of 100 items per response, makes additional calls to ensure all menu items are returned.
        2. Each time a response is returned, extract important information like id, photo_url, etc. for each menu item that belongs to 
        the chain restaurant and appends it as an object to the CURRENT_MENU_ITEMS array.
        3. For each menu item, either adds it to the database as a new Item or checks if there is any information to update if the item
        already exists in the database."""

        if not g.user:
            flash("Please sign in to search for a restaurant's menu items", "danger")
            return redirect("/")
        
        try:
            # Step 1 and 2
            store_all_menu_items(restaurant_id)

            # Step 3
            add_new_menu_items_to_db(CURRENT_MENU_ITEMS)
            db.session.commit()

            flash("New menu items successfully added to database","success")
            return redirect(f"/restaurants/{restaurant_id}/items")
        except:
            flash("There was trouble connecting to the database and/or the Spoonacular API. Please try again later", "danger")
        
        redirect_url = request.referrer or "/"
        return redirect(redirect_url)
    
    @app.route("/restaurants/<restaurant_id>/items")
    def show_menu_item_results(restaurant_id):
        """Displays each item belonging to the restaurant with restaurant_id, each with a link to a page containing more information about that menu item.
        The menu items are listed out in alphabetical order."""

        if not g.user:
            flash("Please sign in to search for menu items wihin a restaurant", "danger")
            return redirect("/")
        
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        menu_items = Item.query.filter(Item.restaurant_chain == restaurant.name).order_by(Item.title)
        number_menu_items = Item.query.filter(Item.restaurant_chain == restaurant.name).count()

        return render_template('/items/search.html', restaurant=restaurant, number_results=number_menu_items, menu_item_results=menu_items)

    ##############################################################################
    # Routes relevant to menu item pages, including adding/removing a menu item from the user's favorites and creating, editing, 
    # and deleting a review for a menu item.
    
    @app.route("/items/<int:item_id>")
    def display_item_page(item_id):
        """Displays detailed information of a particular menu item. The page should have some information about the item. 
        There should also be buttons/links for the user to add/remove the item from their favorites and for a user to create,
        update, and delete their own reviews for the item."""

        if not g.user:
            flash("Please sign in to see details for a specific menu item", "danger")
            return redirect("/")
        
        session[GO_BACK_URL] = request.path
        
        # returns a 404 error if the menu item isn't found in the database.
        item = Item.query.get_or_404(item_id)
        # Get all reviews for this menu item, newest first.
        item_reviews = Item_Review.query.filter(Item_Review.item_id == item_id).order_by(desc(Item_Review.created_at))

        return render_template('/items/details.html', item=item, item_reviews=item_reviews)
    
    @app.route("/items/<int:item_id>/favorite", methods=["POST"])
    def toggle_item_to_favorites(item_id):
        """Adds the menu item to the list of the current logged in user's favorites or removes it if the logged in user currently
        has it in their favorites."""

        if not g.user:
            flash("Please sign in to add a menu item to your list of favorites", "danger")
            return redirect("/")
        
        favorited_item = Item.query.get_or_404(item_id)

        try:
            if favorited_item in g.user.favorite_items:
                g.user.favorite_items = [item for item in g.user.favorite_items if item != favorited_item]
                flash("Menu item successfully removed from favorites!", "success")
            else:
                g.user.favorite_items.append(favorited_item)
                flash("Menu item successfully added to favorites", "success")
            
            db.session.commit()
        except:
            flash("Unable to connect to/access the database. Please try again later.", "danger") 

        redirect_url = request.referrer or "/"
        return redirect(redirect_url)
    
    @app.route("/items/<int:item_id>/reviews/create", methods=["GET", "POST"])
    def create_item_review(item_id):
        """Creates a new review from the logged in user for the menu item with the id of item_id."""

        if not g.user:
            flash("Please sign in to review a menu item", "danger")
            return redirect("/")
        
        item = Item.query.get_or_404(item_id)
        form = ReviewForm()

        if form.validate_on_submit():
            try:
                new_review = Item_Review(
                    author_id = g.user.id,
                    item_id = item_id,
                    title = form.title.data,
                    content = form.content.data
                )
                db.session.add(new_review)
                db.session.commit()

                flash(f"New review for {item.title} successfully added", "success")
                return redirect(f"/items/{item_id}")
            except:
                flash("Unable to add review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")
        
        return render_template("/items/add_review.html", item=item, form=form)
    
    @app.route("/items/<int:item_id>/reviews/<int:review_id>/update", methods=["GET", "POST"])
    def update_item_review(item_id, review_id):
        """Updates a particular review for a particular menu item as long as the review being updated was written by the 
        logged in user currently updating it."""

        if not g.user:
            flash("Please sign in to edit your menu item reviews", "danger")
            return redirect("/")
        
        item = Item.query.get_or_404(item_id)
        review = Item_Review.query.get_or_404(review_id)
        # Only allow users to edit their own menu item reviews
        if review.author.id != g.user.id:
            flash("You can only edit reviews that you created!", "danger")
            redirect_url = request.referrer or "/"
            return redirect(redirect_url)

        form = ReviewForm(obj=review)
        if form.validate_on_submit():
            try:
                review.title = form.title.data
                review.content = form.content.data

                db.session.commit()

                flash(f"Review for {item.title} successfully updated", "success")
                return redirect(f"/items/{item_id}")
            except:
                flash("Unable to edit review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")

        return render_template("/items/edit_review.html", item=item, form=form)
    
    @app.route("/items/<int:item_id>/reviews/<int:review_id>/delete", methods=["POST"])
    def delete_item_review(item_id, review_id):
        """Deletes a menu item review as long as it was written by the currently logged in user."""

        if not g.user:
            flash("Please sign in to delete your menu item reviews", "danger")
            return redirect("/")
        
        item = Item.query.get_or_404(item_id)
        review = Item_Review.query.get_or_404(review_id)
        # Only allow users to delete their own menu item reviews
        if review.author.id != g.user.id:
            flash("You can only delete reviews that you created!", "danger")
            redirect_url = request.referrer or "/"
            return redirect(redirect_url)
        
        try:
            db.session.delete(review)
            db.session.commit()

            flash(f"Your review for {item.title} was successfully deleted!", "success")
        except:
            flash("Unable to delete review. There was trouble in connecting to/accessing the database. Please try again later.", "danger")

        redirect_url = request.referrer or "/"
        return redirect(redirect_url)
    
    ##############################################################################
    @app.route('/')
    def homepage():
        """If user is logged in, show logged in homepage. If user is logged out, show logged out homepage."""
        if g.user:
            # There are multiple pages where you can access the update location form. This is to store the current url so user can easily
            # go back to the page they came from if they decide not to update their location.
            session[GO_BACK_URL] = request.path

            if g.user.location_lat and g.user.location_long and len(CURRENT_RESTAURANTS_NEARBY) == 0:
                get_and_store_nearby_restaurants()

            return render_template("home.html", nearby_restaurants=CURRENT_RESTAURANTS_NEARBY)
        else:
            return render_template("home_anon.html")
    
    @app.errorhandler(404)
    def not_found(e):
        """When the user tries to access a URL that can't be found, return a 404 error message and redirect the user to the homepage."""

        flash("404 Not Found: The URL you requested was not found", "danger")

        return redirect("/")
    
    ##############################################################################
    # Turn off all caching in Flask
    #   (useful for dev; in production, this kind of stuff is typically
    #   handled elsewhere)
    #   Added this as a suggestion, credit to Springboard mentor Jesse B. and Springboard support for directing me to this link:
    #   https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

    @app.after_request
    def add_header(req):
        """Add non-caching headers on every request."""

        req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        req.headers["Pragma"] = "no-cache"
        req.headers["Expires"] = "0"
        req.headers['Cache-Control'] = 'public, max-age=0'
        return req
    
    return app


app = create_app('vouch4food')
if __name__ == '__main__':
    connect_db(app)
    app.run(debug=True)
