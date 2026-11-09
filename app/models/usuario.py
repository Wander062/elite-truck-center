from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.tempo import agora_utc


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    usuario = db.Column(db.String(191), nullable=False, unique=True)
    senha_hash = db.Column(db.String(512), nullable=False)
    perfil = db.Column(db.String(32), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha, method="scrypt")

    def verificar_senha(self, senha):
        if not self.senha_hash or not senha:
            return False
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self):
        return bool(self.ativo)

    def __repr__(self):
        return f"<Usuario {self.id} {self.usuario}>"
