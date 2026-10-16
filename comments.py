from datetime import datetime

from config import COMENTARIO


def ler_texto(locator, timeout=3000):
    try:
        return locator.first.inner_text(timeout=timeout).strip()
    except Exception:
        return ""


def formatar_data(valor):
    """Converte timestamps em segundos/milissegundos ou datas ISO para formato local."""
    if not valor:
        return ""

    try:
        if valor.isdigit():
            timestamp = int(valor)
            if len(valor) >= 13:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")

        dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, OverflowError, OSError, TypeError):
        return valor


def extrair_comentarios(page):
    comentarios = []

    for bloco in page.locator(COMENTARIO).all():
        autor = ler_texto(bloco.locator(".ant-comment-content-author-name"))
        texto = ler_texto(bloco.locator(".ant-comment-content-detail"))
        tempo = bloco.locator(".ant-comment-content-author-time time")

        data = ""
        if tempo.count() > 0:
            elemento_tempo = tempo.first
            valor_datetime = elemento_tempo.get_attribute("datetime") or ""
            data = formatar_data(valor_datetime)
            if not data:
                data = ler_texto(elemento_tempo)

        if autor or texto:
            comentarios.append({
                "autor": autor,
                "data": data,
                "texto": texto,
            })

    return comentarios
