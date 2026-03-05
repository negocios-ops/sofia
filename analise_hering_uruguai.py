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
    
    # 🟢 ESSENCIAIS PARA A NUVEM (Evita que o Chrome trave ou falhe)
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 🟢 O TRUQUE CAMALEÃO: Descobre se está no Mac ou na Nuvem
    if os.path.exists('/usr/bin/chromedriver'):
        # Se achar esse arquivo, a Sofia sabe que está no servidor do Streamlit
        servico = Service('/usr/bin/chromedriver')
    else:
        # Se não achar, a Sofia sabe que está no seu Mac
        servico = Service(ChromeDriverManager().install())
        
    return webdriver.Chrome(service=servico, options=opcoes)

def extrair_produtos_para_pdf(navegador, url, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):
    
    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Acessando URL de {titulo_categoria}...")
    navegador.get(url)
    time.sleep(4) 
    
    relatar(f"Rolando a página para carregar as imagens...")
    for passo in range(20):
        navegador.execute_script("window.scrollBy(0, 700);")
        time.sleep(1)
        
    elementos_encontrados = navegador.find_elements(By.XPATH, "//a[.//img]")
    produtos_capturados = []
    
    relatar(f"Lendo preços e capturando imagens...")
    for i, elemento in enumerate(elementos_encontrados):
        try:
            tamanho = elemento.size
            if tamanho['height'] < 150 or tamanho['width'] < 150:
                continue
            
            elemento_alvo = elemento
            valor_preco = float('inf')
            
            for nivel in range(5):
                try:
                    pai = elemento_alvo.find_element(By.XPATH, "..")
                    texto_visivel = pai.text
                    if "$" in texto_visivel or "UYU" in texto_visivel:
                        elemento_alvo = pai
                        matches = re.findall(r'(?:\$|UYU)\s*([\d\.]+)', texto_visivel)
                        if matches:
                            precos_encontrados = [float(m.replace('.', '')) for m in matches]
                            valor_preco = max(precos_encontrados)
                        break
                except Exception: pass
                
            navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_alvo)
            time.sleep(0.5)
            
            imagem = Image.open(io.BytesIO(elemento_alvo.screenshot_as_png))
            if imagem.mode != 'RGB': imagem = imagem.convert('RGB')
                
            produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
        except Exception: pass
            
    if not produtos_capturados:
        relatar(f"❌ Nenhum produto válido capturado para {titulo_categoria}.")
        return

    produtos_ordenados = sorted(produtos_capturados, key=lambda p: p['preco'])
    imagens_ordenadas = [p['imagem'] for p in produtos_ordenados]

    relatar(f"Analisando {len(produtos_capturados)} produtos e montando o PDF...")
    
# --- MONTAGEM DO PDF (AJUSTADO: Layout Limpo e Rodapé Centralizado) ---
    faixas = [(0, 490, "Até $ 490")]
    for limite in range(490, 1990, 100):
        faixas.append((limite + 0.01, limite + 100, f"De $ {limite + 1} a $ {limite + 100}"))
    faixas.append((1990.01, float('inf'), "Acima de $ 1.990"))

    contagem_precos = {f[2]: 0 for f in faixas}
    total_validos = 0
    
    for p in produtos_ordenados:
        if p['preco'] != float('inf'):
            for min_p, max_p, label in faixas:
                if min_p <= p['preco'] <= max_p:
                    contagem_precos[label] += 1
                    total_validos += 1
                    break

    # Padrão A4
    largura_pagina, altura_pagina = 1240, 1754 
    page_center_x = largura_pagina / 2
    margem = 50
    largura_max_img = (largura_pagina - 3 * margem) // 2
    altura_max_img = (altura_pagina - 3 * margem) // 2
    paginas_pdf = []
    
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
    fonte_titulo = obter_fonte(24, negrito=True) 
    fonte_sub = obter_fonte(18)              
    fonte_titulo_tab = obter_fonte(24, negrito=True)
    fonte_tabela = obter_fonte(16)              
    fonte_data = obter_fonte(12)
    fonte_rodape = obter_fonte(10)           

    # 🎀 AJUSTE DA LOGO
    try:
        logo_img = Image.open("logo.png").convert("RGBA")
        logo_img.thumbnail((150, 60), Image.Resampling.LANCZOS)
    except Exception:
        logo_img = None

    capa = Image.new('RGB', (largura_pagina, altura_pagina), 'white')
    draw = ImageDraw.Draw(capa)
    
    # Cabeçalho Centralizado
    draw.text((page_center_x, 150), "Análise de Mercado - Hering", fill="black", font=fonte_titulo, anchor="mm")
    draw.text((page_center_x, 230), f"Gênero: {titulo_genero}", fill="dimgray", font=fonte_sub, anchor="mm")
    draw.text((page_center_x, 290), f"Categoria: {titulo_categoria}", fill="dimgray", font=fonte_sub, anchor="mm")
    
    y_tabela = 400
    draw.text((page_center_x, y_tabela), "Resumo de Faixas de Preço", fill="black", font=fonte_titulo_tab, anchor="mm")
    y_tabela += 60
    
    # 🎀 FAIXAS DE PREÇO CENTRALIZADAS
    for label, count in contagem_precos.items():
        palavra = "produtos" if count != 1 else "produto"
        texto_linha = f"{label} ........................ {count} {palavra}"
        draw.text((page_center_x, y_tabela), texto_linha, fill="#404040", font=fonte_tabela, anchor="mm")
        y_tabela += 30
        
    y_tabela += 40
    draw.text((page_center_x, y_tabela), f"TOTAL: {total_validos} produtos mapeados", fill="black", font=fonte_titulo_tab, anchor="mm")
    
    # 🎀 RODAPÉ CENTRALIZADO (Capa)
    data_hoje_capa = datetime.now().strftime("%d/%m/%Y")
    draw.text((page_center_x, altura_pagina - 150), f"Gerado em: {data_hoje_capa}", fill="gray", font=fonte_data, anchor="mm")
    draw.text((100, altura - 110), "Conteúdo gerado por:", fill="gray", font=f_rodape)
    
     if logo_img:
            # 100 é a distância da margem esquerda. Pode diminuir para 50 se quiser mais colado na borda!
            capa.paste(logo_img, (100, altura - 80), logo_img)
    
    paginas_pdf.append(capa)
    
    # Produtos - Grade
    for i in range(0, len(imagens_ordenadas), 4):
        lote = imagens_ordenadas[i:i+4]
        pagina = Image.new('RGB', (largura_pagina, altura_pagina), 'white')
        draw_pagina = ImageDraw.Draw(pagina)
        
        for j, img in enumerate(lote):
            img.thumbnail((largura_max_img, altura_max_img), Image.Resampling.LANCZOS)
            linha, coluna = j // 2, j % 2
            pos_x = margem + coluna * (largura_max_img + margem)
            pos_y = margem + linha * (altura_max_img + margem)
            pagina.paste(img, (pos_x, pos_y))
            
        # 🎀 RODAPÉ CENTRALIZADO (Páginas de Produtos)
        draw_pagina.text((page_center_x, altura_pagina - 100), "Conteúdo gerado por:", fill="gray", font=fonte_rodape, anchor="mm")
     if logo_img:
            # 100 é a distância da margem esquerda. Pode diminuir para 50 se quiser mais colado na borda!
            capa.paste(logo_img, (100, altura - 80), logo_img)
            
        paginas_pdf.append(pagina)
        
    if paginas_pdf:
        paginas_pdf[0].save(arquivo_saida, save_all=True, append_images=paginas_pdf[1:])
        relatar(f"✅ PDF finalizado com layout profissional!")
        return arquivo_saida
