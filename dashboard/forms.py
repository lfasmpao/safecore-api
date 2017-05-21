from flask_wtf import FlaskForm
from . import app
from wtforms import StringField, PasswordField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange
from wtfrecaptcha.fields import RecaptchaField
from flask_wtf.file import FileField, FileAllowed, FileRequired


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password', validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=40)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=6, max=40)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=40)])
    password = PasswordField('New Password', [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    captcha = RecaptchaField(public_key=app.config['RECAPTCHA_PUB_KEY'], private_key=app.config['RECAPTCHA_PRIV_KEY'],
                             secure=True)


class LicenseKeyForm(FlaskForm):
    category = SelectField('Category', choices=[(1, 'Premium'), (2, 'VIP')], coerce=int)
    license_key = StringField('License Key', validators=[DataRequired(), Length(min=29, max=29)])
    username = StringField('Sender Username', validators=[DataRequired(), Length(min=4, max=40)])


class CreditKeyForm(FlaskForm):
    license_key = StringField('License Key', validators=[DataRequired(), Length(min=29, max=29)])
    username = StringField('Sender Username', validators=[DataRequired(), Length(min=4, max=40)])


class ImageUpload(FlaskForm):
    upload = FileField('Image Upload', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])


class BuyLicense(FlaskForm):
    category = SelectField('Category', choices=[(1, 'VIP'), (2, 'Premium')], coerce=int)
    qty = SelectField('Qty', choices=[(1, '30 Days'), (2, '60 Days'), (3, '90 Days')], coerce=int)


class CreateLicense(FlaskForm):
    category = SelectField('Category', choices=[(1, 'Premium'), (2, 'VIP')], coerce=int)
    qty = SelectField('Qty', choices=[(1, '30 Days'), (2, '60 Days'), (3, '90 Days')], coerce=int)
    valid_date = DateField('Expiration Date', format='%d/%m/%Y', validators=(DataRequired(),))


class ShareCredits(FlaskForm):
    qty = SelectField('Credits', choices=[(1, '10'), (2, '20'), (3, '25')], coerce=int)


class ShareKey(FlaskForm):
    category = SelectField('Category', choices=[(1, 'Premium'), (2, 'VIP')], coerce=int)
    qty = IntegerField('Qty', validators=[DataRequired(), NumberRange(min=1, max=100)])
    valid_date = DateField('Expiration Date', format='%d/%m/%Y', validators=(DataRequired(),))


class GenerateCredits(FlaskForm):
    qty = IntegerField('Credits', validators=[DataRequired(), NumberRange(min=1, max=100)])


class TrialForm(FlaskForm):
    password = StringField('Password', validators=[DataRequired(), Length(min=6, max=29)])


class MyPage(FlaskForm):
    facebook_url = StringField('Facebook', validators=[DataRequired(), Length(min=6, max=29)])
    twitter_url = StringField('Twitter', validators=[Optional(), Length(min=6, max=29)])


class MyPageInfo(FlaskForm):
    info = StringField('Information', validators=[DataRequired()])
    payment_method = StringField('Payment Method', validators=[DataRequired()])


class ChangePassword(FlaskForm):
    password = PasswordField('New Password', [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


class LockAccount(FlaskForm):
    confirm = StringField('Confirm', validators=[DataRequired(), Length(min=3, max=50)])


class ProfileSettings(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=40)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])