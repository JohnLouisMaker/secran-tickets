from datetime import datetime

from config import SELETOR_COMENTARIO


def obter_texto(localizador, tempo_limite_ms=3000):
    try:
        return localizador.first.inner_text(timeout=tempo_limite_ms).strip()
    except Exception:
        return ""


def formatar_data(valor_data):
    if not valor_data:
        return ""

    try:
        if valor_data.isdigit():
            carimbo_tempo = int(valor_data)
            if len(valor_data) >= 13:
                carimbo_tempo /= 1000
            return datetime.fromtimestamp(carimbo_tempo).strftime("%d/%m/%Y %H:%M")

        data_hora = datetime.fromisoformat(valor_data.replace("Z", "+00:00"))
        if data_hora.tzinfo is not None:
            data_hora = data_hora.astimezone()
        return data_hora.strftime("%d/%m/%Y %H:%M")
    except (ValueError, OverflowError, OSError, TypeError):
        return valor_data


def extrair_comentarios(pagina):
    comentarios = []

    for bloco_comentario in pagina.locator(SELETOR_COMENTARIO).all():
        autor = obter_texto(bloco_comentario.locator(".ant-comment-content-author-name"))
        texto = obter_texto(bloco_comentario.locator(".ant-comment-content-detail"))
        localizador_tempo = bloco_comentario.locator(".ant-comment-content-author-time time")

        data_formatada = ""
        if localizador_tempo.count() > 0:
            campo_tempo = localizador_tempo.first
            valor_atributo_datetime = campo_tempo.get_attribute("datetime") or ""
            data_formatada = formatar_data(valor_atributo_datetime)
            if not data_formatada:
                data_formatada = obter_texto(campo_tempo)

        if autor or texto:
            comentarios.append(
                {
                    "autor": autor,
                    "data": data_formatada,
                    "texto": texto,
                }
            )

    return comentarios
