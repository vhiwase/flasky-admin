import hashlib
from datetime import datetime

from flask import current_app, url_for
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.exceptions import ValidationError

from . import db, login_manager

# from flask import g


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
    """
    UserMixin class that has default implementations of is_authenticated, is_active,
    is_anonymous, get_id(), etc that are appropriate for most cases.
    """

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
    
    # The generate_confirmation_token() method generates a token with 
    # a default validity time of one hour
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    # The confirm() method verifies the token and, if valid, sets 
    # the new confirmed attribute in the user model to True. In addition
    # to verifying the token, the confirm() function checks that the id
    # from the token matches the logged-in user, which is stored in
    # current_user. This ensures that a confirmation token for a given 
    # user cannot be used to confirm a different user.
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

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

    # An expiration time given in seconds is also used to generate token.
    # Here token is decoded using id of the user.
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config["SECRET_KEY"], expires_in=expiration)
        return s.dumps({"id": self.id}).decode("utf-8")

    # This is a static method, as the user will be known only after the token is decoded.
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data["id"])

    def to_json(self):
        # Note : Do not use g.current_user.username in implementation of response.
        # Unit test cases fails when using g.current_user.username
        json_user = {
            "url": url_for("api.get_user", id=self.id),
            "full-url": url_for("api.get_user", id=self.id, _external=True),
            "username": self.username,
            "email": self.email,
            "member_since": self.member_since,
            "last_seen": self.last_seen,
            "confirmed": self.confirmed,
            "name": self.name,
            "location": self.location,
            "about_me": self.about_me,
            "id": self.id
            # 'current_user_username':  g.current_user.username,
        }
        return json_user

    @staticmethod
    def from_json(json_user):
        # check username exist in database
        email = json_user.get("email")
        if email is None or email == "":
            raise ValidationError("please provide valid email address")
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                raise ValidationError("email exist in database")
        # check username exist in database
        username = json_user.get("username")
        if username is None or username == "":
            raise ValidationError("please provide valid username")
        else:
            user = User.query.filter_by(username=username).first()
            if user:
                raise ValidationError("username exist in database")
        # check id exist in database
        id = json_user.get("id")
        if id is None or id == "":
            raise ValidationError("please provide valid user id")
        else:
            user = User.query.filter_by(id=id).first()
            if user:
                raise ValidationError("user id exist in database")
        confirmed = json_user.get("confirmed")
        name = json_user.get("name")
        location = json_user.get("location")
        about_me = json_user.get("about_me")
        return User(
            email=email,
            username=username,
            id=id,
            confirmed=confirmed,
            name=name,
            location=location,
            about_me=about_me,
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

"""
The user identifier will be passed as a string, so the function converts it to
an integer before it passes it to the Flask-SQLAlchemy query that loads the user.
"""


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
