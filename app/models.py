import hashlib
from datetime import datetime

from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


# permission constants
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


# role database model
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    users = db.relationship("User", backref="role", lazy="dynamic")
    permissions = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return "<Role %r>" % self.name

    # creating roles in the database
    @staticmethod
    def insert_roles():
        """
        Note that the "Anonymous" role does not need to be represented in the database,
        as it is the role that represents users who are not known and therefore are not
        in the database.
        """
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
            ],
            "Administrator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }
        default_role = "User"
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
            db.session.add(role)
        db.session.commit()

    # permission management in the Role model
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    # user profile information fields
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    # SQLAlchemy invokes the datetime.utcnow function to produce default values
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))

    # Role Assignment: defining a default role for users
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["APP_ADMIN"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    def __repr__(self):
        return "<User %r>" % self.username

    # password hashing in the User model
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Role Verification: evaluating whether a user has a given permission
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # refreshing a user’s last visit time
    # Ref: app/auth/views.py: pinging the logged-in user
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def gravatar_hash(self):
        return (
            self.email and hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()
        )

    def gravatar(self, size=100, default="identicon", rating="g"):
        url = "https://secure.gravatar.com/avatar"
        hash = self.avatar_hash or self.gravatar_hash()
        return "{url}/{hash}?s={size}&d={default}&r={rating}".format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )


# Role Verification: evaluating whether a user has a given permission
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


"""
Role Verification: Flask-Login is told to use the application’s custom anonymous user
by setting its class in the login_manager.anonymous_user attribute.
"""
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login requires the application to designate a function to be invoked when
    the extension needs to load a user from the database given its identifier.
    The login_manager.user_loader decorator is used to register the function with
    Flask-Login, which will call it when it needs to retrieve information about the
    logged-in user.
    """
    return User.query.get(int(user_id))
