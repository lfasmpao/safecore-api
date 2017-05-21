# SafeCore Web API
### Version
1.1

OpenVPN User Management System

# Features!
  - User Management
  - Administration Panel
  - Fully Functional Mailing System
  - Login and Sign-up System
  - myPage (Referral signup link)
  - mySubscription  (Subscription Sharing)
  - Reseller Panel (Reselling From)
  - System Update Notification
 
### Installation

Our Web API requires [Python](http://python.org/) v2.7+ to run.

Install the dependencies and configure "app_config.py" and start the server.

Installing Dependencies

Linux:
```sh
$ apt-get install python-pip
$ pip install -r requirements.txt
```

Windows:
```sh
$ python -m pip install -r requirements-win.txt
```

Run:
```sh
$ cd safecore-api
$ python migrate.py
$ python run.py
```

### Plugins

Our Web API is currently extended with the following plugins. Instructions on how to use them in your own application are linked below.

| Plugin | README |
| ------ | ------ |
| Flask | https://pypi.python.org/pypi/Flask |
| SQLAlchemy | https://pypi.python.org/pypi/SQLAlchemy |
| Humanize | https://pypi.python.org/pypi/humanize |
| Flask-Login | https://pypi.python.org/pypi/flask-login |
| Flask-WTF | https://pypi.python.org/pypi/flask-wtf |


### Development

Want to contribute? Great!
Just commit your code corrections and improvement

### Conditions

By using this code you must agree to this conditions
   - You must not remove the authors name 
   -

License
----
GNU Affero General Public License v3.0