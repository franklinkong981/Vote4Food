"""Main application file for the Vouch4Food application that contains all the imports, routes, and view functions wrapped up in a
create_app function to create separate instances/application contexts for development and testing."""

import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from forms import SignUpForm, LoginForm, EditProfileForm, ChangePasswordForm, SetLocationForm, SearchRestaurantForm
from models import db, connect_db, User, Restaurant, Item, Restaurant_Review, Item_Review, Restaurant_Favorite, Item_Favorite
from helpers import build_restaurant_address_string, build_restaurant_cuisine_string, format_phone_number, get_restaurant_photo_url

"""This key will be in the Flask session and contain the logged in user's id once a user successfully logs in, will be removed once a user
successfully logs out."""
CURRENT_USER_KEY = "logged_in_user"
GO_BACK_URL = "back_url"
CURRENT_RESTAURANT_SEARCH_RESULTS = "current_restaurant_search_results"

GEOLOCATION_API_URL = "http://api.positionstack.com/v1/forward"
SPOONACULAR_RESTAURANT_SEARCH_URL = "https://api.spoonacular.com/food/restaurants/search"

def create_app(db_name, testing=False):
    """Create an instance of the app to ensure separate production database and testing database, and that sample data inserted into
    database for unit/integration testing purposes doesn't interfere with actual database for production."""
    app = Flask(__name__)
    app.testing = testing
    # Get DB_URI from environ variable (useful for production/testing) or,
    # if not set there, use development local db.
    app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', f'postgresql:///{db_name}'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    toolbar = DebugToolbarExtension(app)
    if app.testing:
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        app.config['SQLALCHEMY_ECHO'] = True
    
    #Routes and view functions for the application.

    ##############################################################################
    # Non-route functions, aka functions to be executed before/after each request, or functions that handle API calls, manipualate
    # caches, etc.

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
    
    def get_address_info(zip_code):
        """Calls the Position Stack Geolocation API which converts the zip_code into an address object that contains information like
        longitude, latitude, region, etc. Returns the long/lat coordinates in the most relevant/first address object found and raises 
        an error if no results are found."""

        response = requests.get(GEOLOCATION_API_URL, params={"access_key": os.environ.get('POSITION_STACK_API_KEY'), "query": str(zip_code)})
        if len(response.json()['data']) == 0:
            raise ValueError("The zip code you entered is not a registered US zip code.")
        address_data = response.json()['data'][0]
        return {'longitude': float(address_data['longitude']), 'latitude': float(address_data['latitude'])}


    ##############################################################################
    # Functions for user login/logout, as well as convenient access to logged in user information.
    
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
        flash("Successfully logged out.", "success")
        return redirect("/")

    ##############################################################################
    # Routes relevant to the logged in user, such as user profile information, user's reviews, and user's favorite restaurants/menu items.

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
    
    @app.route('/users/profile/update_location', methods=['GET', 'POST'])
    def update_location():
        """Show the form that allows the logged in user to update their location by entering their 5-digit zip code. The zip code will then
        be transformed into latitude and longitude coordinates"""

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
                if not g.back_url:
                    return redirect("/")
                return redirect(g.back_url)
            except ValueError as exc:
                flash("Unable to update location, the zip code you entered is not a registered US postal code. Please try again.", "danger")
                print(f"ERROR: {exc}")
            except:
                # Issue with connecting to SQLAlchemy database or Geoloation API.
                flash("There was an error in connecting/accessing the database/geolocation API. Please try again later.", "danger")
        
        return render_template("users/edit_location.html", form=form)

    ##############################################################################
    # Routes relevant to searching for restaurants, mainly through the restaurant search bar in the navbar.

    def get_restaurant_search_results(search_query, latitude, longitude):
        """Calls the Spoonacular API Restaurant Search route and returns the list of restaurant JSON objects that match the search
        query and are located near the latitude and longitude."""

        restaurants_response = requests.get(SPOONACULAR_RESTAURANT_SEARCH_URL, params={"apiKey": os.environ.get('SPOONACULAR_API_KEY'), "query": search_query, "lat": float(latitude), "lng": float(longitude), "distance": 5})
        restaurants_data = restaurants_response.json()["restaurants"]
        return restaurants_data
    
    def store_restaurants_to_session(restaurants):
        """Extract the important information about each restaurant in the most recent restaurant search results such as opening hours,
        name, etc. and store them in the Flask session for persistence."""

        session[CURRENT_RESTAURANT_SEARCH_RESULTS] = []
        for restaurant in restaurants:
            add_restaurant_to_session(restaurant)
    
    def add_restaurant_to_session(restaurant):
        """restaurant is a JSON Restaurant object returned from the Spoonacular API. This function extracts the useful data from it,
        processes them into more readable formats, and adds them to the Flask session as an object."""

        if CURRENT_RESTAURANT_SEARCH_RESULTS not in session:
            session[CURRENT_RESTAURANT_SEARCH_RESULTS] = []

        restaurant_data = {
            'id': restaurant['_id'],
            'name': restaurant['name'],
            'address': build_restaurant_address_string(restaurant['address']),
            'latitude': restaurant['address']['latitude'],
            'longitude': restaurant['address']['longitude'],
            'cuisines': build_restaurant_cuisine_string(restaurant["cuisines"]),
            'description': restaurant["description"] or None,
            'phone': format_phone_number(restaurant["phone_number"]),
            'hours': restaurant['local_hours']['operational'] or None,
            'photo_url': get_restaurant_photo_url(restaurant)
        }
        session[CURRENT_RESTAURANT_SEARCH_RESULTS].append(restaurant_data)


    @app.route("/restaurants/add", methods=["POST"])
    def add_restaurants_to_db():
        """This route consists of 4 steps:
        1. Calls the PositionStack API to return a longitude and latitude corresponding to the zip code the user typed in.
        2. Calls the Spoonacular API to search for all restaurants that match the search query and are located near the zip code.
        3. Extracts several pieces of useful information from each restaurant object in the JSON response to be stored in the Flask session.
        4. Adds each restaurant whose id isn't found in the database into the vouch4Food database as a Restaurant object."""
        
        if not g.user:
            flash("Please sign in to search for restaurants", "danger")
            return redirect("/")
        
        try:
            # Step 1
            zip_code = request.args.get('zip_code')
            coords = get_address_info(zip_code)

            # Step 2
            search_term = request.args.get('query')
            restaurants_data = get_restaurant_search_results(search_term, coords['latitude'], coords['longitude'])

            # Step 3
            store_restaurants_to_session(restaurants_data)

            # Step 4
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

        return render_template('/restaurants/search.html')

    ##############################################################################
    @app.route('/')
    def homepage():
        """If user is logged in, show logged in homepage. If user is logged out, show logged out homepage."""
        if g.user:
            # There are multiple pages where you can access the update location form. This is to store the current url so user can easily
            # go back to the page they came from if they decide not to update their location.
            session[GO_BACK_URL] = request.path

            return render_template("home.html")
        else:
            return render_template("home_anon.html")
    
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