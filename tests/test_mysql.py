import os

import pytest
from flask_migrate import upgrade
from sqlalchemy import func

from app import create_app
from app.extensions import db
from app.models import Solicitacao
from app.services.solicitacoes import criar_solicitacao
from tests.apoio import solicitacao_limpa


def _url_mysql():
    url = os.environ.get("TEST_DATABASE_URL", "")
    return url.startswith("mysql") and "oficina_pecas_test" in url


@pytest.mark.mysql
@pytest.mark.skipif(not _url_mysql(), reason="Defina TEST_DATABASE_URL para o banco oficina_pecas_test")
def test_persistencia_mysql():
    url = os.environ["TEST_DATABASE_URL"]
    aplicacao = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": url,
            "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        },
    )
    with aplicacao.app_context():
        try:
            upgrade()
            solicitacao = criar_solicitacao(
                solicitacao_limpa(
                    responsavel_nome="José Almeida",
                    observacoes_gerais="Persistência MySQL",
                )
            )
            identificador = solicitacao.id
            db.session.expire_all()
            lida = db.session.get(Solicitacao, identificador)
            assert lida is not None
            assert lida.responsavel_nome == "José Almeida"
            assert lida.observacoes_gerais == "Persistência MySQL"
            assert lida.itens[1].quantidade == __import__("decimal").Decimal("2.5")
            assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 1
        finally:
            db.session.rollback()
            db.drop_all()
            db.session.remove()
            db.engine.dispose()
