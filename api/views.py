from . import api
from dashboard import app, mail
from .models import Transactions
from flask import url_for, redirect, flash, request, abort, render_template
from dashboard.models import User, Reseller, LockedAccount, Notifications
from .models import Requests, TrialUser
from dashboard.forms import LicenseKeyForm, BuyLicense, CreateLicense, ShareCredits, TrialForm, LockAccount, ChangePassword, ProfileSettings, MyPage, GenerateCredits, MyPageInfo, CreditKeyForm, ShareKey
from flask_login import current_user, login_required, logout_user
from datetime import datetime
from dashboard.shared import db
from .controllers import is_reseller, email_key_generator
from flask_mail import Message
from dashboard.models import Administrator, ProfileInfo
import hashlib
from .controllers import Management, admin_only


@api.route('/credits/add/', methods=['POST'])
@login_required
def credit_key_verify():
    if request.method == 'POST':
        form = CreditKeyForm()
        if form.validate_on_submit():
            check_transactions = Transactions.query.filter_by(license_key=form.license_key.data,
                                                              sender_username=form.username.data
                                                              ).first()
            if check_transactions is None or check_transactions.confirmed is True:
                flash('License key is not valid', 'warning')
                return redirect(url_for('account_credits'))
            else:
                update_subscription = User.query.filter_by(id=current_user.id).first()
                if check_transactions.is_credit:
                    if current_user.is_reseller:
                        check_transactions.confirmed = True
                        check_transactions.transaction_confirmed_date = datetime.now()
                        check_transactions.receiver_username = current_user.username
                        check_transactions.transaction_login_ip = check_transactions.transaction_login_ip + ',' + request.environ.get(
                            'HTTP_X_REAL_IP', request.remote_addr)
                        reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
                        reseller_id.credit_count = reseller_id.credit_count + check_transactions.qty
                        db.session.add(check_transactions, update_subscription)
                        db.session.commit()
                        flash('License Activated!', 'success')
                        return redirect(url_for('account_credits'))
                    else:
                        flash('You\'re not allowed to use this key!', 'warning')
                        return redirect(url_for('account_credits'))
                else:
                    flash('License key is not valid', 'warning')
                    return redirect(url_for('account_credits'))
        else:
            flash('Something is wrong with your license key', 'warning')
            return redirect(url_for('account_credits'))
    else:
        abort(404)


@api.route('/license_key/add/', methods=['POST'])
@login_required
def license_key_verify():
    if request.method == 'POST':
        form = LicenseKeyForm()
        if form.validate_on_submit():
            if form.category.data == 1:
                subscription_type = 'Premium'
            else:
                subscription_type = 'VIP'
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
                    flash('License key is not valid', 'warning')
                    return redirect(url_for('manage_license'))
                else:
                    if current_user.under_by is None:
                        check_transactions.confirmed = True
                        check_transactions.transaction_confirmed_date = datetime.now()
                        check_transactions.receiver_username = current_user.username
                        check_transactions.transaction_login_ip = check_transactions.transaction_login_ip + ',' + request.environ.get(
                            'HTTP_X_REAL_IP', request.remote_addr)
                        duration = (check_transactions.qty * 86400)
                        if check_transactions.subscription_type == 'VIP':
                            update_subscription.vip_subscription_expiration = (
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
                        if current_user.under_by == check_transactions.receiver_username:
                            check_transactions.confirmed = True
                            check_transactions.transaction_confirmed_date = datetime.now()
                            check_transactions.receiver_username = current_user.username
                            check_transactions.transaction_login_ip = check_transactions.transaction_login_ip + ',' + request.environ.get(
                                'HTTP_X_REAL_IP', request.remote_addr)
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
                            flash('You\'re not allowed to use this key. Please use the key provided by %s' % current_user.under_by, 'info')
                            return redirect(url_for('manage_license'))
        else:
            flash('Something is wrong with your license key', 'warning')
            return redirect(url_for('manage_license'))
    else:
        abort(404)


@api.route('/license/buy', methods=['POST'])
@login_required
def send_request():
    if request.method == 'POST':
        form = BuyLicense()
        if form.validate_on_submit():
            if form.category.data == 1:
                request_type = 'VIP'
            else:
                request_type = 'Premium'
            if form.qty.data == 1:
                qty = 30
            elif form.qty.data == 2:
                qty = 60
            else:
                qty = 90

            sent_request = Requests(user_id=current_user.id, request_type=request_type, request_qty=qty, request_date=datetime.now())
            db.session.add(sent_request)
            db.session.commit()
            flash('Successfully sent a request!!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Internal error 102!', 'warning')
            return redirect(url_for('home'))
    else:
        abort(404)


@api.route('/manage/password', methods=['POST'])
@login_required
def update_password():
    if request.method == 'POST':
        form = ChangePassword()
        check_password_hashed = form.password.data + app.config['PASSWORD_SALT']
        hashed_password = hashlib.md5(check_password_hashed.encode())
        query = User.query.filter_by(id=current_user.id).first()
        query.password = hashed_password.hexdigest()
        my_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        notify = Notifications(user_id=current_user.id, notification_type='change_password',
                               confirmed_date=datetime.now(), notification_ip=my_ip
                               )
        db.session.add(query)
        db.session.add(notify)
        db.session.commit()
        flash('Password successfully changed!', 'success')
        return redirect(url_for('home'))
    else:
        abort(404)


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
                else:
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

                check_admin = Administrator.query.filter_by(user_id=current_user.id).first()
                if check_admin is not None:
                    check_admin.last_transaction_date = datetime.now()
                    check_admin.last_transaction_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                    generate = Transactions(current_user.username, qty, subscription_type, is_credit=False)
                    db.session.add(generate, check_admin)
                    db.session.commit()
                    flash('Successfully created!', 'success')
                    return redirect(url_for('admin_api.mykeys'))
                elif (reseller_id.credit_count - count) < 0:
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


@api.route('/license/share', methods=['POST'])
@login_required
def share_subscription():
    if request.method == 'POST':
        form = ShareKey()
        if form.validate_on_submit():
                if form.category.data == 1:
                    subscription_type = 'Premium'
                else:
                    subscription_type = 'VIP'
                qty = form.qty.data
                count = (form.qty.data * 86400)
                if subscription_type == 'VIP':
                    if (current_user.vip_subscription_expiration - count) < 0:
                        flash('Not enough subscription!', 'warning')
                        return redirect(url_for('share_license'))
                else:
                    if (current_user.premium_subscription_expiration - count) < 0:
                        flash('Not enough subscription!', 'warning')
                        return redirect(url_for('share_license'))
                user = current_user
                if subscription_type == 'VIP':
                    user.vip_subscription_expiration = user.vip_subscription_expiration - count
                else:
                    user.premium_subscription_expiration = user.premium_subscription_expiration - count
                generate = Transactions(user.username, qty, subscription_type, is_credit=False)
                db.session.add(generate, user)
                db.session.commit()
                flash('Successfully created!', 'success')
                return redirect(url_for('share_license_list'))
        else:
            flash('Please fill up the forms!', 'warning')
            return redirect(url_for('share_license'))


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


@api.route('/license/generate/key', methods=['POST'])
@login_required
@admin_only
def generate_credit_key():
    if request.method == 'POST':
        form = GenerateCredits()
        if form.validate_on_submit():
            admin_id = Administrator.query.filter_by(user_id=current_user.id).first()
            if admin_id is not None:
                credits = form.qty.data
                generate = Transactions(sender_username=current_user.username, qty=credits,
                                        subscription_type='Premium', is_credit=True)
                admin_id.last_transaction_date = datetime.now()
                admin_id.last_transaction_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                db.session.add(generate, admin_id)
                db.session.commit()
                flash('Successfully shared!', 'success')
                return redirect(url_for('admin_api.mykeys'))
        else:
            flash('Something went wrong with your input', 'info')
            return redirect(url_for('admin_api.management'))
    else:
        abort(404)


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
    elif Transactions.query.filter_by(license_key=key).first is not None:
        reseller_id = Reseller.query.filter_by(user_id=current_user.id).first()
        query = Transactions.query.filter_by(sender_username=current_user.username, license_key=key).first()
        admin_id = Administrator.query.filter_by(user_id=current_user.id).first()
        if admin_id is not None:
            query = Transactions.query.filter_by(license_key=key).first()
            db.session.delete(query)
            db.session.commit()
            flash('Successfully deleted!', 'success')
            return redirect(url_for('admin_api.mykeys'))
        elif query is not None and query.confirmed is False:
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


@api.route('/ban/<string:username>', methods=['GET'])
@login_required
@admin_only
def ban_user(username=None):
    if username is None:
        abort(404)
    elif Administrator.query.filter_by(user_id=current_user.id) is not None:
        query = User.query.filter_by(username=username).first()
        if query is not None:
            query.account_status = 'banned'
            db.session.add(query)
            db.session.commit()
            flash('Successfully banned!', 'success')
            return redirect(url_for('admin_api.users'))
        else:
            abort(404)
    else:
        abort(404)


@api.route('/reset/<string:username>', methods=['GET'])
@login_required
@admin_only
def reset_user(username=None):
    if username is None:
        abort(404)
    elif Administrator.query.filter_by(user_id=current_user.id) is not None:
        query = User.query.filter_by(username=username).first()
        if query is not None:
            query.connection_status = 1
            db.session.add(query)
            db.session.commit()
            flash('Successfully reseted!', 'success')
            return redirect(url_for('admin_api.users'))
        else:
            abort(404)
    else:
        abort(404)


@api.route('/reseller/reset/<string:username>', methods=['GET'])
@login_required
@is_reseller
def reset_user_reseller(username=None):
    if username is None:
        abort(404)
    else:
        query = User.query.filter_by(username=username, under_by=current_user.username).first_or_404()
        if query is not None:
            query.connection_status = 1
            init = Management()
            disconnect_user = init.send(current_user.username, current_user.connected_server_ip, 5555)
            if disconnect_user is None:
                flash('Something went wrong. Please try again later!', 'info')
                return redirect(url_for('home'))
            db.session.add(query)
            db.session.commit()
            flash('Successfully refreshed', 'success')
            return redirect(url_for('admin_api.users'))


@api.route('/delete/<string:username>', methods=['GET'])
@login_required
@admin_only
def delete_user(username=None):
    if username is None:
        abort(404)
    elif Administrator.query.filter_by(user_id=current_user.id) is not None:
        query = User.query.filter_by(username=username).first()
        if query is not None:
            db.session.delete(query)
            db.session.commit()
            flash('Successfully deleted!', 'success')
            return redirect(url_for('admin_api.users'))
        else:
            abort(404)
    else:
        abort(404)


@api.route('/user/delete/<string:username>', methods=['GET'])
@login_required
@is_reseller
def delete_user_reseller(username=None):
    if username is None:
        abort(404)
    else:
        query = User.query.filter_by(username=username, under_by=current_user.username).first_or_404()
        if query is not None:
            db.session.delete(query)
            db.session.commit()
            flash('Successfully deleted!', 'success')
            return redirect(url_for('manage_users'))


@api.route('/account/deactivate', methods=['POST'])
@login_required
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
                              recipients=current_user.email
                              )
                msg.html = render_template('reactivation.html',
                                           confirmation=key)
                mail.send(msg)
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


@api.route('/account/reset', methods=['POST'])
@login_required
def reset_account():
    if request.method == 'POST':
        form = LockAccount()
        if form.validate_on_submit():
            if form.confirm.data == 'YES':
                if current_user.connection_status >= 1:
                    flash('Your account is active! No need to use this', 'warning')
                    return redirect(url_for('home'))
                else:
                    init = Management()
                    disconnect_user = init.send(current_user.username, current_user.connected_server_ip, 5555)
                    if disconnect_user is None:
                        flash('Something went wrong!', 'info')
                        return redirect(url_for('home'))
                    user = current_user
                    user.connection_status = 1
                    db.session.add(user)
                    db.session.commit()
                    flash('Successfully refreshed!', 'info')
                    return redirect(url_for('home'))
            else:
                flash('Please type YES', 'warning')
                return redirect(url_for('home'))
        else:
            flash('Please fill up the form', 'warning')
            return redirect(url_for('home'))
    else:
        abort(404)


@api.route('/manage/profile/info', methods=['POST'])
@login_required
def change_info():
    if request.method == 'POST':
        form = ProfileSettings()
        if form.validate_on_submit():
            query = User.query.filter_by(id=current_user.id).first()
            if query is not None:
                query.first_name = form.first_name.data.title()
                query.last_name = form.last_name.data.title()
                db.session.add(query)
                db.session.commit()
                flash('Successfully changed name!', 'success')
                return redirect(url_for('settings'))
            else:
                flash('Internal Error 106', 'warning')
                return redirect(url_for('settings'))
        else:
            flash('Please fill up the form', 'info')
            return redirect(url_for('settings'))


@api.route('/manage/mypage/info', methods=['POST'])
@login_required
@is_reseller
def change_mypage():
    if request.method == 'POST':
        form = MyPageInfo()
        if form.validate_on_submit():
            query = ProfileInfo.query.filter_by(user_id=current_user.id).first()
            if query is not None:
                query.info = form.info.data
                query.payment_method = form.payment_method.data
                db.session.add(query)
                db.session.commit()
                flash('Successfully changed information!', 'success')
                return redirect(url_for('mypage_settings'))
            else:
                flash('Internal Error 107', 'warning')
                return redirect(url_for('settings'))
        else:
            flash('Please fill up the form', 'info')
            return redirect(url_for('settings'))


@api.route('/manage/mypage/url', methods=['POST'])
@login_required
def change_url():
    if request.method == 'POST':
        form = MyPage()
        if form.validate_on_submit():
            query = ProfileInfo.query.filter_by(user_id=current_user.id).first()
            if query is not None:
                if form.twitter_url.data is not None:
                    query.twitter_url = form.twitter_url.data
                query.facebook_url = form.facebook_url.data
                db.session.add(query)
                db.session.commit()
                flash('Successfully changed information!', 'success')
                return redirect(url_for('mypage_settings'))
            else:
                flash('Internal Error 108', 'warning')
                return redirect(url_for('settings'))
        else:
            flash('Please fill up the form', 'info')
            return redirect(url_for('settings'))
