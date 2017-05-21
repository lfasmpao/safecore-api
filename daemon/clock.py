import MySQLdb
import time


def connection():
    conn = MySQLdb.connect(host="",
                           user="",
                           passwd="",
                           db="")
    c = conn.cursor()
    return c, conn

c, conn = connection()

print '[*] Daemon Running'

while True:
    c.execute(
        "UPDATE users SET `premium_subscription_expiration` = CASE WHEN `premium_subscription_expiration` <= 60 THEN `premium_subscription_expiration` = 0 ELSE `premium_subscription_expiration` - 60 END, `vip_subscription_expiration` = CASE WHEN `vip_subscription_expiration` <= 60 THEN `vip_subscription_expiration` = 0 ELSE `vip_subscription_expiration` - 60 END"
    )
    c.execute("UPDATE trial_users SET `trial_duration` = CASE WHEN `trial_duration` <= 60 THEN `trial_duration` = 0 ELSE `trial_duration` - 60 END")
    conn.commit()
    time.sleep(60)


