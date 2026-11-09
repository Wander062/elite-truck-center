from pathlib import Path

from flask_migrate import upgrade
from sqlalchemy import func

from app import create_app
from app.extensions import db
from app.models import Solicitacao
from app.services.solicitacoes import criar_solicitacao
from tests.apoio import solicitacao_limpa


def test_migracao_cria_e_grava(tmp_path):
    banco = Path(tmp_path) / "oficina.db"
    aplicacao = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + banco.as_posix(),
            "SQLALCHEMY_ENGINE_OPTIONS": {},
        },
    )
    with aplicacao.app_context():
        upgrade()
        criada = criar_solicitacao(solicitacao_limpa())
        assert criada.protocolo.startswith("SOL-")
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 1
        db.session.remove()
        db.engine.dispose()
