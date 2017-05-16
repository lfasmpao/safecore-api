from dashboard.shared import db
from datetime import datetime
from flask import request
from .controllers import license_key_generator
import string
import random
from flask_login import current_user

class Transactions(db.Model):
    __tablename__ = 'transactions'
    id = db.Column('id', db.Integer, primary_key=True,  autoincrement=True)
    qty = db.Column('qty', db.Integer, nullable=False)
    receiver_username = db.Column('receiver_username', db.String(120), nullable=True)
    sender_username = db.Column('sender_username', db.String(120), nullable=False)
    subscription_type = db.Column('subscription_type', db.Enum('Premium', 'VIP'), nullable=False)
    is_credit = db.Column('is_credit', db.Boolean, nullable=False)
    confirmed = db.Column('confirmed', db.Boolean, nullable=False)
    transaction_date = db.Column('transaction_date', db.DateTime, nullable=False)
    transaction_login_ip = db.Column('transaction_login_ip', db.String(120), nullable=False)
    transaction_confirmed_date = db.Column('transaction_confirmed_date', db.DateTime, nullable=True)
    license_key = db.Column('license_key', db.String(30), nullable=False)

    def __init__(self, sender_username, qty, subscription_type, is_credit):
        self.qty = qty
        self.is_credit = is_credit
        self.transaction_login_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        self.sender_username = sender_username
        self.subscription_type = subscription_type
        self.license_key = license_key_generator()
        self.confirmed = False
        self.transaction_date = datetime.now()

    def __repr__(self):
        return '<User %r>' % self.sender_username


class Requests(db.Model):
    __tablename__ = 'requests'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column('sender_id', db.Integer, db.ForeignKey('users.user_id'))
    request_type = db.Column('request_type', db.Enum('vip', 'premium'), nullable=False)
    request_qty = db.Column('request_qty', db.Integer, nullable=False)
    request_date = db.Column('request_date', db.DATETIME, nullable=False)
    confirmed = db.Column('confirmed', db.BOOLEAN, nullable=False)
    confirmed_by = db.Column('confirmed_by', db.String(120), nullable=False)
    confirmed_date = db.Column('confirmed_date', db.DATETIME, nullable=False)


class TrialUser(db.Model):
    __tablename__ = 'trial_users'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    trial_login = db.Column('trial_login', db.String(120), nullable=False)
    trial_password = db.Column('trial_password', db.String(30), nullable=False)
    trial_duration = db.Column('trial_duration', db.Integer, nullable=False)
    trial_online_status = db.Column('trial_online_status', db.Boolean, nullable=False)
    created_date = db.Column('confirmed_date', db.DateTime, nullable=False)
    reseller_id = db.Column('reseller_id', db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self, trial_password):
        self.trial_password = trial_password
        self.trial_duration = 4500
        self.trial_online_status = False
        self.created_date = datetime.now()
        self.trial_login = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        self.reseller_id = current_user.id

    def __repr__(self):
        return '<User %r>' % self.sender_username


class Updates(db.Model):
    __tablename__ = 'updates'
    id = db.Column('id', db.Integer, primary_key=True)
    title = db.Column('title', db.Text)
    info = db.Column('info', db.Text)
    conducted_by = db.Column('conducted_by', db.Text)
    scheduled_date = db.Column('scheduled_date', db.DateTime)
    maintenance_level = db.Column('maintenance_level', db.Enum('low', 'medium', 'high'))
    is_done = db.Column('is_done', db.Boolean)


class ServerList(db.Model):
    __tablename__ = 'server_list'
    id = db.Column('id', db.Integer, primary_key=True)
    server_location = db.Column('server_location', db.String(30), nullable=False)
    server_ip = db.Column('server_ip', db.String(30), nullable=False)
    server_status = db.Column('server_status', db.Boolean)
