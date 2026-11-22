"""Verificação ponta a ponta no Power BI Desktop (TOM + ADOMD): atualiza e confere DAX vs SQL.

Marcado com @pytest.mark.desktop — roda apenas quando o usuário passa `pytest --desktop`
em uma máquina Windows com Power BI Desktop instalado.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from modelo_powerbi import ModeloPowerBI, desktop_instalado

RAIZ = Path(__file__).resolve().parents[1]
LIMPA = RAIZ / "data" / "limpa"
GABARITO = RAIZ / "sql" / "gabarito"

pytestmark = pytest.mark.desktop


@pytest.fixture(scope="module")
def modelo(tmp_path_factory):
    if not desktop_instalado():
        pytest.skip("Power BI Desktop não instalado neste computador")
    pasta = tmp_path_factory.mktemp("pbi_desktop")
    m = ModeloPowerBI(LIMPA, pasta)
    try:
        yield m
    finally:
        m.fechar()


def test_desktop_atualiza_tabelas_e_relacionamentos_ativos(modelo):
    tabelas = set(modelo.tabelas())
    assert {
        "dim_calendario",
        "dim_macro_mensal",
        "dim_geo_uf",
        "dim_categoria",
        "dim_faixa_atraso",
        "dim_vendedor",
        "fato_pedidos",
        "fato_itens_pedido",
        "qualidade_auditoria",
        "fontes_metadados",
        "macro_benchmark_atual",
        "Medidas",
    }.issubset(tabelas)
    ligacoes = modelo.ligacoes()
    assert len(ligacoes) == 9
    assert all(ativa for _, _, ativa in ligacoes)


def test_desktop_dax_visao_executiva_bate_100_porcento_com_sql_01(modelo):
    sql01 = pd.read_csv(GABARITO / "01_visao_executiva.csv").iloc[0]
    (row,) = modelo.consultar("""
EVALUATE
ROW (
    "pedidos_brutos", [Pedidos Brutos],
    "pedidos_entregues", [Pedidos Entregues],
    "pedidos_nao_entregues", [Pedidos Não Entregues],
    "pct_excluidos", [% Excluídos da Análise] * 100,
    "clientes_unicos_entregues", [Clientes Únicos],
    "clientes_recompra", [Clientes Recompra],
    "pct_clientes_recompra", [% Clientes Recompra] * 100,
    "itens_vendidos_entregues", [Itens Vendidos],
    "itens_por_pedido", [Itens por Pedido],
    "gmv_nominal", [GMV Nominal],
    "gmv_real_ipca", [GMV Real IPCA],
    "receita_produtos_nominal", [Receita Produtos Nominal],
    "frete_nominal", [Frete Nominal],
    "pct_frete_gmv", [Frete % do GMV] * 100,
    "ticket_medio_nominal", [Ticket Médio Nominal],
    "ticket_medio_real", [Ticket Médio Real],
    "nota_media", [Nota Média],
    "nota_media_no_prazo", [Nota Média no Prazo],
    "nota_media_atrasado", [Nota Média Atrasado],
    "prazo_medio_dias", [Prazo Médio Entrega (d)],
    "pct_no_prazo", [% Entregas no Prazo] * 100,
    "atraso_medio_quando_atrasa", [Atraso Médio quando Atrasa (d)],
    "pct_pedidos_cartao", [% Pedidos Cartão] * 100,
    "pct_cartao_parcelado", [% Cartão Parcelado] * 100,
    "parcelas_medias_cartao", [Parcelas Médias (Cartão)],
    "vendedores_ativos", [Vendedores Ativos],
    "pct_gmv_top10_vendedores", [% GMV Top 10% Vendedores] * 100,
    "var_gmv_nominal_yoy_jan_ago_pct", [GMV Nominal YoY Jan-Ago %] * 100,
    "var_gmv_real_yoy_jan_ago_pct", [GMV Real YoY Jan-Ago %] * 100,
    "efeito_inflacao_yoy_pp", [Efeito Inflação YoY (p.p.)]
)
""")
    for campo, valor_dax in row.items():
        esperado = float(sql01[campo])
        assert float(valor_dax) == pytest.approx(esperado, abs=0.02), (
            f"Divergência DAX vs SQL em {campo}: DAX={valor_dax} vs SQL={esperado}"
        )


def test_desktop_dax_serie_mensal_e_inteligencia_temporal_batem_com_sql_02(modelo):
    sql02 = pd.read_csv(GABARITO / "02_serie_mensal_macro.csv").set_index("ano_mes")
    linhas = modelo.consultar("""
EVALUATE
SUMMARIZECOLUMNS (
    dim_calendario[ano_mes],
    "pedidos", [Pedidos Entregues] + 0,
    "gmv_nominal", [GMV Nominal] + 0,
    "gmv_real", [GMV Real IPCA] + 0,
    "mom_pct", [GMV Real MoM %] * 100,
    "yoy_pct", [GMV Real YoY %] * 100,
    "mm3m", [GMV Real Média Móvel 3m],
    "acum", [GMV Real Acumulado],
    "selic", [Selic Média %] * 100,
    "ipca_12m", [IPCA 12m %] * 100
)
ORDER BY dim_calendario[ano_mes]
""")
    assert len(linhas) == len(sql02)
    for l in linhas:
        ym = l["ano_mes"]
        s = sql02.loc[ym]
        assert int(l["pedidos"]) == int(s["pedidos_entregues"]), ym
        assert float(l["gmv_nominal"]) == pytest.approx(float(s["gmv_nominal"]), abs=0.05), ym
        assert float(l["gmv_real"]) == pytest.approx(float(s["gmv_real_ipca"]), abs=0.05), ym
        assert float(l["mm3m"]) == pytest.approx(float(s["mm3m_gmv_real"]), abs=0.05), ym
        assert float(l["acum"]) == pytest.approx(float(s["gmv_real_acumulado"]), abs=0.05), ym
        assert float(l["selic"]) == pytest.approx(float(s["selic_media"]), abs=0.02), ym
        assert float(l["ipca_12m"]) == pytest.approx(float(s["ipca_acum_12m_pct"]), abs=0.02), ym
        if pd.notna(s["mom_gmv_real_pct"]):
            assert float(l["mom_pct"]) == pytest.approx(float(s["mom_gmv_real_pct"]), abs=0.05), ym
        if pd.notna(s["yoy_gmv_real_pct"]):
            assert float(l["yoy_pct"]) == pytest.approx(float(s["yoy_gmv_real_pct"]), abs=0.05), ym


def test_desktop_dax_uf_sla_e_atraso_vs_avaliacao_batem_com_sql_03_e_04(modelo):
    sql03 = pd.read_csv(GABARITO / "03_logistica_sla_uf.csv").set_index("uf")
    ufs = modelo.consultar("""
EVALUATE
SUMMARIZECOLUMNS (
    dim_geo_uf[uf],
    "pedidos", [Pedidos Entregues] + 0,
    "gmv_real", [GMV Real IPCA] + 0,
    "gmv_100k", [GMV Real / 100 mil hab.],
    "pct_no_prazo", [% Entregas no Prazo] * 100,
    "prazo", [Prazo Médio Entrega (d)],
    "nota", [Nota Média]
)
""")
    assert len(ufs) == 27
    for l in ufs:
        s = sql03.loc[l["uf"]]
        assert int(l["pedidos"]) == int(s["pedidos_entregues"]), l["uf"]
        assert float(l["gmv_real"]) == pytest.approx(float(s["gmv_real_ipca"]), abs=0.05), l["uf"]
        assert float(l["gmv_100k"]) == pytest.approx(float(s["gmv_real_100k_hab"]), abs=0.05), l["uf"]
        assert float(l["pct_no_prazo"]) == pytest.approx(float(s["pct_no_prazo"]), abs=0.02), l["uf"]
        assert float(l["prazo"]) == pytest.approx(float(s["prazo_medio_dias"]), abs=0.02), l["uf"]
        assert float(l["nota"]) == pytest.approx(float(s["nota_media"]), abs=0.02), l["uf"]

    sql04 = pd.read_csv(GABARITO / "04_atraso_vs_avaliacao.csv").set_index("ordem")
    faixas = modelo.consultar("""
EVALUATE
FILTER (
    SUMMARIZECOLUMNS (
        dim_faixa_atraso[ordem],
        dim_faixa_atraso[faixa_atraso],
        "pedidos", [Entregas com Data Válida] + 0,
        "nota", [Nota Média]
    ),
    dim_faixa_atraso[ordem] <= 5
)
ORDER BY dim_faixa_atraso[ordem]
""")
    assert len(faixas) == 5
    for l in faixas:
        s = sql04.loc[int(l["ordem"])]
        assert int(l["pedidos"]) == int(s["pedidos"]), l["faixa_atraso"]
        assert float(l["nota"]) == pytest.approx(float(s["nota_media"]), abs=0.02), l["faixa_atraso"]


def test_desktop_dax_pareto_categorias_e_auditoria_batem_com_sql_05_e_06(modelo):
    sql05 = pd.read_csv(GABARITO / "05_comercial_categorias.csv").set_index("categoria_pt")
    cats = modelo.consultar("""
EVALUATE
SUMMARIZECOLUMNS (
    dim_categoria[categoria_pt],
    "gmv_real", [GMV Itens Real IPCA],
    "pct_gmv", [% GMV Categorias] * 100,
    "pct_acum", [% Acumulado GMV Categorias] * 100
)
""")
    por_cat = {l["categoria_pt"]: l for l in cats if l["gmv_real"] is not None}
    for cat_pt, s in sql05.head(15).iterrows():
        l = por_cat[cat_pt]
        assert float(l["gmv_real"]) == pytest.approx(float(s["gmv_real_ipca"]), abs=0.05), cat_pt
        assert float(l["pct_gmv"]) == pytest.approx(float(s["pct_gmv_real"]), abs=0.02), cat_pt
        assert float(l["pct_acum"]) == pytest.approx(float(s["pct_gmv_acumulado"]), abs=0.05), cat_pt

    sql06 = pd.read_csv(GABARITO / "06_qualidade_dados.csv")
    (aud,) = modelo.consultar("""
EVALUATE
ROW (
    "anomalias", [Anomalias Detectadas],
    "regras", [Regras de Qualidade],
    "reviews_dup", [Reviews Duplicadas]
)
""")
    assert int(aud["anomalias"]) == int(sql06["linhas_afetadas"].sum())
    assert int(aud["regras"]) == len(sql06)
    assert int(aud["reviews_dup"]) == int(
        sql06.loc[sql06["regra_id"] == "Q08_AVALIACOES_DUPLICADAS", "linhas_afetadas"].iloc[0]
    )
