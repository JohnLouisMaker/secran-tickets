from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from browser import abrir_listagem_tickets
from storage import carregar_tickets, salvar_tickets
from tickets import coletar_urls_tickets, extrair_ticket


def main():
    load_dotenv()

    tickets_registrados = carregar_tickets()
    ids_tickets_salvos = {
        str(registro_ticket["ticket_id"])
        for registro_ticket in tickets_registrados
        if registro_ticket.get("ticket_id")
    }

    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=False)
        contexto_navegador = navegador.new_context()
        pagina_listagem = contexto_navegador.new_page()

        try:
            try:
                abrir_listagem_tickets(pagina_listagem)
            except RuntimeError as erro:
                print(erro)
                input(
                    "A janela do navegador ficará aberta para inspeção. "
                    "Depois de verificar a mensagem do site, pressione ENTER para fechar... "
                )
                return

            input("Aplique os filtros desejados na tabela e pressione ENTER para continuar... ")

            tickets_encontrados = coletar_urls_tickets(pagina_listagem)
            print(f"Tickets encontrados na página/listagem atual: {len(tickets_encontrados)}")

            pagina_ticket = contexto_navegador.new_page()
            try:
                for posicao_ticket, (ticket_id, url_ticket) in enumerate(tickets_encontrados, start=1):
                    if ticket_id in ids_tickets_salvos:
                        print(
                            f"[{posicao_ticket}/{len(tickets_encontrados)}] "
                            f"Ticket {ticket_id}: já salvo, ignorando."
                        )
                        continue

                    print(
                        f"[{posicao_ticket}/{len(tickets_encontrados)}] "
                        f"Processando ticket {ticket_id}..."
                    )
                    try:
                        pagina_ticket.goto(url_ticket, wait_until="domcontentloaded", timeout=30000)
                        dados_ticket = extrair_ticket(pagina_ticket, ticket_id)

                        tickets_registrados.append(dados_ticket)
                        salvar_tickets(tickets_registrados)
                        ids_tickets_salvos.add(ticket_id)

                        print(
                            f"  Salvo: {len(dados_ticket['comentarios'])} comentários; "
                            f"assunto: {dados_ticket['assunto'][:70]}"
                        )
                    except Exception as erro:
                        print(f"  ERRO no ticket {ticket_id}: {type(erro).__name__}: {erro}")
            finally:
                pagina_ticket.close()
        finally:
            try:
                navegador.close()
            except Exception as erro:
                print(f"Aviso ao encerrar Chromium: {type(erro).__name__}: {erro}")

    print(f"Concluído: {len(tickets_registrados)} tickets registrados.")


if __name__ == "__main__":
    main()
