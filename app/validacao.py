"""Validação do formulário público.

As peças são uma lista dinâmica, então a checagem fica aqui em vez de um
FieldList fixo. O CSRF continua a cargo do Flask-WTF em toda requisição POST.
"""

import re
import uuid
from decimal import Decimal

from app.constants import (
    MAX_DESCRICAO_PECA,
    MAX_IDENTIFICACAO,
    MAX_ITENS,
    MAX_MARCA,
    MAX_MODELO,
    MAX_OBSERVACAO_PECA,
    MAX_OBSERVACOES,
    MAX_RESPONSAVEL,
    TIPOS_VALIDOS,
    UNIDADES_VALIDAS,
)
from app.erros import DadosInvalidos
from app.formatacao import formatar_quantidade

CHAVE_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PLACA_ANTIGA = re.compile(r"^[A-Z]{3}\d{4}$")
PLACA_MERCOSUL = re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$")
QUANTIDADE_RE = re.compile(r"^\d{1,5}([.,]\d{1,3})?$")
USUARIO_RE = re.compile(r"^[a-z0-9][a-z0-9._@+-]{2,190}$")


def limpar_texto(valor, quebras=False):
    if valor is None:
        return ""
    texto = str(valor).replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto).strip()
    if quebras:
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        return texto
    return re.sub(r"\s+", " ", texto)


def validar_nome_pessoa(valor):
    nome = limpar_texto(valor)
    if not 3 <= len(nome) <= 120 or not re.search(r"[A-Za-zÀ-ÿ]", nome):
        return None
    return nome


def formulario_vazio():
    return {
        "chave_envio": str(uuid.uuid4()),
        "placa": "",
        "placa_fora_padrao": False,
        "tipo_veiculo": "",
        "marca": "",
        "modelo": "",
        "identificacao_adicional": "",
        "responsavel_nome": "",
        "observacoes_gerais": "",
        "itens": [_item_vazio()],
        "excedeu_itens": False,
    }


def rascunho_para_formulario(rascunho):
    return {
        "chave_envio": rascunho["chave_envio"],
        "placa": rascunho["placa"],
        "placa_fora_padrao": bool(rascunho["placa_fora_padrao"]),
        "tipo_veiculo": rascunho["tipo_veiculo"],
        "marca": rascunho["marca"],
        "modelo": rascunho["modelo"],
        "identificacao_adicional": rascunho.get("identificacao_adicional") or "",
        "responsavel_nome": rascunho["responsavel_nome"],
        "observacoes_gerais": rascunho.get("observacoes_gerais") or "",
        "itens": [
            {
                "descricao": item["descricao"],
                "quantidade": formatar_quantidade(item["quantidade"]).replace("—", ""),
                "unidade": item.get("unidade") or "",
                "observacao": item.get("observacao") or "",
            }
            for item in rascunho["itens"]
        ],
        "excedeu_itens": False,
    }


def dados_publicos_do_formulario(formulario):
    descricoes = formulario.getlist("item_descricao")
    quantidades = formulario.getlist("item_quantidade")
    unidades = formulario.getlist("item_unidade")
    observacoes = formulario.getlist("item_observacao")
    excedeu = any(len(lista) > MAX_ITENS for lista in (descricoes, quantidades, unidades, observacoes))
    total = max(len(descricoes), len(quantidades), len(unidades), len(observacoes), 1)
    if total > MAX_ITENS:
        total = MAX_ITENS
        excedeu = True

    def pegar(lista, indice):
        return lista[indice] if indice < len(lista) else ""

    return {
        "chave_envio": (formulario.get("chave_envio") or "").strip(),
        "placa": formulario.get("placa") or "",
        "placa_fora_padrao": formulario.get("placa_fora_padrao") in {"1", "on", "true", "sim"},
        "tipo_veiculo": formulario.get("tipo_veiculo") or "",
        "marca": formulario.get("marca") or "",
        "modelo": formulario.get("modelo") or "",
        "identificacao_adicional": formulario.get("identificacao_adicional") or "",
        "responsavel_nome": formulario.get("responsavel_nome") or "",
        "observacoes_gerais": formulario.get("observacoes_gerais") or "",
        "itens": [
            {
                "descricao": pegar(descricoes, indice),
                "quantidade": pegar(quantidades, indice),
                "unidade": pegar(unidades, indice),
                "observacao": pegar(observacoes, indice),
            }
            for indice in range(total)
        ],
        "excedeu_itens": excedeu,
    }


def validar_solicitacao(dados):
    erros = {}
    chave = str((dados or {}).get("chave_envio") or "").strip().lower()
    if not CHAVE_RE.fullmatch(chave):
        erros["chave_envio"] = "Atualize a página e preencha a solicitação novamente."

    fora_padrao = (dados or {}).get("placa_fora_padrao") in {True, "1", "on", "true", "sim"}
    if fora_padrao:
        placa = _identificacao_livre((dados or {}).get("placa"))
        if placa is None:
            erros["placa"] = "Informe a identificação do veículo (mínimo de 2 caracteres)."
    else:
        placa = _placa_padrao((dados or {}).get("placa"))
        if placa is None:
            erros["placa"] = "Informe a placa no padrão antigo (ABC-1234) ou Mercosul (ABC1D23)."

    tipo = str((dados or {}).get("tipo_veiculo") or "").strip()
    if tipo not in TIPOS_VALIDOS:
        erros["tipo_veiculo"] = "Selecione o tipo de veículo."

    marca = limpar_texto((dados or {}).get("marca"))
    if not 2 <= len(marca) <= MAX_MARCA:
        erros["marca"] = "Informe a marca."

    modelo = limpar_texto((dados or {}).get("modelo"))
    if not 1 <= len(modelo) <= MAX_MODELO:
        erros["modelo"] = "Informe o modelo."

    identificacao = limpar_texto((dados or {}).get("identificacao_adicional"))
    if len(identificacao) > MAX_IDENTIFICACAO:
        erros["identificacao_adicional"] = "A identificação adicional deve ter no máximo 120 caracteres."

    responsavel = limpar_texto((dados or {}).get("responsavel_nome"))
    if not 3 <= len(responsavel) <= MAX_RESPONSAVEL or not re.search(r"[A-Za-zÀ-ÿ]", responsavel):
        erros["responsavel_nome"] = "Informe o nome do responsável."

    observacoes = limpar_texto((dados or {}).get("observacoes_gerais"), quebras=True)
    if len(observacoes) > MAX_OBSERVACOES:
        erros["observacoes_gerais"] = "As observações gerais devem ter no máximo 2000 caracteres."

    itens, erros_itens = _validar_itens((dados or {}).get("itens") or [], (dados or {}).get("excedeu_itens"))
    erros.update(erros_itens)
    if erros:
        raise DadosInvalidos(erros)

    return {
        "chave_envio": chave,
        "placa": placa,
        "placa_fora_padrao": fora_padrao,
        "tipo_veiculo": tipo,
        "marca": marca,
        "modelo": modelo,
        "identificacao_adicional": identificacao,
        "responsavel_nome": responsavel,
        "observacoes_gerais": observacoes,
        "itens": itens,
    }


def _item_vazio():
    return {"descricao": "", "quantidade": "1", "unidade": "UN", "observacao": ""}


def _placa_padrao(valor):
    bruto = re.sub(r"[^A-Z0-9]", "", limpar_texto(valor).upper())
    if PLACA_ANTIGA.fullmatch(bruto):
        return f"{bruto[:3]}-{bruto[3:]}"
    if PLACA_MERCOSUL.fullmatch(bruto):
        return bruto
    return None


def _identificacao_livre(valor):
    texto = limpar_texto(valor).upper()
    if not 2 <= len(texto) <= 30:
        return None
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9 ./-]*", texto):
        return None
    if texto[-1] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        return None
    return texto


def _quantidade(valor):
    bruto = str(valor or "").strip().replace(" ", "")
    if not QUANTIDADE_RE.fullmatch(bruto):
        return None
    quantidade = Decimal(bruto.replace(",", "."))
    if quantidade <= 0:
        return None
    return format(quantidade, "f")


def _intocada(item):
    descricao = limpar_texto(item.get("descricao"))
    observacao = limpar_texto(item.get("observacao"), quebras=True)
    quantidade = str(item.get("quantidade") or "").strip()
    unidade = str(item.get("unidade") or "").strip()
    return descricao == "" and observacao == "" and quantidade in {"", "1"} and unidade in {"", "UN"}


def _validar_itens(itens, excedeu):
    if excedeu:
        return [], {"itens": "Uma solicitação pode ter no máximo 30 peças."}
    if not itens:
        return [], {"itens": "Adicione ao menos uma peça."}

    limpos = []
    linhas = {}
    alguma = False
    for indice, item in enumerate(itens):
        if _intocada(item):
            continue
        alguma = True
        erro_linha = {}
        descricao = limpar_texto(item.get("descricao"))
        if not 2 <= len(descricao) <= MAX_DESCRICAO_PECA:
            erro_linha["descricao"] = "Informe a descrição da peça (mínimo de 2 caracteres)."
        quantidade = _quantidade(item.get("quantidade"))
        if quantidade is None:
            erro_linha["quantidade"] = "Informe uma quantidade maior que zero, com até 3 casas decimais."
        unidade = str(item.get("unidade") or "").strip()
        if unidade not in UNIDADES_VALIDAS:
            erro_linha["unidade"] = "Selecione uma unidade válida."
        observacao = limpar_texto(item.get("observacao"), quebras=True)
        if len(observacao) > MAX_OBSERVACAO_PECA:
            erro_linha["observacao"] = "A observação da peça deve ter no máximo 500 caracteres."
        if erro_linha:
            linhas[indice] = erro_linha
            continue
        limpos.append(
            {
                "descricao": descricao,
                "quantidade": quantidade,
                "unidade": unidade,
                "observacao": observacao,
            }
        )

    erros = {}
    if not alguma:
        erros["itens"] = "Adicione ao menos uma peça."
    if linhas:
        erros["itens_linhas"] = linhas
    return limpos, erros
