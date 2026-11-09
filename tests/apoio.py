import re
import uuid

def extrair_csrf(html):
    padroes = (
        r'name="csrf_token"[^>]*value="([^"]+)"',
        r'value="([^"]+)"[^>]*name="csrf_token"',
    )
    for padrao in padroes:
        encontrado = re.search(padrao, html)
        if encontrado:
            return encontrado.group(1)
    raise AssertionError("Token CSRF não encontrado")


def extrair_chave(html):
    encontrado = re.search(r'name="chave_envio"[^>]*value="([^"]+)"', html)
    if not encontrado:
        raise AssertionError("Chave de envio não encontrada")
    return encontrado.group(1)


def dados_formulario(chave, csrf, **trocas):
    dados = {
        "csrf_token": csrf,
        "chave_envio": chave,
        "placa": "ABC1D23",
        "tipo_veiculo": "caminhao",
        "marca": "Volvo",
        "modelo": "FH 540",
        "identificacao_adicional": "Frota 12",
        "responsavel_nome": "José Almeida",
        "observacoes_gerais": "Barulho no freio dianteiro",
        "item_descricao": ["Filtro de óleo", "Pastilha de freio"],
        "item_quantidade": ["1", "2,5"],
        "item_unidade": ["UN", "JOGO"],
        "item_observacao": ["Motor", "Eixo dianteiro"],
    }
    dados.update(trocas)
    return dados


def solicitacao_limpa(**trocas):
    dados = {
        "chave_envio": str(uuid.uuid4()),
        "placa": "ABC1D23",
        "placa_fora_padrao": False,
        "tipo_veiculo": "caminhao",
        "marca": "Volvo",
        "modelo": "FH 540",
        "identificacao_adicional": "Frota 12",
        "responsavel_nome": "José Almeida",
        "observacoes_gerais": "Barulho no freio dianteiro",
        "excedeu_itens": False,
        "itens": [
            {"descricao": "Filtro de óleo", "quantidade": "1", "unidade": "UN", "observacao": "Motor"},
            {"descricao": "Pastilha de freio", "quantidade": "2,5", "unidade": "JOGO", "observacao": "Eixo dianteiro"},
        ],
    }
    dados.update(trocas)
    return dados


def entrar(client, usuario, senha):
    html = client.get("/entrar").get_data(as_text=True)
    return client.post(
        "/entrar",
        data={"csrf_token": extrair_csrf(html), "usuario": usuario, "senha": senha},
    )


def enviar_para_revisao(client, **trocas):
    pagina = client.get("/")
    assert pagina.status_code == 200
    html = pagina.get_data(as_text=True)
    dados = dados_formulario(extrair_chave(html), extrair_csrf(html), **trocas)
    resposta = client.post("/", data=dados)
    return resposta, dados


def confirmar_envio(client):
    revisao = client.get("/revisao")
    assert revisao.status_code == 200, revisao.get_data(as_text=True)
    html = revisao.get_data(as_text=True)
    resposta = client.post("/revisao/confirmar", data={"csrf_token": extrair_csrf(html)})
    return resposta, html
