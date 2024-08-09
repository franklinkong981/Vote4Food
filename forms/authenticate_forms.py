"""This is the file for where the forms dealing with user authentication are defined, specifically the forms for signing up and logging in.
The app uses WTForms for increased security."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional

class SignUpForm(FlaskForm):
    """Defines the form for user signup when creating a new account. Users will input their first name, last name, email, password,
    and optional profile image URL. The email must be unique and the password must be at least 8 characters long."""

    first_name = StringField('First Name:', validators=[DataRequired(message="You must provide a first name!")])
    last_name = StringField('Last Name:', validators=[DataRequired(message="You must provide a last name!")])
    email = StringField('Email Address:', validators=[DataRequired(message="You must provide an email!"), Email("You must provide a valid email address!")])
    user_image_url = StringField('Profile Image URL (optional):', validators=[Optional()])
    password = PasswordField('Password:', validators=[DataRequired(message="You must provide a password!"), Length(min=8,message="Your password must be at least 8 characters long!")])

class LoginForm(FlaskForm):
    """Defines the form for user login. Users will need to provide the same username and password they provided when signing up."""

    email = StringField('Email Address:', validators=[DataRequired(message="Please enter your email!")])
    password = PasswordField('Password:', validators=[DataRequired(message="Please enter your password!")])