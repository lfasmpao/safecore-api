from dashboard import app, db, mail, login_manager
from flask import render_template, redirect, url_for, request, flash
from .models import User, Email, Reseller, Notifications, LockedAccount
from .controllers import ProfileView
from api.controllers import is_reseller
from .forms import LoginForm, RegistrationForm, LicenseKeyForm, BuyLicense, CreateLicense, ActivateCredits, ShareCredits, TrialForm, LockAccount
from flask_login import current_user, login_required, login_user, logout_user
from datetime import datetime, timedelta
from flask_mail import Message
from api import api
from landing_page import signup
from api.models import Updates
from api.models import Transactions, TrialUser, ServerList
from api.controllers import email_key_generator, dateBack


app.register_blueprint(api, subdomain='api')
app.register_blueprint(signup, subdomain='reseller')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', page_title='Page Not Found'), 404


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()


@app.context_processor
def headers():
    if current_user.is_authenticated:
        return dict(version=app.config['API_VERSION'],
                    user_info=current_user,
                    email=current_user.email,
                    duration=ProfileView.expiration_date(),
                    name=current_user.first_name + ' ' + current_user.last_name,
                    profile_pic=url_for('static', filename='img/profile_pictures/%s.jpg' % current_user.username),
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
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
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


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form,
                            captcha={'ip_address': request.environ.get('HTTP_X_REAL_IP',
                                                                       request.remote_addr)})
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        if form.validate_on_submit():
            registered_user = User.query.filter_by(email=form.email.data,
                                                   username=form.username.data
                                                   ).first()
            if registered_user is None:
                verification_code = email_key_generator()
                msg = Message('SafeCore Identity Confirmation',
                              sender="noreply@safecorevpn.com",
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
                flash('Something went wrong! Please check your form and try again', 'warning')
                return redirect(url_for('register'))
    return render_template('register.html', form=form, page_title='Register')


@app.route('/home/')
def home():
    return render_template('dashboard.html', page_title='Dashboard')


@app.route('/serverstatus/')
@app.route('/serverstatus/<int:page>')
@login_required
def server_status(page=1):
    server_list = ServerList.query.paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False).items
    return render_template('server_status.html', server_list=server_list, page_title='Server Status')


@app.route('/info/')
@app.route('/info/<int:page>/')
@login_required
def profile_info(page=1):
    transaction_list = Transactions.query.filter_by(receiver_username=current_user.username).paginate(page,
                                                                                                      app.config['CONTENT_PER_PAGE'],
                                                                                                      error_out=False
                                                                                                      ).items
    return render_template('profile.html', transaction_list=transaction_list, page_title='Subscription Info')


@app.route('/license/manage/')
@login_required
def manage_license():
    form = LicenseKeyForm()
    buy = BuyLicense()
    return render_template('license.html',
                           buy=buy,
                           form=form,
                           last_transaction=ProfileView.last_transaction(),
                           page_title='Manage License Key'
                           )


@app.route('/reseller/create/license')
@login_required
@is_reseller
def create_license():
    credits = Reseller.query.filter_by(user_id=current_user.id).first()
    form = CreateLicense()
    return render_template('create_license.html',
                           credits=credits,
                           last_transaction=ProfileView.last_reseller_transaction(),
                           form=form,
                           page_title='Create New License Key')


@app.route('/reseller/create/trial')
@login_required
@is_reseller
def create_trial():
    form = TrialForm()
    credits = Reseller.query.filter_by(user_id=current_user.id).first()
    return render_template('create_trial.html',
                           credits=credits,
                           form=form,
                           last_transaction=ProfileView.last_transaction(),
                           page_title='Create Trial')


@app.route('/reseller/manage/trial/')
@app.route('/reseller/manage/trial/<int:page>')
@login_required
@is_reseller
def manage_trial(page=1):
    transaction_list = TrialUser.query.filter_by(
        reseller_id=current_user.id
    ).paginate(page, app.config['CONTENT_PER_PAGE'], error_out=False).items

    return render_template('trial_list.html',
                           transaction_list=transaction_list,
                           page_title='Trial Management')


@app.route('/reseller/manage/key/')
@app.route('/reseller/manage/key/<int:page>')
@login_required
@is_reseller
def manage_key(page=1):
    transaction_list = Transactions.query.filter_by(
        sender_username=current_user.username
    ).paginate(page, app.config[ 'CONTENT_PER_PAGE'], error_out=False).items
    return render_template('license_list.html',
                           transaction_list=transaction_list,
                           page_title='License Key Management')


@app.route('/notifications/')
@app.route('/notifications/<int:page>')
@login_required
def notifications(page=1):
    notification_list = Notifications.query.filter_by(user_id=current_user.id).paginate(page,
                                                                                        app.config['CONTENT_PER_PAGE'],
                                                                                        error_out=False
                                                                                        ).items
    return render_template('notification.html', notification_list=notification_list, page_title='Subscription Info')


@app.route('/email/<code>')
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


@app.route('/activate/<code>')
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


@app.route('/settings')
@login_required
def account_settings():
    return render_template('settings.html', page_title='Account Settings')


@app.route('/account/upload/cover')
@login_required
def upload_cover():
    return render_template('settings.html', page_title='Account Settings')


@app.route('/account/upload/profile')
@login_required
def upload_profile():
    return render_template('settings.html', page_title='Account Settings')


@app.route('/account/lock')
@login_required
def lock_account():
    form = LockAccount()
    return render_template('lock_account.html', form=form, page_title='Disable Your Account')


@app.route('/reseller/credits/')
@login_required
@is_reseller
def account_credits():
    form = ActivateCredits()
    user = Reseller.query.filter_by(user_id=current_user.id).first()
    return render_template('credits.html', user=user, last_transaction=ProfileView.last_transaction(), form=form, page_title='Credits')


@app.route('/reseller/share/')
@login_required
@is_reseller
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
