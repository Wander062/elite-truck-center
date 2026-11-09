import click
from flask import current_app

from app.constants import PERFIS_PAINEL
from app.erros import DadosInvalidos
from app.services.usuarios import criar_usuario


def registrar_comandos(app):
    @app.cli.command("criar-usuario")
    @click.option("--nome", required=True, help="Nome de quem vai acessar o painel.")
    @click.option("--usuario", required=True, help="Usuário ou e-mail de acesso.")
    @click.option("--senha", required=True, help="Senha com pelo menos 8 caracteres.")
    @click.option(
        "--perfil",
        type=click.Choice(list(PERFIS_PAINEL)),
        default="administrador",
        show_default=True,
    )
    def criar_usuario_comando(nome, usuario, senha, perfil):
        """Cria um acesso ao painel do escritório."""
        try:
            criado = criar_usuario(nome, usuario, senha, perfil)
        except DadosInvalidos as exc:
            raise click.ClickException("; ".join(exc.erros.values())) from None
        current_app.logger.info("Usuário %s criado", criado.id)
        click.echo(f"Usuário criado: {criado.usuario} ({criado.perfil})")
