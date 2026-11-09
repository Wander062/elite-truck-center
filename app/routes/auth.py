from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.constants import PERFIS_PAINEL
from app.forms import FormularioLogin
from app.seguranca import destino_interno
from app.services.usuarios import autenticar, registrar_falha_de_login

bp = Blueprint("auth", __name__)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if current_user.is_authenticated and current_user.perfil in PERFIS_PAINEL:
        return redirect(url_for("painel.lista"))

    proximo = destino_interno(request.args.get("next"), "/painel")
    form = FormularioLogin()
    if form.validate_on_submit():
        usuario = autenticar(form.usuario.data, form.senha.data)
        if usuario is None or usuario.perfil not in PERFIS_PAINEL:
            registrar_falha_de_login()
            flash("Usuário ou senha inválidos.", "erro")
            return render_template("auth/entrar.html", form=form, proximo=proximo)
        session.clear()
        session.permanent = True
        login_user(usuario)
        return redirect(proximo or url_for("painel.lista"))
    return render_template("auth/entrar.html", form=form, proximo=proximo)


@bp.post("/sair")
@login_required
def sair():
    logout_user()
    session.clear()
    flash("Sessão encerrada.", "ok")
    return redirect(url_for("auth.entrar"))
