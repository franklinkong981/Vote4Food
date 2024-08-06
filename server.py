from app import create_app
from models import connect_db

app = create_app("vouch4food")
connect_db(app)