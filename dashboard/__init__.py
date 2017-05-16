from flask import Flask
from flask_mail import Mail
from .shared import db
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('app_config')
db.init_app(app)
mail = Mail()
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from . import views