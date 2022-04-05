from flask import g, jsonify, request

from ...models import Permission, User, db
from . import api
from .decorators import permission_required


@api.route("/users/<int:id>", methods=["GET", "POST"])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route("/add_new_user/", methods=["POST"])
@permission_required(Permission.MODERATE)
def new_user():
    """
    This route creates user with default password user123 with moderator level access.
    This also means that admin and moderator can have access to this API endpoint and
    user access will be forbidden.
    """
    user = User.from_json(request.json)
    user.password = "user123"
    # here we can use g.current_user variable and assign it to a new
    # field of user named "current_user_username" which do not exist in
    # database table and model.User but still database commit will happen
    # without reflecting this change of current_user_username meaning the
    # attribute current_user_username will not exist in response and in database.
    # also note that in model.User.to_json() this
    # attribute ("current_user_username": g.current_user.username)
    # is written and hence it is refelcting from there in the output.
    user.current_user_username = g.current_user.username
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_json())
