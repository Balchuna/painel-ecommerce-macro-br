-- Consulta 01: Visão executiva consolidada (cartões de capa das 4 páginas do painel).
-- Todas as métricas comerciais, de SLA e satisfação consideram apenas pedidos entregues (flag_entregue = 1).
-- Valores reais em R$ constantes de 2018-10 (IPCA BCB SGS 433).
WITH base_bruta AS (
    SELECT
        COUNT(*) AS pedidos_brutos,
        SUM(flag_entregue) AS pedidos_entregues,
        SUM(CASE WHEN flag_entregue = 1 AND data_entrega_real IS NOT NULL THEN 1 ELSE 0 END)
            AS pedidos_entregues_data_valida,
        SUM(CASE WHEN flag_entregue = 0 THEN 1 ELSE 0 END) AS pedidos_nao_entregues
    FROM fato_pedidos
),
entregues AS (
    SELECT
        COUNT(*) AS pedidos,
        COUNT(DISTINCT cliente_unico_id) AS clientes_unicos,
        COUNT(DISTINCT CASE WHEN flag_recompra = 1 THEN cliente_unico_id END) AS clientes_recompra,
        COUNT(DISTINCT CASE WHEN meses_desde_coorte BETWEEN 1 AND 6 THEN cliente_unico_id END)
            AS clientes_retidos_6m,
        SUM(qtd_itens) AS itens_vendidos,
        ROUND(SUM(valor_produtos), 2) AS receita_produtos_nominal,
        ROUND(SUM(valor_frete), 2) AS frete_nominal,
        ROUND(SUM(valor_total_nominal), 2) AS gmv_nominal,
        ROUND(SUM(valor_total_real_ipca), 2) AS gmv_real_ipca,
        ROUND(AVG(valor_total_nominal), 2) AS ticket_medio_nominal,
        ROUND(AVG(valor_total_real_ipca), 2) AS ticket_medio_real,
        ROUND(AVG(nota_review), 2) AS nota_media,
        ROUND(AVG(CASE WHEN flag_atraso = 0 THEN nota_review END), 2) AS nota_media_no_prazo,
        ROUND(AVG(CASE WHEN flag_atraso = 1 THEN nota_review END), 2) AS nota_media_atrasado,
        ROUND(AVG(dias_entrega), 2) AS prazo_medio_dias,
        ROUND(
            100.0 * SUM(CASE WHEN flag_atraso = 0 THEN 1 ELSE 0 END)
            / SUM(CASE WHEN data_entrega_real IS NOT NULL THEN 1 ELSE 0 END),
            2
        ) AS pct_no_prazo,
        ROUND(AVG(CASE WHEN flag_atraso = 1 THEN dias_atraso END), 2) AS atraso_medio_quando_atrasa,
        ROUND(
            100.0 * SUM(CASE WHEN tipo_pagamento_principal = 'credit_card' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) AS pct_pedidos_cartao,
        ROUND(
            100.0 * SUM(CASE WHEN tipo_pagamento_principal = 'credit_card' THEN valor_total_real_ipca ELSE 0 END)
            / SUM(valor_total_real_ipca),
            2
        ) AS pct_gmv_cartao,
        ROUND(
            100.0 * SUM(CASE WHEN tipo_pagamento_principal = 'credit_card' AND parcelas > 1 THEN 1 ELSE 0 END)
            / SUM(CASE WHEN tipo_pagamento_principal = 'credit_card' AND parcelas > 0 THEN 1 ELSE 0 END),
            2
        ) AS pct_cartao_parcelado,
        ROUND(
            AVG(CASE WHEN tipo_pagamento_principal = 'credit_card' AND parcelas > 0 THEN parcelas END),
            2
        ) AS parcelas_medias_cartao
    FROM fato_pedidos
    WHERE flag_entregue = 1
),
comparativo_anual AS (
    SELECT
        ROUND(SUM(CASE WHEN c.ano = 2017 THEN p.valor_total_nominal ELSE 0 END), 2) AS gmv_nom_2017_cheio,
        ROUND(SUM(CASE WHEN c.ano = 2017 THEN p.valor_total_real_ipca ELSE 0 END), 2) AS gmv_real_2017_cheio,
        ROUND(SUM(CASE WHEN c.ano = 2017 AND c.mes <= 8 THEN p.valor_total_nominal ELSE 0 END), 2) AS gmv_nom_2017_jan_ago,
        ROUND(SUM(CASE WHEN c.ano = 2017 AND c.mes <= 8 THEN p.valor_total_real_ipca ELSE 0 END), 2) AS gmv_real_2017_jan_ago,
        ROUND(SUM(CASE WHEN c.ano = 2018 AND c.mes <= 8 THEN p.valor_total_nominal ELSE 0 END), 2) AS gmv_nom_2018_jan_ago,
        ROUND(SUM(CASE WHEN c.ano = 2018 AND c.mes <= 8 THEN p.valor_total_real_ipca ELSE 0 END), 2) AS gmv_real_2018_jan_ago
    FROM fato_pedidos AS p
    JOIN dim_calendario AS c ON c.data = p.data_compra
    WHERE p.flag_entregue = 1
),
vendedores AS (
    SELECT
        SUM(vendedores) AS vendedores_ativos,
        MAX(CASE WHEN decil_ordem = 1 THEN pct_gmv_real END) AS pct_gmv_top10_vendedores
    FROM vw_vendedores_decis
),
pareto_cat AS (
    WITH cat_gmv AS (
        SELECT
            categoria_codigo,
            SUM(valor_item_real_ipca) AS gmv_real
        FROM fato_itens_pedido
        WHERE flag_entregue = 1
        GROUP BY categoria_codigo
    ),
    cat_acum AS (
        SELECT
            categoria_codigo,
            100.0 * COALESCE(
                SUM(gmv_real) OVER (
                    ORDER BY gmv_real DESC, categoria_codigo ASC
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                ),
                0.0
            ) / SUM(gmv_real) OVER () AS pct_acum_anterior
        FROM cat_gmv
    )
    SELECT COUNT(*) AS categorias_80pct_gmv
    FROM cat_acum
    WHERE pct_acum_anterior < 80.0
),
macro_extremos AS (
    SELECT
        MAX(CASE WHEN ano_mes = '2016-09' THEN selic_media END) AS selic_inicio_2016_09,
        MAX(CASE WHEN ano_mes = '2018-10' THEN selic_media END) AS selic_fim_2018_10,
        MAX(CASE WHEN ano_mes = '2016-09' THEN ipca_acum_12m_pct END) AS ipca_12m_inicio_2016_09,
        MAX(CASE WHEN ano_mes = '2018-10' THEN ipca_acum_12m_pct END) AS ipca_12m_fim_2018_10
    FROM dim_macro_mensal
)
SELECT
    b.pedidos_brutos,
    b.pedidos_entregues,
    b.pedidos_entregues_data_valida,
    b.pedidos_nao_entregues,
    ROUND(100.0 * b.pedidos_nao_entregues / b.pedidos_brutos, 2) AS pct_excluidos,
    e.clientes_unicos AS clientes_unicos_entregues,
    e.clientes_recompra,
    ROUND(100.0 * e.clientes_recompra / e.clientes_unicos, 2) AS pct_clientes_recompra,
    ROUND(100.0 * e.clientes_retidos_6m / e.clientes_unicos, 2) AS pct_retencao_6m,
    e.itens_vendidos AS itens_vendidos_entregues,
    ROUND(1.0 * e.itens_vendidos / e.pedidos, 2) AS itens_por_pedido,
    e.gmv_nominal,
    e.gmv_real_ipca,
    e.receita_produtos_nominal,
    e.frete_nominal,
    ROUND(100.0 * e.frete_nominal / e.gmv_nominal, 2) AS pct_frete_gmv,
    e.ticket_medio_nominal,
    e.ticket_medio_real,
    e.nota_media,
    e.nota_media_no_prazo,
    e.nota_media_atrasado,
    ROUND(e.nota_media_no_prazo - e.nota_media_atrasado, 2) AS queda_nota_atraso,
    e.prazo_medio_dias,
    e.pct_no_prazo,
    e.atraso_medio_quando_atrasa,
    e.pct_pedidos_cartao,
    e.pct_gmv_cartao,
    e.pct_cartao_parcelado,
    e.parcelas_medias_cartao,
    v.vendedores_ativos,
    v.pct_gmv_top10_vendedores,
    p.categorias_80pct_gmv,
    a.gmv_real_2017_cheio,
    a.gmv_real_2018_jan_ago,
    ROUND(100.0 * (a.gmv_real_2018_jan_ago - a.gmv_real_2017_cheio) / a.gmv_real_2017_cheio, 2)
        AS var_gmv_real_2018_vs_2017_cheio_pct,
    ROUND(100.0 * (a.gmv_nom_2018_jan_ago - a.gmv_nom_2017_cheio) / a.gmv_nom_2017_cheio, 2)
        AS var_gmv_nominal_2018_vs_2017_cheio_pct,
    a.gmv_nom_2017_jan_ago,
    a.gmv_nom_2018_jan_ago,
    ROUND(100.0 * (a.gmv_nom_2018_jan_ago - a.gmv_nom_2017_jan_ago) / a.gmv_nom_2017_jan_ago, 2)
        AS var_gmv_nominal_yoy_jan_ago_pct,
    a.gmv_real_2017_jan_ago,
    ROUND(100.0 * (a.gmv_real_2018_jan_ago - a.gmv_real_2017_jan_ago) / a.gmv_real_2017_jan_ago, 2)
        AS var_gmv_real_yoy_jan_ago_pct,
    ROUND(
        (100.0 * (a.gmv_nom_2018_jan_ago - a.gmv_nom_2017_jan_ago) / a.gmv_nom_2017_jan_ago)
        - (100.0 * (a.gmv_real_2018_jan_ago - a.gmv_real_2017_jan_ago) / a.gmv_real_2017_jan_ago),
        2
    ) AS efeito_inflacao_yoy_pp,
    m.selic_inicio_2016_09,
    m.selic_fim_2018_10,
    m.ipca_12m_inicio_2016_09,
    m.ipca_12m_fim_2018_10
FROM base_bruta AS b
CROSS JOIN entregues AS e
CROSS JOIN comparativo_anual AS a
CROSS JOIN vendedores AS v
CROSS JOIN pareto_cat AS p
CROSS JOIN macro_extremos AS m;
