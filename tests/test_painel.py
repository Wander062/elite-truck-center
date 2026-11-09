from datetime import datetime
from uuid import uuid4

from sqlalchemy import func

from app.extensions import db
from app.models import HistoricoStatus, Solicitacao, Usuario
from app.services.solicitacoes import criar_solicitacao
from tests.apoio import extrair_csrf, solicitacao_limpa


def _html(resposta):
    return resposta.get_data(as_text=True)


def test_painel_exige_login_e_mostra_os_dados_recebidos(client, app, conta_escritorio):
    from tests.apoio import confirmar_envio, enviar_para_revisao, entrar

    enviar_para_revisao(client, observacoes_gerais="Texto exclusivo da solicitação")
    destino = confirmar_envio(client)[0].headers["Location"]
    assert client.get("/painel/").status_code == 302
    assert "/entrar" in client.get("/painel/").headers["Location"]

    assert entrar(client, conta_escritorio["usuario"], conta_escritorio["senha"]).status_code == 302
    lista = client.get("/painel/")
    html = _html(lista)
    assert lista.status_code == 200
    assert "ABC1D23" in html
    assert "FH 540" in html
    assert "José Almeida" in html
    assert "2 itens" in html
    assert "SOL-" in html

    with app.app_context():
        solicitacao_id = db.session.scalars(db.select(Solicitacao)).one().id
    detalhe = _html(client.get(f"/painel/solicitacoes/{solicitacao_id}"))
    assert "Texto exclusivo da solicitação" in detalhe
    assert "Filtro de óleo" in detalhe
    assert "Pastilha de freio" in detalhe
    assert "2,5" in detalhe
    assert "Eixo dianteiro" in detalhe
    assert "Frota 12" in detalhe
    assert "Pendente" in detalhe
    assert "Premium TSI" in detalhe
    assert client.get(destino).status_code == 200


def test_pesquisa_por_placa_periodo_e_status(client, app, cliente_escritorio):
    with app.app_context():
        primeira = criar_solicitacao(
            solicitacao_limpa(placa="ABC1D23", modelo="FH 540", chave_envio=str(uuid4()))
        )
        segunda = criar_solicitacao(
            solicitacao_limpa(placa="XYZ9X99", modelo="O500", chave_envio=str(uuid4()))
        )
        segunda_id = segunda.id
        primeira.criado_em = datetime(2026, 11, 7, 2, 0, 0)
        primeira.atualizado_em = primeira.criado_em
        segunda.criado_em = datetime(2026, 11, 7, 15, 0, 0)
        segunda.atualizado_em = segunda.criado_em
        db.session.commit()

    por_placa = _html(client.get("/painel/?placa=xyz9x99"))
    assert "XYZ9X99" in por_placa
    assert "ABC1D23" not in por_placa

    injecao = _html(client.get("/painel/?placa=" + "' OR 1=1 --"))
    assert "ABC1D23" not in injecao
    assert "XYZ9X99" not in injecao

    dia_local = _html(client.get("/painel/?de=2026-11-06&ate=2026-11-06"))
    assert "ABC1D23" in dia_local
    assert "XYZ9X99" not in dia_local
    outro_dia = _html(client.get("/painel/?de=2026-11-07&ate=2026-11-07"))
    assert "ABC1D23" not in outro_dia

    invertido = _html(client.get("/painel/?de=2026-11-08&ate=2026-11-01"))
    assert "não pode ser posterior" in invertido
    assert "ABC1D23" not in invertido

    with app.app_context():
        registro = db.session.get(Solicitacao, segunda_id)
        registro.status = "concluida"
        db.session.commit()
    concluidas = _html(client.get("/painel/?status=concluida"))
    assert "XYZ9X99" in concluidas
    assert "ABC1D23" not in concluidas


def test_alteracao_de_status_so_grava_depois_da_confirmacao(client, app, cliente_escritorio, conta_escritorio):
    from uuid import uuid4

    with app.app_context():
        solicitacao = criar_solicitacao(solicitacao_limpa(chave_envio=str(uuid4())))
        solicitacao_id = solicitacao.id

    detalhe = client.get(f"/painel/solicitacoes/{solicitacao_id}")
    csrf = extrair_csrf(_html(detalhe))
    pedido = client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status",
        data={"csrf_token": csrf, "status": "em_atendimento"},
    )
    assert pedido.status_code == 302
    confirmacao = client.get(pedido.headers["Location"])
    assert "Em atendimento" in _html(confirmacao)
    with app.app_context():
        assert db.session.get(Solicitacao, solicitacao_id).status == "pendente"

    aplicado = client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status/confirmar",
        data={"csrf_token": extrair_csrf(_html(confirmacao))},
        follow_redirects=True,
    )
    assert "Em atendimento" in _html(aplicado)
    assert conta_escritorio["nome"] in _html(aplicado)
    with app.app_context():
        atual = db.session.get(Solicitacao, solicitacao_id)
        assert atual.status == "em_atendimento"
        assert db.session.scalar(db.select(func.count(HistoricoStatus.id))) == 1

    repetido = client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status",
        data={"csrf_token": extrair_csrf(_html(aplicado)), "status": "em_atendimento"},
        follow_redirects=True,
    )
    assert "já está com esse status" in _html(repetido)
    with app.app_context():
        assert db.session.scalar(db.select(func.count(HistoricoStatus.id))) == 1


def test_cancelar_e_status_invalido_nao_alteram(client, app, cliente_escritorio):
    from uuid import uuid4

    with app.app_context():
        solicitacao_id = criar_solicitacao(solicitacao_limpa(chave_envio=str(uuid4()))).id
    csrf = extrair_csrf(_html(client.get(f"/painel/solicitacoes/{solicitacao_id}")))
    client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status",
        data={"csrf_token": csrf, "status": "concluida"},
    )
    client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status/cancelar",
        data={"csrf_token": csrf},
    )
    with app.app_context():
        assert db.session.get(Solicitacao, solicitacao_id).status == "pendente"
        assert db.session.scalar(db.select(func.count(HistoricoStatus.id))) == 0

    invalido = client.post(
        f"/painel/solicitacoes/{solicitacao_id}/status",
        data={"csrf_token": csrf, "status": "<script>"},
        follow_redirects=True,
    )
    assert "Status inválido." in _html(invalido)
    assert "<script>" not in _html(invalido)
    assert client.get(f"/painel/solicitacoes/{solicitacao_id}/status").status_code == 405


def test_perfil_sem_permissao_recebe_403(client, app):
    with app.app_context():
        usuario = Usuario(nome="Visita", usuario="visita", perfil="visitante", ativo=True)
        usuario.definir_senha("senha-segura")
        db.session.add(usuario)
        db.session.commit()
        usuario_id = usuario.id
    with client.session_transaction() as sessao:
        sessao["_user_id"] = str(usuario_id)
        sessao["_fresh"] = True
    resposta = client.get("/painel/")
    assert resposta.status_code == 403
