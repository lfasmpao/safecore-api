from flask import Blueprint

signup = Blueprint(
    'reseller',
    __name__
)

from . import views