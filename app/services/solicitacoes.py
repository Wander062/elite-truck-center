import re
from decimal import Decimal

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.constants import POR_PAGINA, STATUS_VALIDOS
from app.extensions import db
from app.models import HistoricoStatus, ItemSolicitacao, Solicitacao
from app.tempo import agora_utc
from app.validacao import CHAVE_RE, validar_solicitacao


def criar_solicitacao(dados):
    chave = str((dados or {}).get("chave_envio") or "").strip().lower()
    if CHAVE_RE.fullmatch(chave):
        existente = _por_chave(chave)
        if existente is not None:
            return existente

    limpos = validar_solicitacao(dados)
    existente = _por_chave(limpos["chave_envio"])
    if existente is not None:
        return existente

    agora = agora_utc()
    solicitacao = Solicitacao(
        chave_envio=limpos["chave_envio"],
        placa=limpos["placa"],
        placa_fora_padrao=limpos["placa_fora_padrao"],
        tipo_veiculo=limpos["tipo_veiculo"],
        marca=limpos["marca"],
        modelo=limpos["modelo"],
        identificacao_adicional=limpos["identificacao_adicional"] or None,
        responsavel_nome=limpos["responsavel_nome"],
        observacoes_gerais=limpos["observacoes_gerais"] or None,
        status="pendente",
        criado_em=agora,
        atualizado_em=agora,
    )
    for item in limpos["itens"]:
        solicitacao.itens.append(
            ItemSolicitacao(
                descricao=item["descricao"],
                quantidade=Decimal(item["quantidade"]),
                unidade=item["unidade"] or None,
                observacao=item["observacao"] or None,
            )
        )
    db.session.add(solicitacao)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existente = _por_chave(limpos["chave_envio"])
        if existente is not None:
            return existente
        raise
    current_app.logger.info("Solicitação %s registrada", solicitacao.id)
    return solicitacao


def obter_por_chave(chave):
    if not CHAVE_RE.fullmatch(chave or ""):
        return None
    return db.session.scalars(
        db.select(Solicitacao).options(selectinload(Solicitacao.itens)).where(Solicitacao.chave_envio == chave)
    ).first()


def obter_solicitacao(solicitacao_id):
    return db.session.scalars(
        db.select(Solicitacao)
        .options(
            selectinload(Solicitacao.itens),
            selectinload(Solicitacao.historico).selectinload(HistoricoStatus.usuario),
        )
        .where(Solicitacao.id == solicitacao_id)
    ).first()


def consultar_solicitacoes(placa, inicio_utc, fim_exclusivo_utc, status, pagina):
    consulta = db.select(Solicitacao)
    termo = re.sub(r"[^A-Z0-9]", "", (placa or "").upper())
    if termo:
        coluna = func.upper(Solicitacao.placa)
        for caractere in ("-", " ", ".", "/"):
            coluna = func.replace(coluna, caractere, "")
        consulta = consulta.where(coluna.contains(termo))
    if status:
        consulta = consulta.where(Solicitacao.status == status)
    if inicio_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em >= inicio_utc)
    if fim_exclusivo_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em < fim_exclusivo_utc)
    consulta = consulta.order_by(Solicitacao.criado_em.desc(), Solicitacao.id.desc())
    return db.paginate(consulta, page=max(int(pagina or 1), 1), per_page=POR_PAGINA, error_out=False)


def contar_itens(identificadores):
    if not identificadores:
        return {}
    linhas = db.session.execute(
        db.select(ItemSolicitacao.solicitacao_id, func.count(ItemSolicitacao.id))
        .where(ItemSolicitacao.solicitacao_id.in_(identificadores))
        .group_by(ItemSolicitacao.solicitacao_id)
    ).all()
    return {solicitacao_id: total for solicitacao_id, total in linhas}


def contar_pendentes():
    from app.constants import STATUS_PENDENTE

    total = db.session.scalar(
        db.select(func.count(Solicitacao.id)).where(Solicitacao.status == STATUS_PENDENTE)
    )
    return int(total or 0)


def alterar_status(solicitacao, novo_status, usuario):
    from app.erros import DadosInvalidos

    if novo_status not in STATUS_VALIDOS:
        raise DadosInvalidos({"status": "Status inválido."})
    if novo_status == solicitacao.status:
        raise DadosInvalidos({"status": "A solicitação já está com esse status."})
    anterior = solicitacao.status
    solicitacao.status = novo_status
    solicitacao.atualizado_em = agora_utc()
    db.session.add(
        HistoricoStatus(
            solicitacao=solicitacao,
            status_anterior=anterior,
            status_novo=novo_status,
            usuario=usuario,
        )
    )
    db.session.commit()
    current_app.logger.info(
        "Status da solicitação %s atualizado pelo usuário %s",
        solicitacao.id,
        usuario.id,
    )


def _por_chave(chave):
    return db.session.scalar(db.select(Solicitacao).where(Solicitacao.chave_envio == chave))
