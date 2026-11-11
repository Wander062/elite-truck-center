import re
from decimal import Decimal

from flask import current_app
from sqlalchemy import func, or_
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


_ACENTOS = (
    ("Á", "A"), ("À", "A"), ("Â", "A"), ("Ã", "A"),
    ("É", "E"), ("Ê", "E"), ("Í", "I"),
    ("Ó", "O"), ("Ô", "O"), ("Õ", "O"), ("Ú", "U"), ("Ç", "C"),
    ("á", "A"), ("à", "A"), ("â", "A"), ("ã", "A"),
    ("é", "E"), ("ê", "E"), ("í", "I"),
    ("ó", "O"), ("ô", "O"), ("õ", "O"), ("ú", "U"), ("ç", "C"),
)


def _termo_nome(texto):
    bruto = str(texto or "")
    for origem, destino in _ACENTOS:
        bruto = bruto.replace(origem, destino)
    return " ".join(bruto.upper().split())


def _coluna_nome():
    coluna = Solicitacao.responsavel_nome
    for origem, destino in _ACENTOS:
        coluna = func.replace(coluna, origem, destino)
    return func.upper(coluna)


def consultar_solicitacoes(placa, inicio_utc, fim_exclusivo_utc, status, pagina, excluir_intervalo=None):
    consulta = db.select(Solicitacao)
    termo = re.sub(r"[^A-Z0-9]", "", (placa or "").upper())
    nome_termo = _termo_nome(placa)
    condicoes = []
    if termo:
        coluna = func.upper(Solicitacao.placa)
        for caractere in ("-", " ", ".", "/"):
            coluna = func.replace(coluna, caractere, "")
        condicao = coluna.contains(termo)
        if re.fullmatch(r"SOL\d+", termo) or re.fullmatch(r"\d+", termo):
            numero = int(re.sub(r"\D", "", termo) or "0")
            if 1 <= numero <= 1_000_000_000:
                condicao = or_(condicao, Solicitacao.id == numero)
        condicoes.append(condicao)
    if len(nome_termo) >= 3:
        condicoes.append(_coluna_nome().contains(nome_termo))
    if condicoes:
        consulta = consulta.where(or_(*condicoes))
    if status:
        consulta = consulta.where(Solicitacao.status == status)
    if inicio_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em >= inicio_utc)
    if fim_exclusivo_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em < fim_exclusivo_utc)
    if excluir_intervalo is not None:
        excluir_inicio, excluir_fim = excluir_intervalo
        consulta = consulta.where(
            or_(Solicitacao.criado_em < excluir_inicio, Solicitacao.criado_em >= excluir_fim)
        )
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


def contar_pendentes(inicio_utc=None, fim_exclusivo_utc=None):
    from app.constants import STATUS_PENDENTE

    consulta = db.select(func.count(Solicitacao.id)).where(Solicitacao.status == STATUS_PENDENTE)
    if inicio_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em >= inicio_utc)
    if fim_exclusivo_utc is not None:
        consulta = consulta.where(Solicitacao.criado_em < fim_exclusivo_utc)
    total = db.session.scalar(consulta)
    return int(total or 0)


def versao_da_solicitacao(solicitacao):
    momento = solicitacao.atualizado_em
    if momento is None:
        return ""
    return momento.strftime("%Y-%m-%dT%H:%M:%S.%f")


def contar_fora_do_intervalo(inicio_utc, fim_exclusivo_utc):
    total = db.session.scalar(
        db.select(func.count(Solicitacao.id)).where(
            or_(Solicitacao.criado_em < inicio_utc, Solicitacao.criado_em >= fim_exclusivo_utc)
        )
    )
    return int(total or 0)


def formulario_da_solicitacao(solicitacao):
    from app.formatacao import formatar_quantidade

    return {
        "placa": solicitacao.placa,
        "placa_fora_padrao": bool(solicitacao.placa_fora_padrao),
        "tipo_veiculo": solicitacao.tipo_veiculo,
        "marca": solicitacao.marca,
        "modelo": solicitacao.modelo,
        "identificacao_adicional": solicitacao.identificacao_adicional or "",
        "responsavel_nome": solicitacao.responsavel_nome,
        "observacoes_gerais": solicitacao.observacoes_gerais or "",
        "itens": [
            {
                "descricao": item.descricao,
                "quantidade": formatar_quantidade(item.quantidade).replace("—", ""),
                "unidade": item.unidade or "",
                "observacao": item.observacao or "",
            }
            for item in solicitacao.itens
        ],
    }


def atualizar_solicitacao(solicitacao, dados, versao):
    from app.erros import DadosInvalidos

    if versao_da_solicitacao(solicitacao) != (versao or ""):
        raise DadosInvalidos({
            "versao": "Este pedido mudou desde que você abriu. Nada foi salvo, para não apagar o que já estava gravado.",
        })
    payload = dict(dados or {})
    payload["chave_envio"] = solicitacao.chave_envio
    limpos = validar_solicitacao(payload)
    solicitacao.placa = limpos["placa"]
    solicitacao.placa_fora_padrao = limpos["placa_fora_padrao"]
    solicitacao.tipo_veiculo = limpos["tipo_veiculo"]
    solicitacao.marca = limpos["marca"]
    solicitacao.modelo = limpos["modelo"]
    solicitacao.identificacao_adicional = limpos["identificacao_adicional"] or None
    solicitacao.responsavel_nome = limpos["responsavel_nome"]
    solicitacao.observacoes_gerais = limpos["observacoes_gerais"] or None
    solicitacao.atualizado_em = agora_utc()
    solicitacao.itens = [
        ItemSolicitacao(
            descricao=item["descricao"],
            quantidade=Decimal(item["quantidade"]),
            unidade=item["unidade"] or None,
            observacao=item["observacao"] or None,
        )
        for item in limpos["itens"]
    ]
    db.session.commit()
    return solicitacao


def numero_ordem_valido(valor):
    texto = re.sub(r"\s+", " ", str(valor or "").strip())
    if not texto or len(texto) > 40:
        return None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ./-]*", texto):
        return None
    return texto


def alterar_status(solicitacao, novo_status, usuario, numero_ordem=None):
    from app.erros import DadosInvalidos

    if novo_status not in STATUS_VALIDOS:
        raise DadosInvalidos({"status": "Status inválido."})
    if novo_status == solicitacao.status:
        raise DadosInvalidos({"status": "A solicitação já está com esse status."})
    numero = None
    if novo_status == "concluida":
        numero = numero_ordem_valido(numero_ordem)
        if numero is None:
            raise DadosInvalidos({"numero_ordem": "Informe o número gerado no outro sistema."})
    anterior = solicitacao.status
    solicitacao.status = novo_status
    if numero is not None:
        solicitacao.numero_ordem = numero
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
