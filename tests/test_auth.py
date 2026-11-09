from sqlalchemy import func

from app.extensions import db
from app.models import Usuario
from tests.apoio import entrar, extrair_csrf


def _html(resposta):
    return resposta.get_data(as_text=True)


def test_login_senha_errada_e_redirecionamento_interno(client, app, conta_escritorio):
    ruim = entrar(client, "maria", "senha-errada")
    assert ruim.status_code == 200
    assert "Usuário ou senha inválidos." in _html(ruim)
    assert client.get("/painel/").status_code == 302

    pagina = client.get("/entrar?next=https://example.com")
    resposta = client.post(
        "/entrar?next=https://example.com",
        data={
            "csrf_token": extrair_csrf(_html(pagina)),
            "usuario": "maria",
            "senha": "senha-segura",
        },
    )
    assert resposta.status_code == 302
    assert "/painel" in resposta.headers["Location"]
    assert "example.com" not in resposta.headers["Location"]

    painel = _html(client.get("/painel/"))
    assert "scrypt:" not in painel
    with app.app_context():
        usuario = db.session.scalars(db.select(Usuario)).one()
        assert usuario.senha_hash != "senha-segura"
        assert "senha-segura" not in usuario.senha_hash
        assert usuario.verificar_senha("senha-segura")
        assert not usuario.verificar_senha("outra")


def test_usuario_inativo_perde_o_acesso(client, app, conta_escritorio):
    assert entrar(client, "maria", "senha-segura").status_code == 302
    with app.app_context():
        usuario = db.session.scalars(db.select(Usuario)).one()
        usuario.ativo = False
        db.session.commit()
    assert client.get("/painel/").status_code == 302
    novamente = entrar(client, "maria", "senha-segura")
    assert novamente.status_code == 200
    assert "inválidos" in _html(novamente)


def test_sair_encerra_a_sessao(client, conta_escritorio):
    entrar(client, "maria", "senha-segura")
    painel = client.get("/painel/")
    saida = client.post("/sair", data={"csrf_token": extrair_csrf(_html(painel))})
    assert saida.status_code == 302
    assert client.get("/painel/").status_code == 302
    assert client.get("/sair").status_code == 405


def test_comando_cria_administrador_com_senha_hasheada(app):
    runner = app.test_cli_runner()
    criado = runner.invoke(
        args=["criar-usuario", "--nome", "Ana Costa", "--usuario", "ana", "--senha", "senha-segura", "--perfil", "administrador"]
    )
    assert criado.exit_code == 0, criado.output
    with app.app_context():
        usuario = db.session.scalars(db.select(Usuario).where(Usuario.usuario == "ana")).one()
        assert usuario.perfil == "administrador"
        assert usuario.verificar_senha("senha-segura")
        assert usuario.senha_hash != "senha-segura"

    repetido = runner.invoke(
        args=["criar-usuario", "--nome", "Ana Costa", "--usuario", "ana", "--senha", "senha-segura"]
    )
    assert repetido.exit_code != 0
    curta = runner.invoke(
        args=["criar-usuario", "--nome", "Ana Costa", "--usuario", "outra", "--senha", "curta"]
    )
    assert curta.exit_code != 0
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Usuario.id))) == 1
