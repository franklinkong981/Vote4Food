"""Seed file that will be used throughout development that will be used to either insert sample data into the database
or connect to online Supabase database."""

import os
from app import db, app
from models import db, connect_db, User, Restaurant, Item, Restaurant_Review, Item_Review, Restaurant_Favorite, Item_Favorite
from dotenv import load_dotenv

load_dotenv()
# app = create_app('warbler')
print("The database is: ", os.environ.get('DATABASE_URL'))
connect_db(app)
app.app_context().push()

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