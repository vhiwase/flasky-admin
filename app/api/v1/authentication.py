from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from ...models import User
from . import api
from .errors import forbidden, unauthorized

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """
    With this implementation, token-based authentication is optional; it is up to each
    client to use it or not. To give view functions the ability to distinguish between
    the two authentication methods a "g.token_used" variable is added.
    """

    # If email_or_token field is blank, an anonymous user is assumed, as before
    if email_or_token == "":
        return False
    # If the password is blank, then the email_or_token field is assumed to be a token
    # and validated as such.
    if password == "":
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    # If email_or_token and password fields are nonempty then
    # regular email and password authentication is assumed.
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


# To ensure that the response is consistent with other errors returned by the APIs
@auth.error_handler
def auth_error():
    return unauthorized("Invalid credentials")


# authentication checks will be done automatically for all the routes in the blueprint.
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden("Unconfirmed account")


# authentication token generation
# Note: Since this route is in the blueprint, the above authentication mechanisms added
# to the before_request handler also apply to it.
@api.route("/tokens/", methods=["POST"])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        """
        To prevent clients from authenticating to this route using a previously
        obtained token instead of an email address and password, the g.token_used
        variable is checked, and requests authenticated with a token are rejected.
        The purpose of this is to prevent users from bypassing the token
        expiration by requesting a new token using the old token as authentication.
        """
        return unauthorized("Invalid credentials")
    return jsonify(
        {
            "token": g.current_user.generate_auth_token(expiration=3600),
            "expiration": 3600,
        }
    )
