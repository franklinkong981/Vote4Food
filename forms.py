"""This is the file where the different forms and their different fields/constraints are specified. This application uses WTForms
for increased security."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField
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

class EditProfileForm(FlaskForm):
    """Defines the form that a logged in user can use to edit their profile information. Users can edit their first name, last name,
    email, profile picture, and password. They must also enter their current password to save the changes."""

    first_name = StringField('First Name:', validators=[DataRequired(message="You must provide a first name!")])
    last_name = StringField('Last Name:', validators=[DataRequired(message="You must provide a last name!")])
    email = StringField('Email Address:', validators=[DataRequired(message="You must provide an email!"), Email("You must provide a valid email address!")])
    user_image_url = StringField('Profile Image URL (optional):', validators=[Optional()])
    current_password = PasswordField('Current Password:', validators=[DataRequired(message="You must enter your current password to make changes!")])

class ChangePasswordForm(FlaskForm):
    """Defines the form that a logged in user can use to update their password. Users must also enter their current password to finalize the change."""

    current_password = PasswordField('Current Password:', validators=[DataRequired(message="You must provide your current password!")])
    new_password = PasswordField('New Password:', validators=[DataRequired(message="You must provide a new password!"), Length(min=8,message="Your new password must be at least 8 characters long!")])


