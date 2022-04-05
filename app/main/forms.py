from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, Length, Regexp

from ..models import Role, User


class NameForm(FlaskForm):
    name = StringField("What is your name?", validators=[DataRequired()])
    submit = SubmitField("Submit")


class EditProfileForm(FlaskForm):
    name = StringField("Real name", validators=[Length(0, 64)])
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me")
    submit = SubmitField("Submit")


class EditProfileAdminForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, numbers, dots or " "underscores",
            ),
        ],
    )
    confirmed = BooleanField("Confirmed")
    # The identifier for each tuple in constructor is set to the id of each role, and
    # since these are integers, a coerce=int argument is added to the SelectField
    # constructor so that the field values are stored as integers instead of the
    # default, which is strings.
    role = SelectField("Role", coerce=int)
    name = StringField("Real name", validators=[Length(0, 64)])
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me")
    submit = SubmitField("Submit")

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [
            (role.id, role.name) for role in Role.query.order_by(Role.name).all()
        ]
        self.user = user

    # The validation condition used for email and username fields must first check
    # whether a change to the field was made, and only when there is a change
    # should it ensure that the new value does not duplicate another user’s.
    # To implement this logic, the form’s constructor receives the user object as an
    # argument and saves it as a member variable, which is later used in the
    # custom validation methods.
    def validate_email(self, field):
        if (
            field.data != self.user.email
            and User.query.filter_by(email=field.data).first()
        ):
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if (
            field.data != self.user.username
            and User.query.filter_by(username=field.data).first()
        ):
            raise ValidationError("Username already in use.")


class AddProfileAdminForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, numbers, dots or " "underscores",
            ),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    confirmed = BooleanField("Confirmed")
    role = SelectField("Role", coerce=int)
    name = StringField("Real name", validators=[Length(0, 64)])
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me")
    submit = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        super(AddProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [
            (role.id, role.name) for role in Role.query.order_by(Role.name).all()
        ]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use.")
