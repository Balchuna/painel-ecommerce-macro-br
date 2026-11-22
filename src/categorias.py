"""Normalização de nomes PT-BR e EN das categorias do catálogo Olist."""
from __future__ import annotations

# Mapa PT-BR com acentuação editorial correta para todas as 73 categorias reais da Olist + sem_categoria
CATEGORIAS_PT: dict[str, str] = {
    "agro_industria_e_comercio": "Agro, Indústria e Comércio",
    "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos e Bebidas",
    "artes": "Artes",
    "artes_e_artesanato": "Artes e Artesanato",
    "artigos_de_festas": "Artigos de Festas",
    "artigos_de_natal": "Artigos de Natal",
    "audio": "Áudio",
    "automotivo": "Automotivo",
    "bebes": "Bebês",
    "bebidas": "Bebidas",
    "beleza_saude": "Beleza e Saúde",
    "brinquedos": "Brinquedos",
    "cama_mesa_banho": "Cama, Mesa e Banho",
    "casa_conforto": "Casa e Conforto",
    "casa_conforto_2": "Casa e Conforto II",
    "casa_construcao": "Casa e Construção",
    "cds_dvds_musicais": "CDs e DVDs Musicais",
    "cine_foto": "Cine e Foto",
    "climatizacao": "Climatização",
    "consoles_games": "Consoles e Games",
    "construcao_ferramentas_construcao": "Construção e Ferramentas",
    "construcao_ferramentas_ferramentas": "Ferramentas de Construção",
    "construcao_ferramentas_iluminacao": "Iluminação e Construção",
    "construcao_ferramentas_jardim": "Construção e Jardim",
    "construcao_ferramentas_seguranca": "Segurança na Construção",
    "cool_stuff": "Presentes e Novidades",
    "dvds_blu_ray": "DVDs e Blu-Ray",
    "eletrodomesticos": "Eletrodomésticos",
    "eletrodomesticos_2": "Eletrodomésticos II",
    "eletronicos": "Eletrônicos",
    "eletroportateis": "Eletroportáteis",
    "esporte_lazer": "Esporte e Lazer",
    "fashion_bolsas_e_acessorios": "Moda, Bolsas e Acessórios",
    "fashion_calcados": "Calçados",
    "fashion_esporte": "Moda Esportiva",
    "fashion_roupa_feminina": "Moda Feminina",
    "fashion_roupa_infanto_juvenil": "Moda Infantojuvenil",
    "fashion_roupa_masculina": "Moda Masculina",
    "fashion_underwear_e_moda_praia": "Moda Íntima e Praia",
    "ferramentas_jardim": "Ferramentas de Jardim",
    "flores": "Flores",
    "fraldas_higiene": "Fraldas e Higiene",
    "industria_comercio_e_negocios": "Indústria, Comércio e Negócios",
    "informatica_acessorios": "Informática e Acessórios",
    "instrumentos_musicais": "Instrumentos Musicais",
    "la_cuisine": "La Cuisine",
    "livros_importados": "Livros Importados",
    "livros_interesse_geral": "Livros de Interesse Geral",
    "livros_tecnicos": "Livros Técnicos",
    "malas_acessorios": "Malas e Acessórios",
    "market_place": "Marketplace",
    "moveis_colchao_e_estofado": "Colchões e Estofados",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Móveis de Cozinha e Jantar",
    "moveis_decoracao": "Móveis e Decoração",
    "moveis_escritorio": "Móveis de Escritório",
    "moveis_quarto": "Móveis de Quarto",
    "moveis_sala": "Móveis de Sala",
    "musica": "Música",
    "papelaria": "Papelaria",
    "pc_gamer": "PC Gamer",
    "pcs": "Computadores (PCs)",
    "perfumaria": "Perfumaria",
    "pet_shop": "Pet Shop",
    "portateis_casa_forno_e_cafe": "Portáteis de Casa e Café",
    "portateis_cozinha_e_preparadores_de_alimentos": "Portáteis de Cozinha",
    "relogios_presentes": "Relógios e Presentes",
    "seguros_e_servicos": "Seguros e Serviços",
    "sinalizacao_e_seguranca": "Sinalização e Segurança",
    "tablets_impressao_imagem": "Tablets, Impressão e Imagem",
    "telefonia": "Telefonia",
    "telefonia_fixa": "Telefonia Fixa",
    "utilidades_domesticas": "Utilidades Domésticas",
    "sem_categoria": "Sem Categoria",
}

# Correções de typos da tabela oficial de tradução da Olist + 2 categorias sem tradução oficial
CATEGORIAS_EN_OVERRIDE: dict[str, str] = {
    "casa_conforto": "Home Comfort",
    "construcao_ferramentas_ferramentas": "Construction Tools",
    "construcao_ferramentas_jardim": "Construction & Garden Tools",
    "fashion_roupa_feminina": "Women's Clothing",
    "fashion_roupa_masculina": "Men's Clothing",
    "fashion_roupa_infanto_juvenil": "Kids' Clothing",
    "beleza_saude": "Health & Beauty",
    "relogios_presentes": "Watches & Gifts",
    "cama_mesa_banho": "Bed, Bath & Table",
    "esporte_lazer": "Sports & Leisure",
    "informatica_acessorios": "Computers & Accessories",
    "moveis_decoracao": "Furniture & Decor",
    "utilidades_domesticas": "Housewares",
    "ferramentas_jardim": "Garden Tools",
    "cool_stuff": "Cool Stuff & Gifts",
    "pc_gamer": "PC Gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "Kitchen Small Appliances",
    "sem_categoria": "Uncategorized",
}


def formatar_slug_en(slug: str) -> str:
    palavras = slug.replace("_", " ").split()
    minusculas = {"and", "of", "the", "in"}
    return " ".join(
        p if (i > 0 and p in minusculas) else p.capitalize()
        for i, p in enumerate(palavras)
    )


def nome_categoria_pt(codigo: str) -> str:
    if codigo in CATEGORIAS_PT:
        return CATEGORIAS_PT[codigo]
    return codigo.replace("_", " ").capitalize()


def nome_categoria_en(codigo: str, traducao_olist: str | None) -> str:
    if codigo in CATEGORIAS_EN_OVERRIDE:
        return CATEGORIAS_EN_OVERRIDE[codigo]
    if traducao_olist and str(traducao_olist).strip():
        return formatar_slug_en(str(traducao_olist).strip())
    return formatar_slug_en(codigo)
