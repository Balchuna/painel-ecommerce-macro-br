"""Constantes, fontes oficiais e dicionários de domínio do painel."""
from __future__ import annotations

USER_AGENT = (
    "painel-ecommerce-macro-br/1.0 "
    "(Projeto de portfolio educacional; https://github.com/Balchuna/painel-ecommerce-macro-br)"
)

ATRASO_PADRAO_S = 0.35
TIMEOUT_PADRAO_S = 30.0
TENTATIVAS_PADRAO = 3

# Repositório oficial público da Olist no GitHub (mesmo conjunto publicado no Kaggle sob CC BY-NC-SA 4.0)
OLIST_BASE_URL = (
    "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets"
)
OLIST_ARQUIVOS: tuple[str, ...] = (
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
)

# Banco Central do Brasil — Sistema Gerenciador de Séries Temporais (SGS)
BCB_SGS_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    "?formato=json&dataInicial={inicio}&dataFinal={fim}"
)
BCB_SGS_ULTIMOS_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json"
)
BCB_SERIES = {
    "ipca_433": {
        "codigo": 433,
        "nome": "IPCA - Variação mensal (%)",
        "inicio": "01/10/2015",  # 12 meses antes de 2016-09 para IPCA acumulado 12m exato
        "fim": "31/10/2018",
        "ultimos": 12,
    },
    "selic_432": {
        "codigo": 432,
        "nome": "Taxa de juros - Meta Selic definida pelo Copom (% a.a.)",
        "inicio": "01/09/2016",
        "fim": "31/10/2018",
        "ultimos": 5,
    },
    "ptax_1": {
        "codigo": 1,
        "nome": "Taxa de câmbio - Livre - Dólar americano (venda) - diário (PTAX)",
        "inicio": "01/09/2016",
        "fim": "31/10/2018",
        "ultimos": 5,
    },
}

# IBGE — API de Localidades e API de Agregados (SIDRA)
IBGE_ENDPOINTS = {
    "estados": "https://servicodados.ibge.gov.br/api/v1/localidades/estados",
    # Agregado 6579, variável 9324: Estimativas de População Residente por UF (2018 — contemporânea à base Olist)
    "populacao_2018": (
        "https://servicodados.ibge.gov.br/api/v3/agregados/6579"
        "/periodos/2018/variaveis/9324?localidades=N3[all]"
    ),
    # Agregado 4714, variável 93: Censo Demográfico 2022 — População Residente por UF (referência oficial mais recente)
    "populacao_2022": (
        "https://servicodados.ibge.gov.br/api/v3/agregados/4714"
        "/periodos/2022/variaveis/93?localidades=N3[all]"
    ),
}

# Janela oficial do conjunto Olist (pedidos entre 2016-09 e 2018-10)
ANO_MES_INICIO_OLIST = "2016-09"
ANO_MES_FIM_OLIST = "2018-10"
MES_BASE_DEFLATOR = "2018-10"

# Regra explícita de outlier de frete para auditoria de qualidade
LIMIAR_FRETE_EXTREMO_BRL = 300.0
LIMIAR_RAZAO_FRETE_PRODUTO = 2.0

# Rótulos legíveis para tipos de pagamento Olist
TIPOS_PAGAMENTO = {
    "credit_card": ("Cartão de Crédito", "Credit Card"),
    "boleto": ("Boleto Bancário", "Boleto"),
    "voucher": ("Voucher / Cupom", "Voucher"),
    "debit_card": ("Cartão de Débito", "Debit Card"),
    "not_defined": ("Não definido", "Not Defined"),
    "sem_pagamento": ("Sem registro de pagamento", "No Payment Record"),
}

# Ordem canônica das faixas de atraso logístico (escala ordinal 1..5 em pedidos entregues; 6 = sem entrega)
FAIXAS_ATRASO_ORDEM = {
    "No prazo / antecipado": 1,
    "1–3 dias de atraso": 2,
    "4–7 dias": 3,
    "8–14 dias": 4,
    "15+ dias": 5,
    "Sem entrega": 6,
}

FAIXAS_ATRASO_EN = {
    "No prazo / antecipado": "On time / early",
    "1–3 dias de atraso": "1–3 days late",
    "4–7 dias": "4–7 days late",
    "8–14 dias": "8–14 days late",
    "15+ dias": "15+ days late",
    "Sem entrega": "Not delivered",
}

MESES_PT_ABREV = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}

LICENCAS_FONTES = {
    "olist": "CC BY-NC-SA 4.0 (Olist Brazilian E-Commerce Public Dataset / Kaggle & olist/work-at-olist-data)",
    "bcb": "Dados Públicos Oficiais — Banco Central do Brasil (SGS / Lei de Acesso à Informação)",
    "ibge": "Dados Públicos Oficiais — IBGE (API de Localidades e SIDRA Agregados)",
}
