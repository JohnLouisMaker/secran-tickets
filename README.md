# Secran Tickets Scraper

Scraper modular com Playwright para coletar dados dos tickets que aparecem na listagem filtrada manualmente.

## Requisitos

- Python 3.10 ou superior
- Acesso autorizado ao sistema Secran
- Credenciais válidas

## Instalação

```bash
python -m venv .venv
```

Ative o ambiente virtual:

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Instale as dependências e o navegador Chromium:

```bash
pip install -r requirements.txt
playwright install chromium
```

Crie o arquivo `.env` copiando `.env.example` e preencha as credenciais autorizadas. Não compartilhe esse arquivo nem o envie ao Git.

## Execução

```bash
python main.py
```

O navegador será aberto. Faça login se solicitado, aplique os filtros desejados na tabela e pressione ENTER no terminal.

Os dados serão gravados em `dados/dados_tickets.json`. O programa ignora IDs que já estão no arquivo e salva cada ticket após extraí-lo.

## Limitações conhecidas

- O programa coleta os links que estão presentes na listagem no momento em que você pressiona ENTER. Se houver paginação, carregue cada página separadamente ou adapte `coletar_urls_tickets`.
- Os seletores CSS dependem da estrutura atual do site. Se a interface mudar, podem precisar de ajustes.
- A validação do ID evita salvar a página de outro ticket, mas não garante, por si só, que todos os comentários terminaram de carregar. Confirme isso com o HTML real da aplicação.
- Use somente em dados e contas para os quais você tenha autorização.
