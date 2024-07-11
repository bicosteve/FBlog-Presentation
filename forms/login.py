from wtforms import Form, StringField,  PasswordField,BooleanField,validators

class LoginForm(Form):
	email = StringField('Email',[
        validators.required(),validators.Email(), validators.Length(min=4,max=40)])
	password = PasswordField('Password',[
        validators.required()])
	remember = BooleanField('Remember Me')
	#submit = SubmitField('Login')