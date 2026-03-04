import streamlit as st
import time
import os
import zipfile

# --- IMPORTANDO OS SEUS ROBÔS DE VERDADE ---
# O site vai "puxar" as funções de dentro dos seus scripts
try:
    import analise_renner_uruguai as renner
    import analise_hering_uruguai as hering
except ImportError:
    st.warning("⚠️ Arquivos dos robôs não encontrados na mesma pasta. O site rodará em modo simulação.")

st.set_page_config(page_title="Sofia - Dashboard", page_icon="🎀", layout="centered")

# --- DICIONÁRIO DE URLs DA BIA ---
urls_renner = {
    "Masculino": {
        "Bermudas": "https://www.renner.com/uy/c/masculino/bermudas-y-shorts/cat360002uy",
        "Blusoes": "https://www.renner.com/uy/c/masculino/buzos-y-sueters/buzos/cat360039uy",
        "Camisas": "https://www.renner.com/uy/c/masculino/camisas/cat360007uy",
        "Casacos": "https://www.renner.com/uy/c/masculino/chaquetas/cat360009uy",
        "Calcas": "https://www.renner.com/uy/c/masculino/pantalones/cat360006uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-masc/lst00000045",
        "Pijamas": "https://www.renner.com/uy/c/masculino/pijamas-y-robes/cat360017uy",
        "Polos": "https://www.renner.com/uy/c/masculino/polos/cat360018uy",
        "Camisetas": "https://www.renner.com/uy/c/masculino/remeras/cat360008uy"
    },
    "Feminino": {
        "Vestidos": "https://www.renner.com/uy/c/femenino/vestidos/cat200002uy",
        "Bermudas": "https://www.renner.com/uy/c/femenino/bermudas-y-shorts/cat210004uy",
        "Blusas": "https://www.renner.com/uy/c/femenino/blusas-y-remera/cat210006uy",
        "Calcass": "https://www.renner.com/uy/c/femenino/pantalones/cat210010uy",
        "Casacos": "https://www.renner.com/uy/c/femenino/chaquetas/cat210012uy",
        "Blusoes": "https://www.renner.com/uy/c/femenino/buzos-y-sueters/buzos/cat290050uy",
        "Camisas": "https://www.renner.com/uy/c/femenino/camisas/cat210011uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-fem/lst00000044",
        "Moda Praia": "https://www.renner.com/uy/c/femenino/moda-playa/cat210018uy",
        "Pijamas": "https://www.renner.com/uy/c/femenino/pijamas/cat210019uy"
    },
    "Menina": {
        "Bermudas": "https://www.renner.com/uy/c/infantil/bermudas-y-shorts/cat350002uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350002uy",
        "Blusas": "https://www.renner.com/uy/c/infantil/blusas/cat350003uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350003uy",
        "Bodies": "https://www.renner.com/uy/c/infantil/bodies/cat350005uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Agenre%3AFemenino%3Acategory%3Acat350005uy",
        "Blusoes": "https://www.renner.com/uy/c/infantil/buzos-y-sueters/cat350004uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350004uy",
        "Casacos": "https://www.renner.com/uy/c/infantil/chaquetas-y-sacos/cat350010uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350010uy",
        "Conjuntos": "https://www.renner.com/uy/c/infantil/conjuntos/cat350012uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350012uy",
        "Macacoes": "https://www.renner.com/uy/c/infantil/enteritos-y-jardineros/cat350016uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350016uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-inf/lst00000046?sort=relevance&filters=%3Arelevance%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3AlistCategory%3Alst00000046",
        "Calcas": "https://www.renner.com/uy/c/infantil/pantalones/cat350007uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AFemenino%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350007uy",
        "Saias": "https://www.renner.com/uy/c/infantil/polleras/cat350021uy",
        "Vestidos": "https://www.renner.com/uy/c/infantil/vestidos/cat350022uy"
    },
    "Menino": {
        "Bermudas": "https://www.renner.com/uy/c/infantil/bermudas-y-shorts/cat350002uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350002uy",
        "Blusas": "https://www.renner.com/uy/c/infantil/blusas/cat350003uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350003uy",
        "Bodies": "https://www.renner.com/uy/c/infantil/bodies/cat350005uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AMasculino%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350005uy",
        "Blusoes": "https://www.renner.com/uy/c/infantil/buzos-y-sueters/cat350004uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350004uy",
        "Casacos": "https://www.renner.com/uy/c/infantil/chaquetas-y-sacos/cat350010uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AMasculino%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350010uy",
        "Conjuntos": "https://www.renner.com/uy/c/infantil/conjuntos/cat350012uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350012uy",
        "Macacoes": "https://www.renner.com/uy/c/infantil/enteritos-y-jardineros/cat350016uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350016uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-inf/lst00000046?sort=relevance&filters=%3Arelevance%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3AlistCategory%3Alst00000046",
        "Calcas": "https://www.renner.com/uy/c/infantil/pantalones/cat350007uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350007uy"
    }
}

urls_hering = {
    "Masculino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/bermudas",
        "Blusoes": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/campera",
        "Regatas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/musculosas",
        "Calcas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/pijamas",
        "Polos": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/polo",
        "Jeans": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/jeans"
    },
    "Feminino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/bermudas",
        "Blusas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/blusas",
        "Blusoes": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/campera",
        "Regatas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/musculosas",
        "Calcas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/pijamas",
        "Shorts": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/shorts",
        "Vestidos": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/vestido",
        "Tops": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/top",
        "Jeans": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/jeans"
    },
    "Menina": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/bermudas",
        "Blusas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/blusas",
        "Blusoes": "https://www.hering.com.uy/indumentaria-nina/indumentaria/buzos",
        "Camisetas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/campera",
        "Conjuntos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/conjunto",
        "Regatas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/musculosas",
        "Calcas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/pijamas",
        "Shorts": "https://www.hering.com.uy/indumentaria-nina/indumentaria/shorts",
        "Vestidos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/vestido",
        "Jeans": "https://www.hering.com.uy/indumentaria-nina/indumentaria/jeans"
    },
    "Menino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/bermudas",
        "Blusoes": "https://www.hering.com.uy/indumentaria-nino/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/campera",
        "Conjuntos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/conjunto",
        "Regatas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/musculosas",
        "Calcas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/pijamas",
        "Polos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/polo",
        "Shorts": "https://www.hering.com.uy/indumentaria-nino/indumentaria/shorts",
        "Jeans": "https://www.hering.com.uy/indumentaria-nino/indumentaria/jeans"
    }
}

master_urls = {"Renner": urls_renner, "Hering": urls_hering}

# O cérebro dinâmico puxa os dados automaticamente do seu dicionário
opcoes_catalogo = {
    "🇺🇾 Uruguai": {
        marca: {genero: list(categorias.keys()) for genero, categorias in dados_marca.items()}
        for marca, dados_marca in master_urls.items()
    }
}

# --- CABEÇALHO DO SITE ---
st.title("🎀 Sofia: Inteligência de Mercado")
st.write("Selecione os filtros abaixo para gerar os PDFs atualizados.")
st.divider()

col1, col2 = st.columns(2)

with col1:
    lista_paises = list(opcoes_catalogo.keys())
    pais_selecionado = st.selectbox("🌍 Selecione o País", lista_paises)
    
    lista_marcas = list(opcoes_catalogo[pais_selecionado].keys())
    marca_selecionada = st.selectbox("🏷️ Selecione a Marca", lista_marcas)

with col2:
    lista_generos_base = list(opcoes_catalogo[pais_selecionado][marca_selecionada].keys())
    lista_generos = ["Todos os Gêneros"] + lista_generos_base
    genero_selecionado = st.selectbox("🚻 Selecione o Gênero", lista_generos)
    
    if genero_selecionado == "Todos os Gêneros":
        categorias_unicas = []
        for gen in lista_generos_base:
            for cat in opcoes_catalogo[pais_selecionado][marca_selecionada][gen]:
                if cat not in categorias_unicas:
                    categorias_unicas.append(cat)
        lista_categorias = ["Todas as Categorias"] + sorted(categorias_unicas)
    else:
        lista_categorias_base = sorted(opcoes_catalogo[pais_selecionado][marca_selecionada][genero_selecionado])
        lista_categorias = ["Todas as Categorias"] + lista_categorias_base
        
    categoria_selecionada = st.selectbox("👗 Selecione a Categoria", lista_categorias)

st.divider()

# --- BOTÃO DE AÇÃO (LIGADO AO ROBÔ REAL) ---
if st.button("⏩️ Iniciar Robô Sofia", use_container_width=True):
    
    tarefas = []
    
    if genero_selecionado == "Todos os Gêneros":
        for gen in lista_generos_base:
            if categoria_selecionada == "Todas as Categorias":
                for cat in opcoes_catalogo[pais_selecionado][marca_selecionada][gen]:
                    tarefas.append((gen, cat))
            else:
                if categoria_selecionada in opcoes_catalogo[pais_selecionado][marca_selecionada][gen]:
                    tarefas.append((gen, categoria_selecionada))
    else:
        if categoria_selecionada == "Todas as Categorias":
            for cat in opcoes_catalogo[pais_selecionado][marca_selecionada][genero_selecionado]:
                tarefas.append((genero_selecionado, cat))
        else:
            tarefas.append((genero_selecionado, categoria_selecionada))

    with st.status(f"Sofia está executando {len(tarefas)} tarefa(s)...", expanded=True) as status:
        
        arquivos_gerados = []
        barra_progresso = st.progress(0)
        
        # Caixinha do Walkie-Talkie para a Renner
        texto_dinamico = st.empty()
        def atualizar_tela(mensagem_do_robo):
            texto_dinamico.info(f"🔄 {mensagem_do_robo}")
            
        # 🟢 NOVIDADE: Descobrindo onde é a pasta de Downloads do computador
        pasta_downloads = "."

        for indice, (gen_alvo, cat_alvo) in enumerate(tarefas):
            st.write(f"**Extraindo: {marca_selecionada} ➔ {gen_alvo} ➔ {cat_alvo}**")
            
            url_alvo = master_urls[marca_selecionada][gen_alvo][cat_alvo]
            nome_pdf = f"Sofia_{marca_selecionada}_{gen_alvo}_{cat_alvo}.pdf"
            
            # 🟢 NOVIDADE: Apontando a "mesa de trabalho" para a pasta Downloads
            caminho_arquivo = os.path.join(pasta_downloads, nome_pdf)
            
            try:
                if marca_selecionada == "Renner":
                    navegador = renner.iniciar_navegador()
                    arquivo_final = renner.extrair_produtos_renner(
                        navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo, log_callback=atualizar_tela
                    )
                elif marca_selecionada == "Hering":
                    navegador = hering.iniciar_navegador()
                    atualizar_tela("Rodando robô da Hering... aguarde.")
                    arquivo_final = hering.extrair_produtos_hering(navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo)
                
                if arquivo_final:
                    arquivos_gerados.append(arquivo_final)
                    st.write(f"✅ {cat_alvo} finalizado!")
                else:
                    st.write(f"⚠️ Nenhum produto encontrado para {cat_alvo}.")
            except Exception as e:
                st.error(f"❌ Erro ao processar {cat_alvo}: {e}")
            
            barra_progresso.progress((indice + 1) / len(tarefas))

        status.update(label="Operação Finalizada com Sucesso!", state="complete", expanded=False)

    # --- PREPARANDO O DOWNLOAD REAL ---
    if len(arquivos_gerados) == 1:
        arquivo_para_baixar = arquivos_gerados[0]
        with open(arquivo_para_baixar, "rb") as f:
            dados_download = f.read()
        mime_tipo = "application/pdf"
        nome_botao = os.path.basename(arquivo_para_baixar)
    
    elif len(arquivos_gerados) > 1:
        nome_zip = f"Sofia_Pacote_{marca_selecionada}.zip"
        arquivo_para_baixar = os.path.join(pasta_downloads, nome_zip)
        with zipfile.ZipFile(arquivo_para_baixar, 'w') as zipf:
            for pdf in arquivos_gerados:
                # arcname evita criar pastas estranhas dentro do arquivo ZIP
                zipf.write(pdf, arcname=os.path.basename(pdf))
        with open(arquivo_para_baixar, "rb") as f:
            dados_download = f.read()
        mime_tipo = "application/zip"
        nome_botao = nome_zip

    if arquivos_gerados:
        st.success(f"🎉 Arquivo gerado de verdade!")
        st.download_button(
            label=f"📥 Baixar Relatório(s)",
            data=dados_download,
            file_name=nome_botao,
            mime=mime_tipo,
            use_container_width=True
        )
