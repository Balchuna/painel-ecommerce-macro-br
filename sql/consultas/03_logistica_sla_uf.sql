-- Consulta 03: Logística, SLA e penetração de e-commerce por UF (IBGE).
-- Ranking de GMV real por 100 mil habitantes e participação no total nacional via funções de janela.
WITH ufs AS (
    SELECT * FROM vw_uf_sla
)
SELECT
    RANK() OVER (ORDER BY gmv_real_100k_hab DESC, uf ASC) AS rank_gmv_100k,
    uf,
    nome,
    regiao,
    populacao_ibge,
    populacao_censo_2022,
    pedidos_entregues,
    gmv_nominal,
    gmv_real_ipca,
    ROUND(100.0 * gmv_real_ipca / SUM(gmv_real_ipca) OVER (), 2) AS pct_participacao_gmv,
    ROUND(
        100.0 * SUM(gmv_real_ipca) OVER (PARTITION BY regiao) / SUM(gmv_real_ipca) OVER (),
        2
    ) AS pct_gmv_regiao,
    gmv_real_100k_hab,
    pct_frete_gmv,
    ticket_medio_real,
    prazo_medio_dias,
    pct_no_prazo,
    atraso_medio_dias,
    nota_media
FROM ufs
ORDER BY gmv_real_100k_hab DESC, uf ASC;
