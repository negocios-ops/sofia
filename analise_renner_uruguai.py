import io
import time
import re
import os
import hashlib
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
    
    # 🟢 ESSENCIAIS PARA A NUVEM (Evita que o Chrome trave ou falhe)
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 🟢 O TRUQUE CAMALEÃO: Descobre se está no Mac ou na Nuvem
    if os.path.exists('/usr/bin/chromedriver'):
        servico = Service('/usr/bin/chromedriver')
    else:
        servico = Service(ChromeDriverManager().install())
        
    return webdriver.Chrome(service=servico, options=opcoes)

def extrair_produtos_renner(navegador, url_base, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):
    
    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Iniciando captura de {titulo_categoria}...")
    produtos_capturados = []
    links_vistos = set() 
    
    for pagina_atual in range(1, 16):
        uniao = "&" if "?" in url_base else "?"
        url_paginada = f"{url_base}{uniao}page={pagina_atual}"
        
        relatar(f"Acessando Página {pagina_atual}...")
        navegador.get(url_paginada)
        time.sleep(5)

        try:
            corpo_texto = navegador.find_element(By.TAG_NAME, "body").text
            if "No podemos cargar esta lista en este momento" in corpo_texto:
                relatar(f"Fim da lista detectado na página {pagina_atual}.")
                break
        except: pass

        relatar(f"Rolando a página {pagina_atual} para carregar fotos...")
        for _ in range(6):
            navegador.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.4)

        elementos = navegador.find_elements(By.XPATH, "//a[descendant::*[contains(text(), 'UYU') or contains(text(), '$')]]")
        
        contagem_pagina = 0
        for item in elementos:
            try:
                try:
                    ponto_corte = navegador.find_element(By.XPATH, "//*[contains(text(), 'más vendido en') or contains(text(), 'Recomendados para ti')]")
                    if item.location['y'] >= ponto_corte.location['y']:
                        continue 
                except: pass

                link_produto = item.get_attribute("href")
                if not link_produto or link_produto in links_vistos:
                    continue

                texto_item = item.get_attribute("innerText")
                if not texto_item or "UYU" not in texto_item: continue

                matches = re.findall(r'(?:UYU|\$)\s*([\d\.]+)', texto_item)
                if matches:
                    valor_preco = float(matches[0].replace('.', ''))
                    
                    links_vistos.add(link_produto)
                    print_binario = item.screenshot_as_png
                    imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                    produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                    contagem_pagina += 1
            except: continue
        
        relatar(f"Página {pagina_atual} finalizada: {contagem_pagina} novos produtos salvos.")

    if not produtos_capturados: 
        relatar("Nenhum produto encontrado.")
        return None

    # --- MONTAGEM DO PDF ---
    relatar(f"Montando PDF de {titulo_categoria} com {len(produtos_capturados)} itens...")
    largura, altura = 1240, 1754
    paginas_pdf = []
    data_geracao = datetime.now().strftime("%d/%m/%Y")
    
    # 🎀 CARREGANDO E AUMENTANDO A LOGO 
    try:
        logo_img = Image.open("logo.png").convert("RGBA")
        logo_img.thumbnail((200, 80), Image.Resampling.LANCZOS)
    except Exception:
        logo_img = None

    capa = Image.new('RGB', (largura, altura), 'white')
    draw = ImageDraw.Draw(capa)
    try:
        f_tit = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 55)
        f_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 45)
        f_txt = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 30)
        f_rodape = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 25) 
    except: 
        f_tit = f_sub = f_txt = f_rodape = ImageFont.load_default()

    draw.text((620, 150), "Análise de Mercado - Renner Uruguay", fill="black", font=f_tit, anchor="mm")
    draw.text((620, 230), f"Gênero: {titulo_genero}", fill="gray", font=f_sub, anchor="mm")
    draw.text((620, 290), f"Categoria: {titulo_categoria}", fill="gray", font=f_sub, anchor="mm")
    draw.text((620, 420), "Resumo de Faixas de Preço", fill="black", font=f_sub, anchor="mm")

    y_pos = 500
    precos = [p['preco'] for p in produtos_capturados]
    qtd_base = len([p for p in precos if p <= 490])
    draw.text((350, y_pos), f"Até UYU 490 ........................... {qtd_base} produtos", fill="black", font=f_txt)
    y_pos += 45

    for i in range(491, 1991, 100):
        fim = i + 99
        qtd = len([p for p in precos if i <= p <= fim])
        draw.text((350, y_pos), f"De UYU {i} a UYU {fim} ................. {qtd} produtos", fill="black", font=f_txt)
        y_pos += 45
    
    qtd_final = len([p for p in precos if p > 1990])
    draw.text((350, y_pos), f"Acima de UYU 1.990 .................... {qtd_final} produtos", fill="black", font=f_txt)
    draw.text((620, y_pos + 100), f"TOTAL: {len(produtos_capturados)} produtos únicos mapeados", fill="black", font=f_tit, anchor="mm")
    draw.text((620, altura - 100), f"Gerado em: {data_geracao}", fill="gray", font=f_txt, anchor="mm")
    
    # 🎀 CARIMBO MOVIDO PARA A DIREITA (Capa)
    draw.text((950, 1680), "Conteúdo gerado por:", fill="gray", font=f_rodape)
    if logo_img: 
        capa.paste(logo_img, (1170, 1660), logo_img)

    paginas_pdf.append(capa)

    ordenados = sorted(produtos_capturados, key=lambda p: p['preco'])
    for i in range(0, len(ordenados), 9):
        lote = ordenados[i:i+9]
        pagina = Image.new('RGB', (largura, altura), 'white')
        d_pagina = ImageDraw.Draw(pagina) 
        
        for j, prod in enumerate(lote):
            img_copy = prod['imagem'].copy()
            img_copy.thumbnail((380, 520), Image.Resampling.LANCZOS)
            d_prod = ImageDraw.Draw(img_copy)
            d_prod.rectangle([0, 0, 180, 50], fill="red")
            d_prod.text((10, 5), f"UYU {prod['preco']:.0f}", fill="white", font=f_txt)
            x, y = 20 + ((j % 3) * 400), 30 + ((j // 3) * 560) 
            pagina.paste(img_copy, (x, y))
            
        # 🎀 CARIMBO MOVIDO PARA A DIREITA (Páginas de Produtos)
        d_pagina.text((950, 1680), "Conteúdo gerado por:", fill="gray", font=f_rodape)
        if logo_img: 
            pagina.paste(logo_img, (1170, 1660), logo_img)
        paginas_pdf.append(pagina)

    paginas_pdf[0].save(arquivo_saida, save_all=True, append_images=paginas_pdf[1:])
    relatar(f"PDF de {titulo_categoria} pronto!")
    return arquivo_saida
