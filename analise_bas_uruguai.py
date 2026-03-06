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

def extrair_produtos_bas(navegador, url_alvo, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):
    
    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Iniciando captura de {titulo_categoria} (Bas Uruguai)...")
    produtos_capturados = []
    links_vistos = set()
    
    navegador.get(url_alvo)
    time.sleep(6)
    
    # 🎀 PASSEIO LENTO (LAZY-LOAD) E CLIQUE AUTOMÁTICO
    for i in range(1, 16):
        relatar(f"Descendo a página suavemente para revelar fotos ocultas (Ciclo {i})...")
        
        # Rolagem em "degraus" para forçar as imagens a carregarem
        for _ in range(12):
            navegador.execute_script("window.scrollBy(0, 700);")
            time.sleep(0.5)
            
        js_click = """
        var botoes = document.querySelectorAll('button, a, div, span');
        for (var b = 0; b < botoes.length; b++) {
            var txt = botoes[b].innerText ? botoes[b].innerText.toUpperCase() : '';
            if (txt.includes('CARGAR') || txt.includes('VER MÁS')) {
                botoes[b].click();
                return true;
            }
        }
        return false;
        """
        clicou = navegador.execute_script(js_click)
        
        if clicou:
            relatar(f"Botão 'Cargar Más' ativado! Aguardando o catálogo expandir...")
            time.sleep(4)
        else:
            relatar("Fim do catálogo alcançado! Nenhuma página extra.")
            break
            
    # Volta para o topo rápido para começar as fotos
    navegador.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    # 🎀 BARREIRA DO "TE PUEDE INTERESAR"
    limite_y = float('inf')
    try:
        js_limite = """
        var elementos = document.querySelectorAll('h2, h3, div, span, p');
        for (var i = 0; i < elementos.length; i++) {
            if (elementos[i].innerText && elementos[i].innerText.toUpperCase().includes('TE PUEDE INTERESAR')) {
                return elementos[i].getBoundingClientRect().top + window.scrollY;
            }
        }
        return -1;
        """
        y_encontrado = navegador.execute_script(js_limite)
        if y_encontrado != -1:
            limite_y = y_encontrado
            relatar("🛡️ Barreira 'TE PUEDE INTERESAR' ativada! Ignorando carrossel extra.")
    except Exception:
        pass

    # 🎀 RADAR 3.0: Encontrando a caixa inteira do produto
    relatar("Escaneando e fotografando produtos visíveis...")
    imagens = navegador.find_elements(By.TAG_NAME, "img")
    elementos_validos = []
    
    for img in imagens:
        try:
            # Pula logos e ícones pequenos (Se for invisível, agora já tem tamanho por causa do scroll suave)
            if img.size['height'] < 100 or img.size['width'] < 100:
                continue
                
            # Olha para a foto e sobe até achar a "Caixa Mestre" que tem o símbolo do dinheiro
            card = img.find_element(By.XPATH, "./ancestor::*[contains(., '$') or contains(., 'UYU')][1]")
            
            # Filtro de segurança para não pegar o site inteiro
            if card.size['height'] < 1200 and card.size['width'] < 800:
                if card not in elementos_validos:
                    elementos_validos.append(card)
        except Exception:
            continue
            
    for item in elementos_validos:
        try:
            item_y = item.location['y']
            if item_y > limite_y: # Se a roupa passou da barreira proibida, descarta!
                continue
                
            try:
                # Tenta pegar o link do produto
                link_produto = item.find_element(By.XPATH, ".//a").get_attribute("href")
            except:
                link_produto = item.get_attribute("href") if item.tag_name == "a" else str(item.location)
                
            if not link_produto or link_produto in links_vistos:
                continue
                
            texto_item = item.get_attribute("innerText")
            if not texto_item:
                continue
                
            # 🎀 INTELIGÊNCIA DE PREÇO: Ex: "$ 559, $ 799, OCA $ 447"
            matches = re.findall(r'(?:\$|UYU)\s*([\d\.,]+)', texto_item)
            if matches:
                precos_convertidos = []
                for m in matches:
                    valor_str = m.replace('.', '').replace(',', '') if m.count('.') > 1 or ('.' in m and ',' in m) else m.replace(',', '.')
                    try:
                        precos_convertidos.append(float(valor_str))
                    except:
                        pass
                
                if not precos_convertidos:
                    continue
                    
                # A Mágica: Ele extrai todos os números que têm $ e pega SEMPRE O MAIOR (O Preço Original Riscado)
                valor_preco = max(precos_convertidos)
                
                links_vistos.add(link_produto)
                
                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                time.sleep(0.4)
                
                print_binario = item.screenshot_as_png
                imagem = Image.open(io.BytesIO(print_binario)).convert('RGB')
                imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                
                produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
        except Exception:
            continue
            
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

    faixas = [(0, 499.99, "Até $ 499")]
    for limite in range(500, 3000, 500):
        faixas.append((limite, limite + 499.99, f"De $ {limite} a $ {limite + 499}"))
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
