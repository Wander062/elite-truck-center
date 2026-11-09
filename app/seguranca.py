from functools import wraps
from urllib.parse import urlparse

from flask import abort, redirect, request, url_for
from flask_login import current_user

from app.constants import PERFIS_PAINEL


def requer_painel(view):
    @wraps(view)
    def protegida(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.entrar", next=request.path))
        if current_user.perfil not in PERFIS_PAINEL or not current_user.ativo:
            abort(403)
        return view(*args, **kwargs)

    return protegida


def destino_interno(destino, prefixo):
    if not destino or not isinstance(destino, str):
        return None
    if not destino.startswith(prefixo) or destino.startswith("//") or "\\" in destino:
        return None
    partes = urlparse(destino)
    if partes.scheme or partes.netloc:
        return None
    return destino


def referencia_da_lista(referencia, host):
    if not referencia:
        return None
    partes = urlparse(referencia)
    if partes.scheme not in {"http", "https"}:
        return None
    if partes.netloc != host or partes.path != "/painel":
        return None
    return referencia
