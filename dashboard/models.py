from . import app
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_method
from flask import request
import hashlib
from .shared import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('user_id', db.Integer, primary_key=True,  autoincrement=True)
    email = db.Column('email', db.String(120), nullable=False)
    username = db.Column('username', db.String(120), nullable=False)
    first_name = db.Column('first_name', db.String(120), nullable=False)
    last_name = db.Column('last_name', db.String(120), nullable=False)
    premium_subscription_expiration = db.Column('premium_subscription_expiration', db.Integer, nullable=False, default=0)
    vip_subscription_expiration = db.Column('vip_subscription_expiration', db.Integer, nullable=False, default=0)
    is_reseller = db.Column('is_reseller', db.Boolean, nullable=False)
    privilage_level = db.Column('privilage_level', db.Enum('normal', 'subscribed'), nullable=False)
    password = db.Column('password', db.String(120), nullable=False)
    login_date = db.Column('last_login_date', db.DateTime(), nullable=False)
    login_ip = db.Column('last_login_ip', db.String(39), nullable=False)
    authenticated = db.Column('online_status', db.Boolean, default=False)
    account_status = db.Column('account_status', db.Enum('active',  'disabled',  'banned'), nullable=False)
    connection_status = db.Column('connection_status', db.Integer, default=0)
    requests = db.relationship('Requests', backref='user', lazy='dynamic')
    profile_info = db.relationship('ProfileInfo', backref='user', lazy='dynamic')
    email_verification = db.relationship('Email', backref='user', lazy='dynamic')
    trial_account = db.relationship('TrialUser', backref='user', lazy='dynamic')

    def __init__(self, first_name, last_name, email, username, password):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.account_status = 'active'
        self.is_reseller = False
        check_password_hashed = password + app.config['PASSWORD_SALT']
        self.password = (hashlib.md5(check_password_hashed.encode())).hexdigest()
        self.premium_subscription_expiration = 0
        self.vip_subscription_expiration = 0
        self.email_confirmation = False
        self.connection_status = 0
        self.login_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        self.login_date = datetime.now()
        self.privilage_level = 'normal'
        self.authenticated = False
        self.email_confirmation = False

    @hybrid_method
    def is_correct_password(self, password):
        check_password_hashed = password+app.config['PASSWORD_SALT']
        hashed_password = hashlib.md5(check_password_hashed.encode())
        return self.password == hashed_password.hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.email


class ProfileInfo(db.Model):
    __tablename__ = 'profile_info'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
    facebook_url = db.Column('facebook_url', db.String(255))
    twitter_url = db.Column('twitter_url', db.String(255))
    payment_method = db.Column('payment_method', db.String(255))
    info = db.Column('info', db.String(255))


class LockedAccount(db.Model):
    __tablename__ = 'locked_accounts'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
    is_valid = db.Column('is_valid', db.Boolean, nullable=False)
    deactivation_date = db.Column('deactivation_date', db.DateTime)
    reactivation_date = db.Column('reactivation_date', db.DateTime)
    activation_login_ip = db.Column('activation_login_ip', db.String(255))
    activation_key = db.Column('activation_key', db.String(255))


class Email(db.Model):
    __tablename__ = 'email_verification'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
    registration_date = db.Column('registration_date', db.DateTime, nullable=False)
    expiration_date = db.Column('expiration_date', db.DateTime, nullable=False)
    confirmation_key = db.Column('confirmation_key', db.String(120), nullable=False)
    valid = db.Column('valid', db.Boolean, nullable=False)


class Notifications(db.Model):
    __tablename__ = 'notifications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
    notification_type = db.Column('notification_type', db.Enum('login', 'signup', 'change_password'), nullable=False)
    confirmed_date = db.Column('confirmed_date', db.DATETIME, nullable=False)


class Reseller(db.Model):
    __tablename__ = 'resellers'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
    credit_count = db.Column('credit_count', db.Integer, nullable=False)
    trial_generation_count = db.Column('trial_generation_count', db.Integer, nullable=False)
    last_transaction_date = db.Column('last_transaction_date', db.Integer, nullable=False)
    last_transaction_ip = db.Column('last_transaction_ip', db.Text, nullable=False)
