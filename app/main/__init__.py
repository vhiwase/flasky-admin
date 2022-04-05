from flask import Blueprint

main = Blueprint("main", __name__)

from ..models import Permission
from . import errors, views


# Permissions may also need to be checked from templates, so the Permission class with all its constants needs to be accessible to them. To avoid having to add a template argument in every render_template() call, a context processor can be used. Context processors make variables available to all templates during rendering.
# adding the Permission class to the template context
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
