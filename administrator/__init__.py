from flask import Blueprint

admin_api = Blueprint(
    'admin_api',
    __name__,
    template_folder='./templates',
)

from . import views
