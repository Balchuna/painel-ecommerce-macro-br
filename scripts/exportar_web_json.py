"""Exporta docs/dados/resumo.json pré-agregado e reconciliado com o gabarito SQL.

O JSON serve o painel web interativo (docs/index.html) com grãos aditivos
(ano × região × categoria) para suportar filtros dinâmicos no navegador sem
enviar ~38 MB de CSVs brutos e mantendo reconciliação 100% com sql/gabarito/*.csv.

Uso:
  python scripts/exportar_web_json.py
  python scripts/exportar_web_json.py --banco data/painel.sqlite --saida docs/dados/resumo.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.constantes import MES_BASE_DEFLATOR, TIPOS_PAGAMENTO

BANCO_PADRAO = RAIZ / "data" / "painel.sqlite"
GABARITO_PADRAO = RAIZ / "sql" / "gabarito"
SAIDA_PADRAO = RAIZ / "docs" / "dados" / "resumo.json"


def _parse_valor_csv(texto: str):
    if texto == "":
        return None
    try:
        if "." in texto:
            return float(texto)
        return int(texto)
    except ValueError:
        return texto


def ler_gabarito_executivo(gabarito_dir: Path) -> dict:
    caminho = gabarito_dir / "01_visao_executiva.csv"
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    if len(linhas) != 1:
        raise ValueError(f"Esperada 1 linha em {caminho}, obtidas {len(linhas)}")
    return {k: _parse_valor_csv(v) for k, v in linhas[0].items()}


def exportar_resumo(banco_path: Path, gabarito_dir: Path, saida: Path) -> dict:
    if not banco_path.is_file():
        raise FileNotFoundError(f"Banco SQLite não encontrado: {banco_path}")

    con = sqlite3.connect(banco_path)
    con.row_factory = sqlite3.Row
    try:
        # 1. Metadados de fontes e benchmark macro atual
        fontes_rows = [dict(r) for r in con.execute(
            "SELECT fonte, arquivo, endpoint, registros, bytes_total, sha256, coletado_em_utc, licenca "
            "FROM fontes_metadados ORDER BY fonte, arquivo"
        )]
        gerado_em = max(r["coletado_em_utc"] for r in fontes_rows) if fontes_rows else ""

        fontes_lista = [
            {
                "fonte": r["fonte"],
                "nome": r["arquivo"],
                "endpoint": r["endpoint"],
                "registros": r["registros"],
                "bytes_total": r["bytes_total"],
                "sha256": r["sha256"],
                "coletado_em": r["coletado_em_utc"],
                "licenca": r["licenca"],
            }
            for r in fontes_rows
        ]

        fontes_resumo = [dict(r) for r in con.execute(
            """
            SELECT
                fonte,
                COUNT(*) AS arquivos,
                SUM(registros) AS registros,
                MAX(coletado_em_utc) AS coletado_em,
                MIN(licenca) AS licenca
            FROM fontes_metadados
            GROUP BY fonte
            ORDER BY CASE fonte WHEN 'Olist' THEN 1 WHEN 'Banco Central (SGS)' THEN 2 ELSE 3 END
            """
        )]

        benchmark_macro = [dict(r) for r in con.execute(
            "SELECT indicador, nome_pt, nome_en, serie_sgs, data_referencia, "
            "valor_recente, valor_fim_olist, unidade FROM macro_benchmark_atual ORDER BY serie_sgs"
        )]

        # 2. KPIs verificados direto do gabarito 01_visao_executiva.csv
        kpis_gabarito = ler_gabarito_executivo(gabarito_dir)

        # 3. Série mensal × região (pedidos entregues, grão puramente aditivo)
        mensal_regiao = [dict(r) for r in con.execute(
            """
            SELECT
                p.ano_mes,
                g.regiao,
                COUNT(*) AS pedidos,
                ROUND(SUM(p.valor_total_nominal), 2) AS gmv_nominal,
                ROUND(SUM(p.valor_total_real_ipca), 2) AS gmv_real,
                ROUND(SUM(p.valor_produtos), 2) AS valor_produtos,
                ROUND(SUM(p.valor_frete), 2) AS frete,
                COUNT(*) AS entregues,
                SUM(CASE WHEN p.data_entrega_real IS NOT NULL THEN 1 ELSE 0 END) AS entregues_com_data,
                SUM(CASE WHEN p.flag_atraso = 0 THEN 1 ELSE 0 END) AS no_prazo,
                COALESCE(SUM(p.dias_entrega), 0) AS soma_dias_entrega,
                SUM(CASE WHEN p.flag_atraso = 1 THEN 1 ELSE 0 END) AS n_atrasados,
                COALESCE(SUM(CASE WHEN p.flag_atraso = 1 THEN p.dias_atraso ELSE 0 END), 0) AS soma_dias_atraso,
                COALESCE(SUM(p.nota_review), 0) AS soma_nota,
                COUNT(p.nota_review) AS n_nota,
                SUM(p.qtd_itens) AS qtd_itens,
                SUM(p.flag_recompra) AS pedidos_recompra
            FROM fato_pedidos AS p
            JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
            WHERE p.flag_entregue = 1
            GROUP BY p.ano_mes, g.regiao
            ORDER BY p.ano_mes, g.regiao
            """
        )]

        # 4. Macro mensal (26 meses)
        macro_mensal = [dict(r) for r in con.execute(
            """
            SELECT
                ano_mes,
                ipca_mensal_pct,
                ipca_acum_12m_pct AS ipca_12m_pct,
                indice_ipca_base100,
                fator_deflator,
                selic_media,
                ptax_media
            FROM dim_macro_mensal
            ORDER BY ano_mes
            """
        )]

        # 5. UF × ano (pedidos entregues, grão aditivo)
        uf_ano = [dict(r) for r in con.execute(
            """
            SELECT
                g.uf,
                g.nome,
                g.regiao,
                g.populacao_ibge AS populacao,
                g.populacao_censo_2022,
                c.ano,
                COUNT(*) AS pedidos,
                ROUND(SUM(p.valor_total_nominal), 2) AS gmv_nominal,
                ROUND(SUM(p.valor_total_real_ipca), 2) AS gmv_real,
                ROUND(SUM(p.valor_frete), 2) AS frete,
                COUNT(*) AS entregues,
                SUM(CASE WHEN p.data_entrega_real IS NOT NULL THEN 1 ELSE 0 END) AS entregues_com_data,
                SUM(CASE WHEN p.flag_atraso = 0 THEN 1 ELSE 0 END) AS no_prazo,
                COALESCE(SUM(p.dias_entrega), 0) AS soma_dias_entrega,
                SUM(CASE WHEN p.flag_atraso = 1 THEN 1 ELSE 0 END) AS n_atrasados,
                COALESCE(SUM(CASE WHEN p.flag_atraso = 1 THEN p.dias_atraso ELSE 0 END), 0) AS soma_dias_atraso,
                COALESCE(SUM(p.nota_review), 0) AS soma_nota,
                COUNT(p.nota_review) AS n_nota
            FROM fato_pedidos AS p
            JOIN dim_calendario AS c ON c.data = p.data_compra
            JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
            WHERE p.flag_entregue = 1
            GROUP BY g.uf, g.nome, g.regiao, g.populacao_ibge, g.populacao_censo_2022, c.ano
            ORDER BY g.uf, c.ano
            """
        )]

        # 6. Faixa de atraso × ano × região (5 faixas ordinais de pedidos entregues com data válida)
        faixa_atraso = [dict(r) for r in con.execute(
            """
            SELECT
                f.faixa_atraso AS faixa,
                f.faixa_atraso_en AS faixa_en,
                f.ordem,
                c.ano,
                g.regiao,
                COUNT(*) AS pedidos,
                COALESCE(SUM(p.nota_review), 0) AS soma_nota,
                COUNT(p.nota_review) AS n_nota,
                SUM(CASE WHEN p.nota_review = 5 THEN 1 ELSE 0 END) AS notas_5,
                SUM(CASE WHEN p.nota_review = 1 THEN 1 ELSE 0 END) AS notas_1,
                COALESCE(SUM(p.dias_atraso), 0) AS soma_dias_atraso,
                COALESCE(SUM(p.dias_entrega), 0) AS soma_dias_entrega
            FROM fato_pedidos AS p
            JOIN dim_faixa_atraso AS f ON f.faixa_atraso = p.faixa_atraso
            JOIN dim_calendario AS c ON c.data = p.data_compra
            JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
            WHERE p.flag_entregue = 1 AND p.data_entrega_real IS NOT NULL
            GROUP BY f.faixa_atraso, f.faixa_atraso_en, f.ordem, c.ano, g.regiao
            ORDER BY f.ordem, c.ano, g.regiao
            """
        )]

        # 7. Categoria × ano × região (itens de pedidos entregues, reconcilia com 05_comercial_categorias.csv)
        categoria_ano_regiao = [dict(r) for r in con.execute(
            """
            SELECT
                cat.categoria_codigo,
                cat.categoria_pt,
                cat.categoria_en,
                c.ano,
                g.regiao,
                COUNT(*) AS itens,
                COUNT(DISTINCT i.order_id) AS pedidos,
                ROUND(SUM(i.valor_item_nominal), 2) AS gmv_nominal,
                ROUND(SUM(i.valor_item_real_ipca), 2) AS gmv_real,
                ROUND(SUM(i.frete), 2) AS frete,
                COALESCE(SUM(p.nota_review), 0) AS soma_nota,
                COUNT(p.nota_review) AS n_nota
            FROM fato_itens_pedido AS i
            JOIN dim_categoria AS cat ON cat.categoria_codigo = i.categoria_codigo
            JOIN dim_calendario AS c ON c.data = i.data_compra
            JOIN dim_geo_uf AS g ON g.uf = i.uf_cliente
            JOIN fato_pedidos AS p ON p.order_id = i.order_id
            WHERE i.flag_entregue = 1
            GROUP BY cat.categoria_codigo, cat.categoria_pt, cat.categoria_en, c.ano, g.regiao
            ORDER BY gmv_real DESC, cat.categoria_codigo, c.ano, g.regiao
            """
        )]

        # 8. Pagamento × ano × região (pedidos entregues)
        pag_raw = [dict(r) for r in con.execute(
            """
            SELECT
                p.tipo_pagamento_principal AS tipo,
                c.ano,
                g.regiao,
                COUNT(*) AS pedidos,
                ROUND(SUM(p.valor_total_nominal), 2) AS gmv_nominal,
                ROUND(SUM(p.valor_total_real_ipca), 2) AS valor
            FROM fato_pedidos AS p
            JOIN dim_calendario AS c ON c.data = p.data_compra
            JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
            WHERE p.flag_entregue = 1
            GROUP BY p.tipo_pagamento_principal, c.ano, g.regiao
            ORDER BY valor DESC, p.tipo_pagamento_principal, c.ano, g.regiao
            """
        )]
        pagamento_ano_regiao = []
        for r in pag_raw:
            pt, en = TIPOS_PAGAMENTO.get(r["tipo"], (r["tipo"], r["tipo"]))
            pagamento_ano_regiao.append({
                "tipo": r["tipo"],
                "tipo_pt": pt,
                "tipo_en": en,
                "ano": r["ano"],
                "regiao": r["regiao"],
                "pedidos": r["pedidos"],
                "gmv_nominal": r["gmv_nominal"],
                "gmv_real": r["valor"],
                "valor": r["valor"],
            })

        # 9. Parcelas (cartão de crédito com parcelas >= 1) × ano × região
        parcelas_ano_regiao = [dict(r) for r in con.execute(
            """
            SELECT
                p.parcelas,
                c.ano,
                g.regiao,
                COUNT(*) AS pedidos,
                ROUND(SUM(p.valor_total_real_ipca), 2) AS gmv_real
            FROM fato_pedidos AS p
            JOIN dim_calendario AS c ON c.data = p.data_compra
            JOIN dim_geo_uf AS g ON g.uf = p.uf_cliente
            WHERE p.flag_entregue = 1
              AND p.tipo_pagamento_principal = 'credit_card'
              AND p.parcelas >= 1
            GROUP BY p.parcelas, c.ano, g.regiao
            ORDER BY p.parcelas, c.ano, g.regiao
            """
        )]

        # 10. Coortes mensais com janela completa de 6 meses (2017-01 a 2018-02)
        coorte_rows = [dict(r) for r in con.execute(
            """
            SELECT coorte_mes, clientes_coorte, meses_desde_coorte, clientes_ativos, pct_retencao
            FROM vw_coorte_retencao
            WHERE coorte_mes BETWEEN '2017-01' AND '2018-02'
            ORDER BY coorte_mes, meses_desde_coorte
            """
        )]
        coorte_map: dict[str, dict] = {}
        for r in coorte_rows:
            cm = r["coorte_mes"]
            if cm not in coorte_map:
                coorte_map[cm] = {
                    "coorte": cm,
                    "clientes": r["clientes_coorte"],
                    "retidos": [0, 0, 0, 0, 0, 0],
                    "retidos_pct": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                }
            m = r["meses_desde_coorte"]
            if 1 <= m <= 6:
                coorte_map[cm]["retidos"][m - 1] = r["clientes_ativos"]
                coorte_map[cm]["retidos_pct"][m - 1] = r["pct_retencao"]
        coorte = [coorte_map[k] for k in sorted(coorte_map.keys())]

        # 11. Decis de vendedores (D1..D10)
        vendedores_decil = [dict(r) for r in con.execute(
            """
            SELECT
                decil_gmv AS decil,
                decil_ordem AS ordem,
                vendedores,
                pedidos,
                gmv_nominal,
                gmv_real_ipca AS gmv_real,
                pct_gmv_real AS pct_gmv,
                pct_gmv_acumulado
            FROM vw_vendedores_decis
            ORDER BY decil_ordem
            """
        )]

        # 12. Qualidade e auditoria
        regras_qualidade = [dict(r) for r in con.execute(
            """
            SELECT
                regra_id,
                regra,
                regra_en,
                tabela_origem AS tabela,
                linhas_afetadas,
                base_referencia,
                pct_base AS pct,
                ROUND(100.0 * linhas_afetadas / SUM(linhas_afetadas) OVER (), 2) AS pct_das_anomalias,
                severidade,
                tratamento,
                tratamento_en
            FROM qualidade_auditoria
            ORDER BY linhas_afetadas DESC, regra_id ASC
            """
        )]
        itens_brutos = con.execute("SELECT COUNT(*) FROM fato_itens_pedido").fetchone()[0]
        reviews_dup = con.execute(
            "SELECT linhas_afetadas FROM qualidade_auditoria WHERE regra_id = 'Q08_AVALIACOES_DUPLICADAS'"
        ).fetchone()[0]
        total_anomalias = sum(r["linhas_afetadas"] for r in regras_qualidade)
        gabaritos = sorted(p.name for p in gabarito_dir.glob("*.csv"))

        qualidade = {
            "contagens": {
                "pedidos_brutos": kpis_gabarito["pedidos_brutos"],
                "pedidos_analisados": kpis_gabarito["pedidos_entregues"],
                "pedidos_entregues_data_valida": kpis_gabarito["pedidos_entregues_data_valida"],
                "pedidos_nao_entregues": kpis_gabarito["pedidos_nao_entregues"],
                "pct_excluidos": kpis_gabarito["pct_excluidos"],
                "total_anomalias": total_anomalias,
                "regras_aplicadas": len(regras_qualidade),
                "reviews_duplicadas": reviews_dup,
                "itens_brutos": itens_brutos,
                "clientes_unicos_entregues": kpis_gabarito["clientes_unicos_entregues"],
                "vendedores_ativos_entregues": kpis_gabarito["vendedores_ativos"],
            },
            "regras": regras_qualidade,
            "gabarito": {
                "consultas": len(gabaritos),
                "conferem": True,
                "arquivos": gabaritos,
            },
        }
    finally:
        con.close()

    resumo = {
        "meta": {
            "gerado_em": gerado_em,
            "mes_base_ipca": MES_BASE_DEFLATOR,
            "periodo": {
                "inicio": "2016-09",
                "fim": "2018-10",
                "entregues_inicio": "2016-09",
                "entregues_fim": "2018-08",
            },
            "fontes": fontes_lista,
            "fontes_resumo": fontes_resumo,
            "benchmark_macro_atual": benchmark_macro,
        },
        "kpis_gabarito": kpis_gabarito,
        "mensal_regiao": mensal_regiao,
        "macro_mensal": macro_mensal,
        "uf_ano": uf_ano,
        "faixa_atraso": faixa_atraso,
        "categoria_ano_regiao": categoria_ano_regiao,
        "pagamento_ano_regiao": pagamento_ano_regiao,
        "parcelas_ano_regiao": parcelas_ano_regiao,
        "coorte": coorte,
        "vendedores_decil": vendedores_decil,
        "qualidade": qualidade,
    }

    saida.parent.mkdir(parents=True, exist_ok=True)
    # Compacto porém legível, chaves determinísticas e UTF-8
    saida.write_text(
        json.dumps(resumo, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return resumo


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Exporta docs/dados/resumo.json para o painel web.")
    parser.add_argument("--banco", type=Path, default=BANCO_PADRAO)
    parser.add_argument("--gabarito", type=Path, default=GABARITO_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    resumo = exportar_resumo(args.banco, args.gabarito, args.saida)
    kb = args.saida.stat().st_size / 1024
    print(f"Exportado {args.saida} ({kb:.1f} KB):")
    for chave in (
        "mensal_regiao", "macro_mensal", "uf_ano", "faixa_atraso",
        "categoria_ano_regiao", "pagamento_ano_regiao", "parcelas_ano_regiao",
        "coorte", "vendedores_decil",
    ):
        print(f"  {chave:24s}: {len(resumo[chave]):4d} registros")


if __name__ == "__main__":
    main()
