from decimal import Decimal, InvalidOperation

from app.constants import STATUS_SOLICITACAO, TIPOS_VEICULO, UNIDADES


def rotulo_status(valor):
    return dict(STATUS_SOLICITACAO).get(valor, str(valor or "—"))


def rotulo_tipo(valor):
    return dict(TIPOS_VEICULO).get(valor, str(valor or "—"))


def rotulo_unidade(valor):
    if not valor:
        return "—"
    return dict(UNIDADES).get(valor, str(valor))


def rotulo_contagem(quantidade):
    total = int(quantidade or 0)
    if total == 1:
        return "1 item"
    return f"{total} itens"


def formatar_quantidade(valor):
    if valor is None or valor == "":
        return "—"
    try:
        quantidade = Decimal(str(valor))
    except InvalidOperation:
        return str(valor)
    texto = f"{quantidade:.3f}".rstrip("0").rstrip(".")
    if "." in texto:
        inteiro, fracao = texto.split(".", 1)
        return f"{inteiro},{fracao}"
    return texto
