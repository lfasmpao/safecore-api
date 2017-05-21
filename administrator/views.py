from . import admin_api
from flask import url_for, redirect, render_template, flash, request
from dashboard import db, app
from api.models import Transactions
from dashboard.forms import CreateLicense, GenerateCredits
from flask_login import login_required, current_user, logout_user
from flask_cors import cross_origin
from dashboard.forms import LockAccount
from api.controllers import admin_only
from dashboard.models import User, Reseller, ProfileInfo
from sqlalchemy import desc


@admin_api.route('/management/panel/')
@login_required
@admin_only
@cross_origin()
def management():
    form = CreateLicense()
    form1 = GenerateCredits()
    return render_template('generate_license.html', form=form, form1=form1, page_title='Administrative Login')


@admin_api.route('/management/panel/list')
@admin_api.route('/management/panel/list/<int:page>')
@login_required
@admin_only
@cross_origin()
def license_list(page=1):
    user_list = Transactions.query.order_by(desc(Transactions.transaction_date)).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
    return render_template('admin_license_list.html', user_list=user_list, page_title='License Key List')


@admin_api.route('/management/panel/user/list')
@admin_api.route('/management/panel/user/list/<int:page>')
@login_required
@admin_only
@cross_origin()
def users(page=1):
    form = LockAccount()
    user_list = User.query.order_by(desc(User.registered_date)).paginate(page, app.config['CONTENT_PER_PAGE'], False)
    return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')


@admin_api.route('/management/panel/user/search/', methods=['GET', 'POST'])
@admin_api.route('/management/panel/user/search/<string:name>/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_only
@cross_origin()
def search_user(name=None, page=1):
    form = LockAccount()
    if request.method == 'POST':
        user_list = User.query.filter_by(username=form.confirm.data).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
        return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')
    else:
        if name is not None:
            user_list = User.query.filter_by(username=name).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
        elif name is None:
            user_list = User.query.all()
        return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')


@admin_api.route('/management/panel/user/mylist')
@admin_api.route('/management/panel/user/mylist/<int:page>')
@login_required
@admin_only
@cross_origin()
def mykeys(page=1):
    user_list = Transactions.query.filter_by(sender_username=current_user.username).order_by(desc(Transactions.transaction_date)).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
    return render_template('my_keys.html', user_list=user_list, page_title='My License List')


@admin_api.route('/management/panel/user/reseller/', methods=['GET', 'POST'])
@admin_api.route('/management/panel/user/reseller/<int:page>/', methods=['GET', 'POST'])
@login_required
@admin_only
@cross_origin()
def make_reseller(page=1):
    form = LockAccount()
    if request.method == 'POST':
        if form.validate_on_submit():
            select_user = User.query.filter_by(username=form.confirm.data).first()
            if select_user is not None:
                user_id = select_user.id
                select_user.is_reseller = True
                query = Reseller(user_id=user_id, credit_count=0, trial_generation_count=60)
                profile_info = ProfileInfo(user_id=user_id)
                db.session.add(query)
                db.session.add(select_user)
                db.session.add(profile_info)
                db.session.commit()
                flash('Successfully created!', 'success')
                return redirect(url_for('admin_api.make_reseller'))
            else:
                flash('Client username is not valid!', 'info')
                return redirect(url_for('admin_api.make_reseller'))
        else:
            flash('Internal error 105!', 'warning')
            return redirect(url_for('admin_api.make_reseller'))
    reseller_list = User.query.filter_by(is_reseller=True).join(Reseller,
                                                                User.id == Reseller.user_id
                                                                ).add_columns(Reseller.credit_count,
                                                                              Reseller.trial_generation_count,
                                                                              User.username,
                                                                              User.email,
                                                                              User.connection_status,
                                                                              User.first_name,
                                                                              User.last_name,
                                                                              User.login_ip,
                                                                              User.login_date,
                                                                              User.privilage_level,
                                                                              User.vip_subscription_expiration,
                                                                              User.premium_subscription_expiration,
                                                                              User.account_status,
                                                                              User.registered_date,

                                                                              ).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
    return render_template('admin_resellers.html', form=form, reseller_list=reseller_list, page_title='Manage Resellers')


@admin_api.route('/management/logout')
@login_required
@admin_only
@cross_origin()
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))