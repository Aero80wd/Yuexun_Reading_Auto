from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, SubmitField
class LoginForm(FlaskForm):
    username = StringField('用户名/手机号', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField("登陆")
