"""This is the file where forms dealing with the user profile settings are defined, they include the form for editing a user's
profile information as well as the form for setting a user's current location through zip code entry.
The app uses WTForms for increased security."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Email, Length, Optional

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

class SetLocationForm(FlaskForm):
    """Defines the form displayed on the profile page where a user can set their current location/address by entering a 5-digit US postal code.
    The approximate latitude and longitude based on the zip code will be calculated on form submission."""

    address_zip = IntegerField('Zip code (first 5 digits):', validators=[DataRequired(message="You must enter a zip code to set your location!"), NumberRange(min=10000, max=99999, message="Your zip code must be 5 digits long!")])
