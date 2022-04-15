from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from config import config

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()

# Flask-Login is initialized in the application factory function.
login_manager = LoginManager()
"""
The login_view attribute of the LoginManager object sets the endpoint
for the login page. Flask-Login will redirect to the login page when
an anonymous user tries to access a protected page. Because the login
route is inside a blueprint, it needs to be prefixed with the blueprint
name.
"""
login_manager.login_view = "auth.login"


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    login_manager.init_app(app)

    if app.config["SSL_REDIRECT"]:
        from flask_sslify import SSLify

        sslify = SSLify(app)

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .api.v1 import api as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix="/api/v1")

    # attach routes and custom error pages here

    return app
