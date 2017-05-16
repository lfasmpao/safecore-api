import random
import string
from dashboard import app
from functools import wraps
from flask import abort
from flask_login import current_user
from datetime import datetime, timedelta

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def license_key_generator():
    licence_key = []
    for x in range(5):
        licence_key.append(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)))
    return "-".join(licence_key)


def email_key_generator():
    confirmation_code = []
    for x in range(5):
        confirmation_code.append(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)))
    return "-".join(confirmation_code)


def is_reseller(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_reseller:
            return f(*args, **kwargs)
        else:
            abort(404)
    return wrap


def dateBack(date, precise=False, fromdate=None):
    delta = fromdate - date
    deltaminutes = delta.seconds // 60
    deltahours = delta.seconds // 3600
    deltaminutes -= deltahours * 60
    deltaweeks = delta.days // 7
    deltaseconds = delta.seconds - deltaminutes * 60 - deltahours * 3600
    deltadays = delta.days - deltaweeks * 7
    deltamilliseconds = delta.microseconds // 1000
    deltamicroseconds = delta.microseconds - deltamilliseconds * 1000

    values_and_names = [(deltaweeks, "week"), (deltadays, "day"),
                      (deltahours, "hour"), (deltaminutes, "minute"),
                      (deltaseconds, "second")]
    if precise:
        values_and_names.append((deltamilliseconds, "millisecond"))
        values_and_names.append((deltamicroseconds, "microsecond"))

    text = ""
    for value, name in values_and_names:
        if value > 0:
            text += len(text) and ", " or ""
            text += "%d %s" % (value, name)
            text += (value > 1) and "s" or ""

    if text.find(",") > 0:
        text = " and ".join(text.rsplit(", ", 1))

    return text