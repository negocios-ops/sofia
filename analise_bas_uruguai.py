import io
import time
import re
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def iniciar_navegador():
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument('--headless')
    opcoes.add_argument('--window-size=1920,1080')
    opcoes.add_argument('--disable-notifications')
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    if os.path.exists('/usr/bin/chromedriver'):
        servico = Service('/usr/bin/chromedriver')
    else:
        servico = Service(ChromeDriverManager().install())
        
    return webdriver.Chrome(service=servico, options=opcoes)

def extrair_produtos_bas(navegador, url_alvo, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):

    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Iniciando captura de {titulo_categoria} (Bas Uruguai)...")

    produtos_capturados = []
    links_vistos = set()

    tem_paginacao = "page=" in url_alvo

    for pagina_atual in range(1, 15):

        if tem_paginacao:
            url_pagina = re.sub(r'page=\d+', f'page={pagina_atual}', url_alvo)
        else:
            separador = "&" if "?" in url_alvo else "?"
            url_pagina = f"{url_alvo}{separador}page={pagina_atual}"

        relatar(f"🌐 Página {pagina_atual}")

        navegador.get(url_pagina)
        time.sleep(5)

        # força carregar lazy load
        navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        try:
            navegador.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except:
            pass

        produtos_nesta_pagina = 0

        for _ in range(25):

            imagens = navegador.find_elements(By.TAG_NAME, "img")

            for img in imagens:

                try:

                    # pega qualquer atributo possível da imagem
                    src = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or img.get_attribute("srcset")
                        or ""
                    )

                    if "vtexassets" not in src:
                        continue

                    container = img
                    txt = container.text

                    # subida segura do DOM
                    for nivel in range(6):

                        if "$" in txt or "UYU" in txt:
                            break

                        try:
                            container = container.find_element(By.XPATH, "..")
                            txt = container.text
                        except:
                            break

                    if "$" not in txt and "UYU" not in txt:
                        continue

                    try:
                        href = container.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        href = src

                    if not href or href in links_vistos:
                        continue

                    matches = re.findall(r'(?:\$|UYU)\s*([\d\.,]+)', txt)

                    if not matches:
                        continue

                    precos = []

                    for m in matches:

                        clean_str = m.replace(' ', '')

                        if ',' in clean_str and '.' in clean_str:
                            if clean_str.rfind(',') > clean_str.rfind('.'):
                                clean_str = clean_str.replace('.', '').replace(',', '.')
                            else:
                                clean_str = clean_str.replace(',', '')

                        elif ',' in clean_str:
                            if len(clean_str.split(',')[-1]) == 2:
                                clean_str = clean_str.replace(',', '.')
                            else:
                                clean_str = clean_str.replace(',', '')

                        elif '.' in clean_str:
                            if len(clean_str.split('.')[-1]) != 2:
                                clean_str = clean_str.replace('.', '')

                        try:
                            precos.append(float(clean_str))
                        except:
                            pass

                    if not precos:
                        continue

                    valor_preco = max(precos)

                    navegador.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        container
                    )

                    time.sleep(0.3)

                    screenshot = container.screenshot_as_png

                    imagem = Image.open(io.BytesIO(screenshot)).convert('RGB')

                    if imagem.size[1] < 120:
                        continue

                    imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)

                    links_vistos.add(href)

                    produtos_capturados.append({
                        'imagem': imagem,
                        'preco': valor_preco
                    })

                    produtos_nesta_pagina += 1

                except:
                    continue

            navegador.execute_script("window.scrollBy(0, 700);")
            time.sleep(0.4)

        relatar(
            f"✅ {produtos_nesta_pagina} produtos encontrados na página {pagina_atual}. "
            f"Total: {len(produtos_capturados)}"
        )

        if produtos_nesta_pagina == 0:
            relatar("Fim das páginas.")
            break

    if not produtos_capturados:
        relatar("❌ Nenhum produto encontrado.")
        return None

    relatar(f"Total capturado: {len(produtos_capturados)} produtos")

    return produtos_capturados
