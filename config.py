from pathlib import Path

URL_BASE = "https://secran.digital"
URL_LISTAGEM_TICKETS = f"{URL_BASE}/admin/cards/tickets"

SELETOR_LINK_TICKET = "td.ant-table-cell a[href*='/cards/view/']"
SELETOR_LINHAS_DESCRICAO = "tr.ant-descriptions-row"
SELETOR_COMENTARIO = "div.ant-comment"

ARQUIVO_TICKETS = Path("dados/dados_tickets.json")
TEMPO_LIMITE_MS = 15000
TEMPO_LIMITE_LOGIN_MS = 30000
