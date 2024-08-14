"""This is the file for defining the form for users to leave a review. This review form can be used for both restaurants and menu items."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class ReviewForm(FlaskForm):
    """The form that allows a logged in user to create a review for a specific restaurant location or menu item. 
    Must have a title no longer than 100 characters. This is also the form that's used for updating a specific review."""

    title = StringField('Title:', validators=[DataRequired(message="Your review must have a title!"), Length(max=100, message="Your review title can't have more than 100 characters!")])
    content = TextAreaField('Content:', validators=[DataRequired(message="Your review can't be empty!")])
