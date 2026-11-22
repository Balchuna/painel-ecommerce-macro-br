-- Esquema Star Schema do Painel E-Commerce & Macroeconomia Brasil.
-- Carregado a partir de data/limpa/*.csv por scripts/gerar_gabarito.py.
-- Qualquer violação de chave estrangeira, domínio ou data interrompe a carga.

PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS vw_vendedores_decis;
DROP VIEW IF EXISTS vw_coorte_retencao;
DROP VIEW IF EXISTS vw_pagamentos_mix;
DROP VIEW IF EXISTS vw_uf_sla;
DROP VIEW IF EXISTS vw_serie_mensal_macro;
DROP VIEW IF EXISTS vw_pedidos_entregues;

DROP TABLE IF EXISTS macro_benchmark_atual;
DROP TABLE IF EXISTS fontes_metadados;
DROP TABLE IF EXISTS qualidade_auditoria;
DROP TABLE IF EXISTS fato_itens_pedido;
DROP TABLE IF EXISTS fato_pedidos;
DROP TABLE IF EXISTS dim_vendedor;
DROP TABLE IF EXISTS dim_faixa_atraso;
DROP TABLE IF EXISTS dim_categoria;
DROP TABLE IF EXISTS dim_geo_uf;
DROP TABLE IF EXISTS dim_calendario;
DROP TABLE IF EXISTS dim_macro_mensal;

-- Dimensão macroeconômica mensal: BCB SGS 433 (IPCA), 432 (Selic) e 1 (PTAX USD).
-- fator_deflator = 1.000000 no mês-base (2018-10).
CREATE TABLE dim_macro_mensal (
    ano_mes             TEXT    PRIMARY KEY CHECK (length(ano_mes) = 7),
    data_mes            TEXT    NOT NULL UNIQUE CHECK (data_mes IS date(data_mes)),
    ipca_mensal_pct     REAL    NOT NULL,
    ipca_acum_12m_pct   REAL    NOT NULL,
    indice_ipca_base100 REAL    NOT NULL CHECK (indice_ipca_base100 > 0),
    fator_deflator      REAL    NOT NULL CHECK (fator_deflator > 0),
    selic_media         REAL    NOT NULL CHECK (selic_media >= 0),
    ptax_media          REAL    NOT NULL CHECK (ptax_media > 0)
);

-- Dimensão calendário diária cobrindo toda a janela Olist (2016-09-01 a 2018-10-31).
CREATE TABLE dim_calendario (
    data             TEXT    PRIMARY KEY CHECK (data IS date(data)),
    ano              INTEGER NOT NULL CHECK (ano BETWEEN 2016 AND 2018),
    trimestre        TEXT    NOT NULL CHECK (length(trimestre) = 7),
    trimestre_num    INTEGER NOT NULL,
    mes              INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ano_mes          TEXT    NOT NULL REFERENCES dim_macro_mensal (ano_mes),
    ano_mes_num      INTEGER NOT NULL,
    mes_ano_pt       TEXT    NOT NULL,
    dia_semana       INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    eh_fim_de_semana INTEGER NOT NULL CHECK (eh_fim_de_semana IN (0, 1))
);

-- Dimensão geográfica oficial IBGE (27 UFs + população estimada 2018 e Censo 2022).
CREATE TABLE dim_geo_uf (
    uf                   TEXT    PRIMARY KEY CHECK (length(uf) = 2),
    codigo_ibge          INTEGER NOT NULL UNIQUE,
    nome                 TEXT    NOT NULL CHECK (nome <> ''),
    regiao_sigla         TEXT    NOT NULL CHECK (regiao_sigla IN ('N', 'NE', 'CO', 'SE', 'S')),
    regiao               TEXT    NOT NULL CHECK (regiao IN ('Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul')),
    populacao_ibge       INTEGER NOT NULL CHECK (populacao_ibge > 0),
    populacao_censo_2022 INTEGER NOT NULL CHECK (populacao_censo_2022 > 0)
);

-- Dimensão de categorias de produtos Olist com rótulos PT-BR e EN limpos.
CREATE TABLE dim_categoria (
    categoria_codigo       TEXT    PRIMARY KEY CHECK (categoria_codigo <> ''),
    categoria_pt           TEXT    NOT NULL CHECK (categoria_pt <> ''),
    categoria_en           TEXT    NOT NULL CHECK (categoria_en <> ''),
    traducao_oficial_olist INTEGER NOT NULL CHECK (traducao_oficial_olist IN (0, 1))
);

-- Dimensão ordinal de faixas de atraso logístico (1..5 entregues, 6 sem entrega).
CREATE TABLE dim_faixa_atraso (
    faixa_atraso    TEXT    PRIMARY KEY,
    faixa_atraso_en TEXT    NOT NULL,
    ordem           INTEGER NOT NULL UNIQUE CHECK (ordem BETWEEN 1 AND 6),
    eh_atrasado     INTEGER NOT NULL CHECK (eh_atrasado IN (0, 1))
);

-- Dimensão de vendedores com decil de concentração de GMV real entregue (D1 = top 10%).
CREATE TABLE dim_vendedor (
    seller_id         TEXT    PRIMARY KEY CHECK (seller_id <> ''),
    uf_vendedor       TEXT    NOT NULL REFERENCES dim_geo_uf (uf),
    cidade_vendedor   TEXT    NOT NULL,
    gmv_real_entregue REAL    NOT NULL CHECK (gmv_real_entregue >= 0),
    pedidos_entregues INTEGER NOT NULL CHECK (pedidos_entregues >= 0),
    decil_gmv         TEXT    NOT NULL,
    decil_ordem       INTEGER NOT NULL CHECK (decil_ordem BETWEEN 1 AND 11)
);

-- Fato de pedidos: 1 linha por pedido bruto Olist (99.441 linhas, sem descarte silencioso).
CREATE TABLE fato_pedidos (
    order_id                 TEXT    PRIMARY KEY CHECK (order_id <> ''),
    data_compra              TEXT    NOT NULL REFERENCES dim_calendario (data) CHECK (data_compra IS date(data_compra)),
    ano_mes                  TEXT    NOT NULL REFERENCES dim_macro_mensal (ano_mes),
    data_aprovacao           TEXT             CHECK (data_aprovacao IS date(data_aprovacao)),
    data_entrega_estimada    TEXT    NOT NULL CHECK (data_entrega_estimada IS date(data_entrega_estimada)),
    data_entrega_real        TEXT             CHECK (data_entrega_real IS date(data_entrega_real)),
    dias_entrega             INTEGER          CHECK (dias_entrega IS NULL OR dias_entrega >= 0),
    dias_atraso              INTEGER,
    flag_atraso              INTEGER          CHECK (flag_atraso IS NULL OR flag_atraso IN (0, 1)),
    faixa_atraso             TEXT    NOT NULL REFERENCES dim_faixa_atraso (faixa_atraso),
    status                   TEXT    NOT NULL CHECK (status IN (
                                'delivered', 'shipped', 'canceled', 'unavailable',
                                'invoiced', 'processing', 'created', 'approved'
                             )),
    flag_entregue            INTEGER NOT NULL CHECK (flag_entregue IN (0, 1)),
    uf_cliente               TEXT    NOT NULL REFERENCES dim_geo_uf (uf),
    categoria_principal      TEXT    NOT NULL REFERENCES dim_categoria (categoria_codigo),
    nota_review              INTEGER          CHECK (nota_review IS NULL OR nota_review BETWEEN 1 AND 5),
    qtd_itens                INTEGER NOT NULL CHECK (qtd_itens >= 0),
    valor_produtos           REAL    NOT NULL CHECK (valor_produtos >= 0),
    valor_frete              REAL    NOT NULL CHECK (valor_frete >= 0),
    valor_total_nominal      REAL    NOT NULL CHECK (valor_total_nominal >= 0),
    valor_total_real_ipca    REAL    NOT NULL CHECK (valor_total_real_ipca >= 0),
    tipo_pagamento_principal TEXT    NOT NULL CHECK (tipo_pagamento_principal IN (
                                'credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined', 'sem_pagamento'
                             )),
    parcelas                 INTEGER NOT NULL CHECK (parcelas >= 0),
    cliente_unico_id         TEXT    NOT NULL CHECK (cliente_unico_id <> ''),
    coorte_mes               TEXT    NOT NULL CHECK (length(coorte_mes) = 7),
    meses_desde_coorte       INTEGER NOT NULL,
    flag_recompra            INTEGER NOT NULL CHECK (flag_recompra IN (0, 1)),
    flag_frete_outlier       INTEGER NOT NULL CHECK (flag_frete_outlier IN (0, 1))
);

-- Fato de itens de pedido: 1 linha por item vendido (112.650 linhas) para categoria e vendedor.
CREATE TABLE fato_itens_pedido (
    order_id             TEXT    NOT NULL REFERENCES fato_pedidos (order_id),
    order_item_id        INTEGER NOT NULL CHECK (order_item_id >= 1),
    data_compra          TEXT    NOT NULL REFERENCES dim_calendario (data) CHECK (data_compra IS date(data_compra)),
    ano_mes              TEXT    NOT NULL REFERENCES dim_macro_mensal (ano_mes),
    status               TEXT    NOT NULL,
    flag_entregue        INTEGER NOT NULL CHECK (flag_entregue IN (0, 1)),
    uf_cliente           TEXT    NOT NULL REFERENCES dim_geo_uf (uf),
    categoria_codigo     TEXT    NOT NULL REFERENCES dim_categoria (categoria_codigo),
    seller_id            TEXT    NOT NULL REFERENCES dim_vendedor (seller_id),
    uf_vendedor          TEXT    NOT NULL REFERENCES dim_geo_uf (uf),
    preco                REAL    NOT NULL CHECK (preco >= 0),
    frete                REAL    NOT NULL CHECK (frete >= 0),
    valor_item_nominal   REAL    NOT NULL CHECK (valor_item_nominal >= 0),
    valor_item_real_ipca REAL    NOT NULL CHECK (valor_item_real_ipca >= 0),
    flag_frete_outlier   INTEGER NOT NULL CHECK (flag_frete_outlier IN (0, 1)),
    PRIMARY KEY (order_id, order_item_id)
);

-- Auditoria de qualidade: anomalias reais encontradas na base Olist e tratamento aplicado.
CREATE TABLE qualidade_auditoria (
    regra_id        TEXT    PRIMARY KEY,
    regra           TEXT    NOT NULL,
    regra_en        TEXT    NOT NULL,
    tabela_origem   TEXT    NOT NULL,
    linhas_afetadas INTEGER NOT NULL CHECK (linhas_afetadas >= 0),
    base_referencia INTEGER NOT NULL CHECK (base_referencia > 0),
    pct_base        REAL    NOT NULL CHECK (pct_base >= 0),
    severidade      TEXT    NOT NULL,
    tratamento      TEXT    NOT NULL,
    tratamento_en   TEXT    NOT NULL
);

-- Linhagem das fontes coletadas (URLs, timestamps UTC, SHA-256, registros e licenças).
CREATE TABLE fontes_metadados (
    arquivo         TEXT    PRIMARY KEY,
    fonte           TEXT    NOT NULL,
    endpoint        TEXT    NOT NULL,
    registros       INTEGER NOT NULL CHECK (registros >= 0),
    bytes_total     INTEGER NOT NULL CHECK (bytes_total > 0),
    sha256          TEXT    NOT NULL CHECK (length(sha256) = 64),
    coletado_em_utc TEXT    NOT NULL,
    licenca         TEXT    NOT NULL
);

-- Retrato macroeconômico recente (BCB SGS) para benchmark frente ao fim do recorte Olist.
CREATE TABLE macro_benchmark_atual (
    indicador       TEXT    PRIMARY KEY,
    nome_pt         TEXT    NOT NULL,
    nome_en         TEXT    NOT NULL,
    serie_sgs       INTEGER NOT NULL,
    data_referencia TEXT    NOT NULL CHECK (data_referencia IS date(data_referencia)),
    valor_recente   REAL    NOT NULL,
    valor_fim_olist REAL    NOT NULL,
    unidade         TEXT    NOT NULL
);

CREATE INDEX idx_pedidos_entregue_mes ON fato_pedidos (flag_entregue, ano_mes);
CREATE INDEX idx_pedidos_uf ON fato_pedidos (uf_cliente);
CREATE INDEX idx_pedidos_faixa ON fato_pedidos (faixa_atraso);
CREATE INDEX idx_pedidos_cliente ON fato_pedidos (cliente_unico_id);
CREATE INDEX idx_itens_entregue_cat ON fato_itens_pedido (flag_entregue, categoria_codigo);
CREATE INDEX idx_itens_seller ON fato_itens_pedido (seller_id);
