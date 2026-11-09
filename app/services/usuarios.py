from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import PERFIS_PAINEL
from app.erros import DadosInvalidos
from app.extensions import db
from app.models import Usuario
from app.tempo import agora_utc
from app.validacao import USUARIO_RE, validar_nome_pessoa

_hash_falso = None


def autenticar(identificador, senha):
    if not identificador or not senha or len(senha) > 128:
        _comparar_senha(None, senha or "")
        return None
    usuario = db.session.scalar(db.select(Usuario).where(Usuario.usuario == identificador.strip().lower()))
    if not _comparar_senha(usuario, senha):
        return None
    if usuario is None or not usuario.ativo:
        return None
    return usuario


def criar_usuario(nome, identificador, senha, perfil):
    erros = {}
    nome_limpo = validar_nome_pessoa(nome)
    if not nome_limpo:
        erros["nome"] = "Informe o nome com pelo menos 3 caracteres."
    usuario_limpo = (identificador or "").strip().lower()
    if not USUARIO_RE.fullmatch(usuario_limpo):
        erros["usuario"] = "Use um usuário ou e-mail válido, com pelo menos 3 caracteres, sem espaços."
    if not isinstance(senha, str) or not 8 <= len(senha) <= 128:
        erros["senha"] = "A senha deve ter entre 8 e 128 caracteres."
    if perfil not in PERFIS_PAINEL:
        erros["perfil"] = "Perfil inválido."
    if erros:
        raise DadosInvalidos(erros)
    if db.session.scalar(db.select(Usuario).where(Usuario.usuario == usuario_limpo)) is not None:
        raise DadosInvalidos({"usuario": "Já existe um usuário com esse acesso."})

    usuario = Usuario(nome=nome_limpo, usuario=usuario_limpo, perfil=perfil, ativo=True, criado_em=agora_utc())
    usuario.definir_senha(senha)
    db.session.add(usuario)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise DadosInvalidos({"usuario": "Já existe um usuário com esse acesso."}) from None
    return usuario


def _comparar_senha(usuario, senha):
    global _hash_falso
    if usuario is not None and usuario.ativo:
        alvo = usuario.senha_hash
    else:
        if _hash_falso is None:
            _hash_falso = generate_password_hash("senha-inexistente-para-tempo", method="scrypt")
        alvo = _hash_falso
    return check_password_hash(alvo, senha or "")


def registrar_falha_de_login():
    current_app.logger.warning("Falha de login")
