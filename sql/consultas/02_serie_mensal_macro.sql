-- Consulta 02: Série mensal de GMV nominal vs real (IPCA) com funções de janela
-- (MoM %, YoY %, média móvel de 3 meses e acumulado) e cenário macro BCB SGS.
WITH serie AS (
    SELECT
        ano_mes,
        pedidos_entregues,
        clientes_unicos,
        gmv_nominal,
        gmv_real_ipca,
        ticket_medio_real,
        pct_no_prazo,
        prazo_medio_dias,
        nota_media,
        ipca_mensal_pct,
        ipca_acum_12m_pct,
        fator_deflator,
        selic_media,
        ptax_media,
        LAG(gmv_real_ipca, 1) OVER (ORDER BY ano_mes) AS gmv_real_mes_anterior,
        LAG(gmv_real_ipca, 12) OVER (ORDER BY ano_mes) AS gmv_real_ano_anterior,
        ROUND(
            AVG(gmv_real_ipca) OVER (ORDER BY ano_mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),
            2
        ) AS mm3m_gmv_real,
        ROUND(
            SUM(gmv_real_ipca) OVER (ORDER BY ano_mes ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
            2
        ) AS gmv_real_acumulado
    FROM vw_serie_mensal_macro
)
SELECT
    ano_mes,
    pedidos_entregues,
    clientes_unicos,
    gmv_nominal,
    gmv_real_ipca,
    CASE
        WHEN gmv_real_mes_anterior > 0 AND gmv_real_ipca > 0
        THEN ROUND(100.0 * (gmv_real_ipca - gmv_real_mes_anterior) / gmv_real_mes_anterior, 2)
        ELSE NULL
    END AS mom_gmv_real_pct,
    CASE
        WHEN gmv_real_ano_anterior > 0 AND gmv_real_ipca > 0
        THEN ROUND(100.0 * (gmv_real_ipca - gmv_real_ano_anterior) / gmv_real_ano_anterior, 2)
        ELSE NULL
    END AS yoy_gmv_real_pct,
    mm3m_gmv_real,
    gmv_real_acumulado,
    ticket_medio_real,
    pct_no_prazo,
    prazo_medio_dias,
    nota_media,
    ipca_mensal_pct,
    ipca_acum_12m_pct,
    fator_deflator,
    selic_media,
    ptax_media
FROM serie
ORDER BY ano_mes;
