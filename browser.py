import os
import time
from urllib.parse import urlsplit

from config import TEMPO_LIMITE_LOGIN_MS, TEMPO_LIMITE_MS, URL_LISTAGEM_TICKETS


def _primeiro_elemento_visivel(pagina, seletores_css):
    primeiro_elemento_existente = None
    for seletor_css in seletores_css:
        elementos_encontrados = pagina.locator(seletor_css)
        if not elementos_encontrados.count():
            continue
        elemento_encontrado = elementos_encontrados.first
        if primeiro_elemento_existente is None:
            primeiro_elemento_existente = elemento_encontrado
        try:
            if elemento_encontrado.is_visible():
                return elemento_encontrado
        except Exception:
            continue
    return primeiro_elemento_existente


def _localizar_formulario_acesso(pagina):
    seletores_campo_email = (
        "#login_email",
        "input[placeholder='Email' i]",
        "input[type='email']",
        "input[name*='email' i]",
        "input[id*='email' i]",
        "input[autocomplete='username']",
        "input[type='text']:visible",
    )
    seletores_campo_senha = (
        "#login_password",
        "input[placeholder='Senha' i]",
        "input[type='password']",
        "input[name*='password' i]",
        "input[id*='password' i]",
    )

    for quadro in pagina.frames:
        campo_senha_encontrado = _primeiro_elemento_visivel(quadro, seletores_campo_senha)
        campo_email_encontrado = _primeiro_elemento_visivel(quadro, seletores_campo_email)
        if campo_senha_encontrado and not campo_email_encontrado:
            campo_email_encontrado = _primeiro_elemento_visivel(
                quadro,
                ("input[name*='user' i]", "input[id*='user' i]", "input[type='text']:visible"),
            )
        if campo_email_encontrado and campo_senha_encontrado:
            return quadro, campo_email_encontrado, campo_senha_encontrado

    return None, None, None


def _diagnostico_pagina(pagina):
    if pagina.is_closed():
        return (
            "A aba do Chromium foi fechada antes de concluir o login. "
            "Não feche a janela enquanto o script estiver executando."
        )

    try:
        texto_pagina = pagina.locator("body").inner_text(timeout=5000)[:2000]
    except Exception as erro:
        texto_pagina = f"Não foi possível ler o conteúdo da página: {erro}"

    try:
        pagina.screenshot(path="debug_pagina.png", full_page=True)
    except Exception:
        pass

    try:
        endereco_atual = pagina.url
    except Exception as erro:
        endereco_atual = f"indisponível ({type(erro).__name__})"

    try:
        titulo_pagina = pagina.title()
    except Exception as erro:
        titulo_pagina = f"indisponível ({type(erro).__name__})"

    return f"URL: {endereco_atual}\nTítulo: {titulo_pagina}\nConteúdo: {texto_pagina}"


def _diagnostico_campos_formulario(pagina):
    linhas_diagnostico = []
    for indice_quadro, quadro in enumerate(pagina.frames):
        try:
            campos_input = quadro.locator("input").all()
            for campo_input in campos_input:
                detalhes_campo = campo_input.evaluate(
                    "element => ({"
                    "type: element.type, id: element.id, name: element.name, "
                    "placeholder: element.placeholder, visible: !!(element.offsetWidth || element.offsetHeight)"
                    "})"
                )
                linhas_diagnostico.append(f"frame {indice_quadro} {quadro.url}: {detalhes_campo}")
        except Exception as erro:
            linhas_diagnostico.append(
                f"frame {indice_quadro} {quadro.url}: não foi possível inspecionar inputs ({type(erro).__name__})"
            )
    return (
        "\n".join(linhas_diagnostico) if linhas_diagnostico else "Nenhum elemento <input> encontrado em qualquer frame."
    )


def _registrar_requisicao_acesso(requisicoes_registradas):
    def registrar_requisicao(requisicao):
        partes_url = urlsplit(requisicao.url)
        requisicoes_registradas.append((requisicao.method.upper(), f"{partes_url.netloc}{partes_url.path}"))

    return registrar_requisicao


def _registrar_resposta_acesso(respostas_registradas):
    def registrar_resposta(resposta):
        partes_url = urlsplit(resposta.url)
        respostas_registradas.append((resposta.status, f"{partes_url.netloc}{partes_url.path}"))

    return registrar_resposta


def abrir_listagem_tickets(pagina):
    email_acesso = os.getenv("SECRAN_EMAIL")
    senha_acesso = os.getenv("SECRAN_PASSWORD")

    if not email_acesso or not senha_acesso:
        raise RuntimeError("Configure SECRAN_EMAIL e SECRAN_PASSWORD no arquivo .env")

    pagina.goto(
        URL_LISTAGEM_TICKETS,
        wait_until="domcontentloaded",
        timeout=TEMPO_LIMITE_LOGIN_MS,
    )

    quadro_login = campo_email = campo_senha = None
    prazo_busca_formulario = time.monotonic() + 10
    while time.monotonic() < prazo_busca_formulario:
        quadro_login, campo_email, campo_senha = _localizar_formulario_acesso(pagina)
        if quadro_login:
            break
        pagina.wait_for_timeout(250)

    respostas_login = []
    requisicoes_login = []

    if quadro_login:
        print(f"Login: campos encontrados no frame {quadro_login.url!r}; preenchendo...")
        campo_email.fill(email_acesso)
        campo_senha.fill(senha_acesso)
        email_preenchido = campo_email.input_value() == email_acesso
        senha_preenchida = campo_senha.input_value() == senha_acesso
        if not email_preenchido or not senha_preenchida:
            raise RuntimeError(
                "Falha ao preencher o formulário: "
                f"email conferido={email_preenchido}, senha conferida={senha_preenchida}."
            )

        botao_entrar = _primeiro_elemento_visivel(
            quadro_login,
            (
                "button:has-text('Entrar')",
                "[role='button']:has-text('Entrar')",
                "button[type='submit']",
                "input[type='submit']",
                "form button",
            ),
        )
        if botao_entrar:
            pagina.on("request", _registrar_requisicao_acesso(requisicoes_login))
            pagina.on("response", _registrar_resposta_acesso(respostas_login))
            print("Login: valores preenchidos e conferidos; clicando em Entrar...")
            botao_entrar.click()
        else:
            raise RuntimeError(
                "Campos encontrados e preenchidos, mas o botão Entrar não foi localizado.\n"
                + _diagnostico_pagina(pagina)
            )
    else:
        raise RuntimeError(
            "A tela mostra login, mas os campos não foram localizados; nenhum dado foi enviado.\n"
            + _diagnostico_pagina(pagina)
            + "\nInputs encontrados (sem valores):\n"
            + _diagnostico_campos_formulario(pagina)
        )

    prazo_login = time.monotonic() + max(TEMPO_LIMITE_MS, TEMPO_LIMITE_LOGIN_MS) / 1000
    while time.monotonic() < prazo_login:
        if pagina.is_closed():
            raise RuntimeError(
                "A aba fechou enquanto aguardava a resposta do login. "
                "O site não confirmou que a autenticação foi concluída."
            )
        if pagina.locator("div.ant-table").count() and pagina.locator("div.ant-table").first.is_visible():
            print("Login: tabela de tickets detectada.")
            break
        pagina.wait_for_timeout(250)
    else:
        requisicoes_formatadas = ", ".join(f"{metodo} {endpoint}" for metodo, endpoint in requisicoes_login)
        respostas_formatadas = ", ".join(f"HTTP {status} {endpoint}" for status, endpoint in respostas_login)
        detalhe_envio = (
            f"Requisições: {requisicoes_formatadas or 'nenhuma (nenhum clique/envio confirmado)'}; "
            f"respostas: {respostas_formatadas or 'nenhuma resposta observada'}"
        )
        raise RuntimeError(
            "O site continuou na tela de login. "
            "Verifique se apareceu uma mensagem de credenciais inválidas ou CAPTCHA.\n"
            f"Envio: {detalhe_envio}\n" + _diagnostico_pagina(pagina)
        )

    print("Login concluído. URL atual:", pagina.url)
