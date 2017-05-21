from dashboard import app, db, mail, login_manager
from flask import render_template, redirect, url_for, request, flash, abort
from .models import User, Email, Reseller, Notifications, LockedAccount, ProfileInfo
from .controllers import ProfileView
from api.controllers import is_reseller, nocache
from .forms import LoginForm, RegistrationForm, LicenseKeyForm, BuyLicense, CreateLicense, CreditKeyForm, ShareCredits, TrialForm, LockAccount, ChangePassword, ProfileSettings, ImageUpload, MyPage, MyPageInfo, ShareKey
from flask_login import current_user, login_required, login_user, logout_user
from datetime import datetime, timedelta
from flask_mail import Message
from api import api
from homepage import homepage
from landing_page import signup
from administrator import admin_api
from api.models import Updates
from api.models import Transactions, TrialUser, ServerList
from api.controllers import email_key_generator, dateBack
import PIL
from PIL import Image
from StringIO import StringIO
import os
from flask_cors import cross_origin
from sqlalchemy import desc


app.register_blueprint(api, subdomain='api')
app.register_blueprint(signup, subdomain='signup')
app.register_blueprint(admin_api, subdomain='administrator')
app.register_blueprint(homepage, subdomain='www')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', page_title='Page Not Found'), 404


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()


@app.context_processor
def headers():
    if current_user.is_authenticated:
        query = ServerList.query.filter_by(server_status=True).count()
        return dict(version=app.config['API_VERSION'],
                    user_info=current_user,
                    email=current_user.email,
                    duration=ProfileView.expiration_date(),
                    name=current_user.first_name + ' ' + current_user.last_name,
                    profile_pic=url_for('static', filename='img/profile_pictures/%s.jpg' % current_user.username),
                    server_count=query,
                    updates=Updates.query.all()
                    )
    else:
        return dict(version=app.config['API_VERSION'])


@app.context_processor
def utility_processor():
    def format_date(second):
        from_date = datetime(year=2012, month=4, day=26, hour=8, minute=40, second=45)
        return dateBack(from_date - timedelta(seconds=second), precise=False, fromdate=from_date)
    return dict(format_date=format_date)


@app.route('/')
def index():
    return redirect(url_for('homepage.home'))


@app.route('/', subdomain='cp')
def red_login():
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'], subdomain='cp')
@cross_origin()
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.is_correct_password(form.password.data):
                if user.account_status == 'disabled' or user.account_status == 'banned':
                    flash('Account deactivated or banned!', 'warning')
                    return redirect(url_for('login'))
                else:
                    email_check = Email.query.filter_by(user_id=user.id).first()
                    if email_check is not None and email_check.valid is False:
                        user.authenticated = True
                        user.login_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                        user.login_date = datetime.now()
                        db.session.add(user)
                        db.session.commit()
                        login_user(user)
                        return redirect(url_for('home'))
                    else:
                        flash('Email not yet verified!', 'warning')
                        return redirect(url_for('login'))
            else:
                flash('Invalid email or password!', 'warning')
                return redirect(url_for('login'))
        else:
            flash('Invalid email or password!', 'warning')
    return render_template('login.html', form=LoginForm(), page_title='Login')


@app.route('/register/', methods=['GET', 'POST'], subdomain='cp')
@cross_origin()
def register():
    form = RegistrationForm(request.form,
                            captcha={'ip_address': request.environ.get('HTTP_X_REAL_IP',
                                                                       request.remote_addr)})
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        if form.validate_on_submit():
            restrict_email = form.email.data.split('@')
            if restrict_email[1] == 'gmail.com' or restrict_email[1] == 'yahoo.com':
                registered_email = User.query.filter_by(email=form.email.data).first()
                registered_user = User.query.filter_by(username=form.username.data).first()
                if registered_user is None and registered_email is None:
                    verification_code = email_key_generator()
                    msg = Message('SafeCore Identity Confirmation',
                                  recipients=[form.email.data]
                                  )
                    msg.html = render_template('email.html',
                                               email=form.email.data,
                                               confirmation=verification_code)
                    mail.send(msg)
                    query = User(
                        form.first_name.data,
                        form.last_name.data,
                        form.email.data,
                        form.username.data,
                        form.password.data
                    )
                    email_expiration = datetime.now() + timedelta(days=1)
                    email_verify = Email(user=query,
                                         confirmation_key=verification_code,
                                         registration_date=datetime.now(),
                                         valid=True,
                                         expiration_date=email_expiration
                                         )
                    db.session.add(query, email_verify)
                    db.session.commit()
                    flash('Please check your email for verification!', 'info')
                    return redirect(url_for('login'))
                else:
                    flash('Username or email already exists!', 'warning')
                    return redirect(url_for('register'))
            else:
                flash('We only accept email in Google and Yahoo', 'warning')
                return redirect(url_for('register'))
        else:
            flash('Something went wrong! Please check your form and try again', 'warning')
            return redirect(url_for('register'))
    return render_template('register.html', form=form, page_title='Register')


@app.route('/home/', subdomain='cp')
@login_required
@nocache
def home():
    return render_template('dashboard.html', page_title='Dashboard')


@app.route('/serverstatus/')
@app.route('/serverstatus/<int:page>')
@login_required
@cross_origin()
def server_status(page=1):
    server_list = ServerList.query.paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
    return render_template('server_status.html', server_list=server_list, page_title='Server Status')


@app.route('/info/')
@app.route('/info/<int:page>/')
@login_required
@cross_origin()
def profile_info(page=1):
    transaction_list = Transactions.query.filter_by(receiver_username=current_user.username).paginate(page,
                                                                                                      app.config['CONTENT_PER_PAGE'],
                                                                                                      error_out=False
                                                                                                      )
    return render_template('profile.html', transaction_list=transaction_list, page_title='Subscription Info')


@app.route('/license/manage/', subdomain='cp')
@login_required
@cross_origin()
def manage_license():
    form = LicenseKeyForm()
    buy = BuyLicense()
    return render_template('license.html',
                           buy=buy,
                           form=form,
                           last_transaction=ProfileView.last_transaction(),
                           page_title='Manage License Key'
                           )


@app.route('/license/manage/share/', subdomain='cp')
@login_required
@cross_origin()
def share_license():
    if current_user.under_by is None:
        form = ShareKey()
        return render_template('share.html',
                               form=form,
                               last_transaction=ProfileView.last_transaction(),
                               page_title='Share mySubscription'
                               )
    else:
        abort(404)


@app.route('/license/manage/share/list/', subdomain='cp')
@app.route('/license/manage/share/list/<string:page>', subdomain='cp')
@login_required
@cross_origin()
def share_license_list(page=1):
    if current_user.under_by is None:
        transaction_list = Transactions.query.filter_by(
            sender_username=current_user.username
        ).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
        return render_template('share_list.html',
                               transaction_list=transaction_list,
                               page_title='Manage License Key'
                               )
    else:
        abort(404)

@app.route('/reseller/create/license', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def create_license():
    credits = Reseller.query.filter_by(user_id=current_user.id).first()
    form = CreateLicense()
    return render_template('create_license.html',
                           credits=credits,
                           last_transaction=ProfileView.last_reseller_transaction(),
                           form=form,
                           page_title='Create New License Key')


@app.route('/reseller/create/trial', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def create_trial():
    form = TrialForm()
    credits = Reseller.query.filter_by(user_id=current_user.id).first()
    return render_template('create_trial.html',
                           credits=credits,
                           form=form,
                           last_transaction=ProfileView.last_transaction(),
                           page_title='Create Trial')


@app.route('/reseller/manage/trial/', subdomain='cp')
@app.route('/reseller/manage/trial/<int:page>', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def manage_trial(page=1):
    transaction_list = TrialUser.query.filter_by(
        reseller_id=current_user.id
    ).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)

    return render_template('trial_list.html',
                           transaction_list=transaction_list,
                           page_title='Trial Management')


@app.route('/reseller/manage/key/', subdomain='cp')
@app.route('/reseller/manage/key/<int:page>', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def manage_key(page=1):
    transaction_list = Transactions.query.filter_by(
        sender_username=current_user.username
    ).paginate(page, app.config[ 'CONTENT_PER_PAGE'], error_out=False)
    return render_template('license_list.html',
                           transaction_list=transaction_list,
                           page_title='License Key Management')


@app.route('/notifications/', subdomain='cp')
@app.route('/notifications/<int:page>', subdomain='cp')
@login_required
@cross_origin()
def notifications(page=1):
    notification_list = Notifications.query.filter_by(user_id=current_user.id).paginate(page,
                                                                                        app.config['CONTENT_PER_PAGE'],
                                                                                        error_out=False
                                                                                        )
    return render_template('notification.html', notification_list=notification_list, page_title='Subscription Info')


@app.route('/email/<code>', subdomain='www')
def confirm_email(code):
    user = Email.query.filter_by(confirmation_key=code).first_or_404()
    if user.valid and user.expiration_date >= datetime.now():
        user.valid = False
        flash('Successfully verified email! You can login now!', 'success')
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        flash('Account already activated!', 'warning')
        return redirect(url_for('login'))


@app.route('/activate/<code>', subdomain='www')
def activate_account(code):
    user = LockedAccount.query.filter_by(activation_key=code).first_or_404()
    if user.is_valid:
        user.is_valid = False
        flash('Successfully reactivated! You can login now!', 'success')
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        flash('Activation key is not valid!', 'warning')
        return redirect(url_for('login'))


@app.route('/settings', subdomain='cp')
@login_required
@cross_origin()
def account_settings():
    form = ProfileSettings()
    form1 = ChangePassword()
    return render_template('settings.html', form=form, form1=form1, page_title='Account Settings')


@app.route('/myusers/create', subdomain='cp', methods=['GET', 'POST'])
@login_required
@is_reseller
@cross_origin()
def create_user():
    form = RegistrationForm(request.form,
                            captcha={'ip_address': request.environ.get('HTTP_X_REAL_IP',
                                                                       request.remote_addr)})
    if request.method == 'POST':
        if form.validate_on_submit():
            restrict_email = form.email.data.split('@')
            if restrict_email[1] == 'gmail.com' or restrict_email[1] == 'yahoo.com':
                registered_email = User.query.filter_by(email=form.email.data).first()
                registered_user = User.query.filter_by(username=form.username.data).first()
                if registered_user is None and registered_email is None:
                    verification_code = email_key_generator()
                    query = User(
                        form.first_name.data,
                        form.last_name.data,
                        form.email.data,
                        form.username.data,
                        form.password.data,
                        under_by=current_user.username
                    )
                    email_expiration = datetime.now() + timedelta(days=1)
                    email_verify = Email(user=query,
                                         confirmation_key=verification_code,
                                         registration_date=datetime.now(),
                                         valid=False,
                                         expiration_date=email_expiration
                                         )
                    db.session.add(query, email_verify)
                    db.session.commit()
                    flash('User Created Successfully!', 'info')
                    return redirect(url_for('create_user'))
                else:
                    flash('Username or email already exists!', 'warning')
                    return redirect(url_for('create_user'))
            else:
                flash('We only accept email in Google and Yahoo', 'warning')
                return redirect(url_for('create_user'))
        else:
            flash('Something went wrong! Please check your form and try again', 'warning')
            return redirect(url_for('create_user'))

    return render_template('create_user.html', form=form, page_title='Create User')


@app.route('/myusers/search', methods=['GET', 'POST'])
@app.route('/myusers/search/<string:name>', methods=['GET', 'POST'])
@login_required
@is_reseller
@cross_origin()
def search_user(name=None, page=1):
    form = LockAccount()
    if request.method == 'POST':
        user_list = User.query.filter_by(username=form.confirm.data, under_by=current_user.username).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
        return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')
    else:
        if name is not None:
            user_list = User.query.filter_by(username=name, under_by=current_user.username).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False)
        else:
            abort(404)
        return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')


@app.route('/myusers/list')
@app.route('/myusers/list/<int:page>')
@login_required
@is_reseller
@cross_origin()
def manage_users(page=1):
    form = LockAccount()
    user_list = User.query.filter_by(under_by=current_user.username).order_by(desc(User.registered_date)).paginate(page, app.config['CONTENT_PER_PAGE'], False)
    return render_template('user_list.html', form=form, user_list=user_list, page_title='User List')


@app.route('/reseller/mypage/settings', subdomain='cp')
@login_required
@cross_origin()
def mypage_settings():
    form = MyPageInfo()
    form1 = MyPage()
    query = ProfileInfo.query.filter_by(user_id=current_user.id).first()
    return render_template('mypage_settings.html', query=query, form=form, form1=form1, page_title='My Page Settings')


@app.route('/account/upload/cover', methods=['GET', 'POST'], subdomain='cp')
@login_required
@cross_origin()
def upload_cover():
    form = ImageUpload()
    if request.method == 'POST':
        if form.validate_on_submit():
            location = 'cover_photos/'
            img = form.upload.data
            img.save(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_cover_temp'+'.jpg')
            filename = StringIO(open(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_cover_temp'+'.jpg', 'rb').read())
            img = Image.open(filename)
            img = img.resize((1500, 1125), PIL.Image.ANTIALIAS)
            img.save(app.config['UPLOAD_FOLDER'] + location + current_user.username + '.jpg')
            os.remove(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_cover_temp'+'.jpg')
            flash('Profile successfully updated!', 'success')
            return redirect(url_for('upload_profile'))
        else:
            flash('Please upload an image file!', 'warning')
            return redirect(url_for('upload_profile'))
    return render_template('upload.html', type=2, form=form, page_title='Account Settings')


@app.route('/account/upload/profile', methods=['GET', 'POST'], subdomain='cp')
@login_required
@cross_origin()
def upload_profile():
    form = ImageUpload()
    if request.method == 'POST':
        if form.validate_on_submit():
            base_width = 300
            location = 'profile_pictures/'
            img = form.upload.data
            img.save(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_temp'+'.jpg')
            filename = StringIO(open(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_temp'+'.jpg', 'rb').read())
            img = Image.open(filename)
            percent = base_width / float(img.size[0])
            height = int((float(img.size[1]) * float(percent)))
            img = img.resize((base_width, height), PIL.Image.ANTIALIAS)
            img.save(app.config['UPLOAD_FOLDER'] + location + current_user.username + '.jpg')
            os.remove(app.config['UPLOAD_FOLDER']+'tmp/'+current_user.username+'_temp'+'.jpg')
            flash('Profile successfully updated!', 'success')
            return redirect(url_for('upload_profile'))
        else:
            flash('Please upload an image file!', 'warning')
            return redirect(url_for('upload_profile'))
    return render_template('upload.html', type=1, form=form, page_title='Account Settings')


@app.route('/account/lock', subdomain='cp')
@login_required
@cross_origin()
def lock_account():
    form = LockAccount()
    return render_template('lock_account.html', form=form, page_title='Disable Your Account')


@app.route('/account/reset', subdomain='cp')
@login_required
@cross_origin()
def reset_account():
    form = LockAccount()
    return render_template('reset_account.html', form=form, page_title='Disable Your Account')


@app.route('/reseller/credits/', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def account_credits():
    form = CreditKeyForm()
    user = Reseller.query.filter_by(user_id=current_user.id).first()
    return render_template('credits.html', user=user, last_transaction=ProfileView.last_transaction(), form=form, page_title='Credits')


@app.route('/reseller/share/', subdomain='cp')
@login_required
@is_reseller
@cross_origin()
def share_credits():
    form = ShareCredits()
    credits = Reseller.query.filter_by(user_id=current_user.id).first()
    return render_template('share_credits.html', credits=credits, last_transaction=ProfileView.last_transaction(), form=form, page_title='Share Credits')


@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))
