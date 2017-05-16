from flask import Blueprint

adminAPI = Blueprint(
    'adminAPI',
    __name__
)

from . import views
