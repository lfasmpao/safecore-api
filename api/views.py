from . import api
from dashboard import app, mail
from .models import Transactions
from flask import url_for, redirect, flash, request, abort, render_template
from dashboard.models import User, Reseller, LockedAccount
from .models import Requests, TrialUser
from dashboard.forms import LicenseKeyForm, BuyLicense, CreateLicense, ShareCredits, TrialForm, LockAccount
from flask_login import current_user, login_required, logout_user
from datetime import datetime
from dashboard.shared import db
import PIL
from PIL import Image
from StringIO import StringIO
from .controllers import is_reseller, email_key_generator
from flask_mail import Message

@api.route('/license_key/add/', methods=['POST'])
@login_required
def license_key_verify():
    if request.method == 'POST':
        form = LicenseKeyForm()
        if form.validate_on_submit():
            if form.category.data == 1:
                subscription_type = 'Premium'
            elif form.category.data == 2:
                subscription_type = 'VIP'
            else:
                abort(404)
            check_transactions = Transactions.query.filter_by(license_key=form.license_key.data,
                                                              sender_username=form.username.data,
                                                              subscription_type=subscription_type
                                                              ).first()
            if check_transactions is None or check_transactions.confirmed is True:
                flash('License key is not valid', 'warning')
                return redirect(url_for('manage_license'))
            else:
                update_subscription = User.query.filter_by(id=current_user.id).first()
                if check_transactions.is_credit:
                    check_transactions.confirmed = True
                    check_transactions.transaction_confirmed_date = datetime.now()
                    check_transactions.receiver_username = current_user.username
                    check_transactions.transaction_login_ip = check_transactions.transaction_login_ip + ',' + request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                    reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
                    reseller_id.credit_count = reseller_id.credit_count + check_transactions.qty
                    db.session.add(check_transactions, update_subscription)
                    db.session.commit()
                else:
                    check_transactions.confirmed = True
                    check_transactions.transaction_confirmed_date = datetime.now()
                    check_transactions.receiver_username = current_user.username
                    check_transactions.transaction_login_ip = check_transactions.transaction_login_ip + ',' + request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                    duration = (check_transactions.qty * 86400)
                    if check_transactions.subscription_type == 'VIP':
                        update_subscription.subscription_expiration = (
                            update_subscription.vip_subscription_expiration + duration
                        )
                    elif check_transactions.subscription_type == 'Premium':
                        update_subscription.premium_subscription_expiration = (
                            update_subscription.premium_subscription_expiration + duration
                        )
                    update_subscription.privilage_level = 'subscribed'
                    db.session.add(check_transactions, update_subscription)
                    db.session.commit()
                flash('License Activated!', 'success')
                return redirect(url_for('manage_license'))
        else:
            flash('Something is wrong with your license key', 'warning')
            return redirect(url_for('manage_license'))
    else:
        abort(404)


@api.route('/profile/<img_type>/upload', methods=['POST'])
@login_required
def upload_picture(img_type):
    if request.method == 'POST':
        if img_type == 1:
            location = '/profile_picture/'
        elif img_type == 2:
            location = '/cover_photo/'
        base_width = 300
        filename = StringIO(open("dashboard/static/img/logo.png", 'rb').read())
        img = Image.open(filename)
        percent = base_width / float(img.size[0])
        height = int((float(img.size[1]) * float(percent)))
        img = img.resize((base_width, height), PIL.Image.ANTIALIAS)
        img.save(app.config['UPLOAD_FOLDER'] + location + current_user.username + '.png')
    else:
        abort(404)


@api.route('/license/buy', methods=['POST'])
@login_required
def send_request():
    if request.method == 'POST':
        form = BuyLicense()
        if form.validate_on_submit():
            send_request = Requests()
            pass


@api.route('/license/generate', methods=['POST'])
@login_required
@is_reseller
def generate_key():
    if request.method == 'POST':
        form = CreateLicense()
        if form.validate_on_submit():
            reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
            if reseller_id is not None:
                if form.category.data == 1:
                    subscription_type = 'Premium'
                    if form.qty.data == 1:
                        count = 1
                        qty = 30
                    elif form.qty.data == 2:
                        count = 2
                        qty = 60
                    else:
                        count = 3
                        qty = 90
                elif form.category.data == 2:
                    subscription_type = 'VIP'
                    if form.qty.data == 1:
                        count = 2
                        qty = 30
                    elif form.qty.data == 2:
                        count = 4
                        qty = 60
                    else:
                        count = 6
                        qty = 90

                if (reseller_id.credit_count - count) < 0:
                    flash('Not enough credits!', 'warning')
                    return redirect(url_for('manage_key'))
                else:
                    reseller_id.credit_count = reseller_id.credit_count - count
                    generate = Transactions(current_user.username, qty, subscription_type, is_credit=False)
                    reseller_id.last_transaction_date = datetime.now()
                    reseller_id.last_transaction_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                    db.session.add(generate, reseller_id)
                    db.session.commit()
                    flash('Successfully created!', 'success')
                    return redirect(url_for('manage_key'))
            else:
                flash('Internal Error 101!', 'warning')
                return redirect(url_for('manage_key'))
        else:
            flash('Internal Error 100!', 'warning')
            return redirect(url_for('manage_key'))


@api.route('/user/trial/generate', methods=['POST'])
@login_required
@is_reseller
def generate_trial():
    if request.method == 'POST':
        form = TrialForm()
        if form.validate_on_submit():
            reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
            reseller_id.trial_generation_count = reseller_id.trial_generation_count - 1
            if (reseller_id.trial_generation_count - 1) < 0:
                flash('Not trial creation credits!', 'warning')
                return redirect(url_for('manage_trial'))
            else:
                query = TrialUser(form.password.data)
                db.session.add(query, reseller_id)
                db.session.commit()
                flash('Successfully created!', 'success')
                return redirect(url_for('manage_trial'))
        else:
            flash('Error in password', 'warn')
            return redirect(url_for('manage_trial'))


@api.route('/license/share/credits', methods=['POST'])
@login_required
@is_reseller
def share_key():
    if request.method == 'POST':
        form = ShareCredits()
        if form.validate_on_submit():
            reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
            if reseller_id is not None:
                if form.qty.data == 1:
                    credits = 10
                elif form.qty.data == 2:
                    credits = 20
                else:
                    credits = 25
                if (reseller_id.credit_count - credits) < 0:
                    flash('Not enough credits!', 'warning')
                    return redirect(url_for('manage_key'))
                else:
                    generate = Transactions(sender_username=current_user.username, qty=credits,
                                            subscription_type='Premium', is_credit=True)
                    reseller_id.last_transaction_date = datetime.now()
                    reseller_id.last_transaction_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                    reseller_id.credit_count = reseller_id.credit_count - credits
                    db.session.add(generate, reseller_id)
                    db.session.commit()
                    flash('Successfully shared!', 'success')
                    return redirect(url_for('manage_key'))

        else:
            flash('Something went wrong with your input', 'info')
            return redirect(url_for('manage_key'))
    else:
        abort(404)


@api.route('/license/delete/<key>', methods=['GET'])
@login_required
@is_reseller
def delete_key(key=None):
    if key is None:
        abort(404)
    elif Transactions.query.filter_by(sender_username=current_user.username, license_key=key).first is not None:
        reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
        query = Transactions.query.filter_by(sender_username=current_user.username, license_key=key).first()
        if query is not None and query.confirmed is False:
            if query.is_credit is True:
                reseller_id.credit_count = reseller_id.credit_count + query.qty
            else:
                if query.subscription_type == 'Premium':
                    if query.qty == 90:
                        reseller_id.credit_count = reseller_id.credit_count + 3
                    elif query.qty == 60:
                        reseller_id.credit_count = reseller_id.credit_count + 2
                    else:
                        reseller_id.credit_count = reseller_id.credit_count + 1
                elif query.subscription_type == 'VIP':
                    if query.qty == 90:
                        reseller_id.credit_count = reseller_id.credit_count + 6
                    elif query.qty == 60:
                        reseller_id.credit_count = reseller_id.credit_count + 4
                    else:
                        reseller_id.credit_count = reseller_id.credit_count + 2
            db.session.add(reseller_id)
            db.session.delete(query)
            db.session.commit()
            flash('Successfully deleted!', 'success')
            return redirect(url_for('manage_key'))
        else:
            abort(404)
    else:
        abort(404)


@api.route('/trial/delete/<key>', methods=['GET'])
@login_required
@is_reseller
def delete_trial(key=None):
    if key is None:
        abort(404)
    elif Transactions.query.filter_by(sender_username=current_user.username, license_key=key).first is not None:
        query = TrialUser.query.filter_by(reseller_id=current_user.id, trial_login=key).first()
        if query is not None:
            db.session.delete(query)
            db.session.commit()
            flash('Successfully deleted!', 'success')
            return redirect(url_for('manage_trial'))
        else:
            abort(404)
    else:
        abort(404)


@api.route('/account/deactivate', methods=['POST'])
@login_required
@is_reseller
def lock_account():
    if request.method == 'POST':
        form = LockAccount()
        if form.validate_on_submit():
            if form.confirm.data == 'YES':
                key = email_key_generator()
                query = LockedAccount(user_id=current_user.id,
                                    is_valid=True,
                                    deactivation_date=datetime.now(),
                                    activation_key=key
                                    )
                msg = Message('SafeCore Reactivation Link',
                              sender="noreply@safecorevpn.com",
                              recipients=current_user.email
                              )
                msg.html = render_template('reactivation.html',
                                           confirmation=key)
                #mail.send(msg)
                user = current_user
                user.authenticated = False
                user.account_status = 'disabled'
                db.session.add(query, user)
                db.session.commit()
                logout_user()
                flash('Successfully deactivated account!', 'info')
                return redirect(url_for('login'))
            else:
                flash('Please type YES', 'warning')
                return redirect(url_for('lock_account'))
        else:
            flash('Please fill up the form', 'warning')
            return redirect(url_for('lock_account'))
    else:
        abort(404)
