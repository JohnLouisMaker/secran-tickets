import re
from urllib.parse import urljoin

from comments import extrair_comentarios, ler_texto
from config import (
    BASE_URL,
    COMENTARIO,
    LINHAS_DESCRICAO,
    LINK_TICKET,
    TIMEOUT,
)


def coletar_urls_tickets(lista_page):
    tickets = []
    vistos = set()
    links = lista_page.locator(LINK_TICKET)

    for indice in range(links.count()):
        link = links.nth(indice)
        href = link.get_attribute("href") or ""
        match = re.search(r"/cards/view/(\d+)", href)

        if not match:
            continue

        ticket_id = match.group(1)
        if ticket_id in vistos:
            continue

        vistos.add(ticket_id)
        tickets.append((ticket_id, urljoin(BASE_URL, href)))

    return tickets


def extrair_ticket(page, esperado):
    page.locator(f"{LINHAS_DESCRICAO}, .ant-page-header-heading-title, {COMENTARIO}, h1").first.wait_for(
        state="attached", timeout=TIMEOUT
    )

    match = re.search(r"/cards/view/(\d+)", page.url)
    ticket_id = match.group(1) if match else ""

    if not ticket_id or ticket_id != str(esperado):
        raise ValueError(f"ID esperado {esperado}, ID encontrado {ticket_id or 'não identificado'}")

    dados = {
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

    for linha in page.locator(LINHAS_DESCRICAO).all():
        label = ler_texto(linha.locator("th.ant-descriptions-item-label")).lower()
        valor = ler_texto(linha.locator("td.ant-descriptions-item-content"))

        if "cliente" in label:
            dados["cliente"] = valor
        elif any(palavra in label for palavra in ("cpf", "cnpj", "documento")):
            dados["cpf_cnpj"] = valor
        elif "status" in label:
            dados["status"] = valor
        elif "setor" in label:
            dados["setor"] = valor
        elif "modelo" in label:
            dados["modelo"] = valor
        elif "tipo" in label:
            dados["tipo"] = valor
        elif "prioridade" in label:
            dados["prioridade"] = valor
        elif "vencimento" in label:
            dados["vencimento"] = valor
        elif label.strip() == "id" and not dados["ticket_id"]:
            dados["ticket_id"] = valor

    for seletor in (".ant-page-header-heading-title", "h1"):
        dados["assunto"] = ler_texto(page.locator(seletor))
        if dados["assunto"]:
            break

    dados["comentarios"] = extrair_comentarios(page)
    return dados
