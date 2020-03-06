import os
from dotenv import load_dotenv

def load(app):
    APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
    dotenv_path = os.path.join(APP_ROOT, '.env')
    load_dotenv(dotenv_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]