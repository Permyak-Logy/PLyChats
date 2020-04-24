from flask_wtf import FlaskForm
from flask_wtf.html5 import EmailField
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = EmailField('Логин / почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    name = StringField('Имя*', validators=[DataRequired()])
    surname = StringField('Фамилия*', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    email = EmailField('Логин / почта*', validators=[DataRequired()])
    password = PasswordField('Пароль*', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль*', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class AccountForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    about = TextAreaField('О себе')
    email = EmailField('Логин / Почта')
    phone = StringField('Телефон')
    address = StringField('Адрес')
    submit = SubmitField('Сохранить')


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')


class MessageForm(FlaskForm):
    content = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('Добавить сообщение')
