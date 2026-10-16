import os
import time
from urllib.parse import urlsplit

from config import LISTA_URL, TIMEOUT, TIMEOUT_LOGIN


def _primeiro_visivel(page, seletores):
    primeiro_existente = None
    for seletor in seletores:
        elementos = page.locator(seletor)
        if not elementos.count():
            continue
        elemento = elementos.first
        if primeiro_existente is None:
            primeiro_existente = elemento
        try:
            if elemento.is_visible():
                return elemento
        except Exception:
            continue
    return primeiro_existente


def _localizar_formulario_login(page):
    seletores_email = (
        "#login_email",
        "input[placeholder='Email' i]",
        "input[type='email']",
        "input[name*='email' i]",
        "input[id*='email' i]",
        "input[autocomplete='username']",
        "input[type='text']:visible",
    )
    seletores_senha = (
        "#login_password",
        "input[placeholder='Senha' i]",
        "input[type='password']",
        "input[name*='password' i]",
        "input[id*='password' i]",
    )

    for frame in page.frames:
        senha = _primeiro_visivel(frame, seletores_senha)
        email = _primeiro_visivel(frame, seletores_email)
        if senha and not email:
            email = _primeiro_visivel(
                frame,
                ("input[name*='user' i]", "input[id*='user' i]", "input[type='text']:visible"),
            )
        if email and senha:
            return frame, email, senha

    return None, None, None


def _diagnostico(page):
    if page.is_closed():
        return (
            "A aba do Chromium foi fechada antes de concluir o login. "
            "Não feche a janela enquanto o script estiver executando."
        )

    try:
        texto = page.locator("body").inner_text(timeout=5000)[:2000]
    except Exception as erro:
        texto = f"Não foi possível ler o conteúdo da página: {erro}"

    try:
        page.screenshot(path="debug_pagina.png", full_page=True)
    except Exception:
        pass

    try:
        url = page.url
    except Exception as erro:
        url = f"indisponível ({type(erro).__name__})"

    try:
        titulo = page.title()
    except Exception as erro:
        titulo = f"indisponível ({type(erro).__name__})"

    return f"URL: {url}\nTítulo: {titulo}\nConteúdo: {texto}"


def _diagnostico_campos(page):
    linhas = []
    for indice, frame in enumerate(page.frames):
        try:
            inputs = frame.locator("input").all()
            for input_element in inputs:
                detalhes = input_element.evaluate(
                    "element => ({"
                    "type: element.type, id: element.id, name: element.name, "
                    "placeholder: element.placeholder, visible: !!(element.offsetWidth || element.offsetHeight)"
                    "})"
                )
                linhas.append(f"frame {indice} {frame.url}: {detalhes}")
        except Exception as erro:
            linhas.append(f"frame {indice} {frame.url}: não foi possível inspecionar inputs ({type(erro).__name__})")
    return "\n".join(linhas) if linhas else "Nenhum elemento <input> encontrado em qualquer frame."


def _registrar_requisicao_login(requisicoes):
    def registrar(request):
        partes = urlsplit(request.url)
        requisicoes.append((request.method.upper(), f"{partes.netloc}{partes.path}"))

    return registrar


def _registrar_resposta_login(respostas):
    def registrar(response):
        partes = urlsplit(response.url)
        respostas.append((response.status, f"{partes.netloc}{partes.path}"))

    return registrar


def abrir_lista(page):
    email = os.getenv("SECRAN_EMAIL")
    senha = os.getenv("SECRAN_PASSWORD")

    if not email or not senha:
        raise RuntimeError("Configure SECRAN_EMAIL e SECRAN_PASSWORD no arquivo .env")

    page.goto(
        LISTA_URL,
        wait_until="domcontentloaded",
        timeout=TIMEOUT_LOGIN,
    )

    frame_login = campo_email = campo_senha = None
    limite_busca = time.monotonic() + 10
    while time.monotonic() < limite_busca:
        frame_login, campo_email, campo_senha = _localizar_formulario_login(page)
        if frame_login:
            break
        page.wait_for_timeout(250)

    respostas_login = []
    requisicoes_login = []

    if frame_login:
        print(f"Login: campos encontrados no frame {frame_login.url!r}; preenchendo...")
        campo_email.fill(email)
        campo_senha.fill(senha)
        email_preenchido = campo_email.input_value() == email
        senha_preenchida = campo_senha.input_value() == senha
        if not email_preenchido or not senha_preenchida:
            raise RuntimeError(
                "Falha ao preencher o formulário: "
                f"email conferido={email_preenchido}, senha conferida={senha_preenchida}."
            )

        botao_entrar = _primeiro_visivel(
            frame_login,
            (
                "button:has-text('Entrar')",
                "[role='button']:has-text('Entrar')",
                "button[type='submit']",
                "input[type='submit']",
                "form button",
            ),
        )
        if botao_entrar:
            page.on("request", _registrar_requisicao_login(requisicoes_login))
            page.on("response", _registrar_resposta_login(respostas_login))
            print("Login: valores preenchidos e conferidos; clicando em Entrar...")
            botao_entrar.click()
        else:
            raise RuntimeError(
                "Campos encontrados e preenchidos, mas o botão Entrar não foi localizado.\n" + _diagnostico(page)
            )
    else:
        raise RuntimeError(
            "A tela mostra login, mas os campos não foram localizados; nenhum dado foi enviado.\n"
            + _diagnostico(page)
            + "\nInputs encontrados (sem valores):\n"
            + _diagnostico_campos(page)
        )

    prazo = time.monotonic() + max(TIMEOUT, TIMEOUT_LOGIN) / 1000
    while time.monotonic() < prazo:
        if page.is_closed():
            raise RuntimeError(
                "A aba fechou enquanto aguardava a resposta do login. "
                "O site não confirmou que a autenticação foi concluída."
            )
        if page.locator("div.ant-table").count() and page.locator("div.ant-table").first.is_visible():
            print("Login: tabela de tickets detectada.")
            break
        page.wait_for_timeout(250)
    else:
        requisicoes = ", ".join(f"{metodo} {endpoint}" for metodo, endpoint in requisicoes_login)
        respostas = ", ".join(f"HTTP {status} {endpoint}" for status, endpoint in respostas_login)
        detalhe_envio = (
            f"Requisições: {requisicoes or 'nenhuma (nenhum clique/envio confirmado)'}; "
            f"respostas: {respostas or 'nenhuma resposta observada'}"
        )
        raise RuntimeError(
            "O site continuou na tela de login. "
            "Verifique se apareceu uma mensagem de credenciais inválidas ou CAPTCHA.\n"
            f"Envio: {detalhe_envio}\n" + _diagnostico(page)
        )

    print("Login concluído. URL atual:", page.url)
