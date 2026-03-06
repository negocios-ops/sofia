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
    
    navegador.get(url_alvo)
    relatar("Esperando a página carregar e limpando pop-ups...")
    time.sleep(8)
    
    # Esmagador de Pop-ups (Cookies, Newsletters)
    try:
        navegador.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        navegador.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    except:
        pass

    tentativas_vazias = 0

    # 🎀 ESTRATÉGIA DO ASPIRADOR DE PÓ 2.0 (Sem limite de altura inicial)
    for ciclo in range(1, 40): 
        relatar(f"Aspirando roupas na tela... (Ciclo {ciclo}) - Já temos: {len(produtos_capturados)}")
        
        # 1. Atualiza onde está a barreira proibida
        js_barreira = """
        var elements = document.querySelectorAll('h2, h3, h4, span, div, p');
        for (var i = 0; i < elements.length; i++) {
            var txt = elements[i].textContent || "";
            if (txt.toUpperCase().includes('TE PUEDE INTERESAR') || txt.toUpperCase().includes('VISTO RECIENTEMENTE')) {
                var rect = elements[i].getBoundingClientRect();
                return rect.top + window.scrollY;
            }
        }
        return -1;
        """
        y_barreira = navegador.execute_script(js_barreira)
        
        # 2. Localiza as roupas
        js_finder = """
        var cards = [];
        var images = document.querySelectorAll('img');
        for (var i = 0; i < images.length; i++) {
            var img = images[i];
            
            var pai = img;
            var found = null;
            for (var level = 0; level < 8; level++) {
                pai = pai.parentElement;
                if (!pai) break;
                var txt = pai.textContent || "";
                if (txt.includes('$') || txt.includes('UYU')) {
                    var pRect = pai.getBoundingClientRect();
                    // Verifica se a caixa em volta parece um produto (e não o site inteiro)
                    if (pRect.height > 150 && pRect.height < 1500 && pRect.width > 100 && pRect.width < 900) {
                        found = pai;
                        break;
                    }
                }
            }
            if (found && !cards.includes(found)) {
                cards.push(found);
            }
        }
        return cards;
        """
        elementos_validos = navegador.execute_script(js_finder)
        
        novos_encontrados = 0
        
        # 3. Processa e tira foto
        for item in elementos_validos:
            try:
                # Checa se passou do carrossel proibido
                abs_y = navegador.execute_script("return arguments[0].getBoundingClientRect().top + window.scrollY;", item)
                if y_barreira != -1 and abs_y > y_barreira:
                    continue 
                    
                txt = navegador.execute_script("return arguments[0].textContent;", item)
                
                # Link
                try: link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except: link = str(abs_y)
                
                if not link or link in links_vistos:
                    continue
                    
                # Matemática de extração de preço uruguaio ($ 1.290)
                matches = re.findall(r'(?:\$|UYU)\s*([\d\.,]+)', txt)
                if not matches: continue
                
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
                        if len(clean_str.split('.')[-1]) == 2:
                             pass
                        else:
                             clean_str = clean_str.replace('.', '')
                    try: precos.append(float(clean_str))
                    except: pass
                
                if not precos: continue
                valor_preco = max(precos) # Preço cheio
                
                # Scroll e foto
                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                time.sleep(0.6) # Espera um pouco mais para o lazy load da foto!
                
                print_binario = item.screenshot_as_png
                imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                
                links_vistos.add(link)
                produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                novos_encontrados += 1
            except Exception:
                continue
                
        if novos_encontrados > 0:
            tentativas_vazias = 0
        else:
            tentativas_vazias += 1
            
        # 4. Força scroll e procura botão
        for _ in range(5):
            navegador.execute_script("window.scrollBy(0, 700);")
            time.sleep(0.5)
            
        js_click = """
        var elements = document.querySelectorAll('button, a, span, div');
        for (var i = 0; i < elements.length; i++) {
            var txt = elements[i].textContent || "";
            if (txt.toUpperCase().includes('CARGAR') || txt.toUpperCase().includes('VER MÁS')) {
                var rect = elements[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    elements[i].click();
                    return true;
                }
            }
        }
        return false;
        """
        clicou = navegador.execute_script(js_click)
        if clicou:
            relatar("Botão 'Cargar Más' ativado! Puxando nova leva...")
            time.sleep(5)
            tentativas_vazias = 0 
            
        # Parada de Segurança: 3 ciclos inteiros sem roupa e sem botão
        if tentativas_vazias >= 3:
            relatar("Nenhuma roupa nova ou botão encontrados recentemente. Fim da categoria!")
            break
            
    if not produtos_capturados: 
        relatar("❌ Nenhum produto capturado validamente. A estrutura do site pode estar bloqueando a visão.")
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
