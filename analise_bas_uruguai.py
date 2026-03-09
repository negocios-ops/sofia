import io
import time
import re
import os
import json
import requests
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

# Função detetive para achar qualquer preço escondido no pacote de dados
def encontrar_precos_no_json(obj):
    precos = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            # Procura chaves que tenham "price" no nome (ListPrice, Price, etc)
            if 'price' in k.lower() and isinstance(v, (int, float)) and v > 0:
                precos.append(float(v))
            elif isinstance(v, (dict, list)):
                precos.extend(encontrar_precos_no_json(v))
    elif isinstance(obj, list):
        for item in obj:
            precos.extend(encontrar_precos_no_json(item))
    return precos

def extrair_produtos_bas(navegador, url_alvo, arquivo_saida, titulo_genero, titulo_categoria, log_callback=None):
    
    def relatar(mensagem):
        print(mensagem)
        if log_callback:
            log_callback(mensagem)

    relatar(f"Iniciando captura de {titulo_categoria} (Bas Uruguai) via Modo Hacker (__NEXT_DATA__)...")
    produtos_capturados = []
    links_vistos = set()
    
    tem_paginacao = "page=" in url_alvo

    # 🎀 HACK DA URL + EXTRAÇÃO DIRETA DO CÓDIGO FONTE
    for pagina_atual in range(0, 15):
        if tem_paginacao:
            url_pagina = re.sub(r'page=\d+', f'page={pagina_atual}', url_alvo)
        else:
            separador = "&" if "?" in url_alvo else "?"
            url_pagina = f"{url_alvo}{separador}page={pagina_atual}"
            
        relatar(f"🌐 Acessando Página {pagina_atual} e interceptando dados...")
        navegador.get(url_pagina)
        time.sleep(4) # Não precisamos mais esperar a tela desenhar toda, só o script carregar!
        
        try:
            # 1. Encontra o Santo Graal que você descobriu na foto
            script_tag = navegador.find_element(By.ID, "__NEXT_DATA__")
            json_texto = script_tag.get_attribute('innerHTML')
            dados_site = json.loads(json_texto)
            
            # 2. Navega pelas pastas de dados (conforme sua foto)
            produtos_json = []
            try:
                # O caminho exato baseado no seu print!
                arestas = dados_site['props']['pageProps']['data']['collection']['products']['edges']
                for aresta in arestas:
                    produtos_json.append(aresta['node'])
            except KeyError:
                relatar("Aviso: Estrutura de dados diferente nesta página, tentando busca geral.")
                pass
                
            produtos_nesta_pagina = 0
            
            # 3. Processa cada produto encontrado no pacote de dados
            for prod in produtos_json:
                try:
                    # Pega a URL da Imagem
                    img_url = None
                    if 'image' in prod and len(prod['image']) > 0:
                        img_url = prod['image'][0].get('url')
                        
                    if not img_url or img_url in links_vistos:
                        continue
                        
                    # Extrai TODOS os preços desse produto e pega o maior (Preço Original)
                    todos_os_precos = encontrar_precos_no_json(prod)
                    if not todos_os_precos:
                        continue
                        
                    valor_preco = max(todos_os_precos)
                    
                    # 4. Baixa a imagem perfeitamente via servidor, sem depender da tela
                    resposta_img = requests.get(img_url, timeout=10)
                    if resposta_img.status_size != 200:
                        imagem = Image.open(io.BytesIO(resposta_img.content)).convert('RGB')
                        
                        # Filtro de segurança
                        if imagem.size[1] < 100: continue
                        
                        imagem.thumbnail((300, 420), Image.Resampling.LANCZOS)
                        
                        links_vistos.add(img_url)
                        produtos_capturados.append({'imagem': imagem, 'preco': valor_preco})
                        produtos_nesta_pagina += 1
                        
                except Exception as e:
                    continue
                    
            relatar(f"✅ {produtos_nesta_pagina} produtos interceptados na página {pagina_atual}. Total: {len(produtos_capturados)}")
            
            # Se o pacote de dados vier vazio de produtos novos, acabou o catálogo!
            if produtos_nesta_pagina == 0:
                relatar("Pacote de dados vazio. Fim do catálogo confirmado!")
                break
                
        except Exception as e:
            relatar("Não foi possível ler os dados ocultos desta página. Encerrando busca.")
            break
            
    if not produtos_capturados: 
        relatar("❌ Nenhum produto interceptado com sucesso.")
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
