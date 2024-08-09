from app import create_app
from models.connect import connect_db

app = create_app("vouch4food")
connect_db(app)