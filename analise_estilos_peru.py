import io
import time
import re
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
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

def extrair_produtos_estilos(navegador, url_base, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):
    
    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Iniciando captura de {titulo_categoria} (Estilos Peru)...")
    produtos_capturados = []
    links_vistos = set()

# 🎀 SISTEMA DE TOLERÂNCIA E MEMÓRIA
    paginas_vazias_consecutivas = 0
    
    for pagina_atual in range(1, 71):
        uniao = "&" if "?" in url_base else "?"
        url_paginada = f"{url_base}{uniao}page={pagina_atual}"
        
        relatar(f"Acessando Página {pagina_atual}...")
        navegador.get(url_paginada)
        time.sleep(6) # 🎀 Esperando 1 segundinho a mais para sites lentos
        
        relatar(f"Rolando a página {pagina_atual} para carregar fotos...")
        for _ in range(10): # 🎀 Rolando um pouco mais fundo
            navegador.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.5)
            
        elementos = navegador.find_elements(By.XPATH, "//a[descendant::img and descendant::*[contains(text(), 'S/')]]")
        
        contagem_pagina = 0
        for item in elementos:
            try:
                link_produto = item.get_attribute("href")
                if not link_produto or link_produto in links_vistos:
                    continue
                    
                texto_item = item.get_attribute("innerText")
                if not texto_item or "S/" not in texto_item:
                    continue
                    
                matches = re.findall(r'S/\.?\s*([\d\.,]+)', texto_item)
                if matches:
                    precos_convertidos = []
                    for m in matches:
                        valor_str = m.replace(',', '') if m.count(',') > 1 or (',' in m and '.' in m) else m.replace(',', '.')
                        precos_convertidos.append(float(valor_str))
                    
                    valor_preco = max(precos_convertidos)
                    links_vistos.add(link_produto)
                    
                    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                    time.sleep(0.3)
                    
                    print_binario = item.screenshot_as_png
                    imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                    
                    # 🎀 DIETA MAIS FORTE: Reduzindo ainda mais na memória (não afeta tanto o PDF final)
                    imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                    
                    produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                    contagem_pagina += 1
            except Exception:
                continue
                
        relatar(f"Página {pagina_atual} finalizada: {contagem_pagina} produtos salvos.")
        
        # 🎀 NOVO FREIO INTELIGENTE: Só para se ver 3 páginas vazias seguidas
        if contagem_pagina == 0:
            paginas_vazias_consecutivas += 1
            relatar(f"⚠️ Nenhum produto encontrado. Tentativa vazia {paginas_vazias_consecutivas}/3.")
            if paginas_vazias_consecutivas >= 3:
                relatar(f"Fim da lista confirmado após {pagina_atual} páginas.")
                break
        else:
            paginas_vazias_consecutivas = 0 # Zera o contador se achar produtos!
