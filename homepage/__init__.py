from flask import Blueprint

homepage = Blueprint(
    'homepage',
    __name__,
    template_folder='./templates',
)

from . import views