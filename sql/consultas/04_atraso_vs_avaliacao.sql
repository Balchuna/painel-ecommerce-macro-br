-- Consulta 04: Impacto do atraso logístico na avaliação do cliente (1 a 5 estrelas).
-- Considera pedidos entregues com data real válida (96.470 pedidos), nas 5 faixas ordinais.
WITH faixas AS (
    SELECT
        f.ordem,
        f.faixa_atraso,
        f.faixa_atraso_en,
        COUNT(*) AS pedidos,
        COUNT(p.nota_review) AS pedidos_avaliados,
        ROUND(AVG(p.nota_review), 2) AS nota_media,
        ROUND(
            100.0 * SUM(CASE WHEN p.nota_review = 5 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.nota_review), 0),
            2
        ) AS pct_nota_5,
        ROUND(
            100.0 * SUM(CASE WHEN p.nota_review = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.nota_review), 0),
            2
        ) AS pct_nota_1,
        ROUND(AVG(p.dias_entrega), 2) AS prazo_medio_dias,
        ROUND(AVG(p.dias_atraso), 2) AS atraso_medio_dias
    FROM fato_pedidos AS p
    JOIN dim_faixa_atraso AS f ON f.faixa_atraso = p.faixa_atraso
    WHERE p.flag_entregue = 1 AND p.data_entrega_real IS NOT NULL
    GROUP BY f.ordem, f.faixa_atraso, f.faixa_atraso_en
)
SELECT
    ordem,
    faixa_atraso,
    faixa_atraso_en,
    pedidos,
    ROUND(100.0 * pedidos / SUM(pedidos) OVER (), 2) AS pct_pedidos,
    pedidos_avaliados,
    nota_media,
    ROUND(nota_media - FIRST_VALUE(nota_media) OVER (ORDER BY ordem), 2) AS delta_nota_vs_no_prazo,
    pct_nota_5,
    pct_nota_1,
    prazo_medio_dias,
    atraso_medio_dias
FROM faixas
ORDER BY ordem;
