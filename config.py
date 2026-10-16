from pathlib import Path

BASE_URL = "https://secran.digital"
LISTA_URL = f"{BASE_URL}/admin/cards/tickets"

LINK_TICKET = "td.ant-table-cell a[href*='/cards/view/']"
LINHAS_DESCRICAO = "tr.ant-descriptions-row"
COMENTARIO = "div.ant-comment"

ARQUIVO_DADOS = Path("dados/dados_tickets.json")
TIMEOUT = 15000
TIMEOUT_LOGIN = 30000
