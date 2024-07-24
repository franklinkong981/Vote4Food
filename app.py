"""Main application file for the Vouch4Food application that contains all the imports, routes, and view functions wrapped up in a
create_app function to create separate instances/application contexts for development and testing."""

import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

# from forms import 
from models import db, connect_db, User, Restaurant, Item, Restaurant_Review, Item_Review, Restaurant_Favorite, Item_Favorite

"""This key will be in the Flask session and contain the logged in user's id once a user successfully logs in, will be removed once a user
successfully logs out."""
CURRENT_USER_KEY = "logged_in_user"

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
    # Functions for user login/logout, as well as convenient access to logged in user information.

    @app.before_request
    def add_user_to_g_object():
        """Before sending each request, a user is currently logged in, add the logged in user's instance to the Flask g object."""

        if CURRENT_USER_KEY in session:
            g.user = User.query.get_or_404(session[CURRENT_USER_KEY])
        else:
            g.user = None
    
    def is_user_not_logged_in(error_message):
        """Called when user must be logged out to access the page. If user is currently logged in, redirects them to the home page
        with an error message."""

        if g.user:
            flash(error_message, "danger")
            return redirect('/')
    
    def is_user_logged_in(error_message):
        """Called when the user must be logged in to access the page. If user is currently logged out, redirects them to the home page
        with an error message."""

        if not g.user:
            flash(error_message, "danger")
            return redirect('/')
    
    def login_user(user):
        """Add user's id to the Flask session to indicate that this user is currently logged in."""

        session[CURRENT_USER_KEY] = user.id
    
    def logout_user():
        """Remove the previously logged in user's id from the Flask session to indicate no user is currently logged in."""

        del session[CURRENT_USER_KEY]
    
    @app.route('/signup', methods=['GET', 'POST'])
    def handle_signup():
        is_user_logged_in("You already have an account and are signed in!")
        return "WHERE YOU LEFT OFF"


    ##############################################################################
    @app.route('/')
    def homepage():
        return render_template('home-anon.html')


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