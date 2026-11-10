from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user

from app.constants import STATUS_VALIDOS
from app.erros import DadosInvalidos
from app.extensions import db
from app.models import Usuario
from app.seguranca import referencia_da_lista, requer_painel
from app.services.solicitacoes import (
    alterar_status,
    atualizar_solicitacao,
    consultar_solicitacoes,
    contar_fora_do_intervalo,
    contar_itens,
    contar_pendentes,
    formulario_da_solicitacao,
    obter_solicitacao,
    versao_da_solicitacao,
)
from app.tempo import interpretar_periodo, limites_hoje
from app.validacao import dados_publicos_do_formulario

bp = Blueprint("painel", __name__, url_prefix="/painel")
CHAVE_MUDANCA = "mudanca_status"


@bp.get("/")
@requer_painel
def lista():
    placa = request.args.get("placa", "")
    de_texto = request.args.get("de", "")
    ate_texto = request.args.get("ate", "")
    status = request.args.get("status", "")
    try:
        pagina = int(request.args.get("pagina", "1"))
    except (TypeError, ValueError):
        pagina = 1

    inicio, fim, erros_filtro = interpretar_periodo(de_texto, ate_texto)
    status_filtro = status if status in STATUS_VALIDOS else ""
    if status and status not in STATUS_VALIDOS:
        erros_filtro.append("Status inválido.")
    historico = request.args.get("historico") == "1"
    pesquisando = bool((placa or "").strip() or (de_texto or "").strip() or (ate_texto or "").strip() or status)
    if pesquisando:
        modo = "busca"
    elif historico:
        modo = "historico"
    else:
        modo = "hoje"
    intervalo_hoje = limites_hoje()
    excluir = None
    if not erros_filtro and modo == "hoje":
        inicio, fim = intervalo_hoje
    elif not erros_filtro and modo == "historico":
        inicio, fim = None, None
        excluir = intervalo_hoje

    paginacao = None
    contagens = {}
    if not erros_filtro:
        paginacao = consultar_solicitacoes(
            placa, inicio, fim, status_filtro or None, pagina, excluir_intervalo=excluir
        )
        contagens = contar_itens([item.id for item in paginacao.items])

    return render_template(
        "painel/lista.html",
        paginacao=paginacao,
        contagens=contagens,
        pendentes=contar_pendentes(*intervalo_hoje) if modo == "hoje" else None,
        guardados=contar_fora_do_intervalo(*intervalo_hoje) if modo == "hoje" else None,
        erros_filtro=erros_filtro,
        modo=modo,
        filtros={"placa": placa, "de": de_texto, "ate": ate_texto, "status": status, "historico": historico},
    )


@bp.get("/solicitacoes/<int:solicitacao_id>")
@requer_painel
def detalhe(solicitacao_id):
    solicitacao = obter_solicitacao(solicitacao_id)
    if solicitacao is None:
        abort(404)
    return render_template(
        "painel/detalhe.html",
        solicitacao=solicitacao,
        voltar=referencia_da_lista(request.referrer, request.host) or url_for("painel.lista"),
    )


@bp.route("/solicitacoes/<int:solicitacao_id>/editar", methods=["GET", "POST"])
@requer_painel
def editar(solicitacao_id):
    solicitacao = obter_solicitacao(solicitacao_id)
    if solicitacao is None:
        abort(404)
    if request.method == "GET":
        return render_template(
            "painel/editar.html",
            solicitacao=solicitacao,
            dados=formulario_da_solicitacao(solicitacao),
            erros={},
            versao=versao_da_solicitacao(solicitacao),
        )
    if (request.form.get("pedido_id") or "").strip() != str(solicitacao.id):
        flash("A correção não foi salva. Abra o pedido de novo para não misturar com outro.", "erro")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    dados = dados_publicos_do_formulario(request.form)
    try:
        atualizar_solicitacao(solicitacao, dados, request.form.get("versao"))
    except DadosInvalidos as exc:
        if "versao" in exc.erros:
            flash(exc.erros["versao"], "erro")
            return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
        return render_template(
            "painel/editar.html",
            solicitacao=solicitacao,
            dados=dados,
            erros=exc.erros,
            versao=versao_da_solicitacao(solicitacao),
        ), 400
    flash(f"Pedido {solicitacao.protocolo} corrigido. Os outros pedidos não foram alterados.", "ok")
    return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))


@bp.post("/solicitacoes/<int:solicitacao_id>/status")
@requer_painel
def solicitar_status(solicitacao_id):
    solicitacao = obter_solicitacao(solicitacao_id)
    if solicitacao is None:
        abort(404)
    novo = (request.form.get("status") or "").strip()
    if novo not in STATUS_VALIDOS:
        flash("Status inválido.", "erro")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    if novo == solicitacao.status:
        flash("A solicitação já está com esse status.", "aviso")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    session[CHAVE_MUDANCA] = {"solicitacao_id": solicitacao_id, "status": novo}
    session.modified = True
    return redirect(url_for("painel.confirmar_status", solicitacao_id=solicitacao_id))


@bp.get("/solicitacoes/<int:solicitacao_id>/status/confirmar")
@requer_painel
def confirmar_status(solicitacao_id):
    solicitacao = obter_solicitacao(solicitacao_id)
    if solicitacao is None:
        abort(404)
    mudanca = _mudanca_pendente(solicitacao_id)
    if mudanca is None or mudanca["status"] == solicitacao.status:
        session.pop(CHAVE_MUDANCA, None)
        flash("Nenhuma alteração de status pendente.", "aviso")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    return render_template(
        "painel/confirmar_status.html",
        solicitacao=solicitacao,
        status_novo=mudanca["status"],
    )


@bp.post("/solicitacoes/<int:solicitacao_id>/status/confirmar")
@requer_painel
def aplicar_status(solicitacao_id):
    solicitacao = obter_solicitacao(solicitacao_id)
    if solicitacao is None:
        abort(404)
    mudanca = _mudanca_pendente(solicitacao_id)
    if mudanca is None:
        flash("Nenhuma alteração de status pendente.", "aviso")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    usuario = db.session.get(Usuario, int(current_user.get_id()))
    if usuario is None:
        abort(403)
    try:
        alterar_status(solicitacao, mudanca["status"], usuario)
    except DadosInvalidos as exc:
        session.pop(CHAVE_MUDANCA, None)
        flash(exc.erros.get("status", "Não foi possível alterar o status."), "erro")
        return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))
    session.pop(CHAVE_MUDANCA, None)
    flash("Status atualizado.", "ok")
    return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))


@bp.post("/solicitacoes/<int:solicitacao_id>/status/cancelar")
@requer_painel
def cancelar_status(solicitacao_id):
    session.pop(CHAVE_MUDANCA, None)
    return redirect(url_for("painel.detalhe", solicitacao_id=solicitacao_id))


def _mudanca_pendente(solicitacao_id):
    mudanca = session.get(CHAVE_MUDANCA)
    if not isinstance(mudanca, dict):
        return None
    if mudanca.get("solicitacao_id") != solicitacao_id:
        return None
    if mudanca.get("status") not in STATUS_VALIDOS:
        return None
    return mudanca
