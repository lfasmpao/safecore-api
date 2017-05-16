import os

API_VERSION = '1.0'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SERVER_NAME = '' # server name 'example.com'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

UPLOAD_FOLDER = BASE_DIR + '/uploads'
MAX_CONTENT_PATH = 2097152
THREADS_PER_PAGE = 2
CONTENT_PER_PAGE = 10
CSRF_ENABLED = True

CSRF_SESSION_KEY = "secret"
PASSWORD_SALT = "password-salt" # password salt
SECRET_KEY = os.urandom(24)

MAIL_SERVER = "" # mail server
MAIL_PORT = 25
MAIL_USE_SSL = False
MAIL_USE_TLS = False
MAIL_USERNAME = '' # email 'lfasmpao@gmail.com'
MAIL_PASSWORD = '' # email password

# Database Confirguratiom
# For MySQL Database:
# SQLALCHEMY_DATABASE_URI = 'mysql://(username):(password)@(ip):3306/(database_name)'

SQLALCHEMY_DATABASE_URI = '' 
SQLALCHEMY_TRACK_MODIFICATIONS = True
DATABASE_CONNECT_OPTIONS = {}

RECAPTCHA_PUB_KEY = '' # RECAPTCHA PUBLIC KEY
RECAPTCHA_PRIV_KEY = '' # RECAPTCHA PRIVATE KEY