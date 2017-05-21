from dashboard import mail, db
from flask import render_template, redirect, url_for, request, flash, abort
from dashboard.models import User, Email, Notifications, ProfileInfo
from api.controllers import email_key_generator
from dashboard.forms import RegistrationForm
from flask_login import current_user
from datetime import datetime, timedelta
from flask_mail import Message
from . import signup


@signup.route('/')
@signup.route('/<string:name>')
def landing_page(name=None):
    if name is None:
        abort(404)
    query = User.query.filter_by(is_reseller=True, username=name).join(ProfileInfo, User.id == ProfileInfo.user_id).add_columns(User.first_name,
                                                                                                                                User.username,
                                                                                                                                User.last_name,
                                                                                                                                User.email,
                                                                                                                                ProfileInfo.facebook_url,
                                                                                                                                ProfileInfo.twitter_url,
                                                                                                                                ProfileInfo.payment_method,
                                                                                                                                ProfileInfo.info,
                                                                                                                                ).first()
    if query is not None and User.account_status is not 'banned' or User.account_status is not 'deactivated':
        return render_template('my_page.html', query=query, page_title=query.first_name + ' ' + query.last_name)
    else:
        abort(404)


@signup.route('/<string:name>/signup')
def signup_page(name=None):
    form = RegistrationForm(request.form,
                            captcha={'ip_address': request.environ.get('HTTP_X_REAL_IP',
                                                                       request.remote_addr)})
    if name is None:
        abort(404)
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        if name is None:
            abort(404)
        if form.validate_on_submit():
            query = User.query.filter_by(is_reseller=True, username=name).first_or_404()
            email = form.email.data
            restrict_email = email.split('@')
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
                        form.password.data,
                        query.username
                    )

                    email_expiration = datetime.now() + timedelta(days=1)
                    email_verify = Email(user=query,
                                         confirmation_key=verification_code,
                                         registration_date=datetime.now(),
                                         valid=True,
                                         expiration_date=email_expiration
                                         )
                    notify = Notifications(user_id=query.id, notification_type='signup', confirmed_date=datetime.now(),
                                           notification_ip=request.environ.get('HTTP_X_REAL_IP',
                                                                               request.remote_addr))

                    db.session.add(query, email_verify, notify)
                    db.session.commit()
                    flash('Please check your email for verification!', 'info')
                    return redirect(url_for('login'))
                else:
                    flash('Username or email already exists!', 'warning')
                    return redirect(url_for('reseller.signup_page'))
            else:
                flash('We only accept email in Google and Yahoo', 'warning')
                return redirect(url_for('reseller.signup_page'))
        else:
            flash('Something went wrong! Please check your form and try again', 'warning')
            return redirect(url_for('reseller.signup_page'))
    form = RegistrationForm(request.form,
                            captcha={'ip_address': request.environ.get('HTTP_X_REAL_IP',
                                                                       request.remote_addr)})
    query = User.query.filter_by(is_reseller=True, username=name).first_or_404()
    if query.account_status == 'banned' or query.account_status == 'deactivated':
        abort(404)
    else:
        return render_template('my_page_signup.html', query=User.query.filter_by(is_reseller=True, username=name).first_or_404(), form=form, page_title='Register under ' + query.username)
