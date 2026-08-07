import os
import logging
from dotenv import load_dotenv
from extensions import db

load_dotenv()

def init_database(app):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_dir = os.path.join(app.root_path, "database")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "agroai.db")
        db_url = f"sqlite:///{db_path}"
    
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logging.warning(f"Could not connect to primary DATABASE_URL ({e}). Falling back to SQLite local database.")
            db_dir = os.path.join(app.root_path, "database")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "agroai.db")
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
            try:
                db.create_all()
            except Exception as ex:
                logging.error(f"Failed SQLite fallback creation: {ex}")