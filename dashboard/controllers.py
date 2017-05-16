from flask_login import current_user
import humanize
from api.models import Transactions
from datetime import datetime, timedelta
from sqlalchemy import desc


class ProfileView:
    def __init__(self):
        pass

    @staticmethod
    def expiration_date():
        vip_expiration = humanize.naturaldate(datetime.now() + timedelta(
            seconds=current_user.vip_subscription_expiration)
                                              )
        premium_expiration = humanize.naturaldate(datetime.now() + timedelta(
            seconds=current_user.premium_subscription_expiration)
                                                  )
        return premium_expiration, vip_expiration

    @staticmethod
    def upload_profile():
        pass

    @staticmethod
    def convert_second_to_day():
        vip_duration = current_user.vip_subscription_expiration / 86400
        premium_duration = current_user.premium_subscription_expiration / 86400
        return premium_duration, vip_duration

    @staticmethod
    def last_transaction():
        return Transactions.query.filter_by(
            receiver_username=current_user.username
        ).order_by(desc(Transactions.transaction_confirmed_date)).first()

    @staticmethod
    def last_reseller_transaction():
        return Transactions.query.filter_by(
            sender_username=current_user.username
        ).order_by(desc(Transactions.transaction_confirmed_date)).first()

