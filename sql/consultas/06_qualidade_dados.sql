-- Consulta 06: Auditoria de qualidade dos dados — anomalias reais encontradas na base Olist.
SELECT
    regra_id,
    regra,
    regra_en,
    tabela_origem,
    linhas_afetadas,
    base_referencia,
    pct_base,
    ROUND(100.0 * linhas_afetadas / SUM(linhas_afetadas) OVER (), 2) AS pct_das_anomalias,
    severidade,
    tratamento
FROM qualidade_auditoria
ORDER BY linhas_afetadas DESC, regra_id ASC;
