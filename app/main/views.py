from datetime import datetime

from flask import flash, redirect, render_template, session, url_for, current_app
from flask_login import current_user, login_required
from flask_sqlalchemy import get_debug_queries

from .. import db
from ..decorators import admin_required
from ..models import Role, User
from . import main
from .forms import AddProfileAdminForm, EditProfileAdminForm, EditProfileForm, NameForm

# Logging Slow Database Performance
@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASK_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                    (query.statement, query.parameters, query.duration,
                     query.context))
    return response


@main.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = NameForm()
    if form.validate_on_submit():
        # name = form.name.data
        # old_name = session.get('name')
        # if old_name is not None and old_name != form.name.data:
        # flash('Looks like you have changed your name!')
        user = User.query.filter_by(username=form.name.data).first()
        session["name"] = form.name.data
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session["known"] = False
        else:
            session["known"] = True
        form.name.data = ""
        return redirect(url_for(".index"))
    return render_template(
        "index.html",
        form=form,
        name=session.get("name"),
        known=session.get("known", False),
        current_time=datetime.utcnow(),
    )


@main.route("/user/<username>")
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user)


@main.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash("Your profile has been updated.")
        return redirect(url_for("main.user", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", form=form)


@main.route("/edit-profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash("The profile has been updated.")
        return redirect(url_for("main.user", username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template("edit_profile.html", form=form, user=user)


@main.route("/create-profile/", methods=["GET", "POST"])
@login_required
@admin_required
def create_profile_admin():
    user = User()
    form = AddProfileAdminForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.password = form.password.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash("The profile has been created.")
        return redirect(url_for("main.user", username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template("create_profile.html", form=form, user=user)


@main.route("/show-profile/", methods=["GET", "POST"])
@login_required
@admin_required
def show_profile_admin():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("show_profiles.html", users=users)


@main.route("/delete-profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def delete_profile_admin(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("main.show_profile_admin"))
