from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from browser import abrir_lista
from storage import carregar, salvar
from tickets import coletar_urls_tickets, extrair_ticket


def main():
    load_dotenv()

    dados = carregar()
    salvos = {str(item["ticket_id"]) for item in dados if item.get("ticket_id")}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        lista = context.new_page()

        try:
            try:
                abrir_lista(lista)
            except RuntimeError as exc:
                print(exc)
                input(
                    "A janela do navegador ficará aberta para inspeção. "
                    "Depois de verificar a mensagem do site, pressione ENTER para fechar... "
                )
                return

            input("Aplique os filtros desejados na tabela e pressione ENTER para continuar... ")

            tickets = coletar_urls_tickets(lista)
            print(f"Tickets encontrados na página/listagem atual: {len(tickets)}")

            page = context.new_page()
            try:
                for indice, (ticket_id, url) in enumerate(tickets, start=1):
                    if ticket_id in salvos:
                        print(f"[{indice}/{len(tickets)}] Ticket {ticket_id}: já salvo, ignorando.")
                        continue

                    print(f"[{indice}/{len(tickets)}] Processando ticket {ticket_id}...")
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        info = extrair_ticket(page, ticket_id)

                        dados.append(info)
                        salvar(dados)
                        salvos.add(ticket_id)

                        print(f"  Salvo: {len(info['comentarios'])} comentários; assunto: {info['assunto'][:70]}")
                    except Exception as exc:
                        print(f"  ERRO no ticket {ticket_id}: {type(exc).__name__}: {exc}")
            finally:
                page.close()
        finally:
            try:
                browser.close()
            except Exception as exc:
                print(f"Aviso ao encerrar Chromium: {type(exc).__name__}: {exc}")

    print(f"Concluído: {len(dados)} tickets registrados.")


if __name__ == "__main__":
    main()
