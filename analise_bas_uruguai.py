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

    # 🎀 HACK DA URL COMBINADO COM EXTRAÇÃO EM TEMPO REAL
    for pagina_atual in range(0, 15):
        if tem_paginacao:
            url_pagina = re.sub(r'page=\d+', f'page={pagina_atual}', url_alvo)
        else:
            separador = "&" if "?" in url_alvo else "?"
            url_pagina = f"{url_alvo}{separador}page={pagina_atual}"
            
        relatar(f"🌐 Acessando Página {pagina_atual} diretamente...")
        navegador.get(url_pagina)
        time.sleep(8)
        
        try:
            navegador.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except: pass
        
        produtos_nesta_pagina = 0
        relatar(f"Sugando produtos da página {pagina_atual} passo a passo...")
        
        # Desce a página em 20 "degraus", escaneando e fotografando em cada parada
        for passo in range(25): 
            
            # Pega a barreira para não pegar produtos recomendados
            y_barreira = navegador.execute_script("""
                var elements = document.querySelectorAll('h2, h3, h4, span, div, p');
                for (var i = 0; i < elements.length; i++) {
                    var txt = elements[i].textContent || "";
                    if (txt.toUpperCase().includes('TE PUEDE INTERESAR') || txt.toUpperCase().includes('VISTO RECIENTEMENTE')) {
                        return elements[i].getBoundingClientRect().top + window.scrollY;
                    }
                }
                return -1;
            """)

            elementos_a = navegador.find_elements(By.TAG_NAME, "a")
            
            for a in elementos_a:
                try:
                    href = a.get_attribute("href")
                    if not href or href in links_vistos: continue
                    
                    imgs = a.find_elements(By.TAG_NAME, "img")
                    if not imgs: continue
                    
                    # Checa o preço (sobe na árvore até 3 vezes)
                    container = a
                    txt = container.text
                    for _ in range(3):
                        if "$" in txt or "UYU" in txt: break
                        container = container.find_element(By.XPATH, "..")
                        txt = container.text
                        
                    matches = re.findall(r'(?:\$|UYU)\s*([\d\.,]+)', txt)
                    if not matches: continue
                    
                    # Evita o carrossel de rodapé
                    abs_y = navegador.execute_script("return arguments[0].getBoundingClientRect().top + window.scrollY;", container)
                    if y_barreira != -1 and abs_y > y_barreira - 50:
                        continue
                    
                    # Lógica Intacta do Preço Uruguaio (Preço Original Máximo)
                    precos = []
                    for m in matches:
                        clean_str = m.replace(' ', '')
                        if ',' in clean_str and '.' in clean_str:
                            if clean_str.rfind(',') > clean_str.rfind('.'): clean_str = clean_str.replace('.', '').replace(',', '.')
                            else: clean_str = clean_str.replace(',', '')
                        elif ',' in clean_str:
                            if len(clean_str.split(',')[-1]) == 2: clean_str = clean_str.replace(',', '.')
                            else: clean_str = clean_str.replace(',', '')
                        elif '.' in clean_str:
                            if len(clean_str.split('.')[-1]) == 2: pass
                            else: clean_str = clean_str.replace('.', '')
                        try: precos.append(float(clean_str))
                        except: pass
                    
                    if not precos: continue
                    valor_preco = max(precos)
                    
                    # Bate a foto agora, antes que o site apague a roupa!
                    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
                    time.sleep(0.5) 
                    
                    print_binario = container.screenshot_as_png
                    imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                    
                    if imagem.size[1] < 150: continue # Ignora ícones pequenos
                    
                    imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                    
                    links_vistos.add(href)
                    produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                    produtos_nesta_pagina += 1
                except Exception:
                    continue
                    
            # Após sugar tudo na visão atual, desce um degrau!
            navegador.execute_script("window.scrollBy(0, 600);")
            time.sleep(0.5)
            
        relatar(f"✅ {produtos_nesta_pagina} produtos encontrados e salvos da página {pagina_atual}. Total: {len(produtos_capturados)}")
        
        # Se a página voltar completamente vazia, significa que o estoque do site acabou
        if produtos_nesta_pagina == 0:
            relatar("Fim do catálogo confirmado! (Página vazia)")
            break
            
    if not produtos_capturados: 
        relatar("❌ Nenhum produto capturado validamente.")
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
