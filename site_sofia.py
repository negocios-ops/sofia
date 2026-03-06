import streamlit as st
import time
import os
import zipfile
from datetime import datetime

import analise_renner_uruguai as renner
import analise_hering_uruguai as hering
import analise_estilos_peru as estilos
import analise_bas_uruguai as bas

st.set_page_config(page_title="Sofia - Dashboard", page_icon="🎀", layout="centered")

# --- 🔒 SISTEMA DE SEGURANÇA ---
SENHA_OFICIAL = "trp2018"

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

if not st.session_state.acesso_liberado:
    st.title("🔒 Acesso Restrito")
    st.write("Bem-vindo(a)! Por favor, insira a senha da equipe para acessar a Sofia.")
    
    senha_digitada = st.text_input("Senha de Acesso:", type="password")
    
    if st.button("Entrar ⏩", use_container_width=True):
        if senha_digitada == SENHA_OFICIAL:
            st.session_state.acesso_liberado = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta. Tente novamente.")
            
    st.stop()

# --- DICIONÁRIO DE URLs (COM ORTOGRAFIA CORRIGIDA) ---
urls_renner = {
    "Masculino": {
        "Bermudas": "https://www.renner.com/uy/c/masculino/bermudas-y-shorts/cat360002uy",
        "Blusões": "https://www.renner.com/uy/c/masculino/buzos-y-sueters/buzos/cat360039uy",
        "Camisas": "https://www.renner.com/uy/c/masculino/camisas/cat360007uy",
        "Casacos": "https://www.renner.com/uy/c/masculino/chaquetas/cat360009uy",
        "Calças": "https://www.renner.com/uy/c/masculino/pantalones/cat360006uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-masc/lst00000045",
        "Pijamas": "https://www.renner.com/uy/c/masculino/pijamas-y-robes/cat360017uy",
        "Polos": "https://www.renner.com/uy/c/masculino/polos/cat360018uy",
        "Camisetas": "https://www.renner.com/uy/c/masculino/remeras/cat360008uy"
    },
    "Feminino": {
        "Vestidos": "https://www.renner.com/uy/c/femenino/vestidos/cat200002uy",
        "Bermudas": "https://www.renner.com/uy/c/femenino/bermudas-y-shorts/cat210004uy",
        "Blusas": "https://www.renner.com/uy/c/femenino/blusas-y-remera/cat210006uy",
        "Calças": "https://www.renner.com/uy/c/femenino/pantalones/cat210010uy",
        "Casacos": "https://www.renner.com/uy/c/femenino/chaquetas/cat210012uy",
        "Blusões": "https://www.renner.com/uy/c/femenino/buzos-y-sueters/buzos/cat290050uy",
        "Camisas": "https://www.renner.com/uy/c/femenino/camisas/cat210011uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-fem/lst00000044",
        "Moda Praia": "https://www.renner.com/uy/c/femenino/moda-playa/cat210018uy",
        "Pijamas": "https://www.renner.com/uy/c/femenino/pijamas/cat210019uy"
    },
    "Menina": {
        "Bermudas": "https://www.renner.com/uy/c/infantil/bermudas-y-shorts/cat350002uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350002uy",
        "Blusas": "https://www.renner.com/uy/c/infantil/blusas/cat350003uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350003uy",
        "Bodies": "https://www.renner.com/uy/c/infantil/bodies/cat350005uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Agenre%3AFemenino%3Acategory%3Acat350005uy",
        "Blusões": "https://www.renner.com/uy/c/infantil/buzos-y-sueters/cat350004uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350004uy",
        "Casacos": "https://www.renner.com/uy/c/infantil/chaquetas-y-sacos/cat350010uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350010uy",
        "Conjuntos": "https://www.renner.com/uy/c/infantil/conjuntos/cat350012uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350012uy",
        "Macacões": "https://www.renner.com/uy/c/infantil/enteritos-y-jardineros/cat350016uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350016uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-inf/lst00000046?sort=relevance&filters=%3Arelevance%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1a%3AlistCategory%3Alst00000046",
        "Calças": "https://www.renner.com/uy/c/infantil/pantalones/cat350007uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AFemenino%3Agenre%3ANi%25C3%25B1a%3Acategory%3Acat350007uy",
        "Saias": "https://www.renner.com/uy/c/infantil/polleras/cat350021uy",
        "Vestidos": "https://www.renner.com/uy/c/infantil/vestidos/cat350022uy"
    },
    "Menino": {
        "Bermudas": "https://www.renner.com/uy/c/infantil/bermudas-y-shorts/cat350002uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350002uy",
        "Blusas": "https://www.renner.com/uy/c/infantil/blusas/cat350003uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350003uy",
        "Bodies": "https://www.renner.com/uy/c/infantil/bodies/cat350005uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AMasculino%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350005uy",
        "Blusões": "https://www.renner.com/uy/c/infantil/buzos-y-sueters/cat350004uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350004uy",
        "Casacos": "https://www.renner.com/uy/c/infantil/chaquetas-y-sacos/cat350010uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3AMasculino%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350010uy",
        "Conjuntos": "https://www.renner.com/uy/c/infantil/conjuntos/cat350012uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350012uy",
        "Macacões": "https://www.renner.com/uy/c/infantil/enteritos-y-jardineros/cat350016uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350016uy",
        "Jeans": "https://www.renner.com/uy/l/jeans-inf/lst00000046?sort=relevance&filters=%3Arelevance%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3AlistCategory%3Alst00000046",
        "Calças": "https://www.renner.com/uy/c/infantil/pantalones/cat350007uy?sort=relevance&filters=%3Arelevance%3Acategory%3Acat260027uy%3AlrsaStockLevelStatus%3AinStock%3Agenre%3ANi%25C3%25B1o%3Acategory%3Acat350007uy"
    }
}

urls_hering = {
    "Masculino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/bermudas",
        "Blusões": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/campera",
        "Regatas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/musculosas",
        "Calças": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/pijamas",
        "Polos": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/polo",
        "Jeans": "https://www.hering.com.uy/indumentaria-masculina/indumentaria/jeans"
    },
    "Feminino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/bermudas",
        "Blusas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/blusas",
        "Blusões": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/campera",
        "Regatas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/musculosas",
        "Calças": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/pijamas",
        "Shorts": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/shorts",
        "Vestidos": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/vestido",
        "Tops": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/top",
        "Jeans": "https://www.hering.com.uy/indumentaria-femenina/indumentaria/jeans"
    },
    "Menina": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/bermudas",
        "Blusas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/blusas",
        "Blusões": "https://www.hering.com.uy/indumentaria-nina/indumentaria/buzos",
        "Camisetas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/campera",
        "Conjuntos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/conjunto",
        "Regatas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/musculosas",
        "Calças": "https://www.hering.com.uy/indumentaria-nina/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-nina/indumentaria/pijamas",
        "Shorts": "https://www.hering.com.uy/indumentaria-nina/indumentaria/shorts",
        "Vestidos": "https://www.hering.com.uy/indumentaria-nina/indumentaria/vestido",
        "Jeans": "https://www.hering.com.uy/indumentaria-nina/indumentaria/jeans"
    },
    "Menino": {
        "Bermudas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/bermudas",
        "Blusões": "https://www.hering.com.uy/indumentaria-nino/indumentaria/buzos",
        "Camisas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/camisas",
        "Camisetas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/camisetas",
        "Casacos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/campera",
        "Conjuntos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/conjunto",
        "Regatas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/musculosas",
        "Calças": "https://www.hering.com.uy/indumentaria-nino/indumentaria/pantalones",
        "Pijamas": "https://www.hering.com.uy/indumentaria-nino/indumentaria/pijamas",
        "Polos": "https://www.hering.com.uy/indumentaria-nino/indumentaria/polo",
        "Shorts": "https://www.hering.com.uy/indumentaria-nino/indumentaria/shorts",
        "Jeans": "https://www.hering.com.uy/indumentaria-nino/indumentaria/jeans"
    }
}

urls_estilos = {
    "Masculino": {
        "Blusões": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/poleras",
        "Polos": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/polos",
        "Camisas": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/camisas",
        "Casacos": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/casacas-y-abrigos",
        "Calças": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/pantalones-hombre/pantalones-y-joggers",
        "Jeans": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/pantalones-hombre/jeans-hombre",
        "Shorts e bermudas": "https://www.estilos.com.pe/moda-y-accesorios/hombre/ropa-hombre/shorts-y-bermudas"
    }
}

urls_bas = {
    "Masculino": {
        "Camisetas": "https://www.bas.com.uy/hombre/camisetas?category-1=hombre&category-2=camisetas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Camisas": "https://www.bas.com.uy/hombre/camisas?category-1=hombre&category-2=camisas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/hombre/pantalones?category-1=hombre&category-2=pantalones&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/hombre/jean?category-1=hombre&category-2=jean&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/hombre/hoodies-y-sudaderas?category-1=hombre&category-2=hoodies-y-sudaderas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/hombre/abrigos?category-1=hombre&category-2=abrigos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Bermudas": "https://www.bas.com.uy/hombre/short-y-bermudas?category-1=hombre&category-2=short-y-bermudas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0"
    },
    "Feminino": {
        "Camisetas": "https://www.bas.com.uy/mujer/camisetas?category-1=mujer&category-2=camisetas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Camisas/Blusas": "https://www.bas.com.uy/mujer/blusas-y-camisas?category-1=mujer&category-2=blusas-y-camisas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/mujer/pantalones?category-1=mujer&category-2=pantalones&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/mujer/jean?category-1=mujer&category-2=jean&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/mujer/hoodies-y-sudaderas?category-1=mujer&category-2=hoodies-y-sudaderas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/mujer/abrigos?category-1=mujer&category-2=abrigos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Saias/vestidos": "https://www.bas.com.uy/mujer/faldas-y-vestidos?category-1=mujer&category-2=faldas-y-vestidos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Shorts": "https://www.bas.com.uy/mujer/short-y-bermudas?category-1=mujer&category-2=short-y-bermudas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Pijama": "https://www.bas.com.uy/mujer/ropa-para-dormir?category-1=mujer&category-2=ropa-para-dormir&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0"
    },
    "Menino (0-2 anos)": {
        "Camisetas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=camisetas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Camisas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=camisas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Bodies": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=bodies&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=short-y-bermudas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Conjuntos": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=conjuntos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Macacões": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=enterizos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=hoodies-y-sudaderas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=jean&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=abrigos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Pijamas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=12-14a&talle=12-18m&talle=12-24m&talle=17&talle=18&talle=18-24m&talle=19&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=32&talle=30&talle=33&talle=31&talle=talle-1&talle=0-3m&talle=0-6m&talle=0m&talle=3-6m&talle=9-12m&talle=6-9m&talle=6-12m&category-2=ropa-para-dormir&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0"
    },
    "Menina (0-2 anos)": {
        "Camisetas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=camisetas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Blusas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=blusas-y-camisas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Saias e vestidos": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=faldas-y-vestidos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=short-y-bermudas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Macacões": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=enterizos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Conjuntos": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=conjuntos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=hoodies-y-sudaderas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=abrigos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Pijamas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-18m&talle=12-24m&talle=18-24m&talle=9-12m&talle=unico&talle=talle-1&talle=20&talle=6-9m&talle=6-12m&talle=3-6m&talle=21&category-2=ropa-para-dormir&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0"
    },
    "Menino (1-5 anos)": {
        "Camisetas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=camisetas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Camisas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=camisas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Bodies": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=bodies&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=short-y-bermudas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Macacões": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=enterizos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Conjuntos": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=conjuntos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=pantalones&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=jean&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=hoodies-y-sudaderas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Pijamas": "https://www.bas.com.uy/bebe?category-1=bebe&fuzzy=0&operator=and&talle=1-2a&talle=12-14a&talle=12-18m&talle=12-24m&talle=16a&talle=17&talle=18&talle=18-24m&talle=19&talle=2-3a&talle=20&talle=21&talle=22&talle=23&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=32&talle=30&talle=33&talle=31&talle=34&talle=4-5a&talle=5-6a&talle=talle-2&talle=talle-1&category-2=ropa-para-dormir&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0"
    },
    "Menina (1-5 anos)": {
        "Camisetas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=camisetas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Blusas e camisas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=blusas-y-camisas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Bodies": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=bodies&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Macacões": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=enterizos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Saias e vestidos": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=faldas-y-vestidos&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=hoodies-y-sudaderas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=pantalones&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=0-3m&talle=0-6m&talle=0m&talle=12-24m&talle=unico&talle=talle-1&talle=20&talle=6-12m&talle=21&category-2=abrigos&talle=4-5a&talle=2-3a&talle=3-4a&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=jean&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=short-y-bermudas&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0",
        "Pijamas": "https://www.bas.com.uy/beba?category-1=beba&fuzzy=0&operator=and&talle=1-2a&talle=12-18m&talle=12-24m&talle=18-24m&talle=2-3a&talle=20&talle=21&talle=23&talle=6a&talle=24&talle=25&talle=26&talle=27&talle=28&talle=29&talle=3-4a&talle=4-5a&talle=5-6a&talle=talle-1&talle=talle-2&talle=unico&category-2=ropa-para-dormir&facets=category-1%2Cfuzzy%2Coperator%2Ctalle%2Ccategory-2&sort=release_desc&page=0"
    },
    "Menino (6-14 anos)": {
        "Camisetas": "https://www.bas.com.uy/nino/camisetas?category-1=nino&category-2=camisetas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Camisas": "https://www.bas.com.uy/nino/camisas?category-1=nino&category-2=camisas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/nino/short-y-bermudas?category-1=nino&category-2=short-y-bermudas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/nino/pantalones?category-1=nino&category-2=pantalones&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/nino/jean?category-1=nino&category-2=jean&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/nino/hoodies-y-sudaderas?category-1=nino&category-2=hoodies-y-sudaderas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/nino/abrigos?category-1=nino&category-2=abrigos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0"
    },
    "Menina (6-14 anos)": {
        "Camisetas": "https://www.bas.com.uy/nina/camisetas?category-1=nina&category-2=camisetas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Blusas e camisas": "https://www.bas.com.uy/nina/blusas-y-camisas?category-1=nina&category-2=blusas-y-camisas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Shorts e bermudas": "https://www.bas.com.uy/nina/short-y-bermudas?category-1=nina&category-2=short-y-bermudas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Saias e vestidos": "https://www.bas.com.uy/nina/faldas-y-vestidos?category-1=nina&category-2=faldas-y-vestidos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Calças": "https://www.bas.com.uy/nina/pantalones?category-1=nina&category-2=pantalones&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Jeans": "https://www.bas.com.uy/nina/jean?category-1=nina&category-2=jean&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Blusões": "https://www.bas.com.uy/nina/hoodies-y-sudaderas?category-1=nina&category-2=hoodies-y-sudaderas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Casacos": "https://www.bas.com.uy/nina/abrigos?category-1=nina&category-2=abrigos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Macacões": "https://www.bas.com.uy/nina/enterizos?category-1=nina&category-2=enterizos&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0",
        "Pijamas": "https://www.bas.com.uy/nina/ropa-para-dormir?category-1=nina&category-2=ropa-para-dormir&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=release_desc&page=0"
    }
}

master_urls = {
    "🇺🇾 Uruguai": {
        "Renner": urls_renner, 
        "Hering": urls_hering,
        "Bas": urls_bas
    },
    "🇵🇪 Peru": {
        "Estilos": urls_estilos
    }
}

opcoes_catalogo = master_urls

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

# --- BOTÃO DE AÇÃO ---
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

    st.divider()
    
    caixa_de_mensagem = st.empty()
    barra_progresso = st.progress(0)
    
    def atualizar_tela(mensagem_do_robo):
        caixa_de_mensagem.info(f"🔄 **Ação:** {mensagem_do_robo}")

    pasta_downloads = "."
    arquivos_gerados = []

    for indice, (gen_alvo, cat_alvo) in enumerate(tarefas):
        url_alvo = master_urls[pais_selecionado][marca_selecionada][gen_alvo][cat_alvo]
        # 🎀 NOMEADOR INTELIGENTE DE ARQUIVOS
        data_hoje_arq = datetime.now().strftime("%Y.%m.%d")
        pais_limpo = pais_selecionado.replace("🇺🇾 ", "").replace("🇵🇪 ", "") # Tira a bandeirinha do nome
        nome_pdf = f"{marca_selecionada} {pais_limpo} {gen_alvo} {cat_alvo} - {data_hoje_arq}.pdf"
        caminho_arquivo = os.path.join(pasta_downloads, nome_pdf)
        
        try:
            arquivo_final = None
            if marca_selecionada == "Renner":
                navegador = renner.iniciar_navegador()
                arquivo_final = renner.extrair_produtos_renner(
                    navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo, log_callback=atualizar_tela
                )
            elif marca_selecionada == "Hering":
                navegador = hering.iniciar_navegador()
                arquivo_final = hering.extrair_produtos_hering(
                    navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo, log_callback=atualizar_tela
                )
            elif marca_selecionada == "Estilos": 
                navegador = estilos.iniciar_navegador()
                arquivo_final = estilos.extrair_produtos_estilos(
                    navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo, log_callback=atualizar_tela
                )  
            elif marca_selecionada == "Bas":
                navegador = bas.iniciar_navegador()
                arquivo_final = bas.extrair_produtos_bas(
                    navegador, url_alvo, caminho_arquivo, gen_alvo, cat_alvo, log_callback=atualizar_tela
                )
            if arquivo_final:
                arquivos_gerados.append(arquivo_final)
                
        except Exception as e:
            atualizar_tela(f"Erro inesperado em {cat_alvo}. Pulando para o próximo.")
            time.sleep(2)
        finally:
            try: navegador.quit()
            except: pass
        
        barra_progresso.progress((indice + 1) / len(tarefas))

    # --- PREPARANDO O DOWNLOAD ---
    if arquivos_gerados:
        caixa_de_mensagem.success("🎉 Arquivos gerados com sucesso!")
        
        if len(arquivos_gerados) == 1:
            arquivo_para_baixar = arquivos_gerados[0]
            with open(arquivo_para_baixar, "rb") as f:
                dados_download = f.read()
            mime_tipo = "application/pdf"
            nome_botao = os.path.basename(arquivo_para_baixar)
        else:
            nome_zip = f"Pacote {marca_selecionada} {pais_limpo} - {data_hoje_arq}.zip"
            arquivo_para_baixar = os.path.join(pasta_downloads, nome_zip)
            
            with zipfile.ZipFile(arquivo_para_baixar, 'w') as zipf:
                for pdf_path in arquivos_gerados:
                    # Salva os arquivos direto no ZIP, sem criar pastas internas
                    zipf.write(pdf_path, arcname=os.path.basename(pdf_path))
                    
            with open(arquivo_para_baixar, "rb") as f:
                dados_download = f.read()
            mime_tipo = "application/zip"
            nome_botao = nome_zip

        st.download_button(
            label=f"📥 Baixar Relatório(s)",
            data=dados_download,
            file_name=nome_botao,
            mime=mime_tipo,
            use_container_width=True
        )
    else:
        caixa_de_mensagem.warning("⚠️ Nenhum produto foi encontrado nesta seleção.")
