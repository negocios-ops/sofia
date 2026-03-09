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
    
    relatar("Abrindo site e iniciando o Rolo Compressor...")
    navegador.get(url_alvo)
    time.sleep(8)
    
    # Esmaga pop-ups iniciais
    try:
        navegador.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
    except:
        pass

    tentativas_vazias = 0
    
    # 🎀 ROLO COMPRESSOR: Desce a tela passo a passo e aspira tudo na hora!
    for passo in range(250): # Um limite enorme para nunca parar no meio
        
        # 1. Checa a barreira do rodapé
        limite_y = float('inf')
        try:
            js_barreira = """
            var elements = document.querySelectorAll('h2, h3, h4, span, div, p');
            for (var i = 0; i < elements.length; i++) {
                var txt = elements[i].textContent || "";
                if (txt.toUpperCase().includes('TE PUEDE INTERESAR') || txt.toUpperCase().includes('VISTO RECIENTEMENTE')) {
                    return elements[i].getBoundingClientRect().top + window.scrollY;
                }
            }
            return -1;
            """
            y_barreira = navegador.execute_script(js_barreira)
            if y_barreira != -1: limite_y = y_barreira
        except:
            pass

        # 2. Localiza todos os elementos que misturam Foto + Dinheiro ($ ou UYU)
        candidatos = navegador.find_elements(By.XPATH, "//*[.//img and (contains(., '$') or contains(., 'UYU'))]")
        
        novos_neste_passo = 0
        
        for card in candidatos:
            try:
                h = card.size['height']
                w = card.size['width']
                
                # O filtro mágico: Isola perfeitamente a "caixinha" do produto ignorando o resto do site
                if 250 < h < 1100 and 120 < w < 600:
                    y_pos = card.location['y']
                    
                    # Se for recomendação do rodapé, ignora
                    if y_pos > limite_y:
                        continue
                        
                    # Pega o link para evitar roupas duplicadas
                    try: link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    except: link = str(y_pos)
                    
                    if not link or link in links_vistos:
                        continue
                        
                    texto = card.text
                    matches = re.findall(r'(?:\$|UYU)\s*([\d\.,]+)', texto)
                    if not matches:
                        continue
                        
                    # 3. Matemática do Preço (Intacta)
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
                            if len(clean_str.split('.')[-1]) == 2: pass
                            else: clean_str = clean_str.replace('.', '')
                        try: precos.append(float(clean_str))
                        except: pass
                        
                    if not precos:
                        continue
                        
                    valor_preco = max(precos) # Preço cheio original
                    
                    # Tira a foto imediatamente antes que o site a apague!
                    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                    time.sleep(0.3)
                    
                    print_binario = card.screenshot_as_png
                    imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                    imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                    
                    links_vistos.add(link)
                    produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                    novos_neste_passo += 1
            except:
                continue
                
        if novos_neste_passo > 0:
            tentativas_vazias = 0
            relatar(f"[{passo}] Aspirou +{novos_neste_passo} roupas. Total na mochila: {len(produtos_capturados)}")
        else:
            tentativas_vazias += 1
            
        # 4. Desce a tela como um humano lendo (500 pixels por vez)
        navegador.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.4)
        
        # 5. Se o botão aparecer, o rolo compressor esmaga ele na hora!
        js_click = """
        var elements = document.querySelectorAll('button, a, span, div');
        var clicou = false;
        for (var i = 0; i < elements.length; i++) {
            var txt = elements[i].textContent || "";
            if (txt.toUpperCase().includes('CARGAR MÁS') || txt.toUpperCase().includes('CARGAR MAS')) {
                var rect = elements[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    elements[i].click();
                    clicou = true;
                }
            }
        }
        return clicou;
        """
        if navegador.execute_script(js_click):
            relatar("Botão 'Cargar Más' esmagado! Abrindo mais catálogo...")
            time.sleep(3)
            tentativas_vazias = 0
            
        # Freio de emergência: se der 15 passos seguidos sem ver roupa nem botão, a loja acabou
        if tentativas_vazias > 15:
            relatar("Fim do catálogo confirmado. Vamos ao PDF!")
            break
            
    if not produtos_capturados: 
        relatar("❌ Nenhum produto encontrado. A página pode estar fora do ar.")
        return None

    relatar(f"Montando PDF Profissional de {titulo_categoria} com {len(produtos_capturados)} itens...")
    
    # --- MONTAGEM DO PDF ---
    largura, altura = 1240, 1754 
    page_center_x = largura / 2
    paginas_pdf = []
    data_geracao = datetime.now().strftime("%d/%m/%Y")
    
    def obter_fonte(tamanho, negrito=False):
        caminhos = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]
        for c in caminhos:
            try: return ImageFont.truetype(c, tamanho)
            except: pass
        return ImageFont.load_default()

    f_tit, f_sub, f_txt, f_rodape = obter_fonte(38, True), obter_fonte(28), obter_fonte(20), obter_fonte(16)

    try:
        logo_img = Image.open("logo.png").convert("RGBA")
        logo_img.thumbnail((250, 100), Image.Resampling.LANCZOS)
    except Exception:
        logo_img = None

    capa = Image.new('RGB', (largura, altura), 'white')
    draw = ImageDraw.Draw(capa)
    
    draw.text((page_center_x, 150), "Análise de Mercado - Bas Uruguai", fill="black", font=f_tit, anchor="mm")
    draw.text((page_center_x, 230), f"Gênero: {titulo_genero}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 290), f"Categoria: {titulo_categoria}", fill="gray", font=f_sub, anchor="mm")
    draw.text((page_center_x, 400), "Resumo de Faixas de Preço", fill="black", font=f_sub, anchor="mm")

    faixas = [(0, 99.99, "Até $ 99")]
    for limite in range(100, 3000, 100):
        faixas.append((limite, limite + 99.99, f"De $ {limite} a $ {limite + 99}"))
    faixas.append((3000.00, float('inf'), "Acima de $ 3000"))
    
    contagem_precos = {f[2]: 0 for f in faixas}
    
    for p in produtos_capturados:
        for min_p, max_p, label in faixas:
            if min_p <= p['preco'] <= max_p:
                contagem_precos[label] += 1
                break

    y_pos = 480
    for label, count in contagem_precos.items():
        if count > 0:
            palavra = "produtos" if count != 1 else "produto"
            draw.text((page_center_x, y_pos), f"{label} ........................ {count} {palavra}", fill="black", font=f_txt, anchor="mm")
            y_pos += 30
    
    draw.text((page_center_x, y_pos + 120), f"TOTAL: {len(produtos_capturados)} produtos únicos mapeados", fill="black", font=f_tit, anchor="mm")
    
    draw.text((page_center_x, altura - 150), f"Gerado em: {data_geracao}", fill="gray", font=f_txt, anchor="mm")
    if logo_img:
        capa.paste(logo_img, (100, altura - logo_img.size[1] - 50), logo_img)

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
            d_prod.text((10, 5), f"$ {prod['preco']:.0f}", fill="white", font=f_txt)
            x, y = 20 + ((j % 3) * 400), 30 + ((j // 3) * 560) 
            pagina.paste(img_copy, (x, y))
            
        if logo_img: 
            pagina.paste(logo_img, (100, altura - logo_img.size[1] - 50), logo_img)
            
        paginas_pdf.append(pagina)

    paginas_pdf[0].save(arquivo_saida, save_all=True, append_images=paginas_pdf[1:])
    relatar(f"✅ PDF finalizado com layout profissional!")
    return arquivo_saida
