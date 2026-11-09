from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.solicitacoes import criar_solicitacao, obter_por_chave
from app.validacao import (
    CHAVE_RE,
    dados_publicos_do_formulario,
    formulario_vazio,
    rascunho_para_formulario,
    validar_solicitacao,
)
from app.erros import DadosInvalidos

bp = Blueprint("publico", __name__)
CHAVE_RASCUNHO = "rascunho_solicitacao"


@bp.route("/", methods=["GET", "POST"])
def formulario():
    if request.method == "GET":
        if request.args.get("editar") == "1":
            rascunho = _obter_rascunho()
            if rascunho is not None:
                return render_template(
                    "publico/formulario.html",
                    dados=rascunho_para_formulario(rascunho),
                    erros={},
                )
        _limpar_rascunho()
        return render_template("publico/formulario.html", dados=formulario_vazio(), erros={})

    dados = dados_publicos_do_formulario(request.form)
    chave = str(dados.get("chave_envio") or "").strip().lower()
    if CHAVE_RE.fullmatch(chave) and obter_por_chave(chave) is not None:
        _limpar_rascunho()
        flash(
            "Esta solicitação já foi enviada. Os dados abaixo são os que o escritório recebeu.",
            "aviso",
        )
        return redirect(url_for("publico.confirmacao", chave=chave))

    try:
        limpos = validar_solicitacao(dados)
    except DadosInvalidos as exc:
        return render_template("publico/formulario.html", dados=dados, erros=exc.erros), 400

    _guardar_rascunho(limpos)
    return redirect(url_for("publico.revisao"))


@bp.get("/revisao")
def revisao():
    rascunho = _obter_rascunho()
    if rascunho is None:
        return redirect(url_for("publico.formulario"))
    return render_template("publico/revisao.html", dados=rascunho)


@bp.post("/revisao/confirmar")
def confirmar():
    rascunho = _obter_rascunho()
    if rascunho is None:
        flash("Não há solicitação para confirmar. Preencha o formulário novamente.", "aviso")
        return redirect(url_for("publico.formulario"))
    ja_existia = obter_por_chave(rascunho.get("chave_envio", "")) is not None
    try:
        solicitacao = criar_solicitacao(rascunho)
    except DadosInvalidos as exc:
        return render_template("publico/formulario.html", dados=rascunho_para_formulario(rascunho), erros=exc.erros), 400
    _limpar_rascunho()
    if ja_existia:
        flash(
            "Esta solicitação já foi enviada. Os dados abaixo são os que o escritório recebeu.",
            "aviso",
        )
    return redirect(url_for("publico.confirmacao", chave=solicitacao.chave_envio))


@bp.get("/solicitacao/<chave>")
def confirmacao(chave):
    solicitacao = obter_por_chave((chave or "").lower())
    if solicitacao is None:
        return render_template(
            "erros/erro.html",
            codigo=404,
            titulo="Solicitação não encontrada",
            mensagem="Não há solicitação com esse identificador.",
        ), 404
    return render_template("publico/confirmacao.html", solicitacao=solicitacao)


def _guardar_rascunho(dados):
    session[CHAVE_RASCUNHO] = dados
    session.modified = True


def _obter_rascunho():
    valor = session.get(CHAVE_RASCUNHO)
    if not isinstance(valor, dict) or "chave_envio" not in valor:
        return None
    return valor


def _limpar_rascunho():
    session.pop(CHAVE_RASCUNHO, None)
