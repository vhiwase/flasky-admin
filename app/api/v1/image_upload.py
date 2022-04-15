from . import api
from .authentication import auth


@api.route("/some-endpoint/")
@auth.login_required
def get_method():
    """
    But since all the routes in the blueprint need to be protected in the same
    way, the login_required decorator can be included once in a before_request
    handler for the blueprint.
    """
    pass
