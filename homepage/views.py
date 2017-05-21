from . import homepage
from flask import render_template


@homepage.route('/')
def home():
    return render_template('home.html')