"""Seed file that will be used throughout development that will be used to either insert sample data into the database
or connect to online Supabase database."""

import os
from app import create_app

from models.init_db import db
from models.user import User
from models.restaurant import Restaurant, Restaurant_Favorite, Restaurant_Review
from models.item import Item, Item_Favorite, Item_Review
from models.connect import connect_db

from dotenv import load_dotenv
load_dotenv()

app = create_app('vouch4food')
# print("The database is: ", os.environ.get('DATABASE_URL'))
connect_db(app)
app.app_context().push()

db.session.rollback()

# Create all tables
db.drop_all()
db.create_all()

# If tables aren't empty, empty them
User.query.delete()
Restaurant.query.delete()
Item.query.delete()
Restaurant_Review.query.delete()
Item_Review.query.delete()
Restaurant_Favorite.query.delete()
Item_Favorite.query.delete()

db.session.commit()