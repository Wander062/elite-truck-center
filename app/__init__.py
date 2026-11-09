import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from app.constants import STATUS_SOLICITACAO, TIPOS_VEICULO, UNIDADES
from app.extensions import csrf, db, login_manager, migrate
from app.formatacao import formatar_quantidade, rotulo_contagem, rotulo_status, rotulo_tipo, rotulo_unidade
from app.models import Usuario
from app.tempo import formatar_data_hora


def create_app(config_name=None, config_overrides=None):
    from config import config_by_name
    import os

    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    if config_overrides:
        app.config.update(config_overrides)
    _validar_configuracao(app)
    _ajustar_banco(app)
    _atras_de_proxy(app)

    db.init_app(app)
    migrate.init_app(
        app,
        db,
        directory=str(Path(app.root_path).parent / "migrations"),
        render_as_batch=True,
    )
    login_manager.init_app(app)
    csrf.init_app(app)
    _registrar_login()
    _registrar_filtros(app)
    _registrar_http(app)
    _configurar_logs(app)

    from app.cli import registrar_comandos
    from app.routes import registrar_rotas

    registrar_comandos(app)
    registrar_rotas(app)
    _criar_admin_inicial(app)
    return app


def _validar_configuracao(app):
    if app.config.get("TESTING"):
        return
    faltando = []
    if not app.config.get("SECRET_KEY"):
        faltando.append("SECRET_KEY")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        faltando.append("DATABASE_URL")
    if faltando:
        nomes = ", ".join(faltando)
        raise RuntimeError(f"Defina as variáveis de ambiente: {nomes}. Veja .env.example.")


def _ajustar_banco(app):
    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if uri.startswith("postgres://"):
        uri = "postgresql+psycopg2://" + uri[len("postgres://"):]
    elif uri.startswith("postgresql://"):
        uri = "postgresql+psycopg2://" + uri[len("postgresql://"):]
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    if uri.startswith("mysql"):
        opcoes = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {})
        opcoes.setdefault("pool_pre_ping", True)
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = opcoes


def _atras_de_proxy(app):
    if os.environ.get("TRUST_PROXY") != "1":
        return
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


def _criar_admin_inicial(app):
    if app.testing:
        return
    nome = os.environ.get("ADMIN_NOME", "").strip()
    usuario = os.environ.get("ADMIN_USUARIO", "").strip()
    senha = os.environ.get("ADMIN_SENHA", "")
    if not (nome and usuario and senha):
        return
    if not 8 <= len(senha) <= 128:
        app.logger.warning("ADMIN_SENHA ignorada: use entre 8 e 128 caracteres.")
        return
    from app.erros import DadosInvalidos
    from app.extensions import db
    from app.models import Usuario
    from app.services.usuarios import criar_usuario

    with app.app_context():
        try:
            existente = db.session.scalar(
                db.select(Usuario).where(Usuario.usuario == usuario.strip().lower())
            )
            if existente is not None:
                existente.definir_senha(senha)
                existente.ativo = True
                db.session.commit()
                app.logger.info("Senha do administrador inicial atualizada")
                return
            criar_usuario(nome, usuario, senha, "administrador")
            app.logger.info("Administrador inicial criado")
        except DadosInvalidos as exc:
            app.logger.warning("Administrador inicial não criado: %s", "; ".join(exc.erros.values()))
        except Exception:
            db.session.rollback()
            app.logger.exception("Administrador inicial não criado")


def _registrar_login():
    @login_manager.user_loader
    def carregar_usuario(identificador):
        try:
            usuario_id = int(identificador)
        except (TypeError, ValueError):
            return None
        usuario = db.session.get(Usuario, usuario_id)
        if usuario is None or not usuario.ativo:
            return None
        return usuario


def _registrar_filtros(app):
    app.add_template_filter(formatar_data_hora, "data_hora")
    app.add_template_filter(formatar_quantidade, "quantidade")
    app.add_template_filter(rotulo_status, "rotulo_status")
    app.add_template_filter(rotulo_tipo, "rotulo_tipo")
    app.add_template_filter(rotulo_unidade, "unidade")
    app.add_template_filter(rotulo_contagem, "contagem")

    @app.context_processor
    def injetar_opcoes():
        return {
            "tipos_veiculo": TIPOS_VEICULO,
            "opcoes_unidade": UNIDADES,
            "opcoes_status": STATUS_SOLICITACAO,
        }


def _registrar_http(app):
    @app.after_request
    def cabecalhos(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        resposta.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        resposta.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; form-action 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; object-src 'none'",
        )
        if request.endpoint != "static":
            resposta.headers["Cache-Control"] = "no-store"
        return resposta

    @app.errorhandler(CSRFError)
    def tratar_csrf(_erro):
        app.logger.warning("Falha de verificação CSRF no endpoint %s", request.endpoint)
        return (
            _pagina_erro(
                400,
                "Sessão expirada",
                "Atualize a página e envie os dados novamente. Nada foi gravado em duplicidade.",
            ),
            400,
        )

    @app.errorhandler(403)
    def tratar_proibido(_erro):
        return (
            _pagina_erro(403, "Acesso negado", "Você não tem permissão para acessar esta página."),
            403,
        )

    @app.errorhandler(404)
    def tratar_nao_encontrado(_erro):
        return (_pagina_erro(404, "Página não encontrada", "A página solicitada não existe."), 404)

    @app.errorhandler(413)
    def tratar_tamanho(_erro):
        return (
            _pagina_erro(413, "Envio muito grande", "Reduza o texto e tente novamente."),
            413,
        )

    @app.errorhandler(Exception)
    def tratar_excecao(erro):
        if isinstance(erro, HTTPException):
            return erro
        app.logger.exception("Erro interno no endpoint %s", request.endpoint)
        db.session.rollback()
        if app.testing or app.debug:
            raise erro
        return (
            _pagina_erro(500, "Erro interno", "Não foi possível concluir a operação. Tente novamente."),
            500,
        )


def _pagina_erro(codigo, titulo, mensagem):
    from flask import render_template

    return render_template("erros/erro.html", codigo=codigo, titulo=titulo, mensagem=mensagem)


def _configurar_logs(app):
    if app.testing or getattr(app, "_logs_configurados", False):
        return
    pasta = Path(app.root_path).parent / "logs"
    pasta.mkdir(exist_ok=True)
    arquivo = RotatingFileHandler(
        pasta / "app.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    arquivo.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    nivel = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    arquivo.setLevel(nivel)
    app.logger.addHandler(arquivo)
    app.logger.setLevel(nivel)
    app._logs_configurados = True
