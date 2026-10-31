import re
from urllib.parse import urljoin

from comments import extrair_comentarios, obter_texto
from config import (
    SELETOR_COMENTARIO,
    SELETOR_LINHAS_DESCRICAO,
    SELETOR_LINK_TICKET,
    TEMPO_LIMITE_MS,
    URL_BASE,
)


def coletar_urls_tickets(pagina_listagem):
    tickets_encontrados = []
    ids_ja_vistos = set()
    links_tickets = pagina_listagem.locator(SELETOR_LINK_TICKET)

    for posicao_link in range(links_tickets.count()):
        link_ticket = links_tickets.nth(posicao_link)
        endereco_relativo = link_ticket.get_attribute("href") or ""
        correspondencia_id = re.search(r"/cards/view/(\d+)", endereco_relativo)

        if not correspondencia_id:
            continue

        ticket_id = correspondencia_id.group(1)
        if ticket_id in ids_ja_vistos:
            continue

        ids_ja_vistos.add(ticket_id)
        tickets_encontrados.append((ticket_id, urljoin(URL_BASE, endereco_relativo)))

    return tickets_encontrados


def extrair_ticket(pagina, id_esperado):
    pagina.locator(
        f"{SELETOR_LINHAS_DESCRICAO}, .ant-page-header-heading-title, {SELETOR_COMENTARIO}, h1"
    ).first.wait_for(state="attached", timeout=TEMPO_LIMITE_MS)

    correspondencia_id = re.search(r"/cards/view/(\d+)", pagina.url)
    ticket_id = correspondencia_id.group(1) if correspondencia_id else ""

    if not ticket_id or ticket_id != str(id_esperado):
        raise ValueError(
            f"ID esperado {id_esperado}, ID encontrado {ticket_id or 'não identificado'}"
        )

    dados_ticket = {
        "ticket_id": ticket_id,
        "cliente": "",
        "cpf_cnpj": "",
        "assunto": "",
        "status": "",
        "setor": "",
        "modelo": "",
        "tipo": "",
        "prioridade": "",
        "vencimento": "",
        "comentarios": [],
    }

    for linha_descricao in pagina.locator(SELETOR_LINHAS_DESCRICAO).all():
        rotulo_campo = obter_texto(linha_descricao.locator("th.ant-descriptions-item-label")).lower()
        valor_campo = obter_texto(linha_descricao.locator("td.ant-descriptions-item-content"))

        if "cliente" in rotulo_campo:
            dados_ticket["cliente"] = valor_campo
        elif any(palavra_chave in rotulo_campo for palavra_chave in ("cpf", "cnpj", "documento")):
            dados_ticket["cpf_cnpj"] = valor_campo
        elif "status" in rotulo_campo:
            dados_ticket["status"] = valor_campo
        elif "setor" in rotulo_campo:
            dados_ticket["setor"] = valor_campo
        elif "modelo" in rotulo_campo:
            dados_ticket["modelo"] = valor_campo
        elif "tipo" in rotulo_campo:
            dados_ticket["tipo"] = valor_campo
        elif "prioridade" in rotulo_campo:
            dados_ticket["prioridade"] = valor_campo
        elif "vencimento" in rotulo_campo:
            dados_ticket["vencimento"] = valor_campo
        elif rotulo_campo.strip() == "id" and not dados_ticket["ticket_id"]:
            dados_ticket["ticket_id"] = valor_campo

    for seletor_assunto in (".ant-page-header-heading-title", "h1"):
        dados_ticket["assunto"] = obter_texto(pagina.locator(seletor_assunto))
        if dados_ticket["assunto"]:
            break

    dados_ticket["comentarios"] = extrair_comentarios(pagina)
    return dados_ticket
