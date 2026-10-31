import json

from config import ARQUIVO_TICKETS


def carregar_tickets():
    if not ARQUIVO_TICKETS.exists():
        return []

    try:
        lista_tickets = json.loads(ARQUIVO_TICKETS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise RuntimeError(
            f"O arquivo {ARQUIVO_TICKETS} contém JSON inválido. "
            "Faça uma cópia e corrija/recupere o arquivo antes de continuar."
        ) from erro

    if not isinstance(lista_tickets, list):
        raise ValueError(f"{ARQUIVO_TICKETS} precisa conter uma lista JSON.")

    tickets_por_id = {}
    tickets_sem_id = []

    for registro_ticket in lista_tickets:
        if not isinstance(registro_ticket, dict):
            continue
        ticket_id = str(registro_ticket.get("ticket_id", "")).strip()
        if ticket_id:
            registro_ticket["ticket_id"] = ticket_id
            tickets_por_id[ticket_id] = registro_ticket
        else:
            tickets_sem_id.append(registro_ticket)

    return list(tickets_por_id.values()) + tickets_sem_id


def salvar_tickets(lista_tickets):
    ARQUIVO_TICKETS.parent.mkdir(parents=True, exist_ok=True)
    arquivo_temporario = ARQUIVO_TICKETS.with_suffix(".tmp")
    conteudo_json = json.dumps(lista_tickets, ensure_ascii=False, indent=2)

    arquivo_temporario.write_text(conteudo_json, encoding="utf-8")
    arquivo_temporario.replace(ARQUIVO_TICKETS)
