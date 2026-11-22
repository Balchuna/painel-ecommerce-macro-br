-- Consulta 05: Pareto comercial de categorias sobre itens de pedidos entregues.
-- Usa funções de janela para ranking, participação percentual e acumulado 80/20.
WITH base AS (
    SELECT
        c.categoria_codigo,
        c.categoria_pt,
        c.categoria_en,
        COUNT(DISTINCT i.order_id) AS pedidos_entregues,
        COUNT(*) AS itens_vendidos,
        ROUND(SUM(i.valor_item_nominal), 2) AS gmv_nominal,
        ROUND(SUM(i.valor_item_real_ipca), 2) AS gmv_real_ipca,
        ROUND(AVG(i.preco), 2) AS preco_medio_item,
        ROUND(100.0 * SUM(i.frete) / NULLIF(SUM(i.valor_item_nominal), 0), 2) AS pct_frete_gmv,
        ROUND(AVG(p.nota_review), 2) AS nota_media
    FROM fato_itens_pedido AS i
    JOIN dim_categoria AS c ON c.categoria_codigo = i.categoria_codigo
    JOIN fato_pedidos AS p ON p.order_id = i.order_id
    WHERE i.flag_entregue = 1
    GROUP BY c.categoria_codigo, c.categoria_pt, c.categoria_en
),
pareto AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY gmv_real_ipca DESC, categoria_codigo ASC) AS ranking,
        *,
        ROUND(100.0 * gmv_real_ipca / SUM(gmv_real_ipca) OVER (), 2) AS pct_gmv_real,
        ROUND(
            100.0 * SUM(gmv_real_ipca) OVER (
                ORDER BY gmv_real_ipca DESC, categoria_codigo ASC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) / SUM(gmv_real_ipca) OVER (),
            2
        ) AS pct_gmv_acumulado,
        100.0 * COALESCE(
            SUM(gmv_real_ipca) OVER (
                ORDER BY gmv_real_ipca DESC, categoria_codigo ASC
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ),
            0.0
        ) / SUM(gmv_real_ipca) OVER () AS pct_acum_anterior
    FROM base
)
SELECT
    ranking,
    categoria_codigo,
    categoria_pt,
    categoria_en,
    pedidos_entregues,
    itens_vendidos,
    gmv_nominal,
    gmv_real_ipca,
    pct_gmv_real,
    pct_gmv_acumulado,
    CASE WHEN pct_acum_anterior < 80.0 THEN 1 ELSE 0 END AS no_pareto_80,
    preco_medio_item,
    pct_frete_gmv,
    nota_media
FROM pareto
ORDER BY ranking;
