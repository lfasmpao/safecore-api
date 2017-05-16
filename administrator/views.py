from . import adminAPI
from flask import url_for, redirect

@adminAPI.route('/')
def main():
    return redirect(url_for('home'))
