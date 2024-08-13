"""This is the file for defining forms that have to do with restaurants, specifically for creating a restaurant review and updating a 
restaurant review."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class AddRestaurantReviewForm(FlaskForm):
    """The form that allows a logged in user to create a review for a specific restaurant location. Must have a title no longer than 100
    characters."""

    title = StringField('Title:', validators=[DataRequired(message="Your review must have a title!"), Length(max=100, message="Your review title can't have more than 100 characters!")])
    content = TextAreaField('Content:', validators=[DataRequired(message="Your review can't be empty!")])