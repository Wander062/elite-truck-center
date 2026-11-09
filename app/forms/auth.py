from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class FormularioLogin(FlaskForm):
    usuario = StringField(
        "Usuário ou e-mail",
        validators=[
            DataRequired(message="Informe o usuário ou e-mail."),
            Length(max=191, message="Usuário muito longo."),
        ],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe a senha."),
            Length(max=128, message="Senha muito longa."),
        ],
    )
    entrar = SubmitField("Entrar")
