from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=convention))
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.entrar"
login_manager.login_message = "Faça login para acessar o painel."
login_manager.login_message_category = "aviso"
login_manager.session_protection = None


@event.listens_for(Engine, "connect")
def _chaves_estrangeiras_sqlite(conexao, _registro):
    if conexao.__class__.__module__.startswith("sqlite3"):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
