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

# --- MONTAGEM DO PDF (AJUSTADO: Layout Limpo e Rodapé Centralizado) ---
    relatar(f"Montando PDF Profissional de {titulo_categoria}...")
    
    # Resolução A4 padrão em 150 DPI (aproximadamente)
    largura, altura = 1240, 1754 
    page_center_x = largura / 2
    paginas_pdf = []
    data_geracao = datetime.now().strftime("%d/%m/%Y")
    
    # 🎀 BUSCADOR DE FONTES INTELIGENTE (Puxando DejaVu Sans do Linux)
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

    # 🎀 AJUSTE FINO DE TAMANHOS DE FONTE (Profissional)
    f_tit = obter_fonte(38, negrito=True) # Título principal (Reduzido de 55)
    f_sub = obter_fonte(28)              # Subtítulos (Reduzido de 45)
    f_txt = obter_fonte(20)              # Faixas de preço (Reduzido de 30)
    f_rodape = obter_fonte(16)           # Rodapé (Reduzido de 25)

    # 🎀 AJUSTE DA LOGO (Não precisa ser gigante)
    try:
        logo_img = Image.open("logo.png").convert("RGBA")
        logo_img.thumbnail((150, 60), Image.Resampling.LANCZOS) # Tamanho proporcional
    except Exception:
        logo_img = None

    capa = Image.new('RGB', (largura, altura), 'white')
    draw = ImageDraw.Draw(capa)
    
    # Cabeçalho Centralizado
    draw.text((page_center_x, 150), "Análise de Mercado - Renner Uruguay", fill="black", font=f_tit, anchor="mm")
    draw.text((page_center_x, 230), f"Gênero: {titulo_genero}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 290), f"Categoria: {titulo_categoria}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 400), "Resumo de Faixas de Preço", fill="black", font=f_sub, anchor="mm")

    # 🎀 FAIXAS DE PREÇO AGORA CENTRALIZADAS (horizontalmente)
    y_pos = 480
    precos = [p['preco'] for p in produtos_capturados]
    
    qtd_base = len([p for p in precos if p <= 490])
    draw.text((page_center_x, y_pos), f"Até UYU 490 ........................... {qtd_base} produtos", fill="black", font=f_txt, anchor="mm")
    y_pos += 30 # Passo vertical menor

    for i in range(491, 1991, 100):
        fim = i + 99
        qtd = len([p for p in precos if i <= p <= fim])
        draw.text((page_center_x, y_pos), f"De UYU {i} a UYU {fim} ................. {qtd} produtos", fill="black", font=f_txt, anchor="mm")
        y_pos += 30
    
    qtd_final = len([p for p in precos if p > 1990])
    draw.text((page_center_x, y_pos), f"Acima de UYU 1.990 .................... {qtd_final} produtos", fill="black", font=f_txt, anchor="mm")
    
    # Total centralizado maior
    draw.text((page_center_x, y_pos + 120), f"TOTAL: {len(produtos_capturados)} produtos únicos mapeados", fill="black", font=f_tit, anchor="mm")
    
    # 🎀 NOVA POSIÇÃO E LAYOUT DO RODAPÉ CENTRALIZADO (Página 1)
    
    # 1. Data centralizada mais abaixo
    draw.text((page_center_x, altura - 150), f"Gerado em: {data_geracao}", fill="gray", font=f_txt, anchor="mm")
    
    # 2. "Conteúdo gerado por:" centralizado logo abaixo da data
    draw.text((page_center_x, altura - 100), "Conteúdo gerado por:", fill="gray", font=f_rodape, anchor="mm")
    
    # 3. Logo centralizada logo abaixo do texto de rodapé
    if logo_img:
        logo_w, logo_h = logo_img.size
        # Cálculo para colar a logo centralizada no eixo X
        paste_x = int((largura - logo_w) / 2)
        capa.paste(logo_img, (paste_x, altura - 80), logo_img)

    paginas_pdf.append(capa)

    # Ordenação e Grade de Produtos
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
            
        # 🎀 APLICANDO O MESMO RODAPÉ CENTRALIZADO NAS PÁGINAS DA GRADE
        
        # 1. "Conteúdo gerado por:" centralizado
        d_pagina.text((page_center_x, altura - 100), "Conteúdo gerado por:", fill="gray", font=f_rodape, anchor="mm")
        
        # 2. Logo centralizada abaixo do texto
        if logo_img:
            # Re-calculando apenas para garantir clareza no escopo
            logo_w, logo_h = logo_img.size
            paste_x = int((largura - logo_w) / 2)
            pagina.paste(logo_img, (paste_x, altura - 80), logo_img)
            
        paginas_pdf.append(pagina)

    paginas_pdf[0].save(arquivo_saida, save_all=True, append_images=paginas_pdf[1:])
    relatar(f"✅ PDF finalizado com layout profissional!")
    return arquivo_saida
