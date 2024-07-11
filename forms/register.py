from wtforms import Form, StringField, PasswordField,validators

class RegisterForm(Form):
    name = StringField('Name',[
        validators.required(), validators.Length(min=1,max=60)])
    username = StringField('Username',[
        validators.required(), validators.Length(min=5,max=20)])
    email = StringField('Email',[
        validators.required(),validators.Email(), validators.Length(min=4,max=40)])
    password = PasswordField('Password',[
        validators.required(),validators.EqualTo('confirm',message='password do not match')
    ])
    confirm = PasswordField('Confirm_Password')


    