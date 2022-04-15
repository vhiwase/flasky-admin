import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hard to guess string"
    APP_ADMIN = os.environ.get("APP_ADMIN", "vaibhav@example.com")
    FLASK_USERS_PER_PAGE = 5
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_SLOW_DB_QUERY_TIME = 0.5
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    FLASK_MAIL_SUBJECT_PREFIX = "[Flask]"
    FLASK_MAIL_SENDER = "Flask Admin <vaibhav.hiwase@celebaltech.com>"
    SSL_REDIRECT = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # log to stderr
        import logging

        # Create formatters and add it to handlers
        log_format = "%(levelname)s - [%(filename)s] - %(asctime)s - %(process)d -  %(lineno)d - %(message)s "
        f_format = logging.Formatter(log_format, datefmt="%d-%b-%y %H:%M:%S")
        # Create handlers
        f_handler = logging.FileHandler("dev-error.log")
        f_handler.setLevel(logging.ERROR)
        f_handler.setFormatter(f_format)
        # Add handlers to the logger
        app.logger.addHandler(f_handler)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL") or "sqlite://"
    WTF_CSRF_ENABLED = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # log to stderr
        import logging

        # Create formatters and add it to handlers
        log_format = "%(levelname)s - [%(filename)s] - %(asctime)s - %(process)d -  %(lineno)d - %(message)s "
        f_format = logging.Formatter(log_format, datefmt="%d-%b-%y %H:%M:%S")
        # Create handlers
        f_handler = logging.FileHandler("test-error.log")
        f_handler.setLevel(logging.ERROR)
        f_handler.setFormatter(f_format)
        # Add handlers to the logger
        app.logger.addHandler(f_handler)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "data.sqlite")

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler

        credentials = None
        secure = None
        if getattr(cls, "MAIL_USERNAME", None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, "MAIL_USE_TLS", None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASK_MAIL_SENDER,
            toaddrs=[cls.APP_ADMIN],
            subject=cls.FLASK_MAIL_SUBJECT_PREFIX + " Application Error",
            credentials=credentials,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class AzureConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get("HTTPS_REDIRECT") else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        # https://github.com/Azure-Samples/ms-identity-python-webapp/issues/16#issuecomment-586164031
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler

        file_handler = StreamHandler()
        log_format = "%(levelname)s - [%(filename)s] - %(asctime)s - %(process)d -  %(lineno)d - %(message)s "
        log_formatter = logging.Formatter(log_format, datefmt="%d-%b-%y %H:%M:%S")
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# class DockerConfig(ProductionConfig):
class DockerConfig(DevelopmentConfig):
    @classmethod
    def init_app(cls, app):
        # ProductionConfig.init_app(app)
        DevelopmentConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler

        file_handler = StreamHandler()
        log_format = "%(levelname)s - [%(filename)s] - %(asctime)s - %(process)d -  %(lineno)d - %(message)s "
        log_formatter = logging.Formatter(log_format, datefmt="%d-%b-%y %H:%M:%S")
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# With this configuration, application logs will be written to the
# configured syslog messages file, typically /var/log/messages or
# /var/log/syslog depending on the Linux distribution.
class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler

        syslog_handler = SysLogHandler()
        log_format = "%(levelname)s - [%(filename)s] - %(asctime)s - %(process)d -  %(lineno)d - %(message)s "
        log_formatter = logging.Formatter(log_format, datefmt="%d-%b-%y %H:%M:%S")
        syslog_handler.setFormatter(log_formatter)
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "azure": AzureConfig,
    "docker": DockerConfig,
    "default": DevelopmentConfig,
}
