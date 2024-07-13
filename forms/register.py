from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(2, 40)])
    username = StringField("Username", validators=[DataRequired(), Length(5, 20)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(5, 20)])
    password = StringField(
        "Password", validators=[DataRequired(), EqualTo("Confirm_Password")]
    )
    confirm = StringField(
        "Confirm_Password", validators=[DataRequired(), EqualTo("Password")]
    )
