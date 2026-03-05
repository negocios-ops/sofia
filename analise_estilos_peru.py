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
    
    # Tenta até 15 páginas
    for pagina_atual in range(1, 16):
        uniao = "&" if "?" in url_base else "?"
        url_paginada = f"{url_base}{uniao}page={pagina_atual}"
        
        relatar(f"Acessando Página {pagina_atual}...")
        navegador.get(url_paginada)
        time.sleep(5)
        
        relatar(f"Rolando a página {pagina_atual} para carregar fotos...")
        for _ in range(8):
            navegador.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.5)
            
        # Busca links com imagem e que tenham o texto "S/" (Soles)
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
                    # Limpa o valor para o padrão de leitura em Python
                    valor_str = matches[0].replace(',', '') if matches[0].count(',') > 1 or (',' in matches[0] and '.' in matches[0]) else matches[0].replace(',', '.')
                    valor_preco = float(valor_str)
                    
                    links_vistos.add(link_produto)
                    
                    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                    time.sleep(0.3)
                    
                    print_binario = item.screenshot_as_png
                    imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                    produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                    contagem_pagina += 1
            except Exception:
                continue
                
        relatar(f"Página {pagina_atual} finalizada: {contagem_pagina} produtos salvos.")
        
        # Parada antecipada: se a página não trouxe nenhum produto, acabou o catálogo!
        if contagem_pagina == 0:
            relatar(f"Fim da lista detectado na página {pagina_atual}.")
            break

    if not produtos_capturados: 
        relatar("❌ Nenhum produto encontrado.")
        return None

    relatar(f"Montando PDF Profissional de {titulo_categoria} com {len(produtos_capturados)} itens...")
    
    # --- MONTAGEM DO PDF ---
    largura, altura = 1240, 1754 
    page_center_x = largura / 2
    paginas_pdf = []
    data_geracao = datetime.now().strftime("%d/%m/%Y")
    
    def obter_fonte(tamanho, negrito=False):
        caminhos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if negrito else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "arial.ttf"
        ]
        for caminho in caminhos:
            try: return ImageFont.truetype(caminho, tamanho)
            except: pass
        return ImageFont.load_default()

    f_tit = obter_fonte(38, negrito=True)
    f_sub = obter_fonte(28)              
    f_txt = obter_fonte(20)              
    f_rodape = obter_fonte(16)           

    try:
        logo_img = Image.open("logo.png").convert("RGBA")
        logo_img.thumbnail((150, 60), Image.Resampling.LANCZOS)
    except Exception:
        logo_img = None

    capa = Image.new('RGB', (largura, altura), 'white')
    draw = ImageDraw.Draw(capa)
    
    draw.text((page_center_x, 150), "Análise de Mercado - Estilos Peru", fill="black", font=f_tit, anchor="mm")
    draw.text((page_center_x, 230), f"Gênero: {titulo_genero}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 290), f"Categoria: {titulo_categoria}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 400), "Resumo de Faixas de Preço", fill="black", font=f_sub, anchor="mm")

    # Faixas de preço adaptadas para a moeda SOLES (S/)
    faixas = [
        (0, 49.99, "Até S/ 49"),
        (50, 99.99, "De S/ 50 a S/ 99"),
        (100, 149.99, "De S/ 100 a S/ 149"),
        (150, 199.99, "De S/ 150 a S/ 199"),
        (200, float('inf'), "Acima de S/ 200")
    ]
    
    contagem_precos = {f[2]: 0 for f in faixas}
    
    for p in produtos_capturados:
        for min_p, max_p, label in faixas:
            if min_p <= p['preco'] <= max_p:
                contagem_precos[label] += 1
                break

    y_pos = 480
    for label, count in contagem_precos.items():
        palavra = "produtos" if count != 1 else "produto"
        draw.text((page_center_x, y_pos), f"{label} ........................ {count} {palavra}", fill="black", font=f_txt, anchor="mm")
        y_pos += 30
    
    draw.text((page_center_x, y_pos + 120), f"TOTAL: {len(produtos_capturados)} produtos únicos mapeados", fill="black", font=f_tit, anchor="mm")
    
    # Rodapé da Capa (À esquerda, igual Hering/Renner)
    draw.text((page_center_x, altura - 150), f"Gerado em: {data_geracao}", fill="gray", font=f_txt, anchor="mm")
    draw.text((100, altura - 110), "Conteúdo gerado por:", fill="gray", font=f_rodape)
    if logo_img:
        capa.paste(logo_img, (100, altura - 80), logo_img)

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
            d_prod.rectangle([0, 0, 160, 50], fill="red")
            d_prod.text((10, 5), f"S/ {prod['preco']:.2f}", fill="white", font=f_txt)
            x, y = 20 + ((j % 3) * 400), 30 + ((j // 3) * 560) 
            pagina.paste(img_copy, (x, y))
            
        # Rodapé das Páginas (À Esquerda)
        d_pagina.text((100, altura - 110), "Conteúdo gerado por:", fill="gray", font=f_rodape)
        if logo_img: 
            pagina.paste(logo_img, (100, altura - 80), logo_img)
            
        paginas_pdf.append(pagina)

    paginas_pdf[0].save(arquivo_saida, save_all=True, append_images=paginas_pdf[1:])
    relatar(f"✅ PDF finalizado com layout profissional!")
    return arquivo_saida
