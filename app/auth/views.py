from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User
from . import auth
from .forms import LoginForm


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # invoked to record the user as logged in for the user session
            login_user(user, form.remember_me.data)
            # Flask-Login will have saved original URL in next query string argument,
            # which can be accessed from the request.args dictionary
            original_url = request.args.get("next")
            if original_url is None or not original_url.startswith("/"):
                original_url = url_for("main.index")
            return redirect(original_url)
        flash("Invalid username or password.")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))
