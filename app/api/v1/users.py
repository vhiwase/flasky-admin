from flask import current_app, g, jsonify, request, url_for

from ...models import Permission, User, db
from . import api
from .decorators import permission_required


@api.route("/users/")
def get_users():
    users = User.query.all()
    return jsonify({"users": [user.to_json() for user in users]})


@api.route("/users/<int:id>")
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
    user.current_user_username = g.current_user.username
    """
    here we can use g.current_user variable and assign it to a new
    field of user named "current_user_username" which do not exist in
    database table and model.User but still database commit will happen
    without reflecting this change of current_user_username meaning the
    attribute current_user_username will not exist in response and in database.
    """
    db.session.add(user)
    db.session.commit()
    """
    A user  is created from the JSON data. After the model is written to the database,
    a 201 status code is returned and a Location header is added with the URL of the
    newly created resource.
    """
    return (
        jsonify(user.to_json()),
        201,
        {"Location": url_for("api.get_user", id=user.id)},
    )


@api.route("/users_per_page/")
def get_users_per_page():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.paginate(
        page, per_page=current_app.config["FLASK_USERS_PER_PAGE"], error_out=False
    )
    users = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for("api.get_users_per_page", page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for("api.get_users_per_page", page=page + 1)
    return jsonify(
        {
            "posts": [user.to_json() for user in users],
            "prev_url": prev,
            "next_url": next,
            "count": pagination.total,
        }
    )
