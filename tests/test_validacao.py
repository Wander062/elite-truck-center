import uuid

import pytest

from app.erros import DadosInvalidos
from app.validacao import validar_solicitacao
from tests.apoio import solicitacao_limpa


def test_aceita_placa_antiga_mercosul_e_quantidade_com_virgula():
    antiga = validar_solicitacao(solicitacao_limpa(placa="abc-1234"))
    assert antiga["placa"] == "ABC-1234"
    mercosul = validar_solicitacao(solicitacao_limpa(placa="abc1d23"))
    assert mercosul["placa"] == "ABC1D23"
    assert mercosul["itens"][1]["quantidade"] == "2.5"
    assert mercosul["responsavel_nome"] == "José Almeida"


def test_rejeita_placa_invalida_quantidade_e_campos_vazios():
    with pytest.raises(DadosInvalidos) as erro:
        validar_solicitacao(solicitacao_limpa(placa="ABC", itens=[{"descricao": "", "quantidade": "1", "unidade": "UN", "observacao": ""}]))
    assert "placa" in erro.value.erros
    assert "itens" in erro.value.erros

    with pytest.raises(DadosInvalidos) as quantidade:
        validar_solicitacao(
            solicitacao_limpa(
                itens=[{"descricao": "Parafuso", "quantidade": "0", "unidade": "UN", "observacao": ""}]
            )
        )
    assert "quantidade" in quantidade.value.erros["itens_linhas"][0]

    with pytest.raises(DadosInvalidos):
        validar_solicitacao(
            solicitacao_limpa(
                itens=[{"descricao": "Parafuso", "quantidade": "1.2.3", "unidade": "UN", "observacao": ""}]
            )
        )
    with pytest.raises(DadosInvalidos):
        validar_solicitacao(
            solicitacao_limpa(
                itens=[{"descricao": "Parafuso", "quantidade": "100000", "unidade": "UN", "observacao": ""}]
            )
        )


def test_identificacao_livre_e_limite_de_pecas():
    livre = validar_solicitacao(
        solicitacao_limpa(placa="  frota 12 ", placa_fora_padrao=True)
    )
    assert livre["placa"] == "FROTA 12"
    assert livre["placa_fora_padrao"] is True

    with pytest.raises(DadosInvalidos) as erro:
        validar_solicitacao(solicitacao_limpa(placa="FROTA-12", placa_fora_padrao=False))
    assert "placa" in erro.value.erros

    itens = [
        {"descricao": f"Peça {indice}", "quantidade": "1", "unidade": "UN", "observacao": ""}
        for indice in range(31)
    ]
    with pytest.raises(DadosInvalidos) as limite:
        validar_solicitacao(solicitacao_limpa(itens=itens, excedeu_itens=True, chave_envio=str(uuid.uuid4())))
    assert "30" in limite.value.erros["itens"]


def test_colapsa_espacos_do_responsavel():
    limpos = validar_solicitacao(solicitacao_limpa(responsavel_nome="  José   Almeida  "))
    assert limpos["responsavel_nome"] == "José Almeida"
