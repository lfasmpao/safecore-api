import random
import string
from functools import wraps, update_wrapper
from flask import abort
from flask_login import current_user
from dashboard.models import Administrator
import socket
import time
from datetime import datetime
from flask import make_response


def license_key_generator():
""" Random Key Generation Module
	AUTHOR: Leo Francisco Simpao lfasmpao@gmail.com
	This module will generate a random letters from A-Z UTF-8 and produce it to an 29 digits key with '-',
	Example:
		license_key_generator()
	Dependencies:
		random
"""
    licence_key = []
    for x in range(5):
        licence_key.append(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)))
    return "-".join(licence_key)


def email_key_generator():
""" Email Key Generation Module
	AUTHOR: Leo Francisco Simpao lfasmpao@gmail.com
	This module will generate a random letters from A-Z UTF-8 and produce it to an 24 digits key with '-',
	Example:
		email_key_generator()
	Dependencies:
		random
"""
    confirmation_code = []
    for x in range(5):
        confirmation_code.append(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)))
    return "-".join(confirmation_code)


def admin_only(f):
	""" Check if the user privilages is Administrator """
    @wraps(f)
    def wrap(*args, **kwargs):
        query = Administrator.query.filter_by(user_id=current_user.id).first()
        if query is not None:
            return f(*args, **kwargs)
        else:
            abort(404)
    return wrap


def is_reseller(f):
	""" Check if the user privilages is Reseller """
    @wraps(f)
    def wrap(*args, **kwargs):
        query = Administrator.query.filter_by(user_id=current_user.id).first()
        if query is not None:
            return f(*args, **kwargs)
        elif current_user.is_reseller:
            return f(*args, **kwargs)
        else:
            abort(404)
    return wrap


def nocache(view):
	""" No cache """
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def dateBack(date, precise=False, fromdate=None):
""" Dateback Module
	This module return a value from date to a human readable format
	Example:
		dateBack('12-10-2017', False, '12-10-2017')
		this will return 'now'
	Dependencies:
		datetime
"""
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


class Management:
""" Dateback Module
	AUTHOR: Leo Francisco Simpao lfasmpao@gmail.com
	This module will send a disconnection command to an openvpn management enabled syste,
	Example:
		init = Management() - this will init the class
		init.send(username, 127.0.0.1, 5555)
	Dependencies:
		socket
"""
    def __init__(self):
        self.sock = None
        self.connected = False
        self.timeout = 120
        self.delay = 1

    def send(self, username, ip, port):
        retval = None
        try:
            self.sock = socket.socket()
            if self.sock:
                self.sock.settimeout(self.timeout)
            if self.sock:
                self.sock.connect((ip, port))
            self.connected = True
            count = 0
            if self.sock:
                count = self.sock.send('kill %s\n' % username)
            if count == 0:
                return None
            time.sleep(self.delay)
            if self.sock:
                retval = self.sock.recv(1024)
        except socket.timeout, e:
            return None
        return retval
