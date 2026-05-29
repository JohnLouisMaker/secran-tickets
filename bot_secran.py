import re
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Chrome()
driver.maximize_window()

# ── Seletores XPATH ───────────────────────────────────────────────────────────
XPATH_LINHAS = "//div[contains(@class,'ant-table')]//tbody/tr[contains(@class,'ant-table-row')]"
XPATH_SPINNER = "//div[contains(@class,'ant-spin-nested-loading')]//div[contains(@class,'ant-spin-spinning')]"
XPATH_BLOCO_COMENTARIO = "//ul[contains(@class,'ant-list-items')]/li[.//div[contains(@class,'ant-comment')]]"

XPATH_FECHAR = (
    "/html/body/div[6]/div/div[2]/div/div[2]/button"
    " | //*[contains(@class,'ant-drawer-close')]"
    " | //*[contains(@class,'ant-modal-close')]"
    " | //button[@aria-label='Close']"
    " | //button[contains(@class,'close')]"
    " | //*[@data-icon='close']/ancestor::button[1]"
    " | //span[contains(@class, 'ant-modal-close-x')]"
)
XPATH_MASCARA_MODAL = "//div[contains(@class, 'ant-modal-wrap') or contains(@class, 'ant-drawer-wrap')]"
XPATH_SEGURANCA = (
    '//*[@id="root"]/div/section/section/section/main'
    '/div[2]/div[2]/div[1]/div/div[2]/div/div[1]'
    '/div/div/div/div[2]/div/div/div[1]/input'
)

# ── Funções de Suporte ────────────────────────────────────────────────────────
def contar_linhas():
    return len(driver.find_elements(By.XPATH, XPATH_LINHAS))

def buscar_linha_por_indice(idx_1based):
    xpath = f"({XPATH_LINHAS})[{idx_1based}]"
    return driver.find_element(By.XPATH, xpath)

def capturar_url_e_id():
    """
    Após o modal abrir, captura a URL atual do navegador e extrai o ID do ticket.
    O React Router atualiza a URL para algo como:
      https://secran.digital/admin/cards/tickets/2782449
    Extrai o último segmento numérico com 5+ dígitos.
    Retorna (url, ticket_id).
    """
    url = driver.current_url

    # Padrão principal: /modal/interact/2639764
    match = re.search(r'/interact/(\d+)', url)
    if match:
        return url, match.group(1)

    # Fallback: qualquer segmento numérico com 5+ dígitos
    match = re.search(r'/(\d{5,})(?:[/?#]|$)', url)
    if match:
        return url, match.group(1)

    # Fallback: query string (?id=XXXXX)
    match = re.search(r'[?&](?:id|ticket|card)=(\d{4,})', url)
    if match:
        return url, match.group(1)

    return url, ""

def capturar_id_do_titulo_modal():
    """
    Fallback: lê o ID do título/cabeçalho do drawer ou modal.
    Útil quando a URL não muda após o clique.
    """
    seletores = [
        "//div[contains(@class,'ant-drawer-title')]",
        "//div[contains(@class,'ant-modal-title')]",
        "//h4[contains(@class,'ant-drawer-title')]",
        "//span[contains(@class,'ant-drawer-title')]",
    ]
    for sel in seletores:
        els = driver.find_elements(By.XPATH, sel)
        if els:
            txt = els[0].text.strip()
            match = re.search(r'\d{4,}', txt)
            if match:
                return match.group(0)
    return ""

def esperar_comentarios_carregarem(wait, url_antes, timeout=15):
    # 1. Aguarda URL mudar (React Router navegou para o ticket)
    try:
        WebDriverWait(driver, 6).until(lambda d: d.current_url != url_antes)
    except TimeoutException:
        pass

    # 2. Aguarda spinner sumir
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, XPATH_SPINNER))
        )
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.XPATH, XPATH_SPINNER))
        )
    except TimeoutException:
        pass

    # 3. Aguarda lista de comentários aparecer
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//ul[contains(@class,'ant-list-items')]")
            )
        )
    except TimeoutException:
        pass

    time.sleep(0.5)

def extrair_comentarios():
    blocos = driver.find_elements(By.XPATH, XPATH_BLOCO_COMENTARIO)
    comentarios_processados = []

    for bloco in blocos:
        try:
            texto_comentario = ""
            try:
                detalhe = bloco.find_element(
                    By.XPATH, ".//div[contains(@class,'ant-comment-content-detail')]"
                )
                texto_comentario = driver.execute_script(
                    "return arguments[0].innerText;", detalhe
                ).strip()
            except Exception:
                texto_comentario = bloco.text.strip()

            if not texto_comentario:
                continue

            autor = ""
            try:
                el_autor = bloco.find_element(
                    By.XPATH, ".//*[contains(@class,'ant-comment-content-author-name')]"
                )
                autor = driver.execute_script("return arguments[0].innerText;", el_autor).strip()
            except Exception:
                pass

            # ── Extração da Data Exata via Hover (Tooltip AntD) ───────────────
            data_definitiva = "[Data indisponível]"
            try:
                el_tempo = bloco.find_element(
                    By.XPATH, ".//*[contains(@class,'ant-comment-content-author-time')]"
                )
                
                # Garante o elemento centralizado para o mouse poder alcançá-lo
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el_tempo)
                time.sleep(0.15)

                # Realiza a ação física de hover (passar o mouse por cima)
                actions = ActionChains(driver)
                actions.move_to_element(el_tempo).perform()
                
                # Aguarda o elemento de tooltip do AntDesign aparecer dinamicamente
                xpath_tooltip = "//div[contains(@class,'ant-tooltip') and not(contains(@class,'ant-tooltip-hidden'))]//div[contains(@class,'ant-tooltip-inner')]"
                tooltip_box = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, xpath_tooltip))
                )
                
                # Extrai o texto contendo a data cheia
                data_definitiva = tooltip_box.text.strip()
                
                # Move o ponteiro para fora evitando retenção de tooltips anteriores
                actions.move_by_offset(150, 0).perform()
                
            except Exception:
                # Fallback caso ocorra erro no hover: captura o texto relativo nativo ("há 10 dias")
                try:
                    data_definitiva = driver.execute_script("return arguments[0].innerText;", el_tempo).strip()
                except Exception:
                    pass

            entrada = f"Data: {data_definitiva}"
            if autor:
                entrada += f"\nAutor: {autor}"
            entrada += f"\nMensagem: {texto_comentario}"
            comentarios_processados.append(entrada)

        except Exception:
            continue

    return comentarios_processados

# ── Fluxo Principal ───────────────────────────────────────────────────────────
try:
    print("Abrindo a intranet...")
    driver.get("https://secran.digital/admin/cards/tickets")

    WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.XPATH, XPATH_SEGURANCA))
    )

    input("\nAplique os filtros desejados na tela e pressione [ENTER] no terminal para começar...")

    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.XPATH, XPATH_LINHAS)))
    time.sleep(1.5)

    total_tickets = contar_linhas()
    print(f"Total de tickets encontrados na tabela: {total_tickets}")

    if total_tickets == 0:
        print("Nenhum ticket encontrado. Encerrando.")
        raise SystemExit

    lista_de_dados = []

    for i in range(1, total_tickets + 1):
        print(f"\n[{i}/{total_tickets}] Processando linha...")
        try:
            linha = buscar_linha_por_indice(i)
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", linha
            )
            time.sleep(0.5)

            # Busca o link do ticket na linha
            try:
                botao_abrir = linha.find_element(
                    By.XPATH, ".//a[contains(@href, '/tickets/')]"
                )
            except Exception:
                botao_abrir = linha.find_element(By.XPATH, ".//a")

            # Guarda a URL ANTES do clique para detectar mudança
            url_antes = driver.current_url

            driver.execute_script("arguments[0].click();", botao_abrir)

            # Aguarda modal + comentários carregarem (detectando mudança de URL)
            esperar_comentarios_carregarem(wait, url_antes)

            # ── Captura URL e ID real do ticket ───────────────────────────────
            url_ticket, ticket_id = capturar_url_e_id()

            # Fallback 1: título do modal
            if not ticket_id:
                ticket_id = capturar_id_do_titulo_modal()

            # Fallback 2: texto do link clicado
            if not ticket_id:
                texto_link = botao_abrir.text.strip()
                if re.search(r'\d{4,}', texto_link):
                    ticket_id = re.search(r'\d{4,}', texto_link).group(0)

            # Fallback 3: número da linha
            if not ticket_id:
                ticket_id = f"Linha_{i}"

            comentarios_processados = extrair_comentarios()
            historico = (
                "\n---\n".join(comentarios_processados)
                if comentarios_processados
                else "[ticket sem comentários visíveis]"
            )

            print(f"  → {len(comentarios_processados)} comentário(s) extraído(s)")
            print(f"  → ID: {ticket_id} | URL: {url_ticket}")

            lista_de_dados.append({
                "ticket_id":    ticket_id,
                "url_ticket":   url_ticket,
                "linha_tabela": i,
                "historico":    historico
            })

            # ── Fechamento do Modal ───────────────────────────────────────────
            fechou = False
            try:
                btn = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, XPATH_FECHAR))
                )
                driver.execute_script("arguments[0].click();", btn)
                fechou = True
            except Exception:
                pass

            if not fechou:
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(1.0)
                    fechou = True
                except Exception:
                    pass

            if not fechou:
                try:
                    mascara = driver.find_element(By.XPATH, XPATH_MASCARA_MODAL)
                    driver.execute_script("arguments[0].click();", mascara)
                except Exception:
                    pass

            time.sleep(2.0)

        except Exception as erro:
            print(f"  → ERRO na linha {i}: {erro}")
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass
            time.sleep(2.0)
            continue

    if lista_de_dados:
        with open("dados_tickets.json", "w", encoding="utf-8") as f:
            json.dump(lista_de_dados, f, ensure_ascii=False, indent=4)
        print(f"\n[SUCESSO] Arquivo salvo: dados_tickets.json ({len(lista_de_dados)} tickets salvos)")
    else:
        print("\n[AVISO] Nenhum dado foi coletado.")

except Exception as e:
    print(f"\nErro geral na execução: {e}")
finally:
    print("Finalizando driver...")
    try:
        driver.quit()
    except Exception:
        pass