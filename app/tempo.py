from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

FUSO_OFICINA = ZoneInfo("America/Sao_Paulo")


def agora_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def formatar_data_hora(valor):
    if not valor:
        return "—"
    momento = valor if valor.tzinfo is not None else valor.replace(tzinfo=timezone.utc)
    return momento.astimezone(FUSO_OFICINA).strftime("%d/%m/%Y %H:%M")


def _ler_data(texto):
    bruto = (texto or "").strip()
    if not bruto:
        return None, False
    try:
        return datetime.strptime(bruto, "%Y-%m-%d").date(), True
    except ValueError:
        return None, False


def interpretar_periodo(de_texto, ate_texto):
    erros = []
    inicio, de_ok = _ler_data(de_texto)
    fim, ate_ok = _ler_data(ate_texto)
    if (de_texto or "").strip() and not de_ok:
        erros.append("Informe uma data inicial válida.")
    if (ate_texto or "").strip() and not ate_ok:
        erros.append("Informe uma data final válida.")
    if inicio and fim and inicio > fim:
        erros.append("A data inicial não pode ser posterior à data final.")
    if erros:
        return None, None, erros

    inicio_utc = None
    fim_exclusivo = None
    if inicio:
        local = datetime.combine(inicio, time.min, tzinfo=FUSO_OFICINA)
        inicio_utc = local.astimezone(timezone.utc).replace(tzinfo=None)
    if fim:
        local = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=FUSO_OFICINA)
        fim_exclusivo = local.astimezone(timezone.utc).replace(tzinfo=None)
    return inicio_utc, fim_exclusivo, erros
