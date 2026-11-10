from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import Solicitacao
from tests.apoio import confirmar_envio, dados_formulario, enviar_para_revisao, extrair_chave, extrair_csrf


def _html(resposta):
    return resposta.get_data(as_text=True)


def test_envio_com_varias_pecas_fica_gravado(client, app):
    resposta, _dados = enviar_para_revisao(client)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/revisao")

    confirmacao, revisao = confirmar_envio(client)
    assert "Filtro de óleo" in revisao
    assert "Pastilha de freio" in revisao
    assert "2,5" in revisao
    assert "José Almeida" in revisao
    assert "Frota 12" in revisao
    assert confirmacao.status_code == 302
    assert "/solicitacao/" in confirmacao.headers["Location"]

    pagina = client.get(confirmacao.headers["Location"])
    html = _html(pagina)
    assert pagina.status_code == 200
    assert "SOL-" in html
    assert "ABC1D23" in html
    assert "Filtro de óleo" in html
    assert "2,5" in html
    assert "Barulho no freio dianteiro" in html
    assert "Solicitação registrada" in html

    with app.app_context():
        solicitacoes = db.session.scalars(db.select(Solicitacao)).all()
        assert len(solicitacoes) == 1
        itens = list(solicitacoes[0].itens)
        assert [item.descricao for item in itens] == ["Filtro de óleo", "Pastilha de freio"]
        assert itens[1].quantidade == Decimal("2.5")
        assert itens[1].unidade == "JOGO"
        assert solicitacoes[0].status == "pendente"
        assert solicitacoes[0].responsavel_nome == "José Almeida"


def test_placa_antiga_e_identificacao_fora_do_padrao(client, app):
    resposta, _dados = enviar_para_revisao(client, placa="abc-1234")
    assert resposta.status_code == 302
    confirmar_envio(client)
    with app.app_context():
        assert db.session.scalars(db.select(Solicitacao)).one().placa == "ABC-1234"

    resposta, _dados = enviar_para_revisao(client, placa="frota 12", placa_fora_padrao="1")
    assert resposta.status_code == 302
    confirmar_envio(client)
    with app.app_context():
        placas = {item.placa for item in db.session.scalars(db.select(Solicitacao))}
    assert "FROTA 12" in placas


def test_rejeita_obrigatorios_e_nao_grava(client, app):
    _resposta, dados = enviar_para_revisao(client, marca="", modelo="", responsavel_nome="")
    assert _resposta.status_code == 400
    html = _html(_resposta)
    assert "Informe a marca." in html
    assert "Informe o modelo." in html
    assert "Informe o nome do responsável." in html
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 0

    resposta, _dados = enviar_para_revisao(
        client,
        item_descricao=[""],
        item_quantidade=["1"],
        item_unidade=["UN"],
        item_observacao=[""],
    )
    assert resposta.status_code == 400
    assert "Adicione ao menos uma peça." in _html(resposta)


def test_nao_duplica_quando_a_chave_e_reenviada(client, app):
    _resposta, dados = enviar_para_revisao(client)
    confirmar_envio(client)
    html = _html(client.get("/"))
    dados["csrf_token"] = extrair_csrf(html)
    dados["marca"] = ""
    repetido = client.post("/", data=dados, follow_redirects=True)
    assert repetido.status_code == 200
    assert "já foi enviada" in _html(repetido)
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 1

    novo = client.post("/", data=dados_formulario(extrair_chave(html), extrair_csrf(html)))
    assert novo.status_code == 302
    confirmar_envio(client)
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 2


def test_corrigir_antes_de_confirmar_altera_o_rascunho(client, app):
    enviar_para_revisao(client)
    edicao = client.get("/?editar=1")
    assert 'value="Volvo"' in _html(edicao)
    html = _html(edicao)
    from tests.apoio import extrair_chave

    dados = dados_formulario(extrair_chave(html), extrair_csrf(html), marca="Scania")
    resposta = client.post("/", data=dados)
    assert resposta.status_code == 302
    revisao = _html(client.get("/revisao"))
    assert "Scania" in revisao
    confirmar_envio(client)
    with app.app_context():
        assert db.session.scalars(db.select(Solicitacao)).one().marca == "Scania"


def test_descartar_revisao_nao_grava(client, app):
    enviar_para_revisao(client)
    client.get("/")
    resposta = client.post("/revisao/confirmar", data={"csrf_token": extrair_csrf(_html(client.get("/entrar")))})
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 0


def test_post_sem_csrf_nao_grava(client, app):
    resposta = client.post("/", data={"placa": "ABC1D23"})
    assert resposta.status_code == 400
    assert "Sessão expirada" in _html(resposta)
    with app.app_context():
        assert db.session.scalar(db.select(func.count(Solicitacao.id))) == 0


def test_confirmacao_nao_expoe_outra_solicitacao(client):
    enviar_para_revisao(client, item_observacao=["PECA-UNICA-ALFA", "Eixo"])
    primeira = confirmar_envio(client)
    enviar_para_revisao(client, item_observacao=["PECA-UNICA-BETA", "Eixo"])
    segunda = confirmar_envio(client)
    html_primeira = _html(client.get(primeira[0].headers["Location"]))
    assert "PECA-UNICA-ALFA" in html_primeira
    assert "PECA-UNICA-BETA" not in html_primeira
    assert client.get("/solicitacao/nao-e-um-uuid").status_code == 404
    assert client.get("/solicitacao/" + "a" * 36).status_code == 404


def test_escapa_html_da_observacao(client):
    enviar_para_revisao(client, observacoes_gerais="<script>alert('x')</script>")
    confirmacao, _revisao = confirmar_envio(client)
    html = _html(client.get(confirmacao.headers["Location"]))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
