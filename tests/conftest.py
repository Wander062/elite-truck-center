import pytest

from app import create_app
from app.extensions import db
from app.services.usuarios import criar_usuario
from tests.apoio import entrar


@pytest.fixture
def app():
    aplicacao = create_app("testing")
    with aplicacao.app_context():
        db.create_all()
    yield aplicacao
    with aplicacao.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def conta_escritorio(app):
    with app.app_context():
        criar_usuario("Maria Oliveira", "maria", "senha-segura", "escritorio")
    return {"usuario": "maria", "senha": "senha-segura", "nome": "Maria Oliveira"}


@pytest.fixture
def cliente_escritorio(client, conta_escritorio):
    resposta = entrar(client, conta_escritorio["usuario"], conta_escritorio["senha"])
    assert resposta.status_code == 302
    return client
