-- Views analíticas reutilizáveis do Painel E-Commerce & Macroeconomia Brasil.
-- Todas as métricas comerciais e de SLA consideram apenas pedidos entregues (flag_entregue = 1).

CREATE VIEW vw_pedidos_entregues AS
SELECT
    p.*,
    c.ano,
    c.trimestre,
    c.trimestre_num,
    c.mes,
    c.mes_ano_pt,
    g.nome AS uf_nome,
    g.regiao,
    g.populacao_ibge,
    g.populacao_censo_2022,
    f.ordem AS ordem_faixa_atraso,
    f.faixa_atraso_en,
    f.eh_atrasado,
    cat.categoria_pt,
    cat.categoria_en
FROM fato_pedidos AS p
JOIN dim_calendario AS c ON c.data = p.data_compra
JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
JOIN dim_faixa_atraso AS f ON f.faixa_atraso = p.faixa_atraso
JOIN dim_categoria AS cat ON cat.categoria_codigo = p.categoria_principal
WHERE p.flag_entregue = 1;


-- Série mensal completa (2016-09 a 2018-10) cruzando pedidos entregues com BCB SGS.
CREATE VIEW vw_serie_mensal_macro AS
WITH agg_mensal AS (
    SELECT
        ano_mes,
        COUNT(*) AS pedidos_entregues,
        COUNT(DISTINCT cliente_unico_id) AS clientes_unicos,
        SUM(qtd_itens) AS itens_vendidos,
        ROUND(SUM(valor_produtos), 2) AS receita_produtos_nominal,
        ROUND(SUM(valor_frete), 2) AS frete_nominal,
        ROUND(SUM(valor_total_nominal), 2) AS gmv_nominal,
        ROUND(SUM(valor_total_real_ipca), 2) AS gmv_real_ipca,
        ROUND(AVG(valor_total_real_ipca), 2) AS ticket_medio_real,
        SUM(CASE WHEN data_entrega_real IS NOT NULL THEN 1 ELSE 0 END) AS entregas_com_data,
        SUM(CASE WHEN flag_atraso = 0 THEN 1 ELSE 0 END) AS entregas_no_prazo,
        ROUND(AVG(dias_entrega), 2) AS prazo_medio_dias,
        ROUND(AVG(nota_review), 2) AS nota_media
    FROM fato_pedidos
    WHERE flag_entregue = 1
    GROUP BY ano_mes
)
SELECT
    m.ano_mes,
    m.data_mes,
    COALESCE(a.pedidos_entregues, 0) AS pedidos_entregues,
    COALESCE(a.clientes_unicos, 0) AS clientes_unicos,
    COALESCE(a.itens_vendidos, 0) AS itens_vendidos,
    COALESCE(a.receita_produtos_nominal, 0.0) AS receita_produtos_nominal,
    COALESCE(a.frete_nominal, 0.0) AS frete_nominal,
    COALESCE(a.gmv_nominal, 0.0) AS gmv_nominal,
    COALESCE(a.gmv_real_ipca, 0.0) AS gmv_real_ipca,
    a.ticket_medio_real,
    CASE
        WHEN COALESCE(a.entregas_com_data, 0) > 0
        THEN ROUND(100.0 * a.entregas_no_prazo / a.entregas_com_data, 2)
        ELSE NULL
    END AS pct_no_prazo,
    a.prazo_medio_dias,
    a.nota_media,
    m.ipca_mensal_pct,
    m.ipca_acum_12m_pct,
    m.indice_ipca_base100,
    m.fator_deflator,
    m.selic_media,
    m.ptax_media
FROM dim_macro_mensal AS m
LEFT JOIN agg_mensal AS a ON a.ano_mes = m.ano_mes;


-- Desempenho por UF com população oficial IBGE e GMV por 100 mil habitantes.
CREATE VIEW vw_uf_sla AS
SELECT
    g.uf,
    g.nome,
    g.regiao,
    g.populacao_ibge,
    g.populacao_censo_2022,
    COUNT(p.order_id) AS pedidos_entregues,
    ROUND(SUM(p.valor_total_nominal), 2) AS gmv_nominal,
    ROUND(SUM(p.valor_total_real_ipca), 2) AS gmv_real_ipca,
    ROUND(SUM(p.valor_total_real_ipca) * 100000.0 / g.populacao_ibge, 2) AS gmv_real_100k_hab,
    ROUND(SUM(p.valor_frete), 2) AS frete_nominal,
    ROUND(100.0 * SUM(p.valor_frete) / NULLIF(SUM(p.valor_total_nominal), 0), 2) AS pct_frete_gmv,
    ROUND(AVG(p.valor_total_real_ipca), 2) AS ticket_medio_real,
    ROUND(AVG(p.dias_entrega), 2) AS prazo_medio_dias,
    ROUND(
        100.0 * SUM(CASE WHEN p.flag_atraso = 0 THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN p.data_entrega_real IS NOT NULL THEN 1 ELSE 0 END), 0),
        2
    ) AS pct_no_prazo,
    ROUND(AVG(CASE WHEN p.flag_atraso = 1 THEN p.dias_atraso END), 2) AS atraso_medio_dias,
    ROUND(AVG(p.nota_review), 2) AS nota_media
FROM dim_geo_uf AS g
LEFT JOIN fato_pedidos AS p
    ON p.uf_cliente = g.uf AND p.flag_entregue = 1
GROUP BY g.uf, g.nome, g.regiao, g.populacao_ibge, g.populacao_censo_2022;


-- Mix de pagamento principal sobre pedidos entregues.
CREATE VIEW vw_pagamentos_mix AS
WITH base AS (
    SELECT
        tipo_pagamento_principal AS tipo_pagamento,
        COUNT(*) AS pedidos,
        ROUND(SUM(valor_total_nominal), 2) AS gmv_nominal,
        ROUND(SUM(valor_total_real_ipca), 2) AS gmv_real_ipca,
        ROUND(AVG(CASE WHEN parcelas > 0 THEN parcelas END), 2) AS parcelas_medias
    FROM fato_pedidos
    WHERE flag_entregue = 1
    GROUP BY tipo_pagamento_principal
)
SELECT
    tipo_pagamento,
    pedidos,
    ROUND(100.0 * pedidos / SUM(pedidos) OVER (), 2) AS pct_pedidos,
    gmv_nominal,
    gmv_real_ipca,
    ROUND(100.0 * gmv_real_ipca / SUM(gmv_real_ipca) OVER (), 2) AS pct_gmv_real,
    parcelas_medias
FROM base;


-- Retenção de coorte mensal (clientes únicos entregues que recompram em M+1..M+6).
CREATE VIEW vw_coorte_retencao AS
WITH base_coorte AS (
    SELECT
        coorte_mes,
        COUNT(DISTINCT cliente_unico_id) AS clientes_coorte
    FROM fato_pedidos
    WHERE flag_entregue = 1 AND meses_desde_coorte = 0
    GROUP BY coorte_mes
),
retidos AS (
    SELECT
        coorte_mes,
        meses_desde_coorte,
        COUNT(DISTINCT cliente_unico_id) AS clientes_ativos
    FROM fato_pedidos
    WHERE flag_entregue = 1 AND meses_desde_coorte BETWEEN 0 AND 6
    GROUP BY coorte_mes, meses_desde_coorte
)
SELECT
    r.coorte_mes,
    b.clientes_coorte,
    r.meses_desde_coorte,
    r.clientes_ativos,
    ROUND(100.0 * r.clientes_ativos / b.clientes_coorte, 2) AS pct_retencao
FROM retidos AS r
JOIN base_coorte AS b ON b.coorte_mes = r.coorte_mes;


-- Concentração de receita entregue por decil de vendedores (D1 = top 10%).
CREATE VIEW vw_vendedores_decis AS
WITH base AS (
    SELECT
        v.decil_gmv,
        v.decil_ordem,
        COUNT(DISTINCT v.seller_id) AS vendedores,
        COUNT(DISTINCT i.order_id) AS pedidos,
        ROUND(SUM(i.valor_item_nominal), 2) AS gmv_nominal,
        ROUND(SUM(i.valor_item_real_ipca), 2) AS gmv_real_ipca
    FROM dim_vendedor AS v
    JOIN fato_itens_pedido AS i ON i.seller_id = v.seller_id AND i.flag_entregue = 1
    WHERE v.decil_ordem BETWEEN 1 AND 10
    GROUP BY v.decil_gmv, v.decil_ordem
)
SELECT
    decil_gmv,
    decil_ordem,
    vendedores,
    pedidos,
    gmv_nominal,
    gmv_real_ipca,
    ROUND(100.0 * gmv_real_ipca / SUM(gmv_real_ipca) OVER (), 2) AS pct_gmv_real,
    ROUND(
        100.0 * SUM(gmv_real_ipca) OVER (ORDER BY decil_ordem ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / SUM(gmv_real_ipca) OVER (),
        2
    ) AS pct_gmv_acumulado
FROM base;
