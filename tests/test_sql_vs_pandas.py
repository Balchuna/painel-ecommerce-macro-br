"""Reconciliação independente: gabarito SQL (sql/gabarito/*.csv) vs cálculo puro em pandas.

Nenhuma métrica aqui confia no SQL: cada uma das 6 consultas de resposta
(01_visao_executiva .. 06_qualidade_dados) é recalculada do zero em pandas
sobre data/limpa/*.csv e confrontada linha a linha e coluna a coluna com
o gabarito gerado por SQLite.
"""
from __future__ import annotations

import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
LIMPA = RAIZ / "data" / "limpa"
SQL_DIR = RAIZ / "sql"
GABARITO_DIR = SQL_DIR / "gabarito"
SCRIPT_GABARITO = RAIZ / "scripts" / "gerar_gabarito.py"

CONSULTAS = [
    "01_visao_executiva",
    "02_serie_mensal_macro",
    "03_logistica_sla_uf",
    "04_atraso_vs_avaliacao",
    "05_comercial_categorias",
    "06_qualidade_dados",
]


def ler_csv_texto(caminho: Path) -> list[dict[str, str]]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rodar_gerar_gabarito(limpa: Path, banco: Path, gabarito: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_GABARITO),
            "--limpa",
            str(limpa),
            "--banco",
            str(banco),
            "--gabarito",
            str(gabarito),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def comparar_dataframes(sql_df: pd.DataFrame, pd_df: pd.DataFrame, atol: float = 0.011) -> None:
    """Compara dois DataFrames coluna a coluna (exato em texto/inteiros, tolerância rígida em float)."""
    assert list(sql_df.columns) == list(pd_df.columns), (
        f"Colunas diferem:\n  SQL: {list(sql_df.columns)}\n  PD:  {list(pd_df.columns)}"
    )
    assert len(sql_df) == len(pd_df), f"Linhas diferem: SQL={len(sql_df)} vs PD={len(pd_df)}"

    for col in sql_df.columns:
        s_sql = sql_df[col]
        s_pd = pd_df[col]
        sql_na = s_sql.isna()
        pd_na = s_pd.isna()
        assert (sql_na == pd_na).all(), f"Posições nulas diferem na coluna {col}"
        mask = ~sql_na
        if not mask.any():
            continue
        if pd.api.types.is_numeric_dtype(s_pd) and pd.api.types.is_numeric_dtype(s_sql):
            a = s_sql[mask].astype(float).to_numpy()
            b = s_pd[mask].astype(float).to_numpy()
            if not np.allclose(a, b, atol=atol, rtol=0.0):
                diffs = np.abs(a - b)
                idx = int(np.argmax(diffs))
                raise AssertionError(
                    f"Divergência numérica em '{col}' (linha {idx}): SQL={a[idx]} vs Pandas={b[idx]} (diff={diffs[idx]:.6f})"
                )
        else:
            a_str = s_sql[mask].astype(str).tolist()
            b_str = s_pd[mask].astype(str).tolist()
            assert a_str == b_str, f"Divergência textual em '{col}':\n  SQL={a_str[:5]}\n  PD={b_str[:5]}"


@pytest.fixture(scope="module")
def execucao_gabarito(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("gabarito_check")
    banco = pasta / "painel.sqlite"
    gabarito = pasta / "gabarito"
    res = rodar_gerar_gabarito(LIMPA, banco, gabarito)
    assert res.returncode == 0, res.stderr
    return banco, gabarito


@pytest.fixture(scope="module")
def dados_limpos() -> dict[str, pd.DataFrame]:
    nomes = [
        "dim_calendario",
        "dim_macro_mensal",
        "dim_geo_uf",
        "dim_categoria",
        "dim_faixa_atraso",
        "dim_vendedor",
        "fato_pedidos",
        "fato_itens_pedido",
        "qualidade_auditoria",
    ]
    return {n: pd.read_csv(LIMPA / f"{n}.csv", low_memory=False) for n in nomes}


# ---------------------------------------------------------------------------------------------
# Cálculo independente em pandas puro para cada uma das 6 consultas


def calcular_01_visao_executiva(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fp = d["fato_pedidos"]
    fi = d["fato_itens_pedido"]
    cal = d["dim_calendario"]
    vend = d["dim_vendedor"]
    macro = d["dim_macro_mensal"].set_index("ano_mes")

    ent = fp[fp["flag_entregue"] == 1].copy()
    ent_cal = ent.merge(cal[["data", "ano", "mes"]], left_on="data_compra", right_on="data", how="left")
    itens_ent = fi[fi["flag_entregue"] == 1].copy()

    pedidos_brutos = len(fp)
    pedidos_entregues = len(ent)
    pedidos_entregues_data_valida = int(ent["data_entrega_real"].notna().sum())
    pedidos_nao_entregues = int((fp["flag_entregue"] == 0).sum())
    pct_excluidos = round(100.0 * pedidos_nao_entregues / pedidos_brutos, 2)

    clientes_unicos = int(ent["cliente_unico_id"].nunique())
    clientes_recompra = int(ent.loc[ent["flag_recompra"] == 1, "cliente_unico_id"].nunique())
    clientes_retidos_6m = int(
        ent.loc[ent["meses_desde_coorte"].between(1, 6), "cliente_unico_id"].nunique()
    )
    itens_vendidos = int(ent["qtd_itens"].sum())

    receita_prod = round(float(ent["valor_produtos"].sum()), 2)
    frete_nom = round(float(ent["valor_frete"].sum()), 2)
    gmv_nom = round(float(ent["valor_total_nominal"].sum()), 2)
    gmv_real = round(float(ent["valor_total_real_ipca"].sum()), 2)

    nota_no_prazo = round(float(ent.loc[ent["flag_atraso"] == 0, "nota_review"].mean()), 2)
    nota_atrasado = round(float(ent.loc[ent["flag_atraso"] == 1, "nota_review"].mean()), 2)

    pct_no_prazo = round(
        100.0 * float((ent["flag_atraso"] == 0).sum()) / pedidos_entregues_data_valida, 2
    )
    cartao = ent["tipo_pagamento_principal"] == "credit_card"
    cartao_parc_pos = cartao & (ent["parcelas"] > 0)

    # Top 10% vendedores (D1)
    v_itens = itens_ent.merge(vend[["seller_id", "decil_gmv", "decil_ordem"]], on="seller_id", how="inner")
    v_itens = v_itens[v_itens["decil_ordem"].between(1, 10)]
    gmv_por_decil = v_itens.groupby("decil_ordem")["valor_item_real_ipca"].sum().round(2)
    vendedores_ativos = int(v_itens["seller_id"].nunique())
    pct_top10 = round(100.0 * float(gmv_por_decil.loc[1]) / float(gmv_por_decil.sum()), 2)

    # Pareto 80% categorias
    cat_gmv = (
        itens_ent.groupby("categoria_codigo", as_index=False)["valor_item_real_ipca"]
        .sum()
        .sort_values(["valor_item_real_ipca", "categoria_codigo"], ascending=[False, True])
        .reset_index(drop=True)
    )
    total_cat = float(cat_gmv["valor_item_real_ipca"].sum())
    acum_ant = cat_gmv["valor_item_real_ipca"].cumsum().shift(1, fill_value=0.0) * 100.0 / total_cat
    categorias_80 = int((acum_ant < 80.0).sum())

    # Comparativo anual (2017 cheio vs jan-ago 2018 e YoY homogêneo jan-ago)
    gmv_nom_2017_cheio = round(float(ent_cal.loc[ent_cal["ano"] == 2017, "valor_total_nominal"].sum()), 2)
    gmv_real_2017_cheio = round(float(ent_cal.loc[ent_cal["ano"] == 2017, "valor_total_real_ipca"].sum()), 2)
    gmv_nom_2017_ja = round(
        float(ent_cal.loc[(ent_cal["ano"] == 2017) & (ent_cal["mes"] <= 8), "valor_total_nominal"].sum()), 2
    )
    gmv_real_2017_ja = round(
        float(ent_cal.loc[(ent_cal["ano"] == 2017) & (ent_cal["mes"] <= 8), "valor_total_real_ipca"].sum()), 2
    )
    gmv_nom_2018_ja = round(
        float(ent_cal.loc[(ent_cal["ano"] == 2018) & (ent_cal["mes"] <= 8), "valor_total_nominal"].sum()), 2
    )
    gmv_real_2018_ja = round(
        float(ent_cal.loc[(ent_cal["ano"] == 2018) & (ent_cal["mes"] <= 8), "valor_total_real_ipca"].sum()), 2
    )

    yoy_nom_ja = 100.0 * (gmv_nom_2018_ja - gmv_nom_2017_ja) / gmv_nom_2017_ja
    yoy_real_ja = 100.0 * (gmv_real_2018_ja - gmv_real_2017_ja) / gmv_real_2017_ja

    return pd.DataFrame([{
        "pedidos_brutos": pedidos_brutos,
        "pedidos_entregues": pedidos_entregues,
        "pedidos_entregues_data_valida": pedidos_entregues_data_valida,
        "pedidos_nao_entregues": pedidos_nao_entregues,
        "pct_excluidos": pct_excluidos,
        "clientes_unicos_entregues": clientes_unicos,
        "clientes_recompra": clientes_recompra,
        "pct_clientes_recompra": round(100.0 * clientes_recompra / clientes_unicos, 2),
        "pct_retencao_6m": round(100.0 * clientes_retidos_6m / clientes_unicos, 2),
        "itens_vendidos_entregues": itens_vendidos,
        "itens_por_pedido": round(itens_vendidos / pedidos_entregues, 2),
        "gmv_nominal": gmv_nom,
        "gmv_real_ipca": gmv_real,
        "receita_produtos_nominal": receita_prod,
        "frete_nominal": frete_nom,
        "pct_frete_gmv": round(100.0 * frete_nom / gmv_nom, 2),
        "ticket_medio_nominal": round(float(ent["valor_total_nominal"].mean()), 2),
        "ticket_medio_real": round(float(ent["valor_total_real_ipca"].mean()), 2),
        "nota_media": round(float(ent["nota_review"].mean()), 2),
        "nota_media_no_prazo": nota_no_prazo,
        "nota_media_atrasado": nota_atrasado,
        "queda_nota_atraso": round(nota_no_prazo - nota_atrasado, 2),
        "prazo_medio_dias": round(float(ent["dias_entrega"].mean()), 2),
        "pct_no_prazo": pct_no_prazo,
        "atraso_medio_quando_atrasa": round(float(ent.loc[ent["flag_atraso"] == 1, "dias_atraso"].mean()), 2),
        "pct_pedidos_cartao": round(100.0 * float(cartao.sum()) / pedidos_entregues, 2),
        "pct_gmv_cartao": round(100.0 * float(ent.loc[cartao, "valor_total_real_ipca"].sum()) / gmv_real, 2),
        "pct_cartao_parcelado": round(
            100.0 * float((cartao & (ent["parcelas"] > 1)).sum()) / float(cartao_parc_pos.sum()), 2
        ),
        "parcelas_medias_cartao": round(float(ent.loc[cartao_parc_pos, "parcelas"].mean()), 2),
        "vendedores_ativos": vendedores_ativos,
        "pct_gmv_top10_vendedores": pct_top10,
        "categorias_80pct_gmv": categorias_80,
        "gmv_real_2017_cheio": gmv_real_2017_cheio,
        "gmv_real_2018_jan_ago": gmv_real_2018_ja,
        "var_gmv_real_2018_vs_2017_cheio_pct": round(
            100.0 * (gmv_real_2018_ja - gmv_real_2017_cheio) / gmv_real_2017_cheio, 2
        ),
        "var_gmv_nominal_2018_vs_2017_cheio_pct": round(
            100.0 * (gmv_nom_2018_ja - gmv_nom_2017_cheio) / gmv_nom_2017_cheio, 2
        ),
        "gmv_nom_2017_jan_ago": gmv_nom_2017_ja,
        "gmv_nom_2018_jan_ago": gmv_nom_2018_ja,
        "var_gmv_nominal_yoy_jan_ago_pct": round(yoy_nom_ja, 2),
        "gmv_real_2017_jan_ago": gmv_real_2017_ja,
        "var_gmv_real_yoy_jan_ago_pct": round(yoy_real_ja, 2),
        "efeito_inflacao_yoy_pp": round(yoy_nom_ja - yoy_real_ja, 2),
        "selic_inicio_2016_09": float(macro.loc["2016-09", "selic_media"]),
        "selic_fim_2018_10": float(macro.loc["2018-10", "selic_media"]),
        "ipca_12m_inicio_2016_09": float(macro.loc["2016-09", "ipca_acum_12m_pct"]),
        "ipca_12m_fim_2018_10": float(macro.loc["2018-10", "ipca_acum_12m_pct"]),
    }])


def calcular_02_serie_mensal_macro(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ent = d["fato_pedidos"].query("flag_entregue == 1")
    macro = d["dim_macro_mensal"].sort_values("ano_mes").copy()

    linhas = []
    for _, m in macro.iterrows():
        ym = m["ano_mes"]
        sub = ent[ent["ano_mes"] == ym]
        n = len(sub)
        com_data = int(sub["data_entrega_real"].notna().sum())
        linhas.append({
            "ano_mes": ym,
            "pedidos_entregues": n,
            "clientes_unicos": int(sub["cliente_unico_id"].nunique()) if n else 0,
            "gmv_nominal": round(float(sub["valor_total_nominal"].sum()), 2) if n else 0.0,
            "gmv_real_ipca": round(float(sub["valor_total_real_ipca"].sum()), 2) if n else 0.0,
            "ticket_medio_real": round(float(sub["valor_total_real_ipca"].mean()), 2) if n else np.nan,
            "pct_no_prazo": round(100.0 * float((sub["flag_atraso"] == 0).sum()) / com_data, 2) if com_data else np.nan,
            "prazo_medio_dias": round(float(sub["dias_entrega"].mean()), 2) if com_data else np.nan,
            "nota_media": round(float(sub["nota_review"].mean()), 2) if sub["nota_review"].notna().any() else np.nan,
            "ipca_mensal_pct": m["ipca_mensal_pct"],
            "ipca_acum_12m_pct": m["ipca_acum_12m_pct"],
            "fator_deflator": m["fator_deflator"],
            "selic_media": m["selic_media"],
            "ptax_media": m["ptax_media"],
        })
    df = pd.DataFrame(linhas)
    ant1 = df["gmv_real_ipca"].shift(1)
    ant12 = df["gmv_real_ipca"].shift(12)
    df["mom_gmv_real_pct"] = np.where(
        (ant1 > 0) & (df["gmv_real_ipca"] > 0),
        np.round(100.0 * (df["gmv_real_ipca"] - ant1) / ant1, 2),
        np.nan,
    )
    df["yoy_gmv_real_pct"] = np.where(
        (ant12 > 0) & (df["gmv_real_ipca"] > 0),
        np.round(100.0 * (df["gmv_real_ipca"] - ant12) / ant12, 2),
        np.nan,
    )
    df["mm3m_gmv_real"] = df["gmv_real_ipca"].rolling(3, min_periods=1).mean().round(2)
    df["gmv_real_acumulado"] = df["gmv_real_ipca"].cumsum().round(2)

    cols = [
        "ano_mes", "pedidos_entregues", "clientes_unicos", "gmv_nominal", "gmv_real_ipca",
        "mom_gmv_real_pct", "yoy_gmv_real_pct", "mm3m_gmv_real", "gmv_real_acumulado",
        "ticket_medio_real", "pct_no_prazo", "prazo_medio_dias", "nota_media",
        "ipca_mensal_pct", "ipca_acum_12m_pct", "fator_deflator", "selic_media", "ptax_media",
    ]
    return df[cols]


def calcular_03_logistica_sla_uf(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ent = d["fato_pedidos"].query("flag_entregue == 1")
    geo = d["dim_geo_uf"].copy()

    linhas = []
    for _, g in geo.iterrows():
        sub = ent[ent["uf_cliente"] == g["uf"]]
        com_data = int(sub["data_entrega_real"].notna().sum())
        gmv_nom = round(float(sub["valor_total_nominal"].sum()), 2)
        gmv_real = round(float(sub["valor_total_real_ipca"].sum()), 2)
        frete_nom = round(float(sub["valor_frete"].sum()), 2)
        linhas.append({
            "uf": g["uf"],
            "nome": g["nome"],
            "regiao": g["regiao"],
            "populacao_ibge": int(g["populacao_ibge"]),
            "populacao_censo_2022": int(g["populacao_censo_2022"]),
            "pedidos_entregues": len(sub),
            "gmv_nominal": gmv_nom,
            "gmv_real_ipca": gmv_real,
            "gmv_real_100k_hab": round(float(sub["valor_total_real_ipca"].sum()) * 100_000.0 / g["populacao_ibge"], 2),
            "pct_frete_gmv": round(100.0 * frete_nom / gmv_nom, 2) if gmv_nom else np.nan,
            "ticket_medio_real": round(float(sub["valor_total_real_ipca"].mean()), 2),
            "prazo_medio_dias": round(float(sub["dias_entrega"].mean()), 2),
            "pct_no_prazo": round(100.0 * float((sub["flag_atraso"] == 0).sum()) / com_data, 2),
            "atraso_medio_dias": round(float(sub.loc[sub["flag_atraso"] == 1, "dias_atraso"].mean()), 2),
            "nota_media": round(float(sub["nota_review"].mean()), 2),
        })
    df = pd.DataFrame(linhas).sort_values(["gmv_real_100k_hab", "uf"], ascending=[False, True]).reset_index(drop=True)
    total_gmv = float(df["gmv_real_ipca"].sum())
    regiao_gmv = df.groupby("regiao")["gmv_real_ipca"].transform("sum")
    df["rank_gmv_100k"] = np.arange(1, len(df) + 1)
    df["pct_participacao_gmv"] = np.round(100.0 * df["gmv_real_ipca"] / total_gmv, 2)
    df["pct_gmv_regiao"] = np.round(100.0 * regiao_gmv / total_gmv, 2)

    cols = [
        "rank_gmv_100k", "uf", "nome", "regiao", "populacao_ibge", "populacao_censo_2022",
        "pedidos_entregues", "gmv_nominal", "gmv_real_ipca", "pct_participacao_gmv",
        "pct_gmv_regiao", "gmv_real_100k_hab", "pct_frete_gmv", "ticket_medio_real",
        "prazo_medio_dias", "pct_no_prazo", "atraso_medio_dias", "nota_media",
    ]
    return df[cols]


def calcular_04_atraso_vs_avaliacao(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fp = d["fato_pedidos"]
    sub = fp[(fp["flag_entregue"] == 1) & fp["data_entrega_real"].notna()].merge(
        d["dim_faixa_atraso"], on="faixa_atraso", how="inner"
    )
    linhas = []
    for (ordem, faixa, faixa_en), grp in sub.groupby(["ordem", "faixa_atraso", "faixa_atraso_en"]):
        aval = grp["nota_review"].dropna()
        linhas.append({
            "ordem": int(ordem),
            "faixa_atraso": faixa,
            "faixa_atraso_en": faixa_en,
            "pedidos": len(grp),
            "pedidos_avaliados": len(aval),
            "nota_media": round(float(aval.mean()), 2),
            "pct_nota_5": round(100.0 * float((aval == 5).sum()) / len(aval), 2),
            "pct_nota_1": round(100.0 * float((aval == 1).sum()) / len(aval), 2),
            "prazo_medio_dias": round(float(grp["dias_entrega"].mean()), 2),
            "atraso_medio_dias": round(float(grp["dias_atraso"].mean()), 2),
        })
    df = pd.DataFrame(linhas).sort_values("ordem").reset_index(drop=True)
    df["pct_pedidos"] = np.round(100.0 * df["pedidos"] / df["pedidos"].sum(), 2)
    nota_base = float(df.loc[0, "nota_media"])
    df["delta_nota_vs_no_prazo"] = np.round(df["nota_media"] - nota_base, 2)

    cols = [
        "ordem", "faixa_atraso", "faixa_atraso_en", "pedidos", "pct_pedidos",
        "pedidos_avaliados", "nota_media", "delta_nota_vs_no_prazo",
        "pct_nota_5", "pct_nota_1", "prazo_medio_dias", "atraso_medio_dias",
    ]
    return df[cols]


def calcular_05_comercial_categorias(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fi = d["fato_itens_pedido"].query("flag_entregue == 1").merge(
        d["dim_categoria"], on="categoria_codigo", how="inner"
    ).merge(
        d["fato_pedidos"][["order_id", "nota_review"]], on="order_id", how="inner"
    )
    linhas = []
    for (cod, pt, en), grp in fi.groupby(["categoria_codigo", "categoria_pt", "categoria_en"]):
        gmv_nom = round(float(grp["valor_item_nominal"].sum()), 2)
        gmv_real = round(float(grp["valor_item_real_ipca"].sum()), 2)
        linhas.append({
            "categoria_codigo": cod,
            "categoria_pt": pt,
            "categoria_en": en,
            "pedidos_entregues": int(grp["order_id"].nunique()),
            "itens_vendidos": len(grp),
            "gmv_nominal": gmv_nom,
            "gmv_real_ipca": gmv_real,
            "preco_medio_item": round(float(grp["preco"].mean()), 2),
            "pct_frete_gmv": round(100.0 * float(grp["frete"].sum()) / gmv_nom, 2) if gmv_nom else np.nan,
            "nota_media": round(float(grp["nota_review"].mean()), 2) if grp["nota_review"].notna().any() else np.nan,
        })
    df = pd.DataFrame(linhas).sort_values(["gmv_real_ipca", "categoria_codigo"], ascending=[False, True]).reset_index(drop=True)
    total_real = float(df["gmv_real_ipca"].sum())
    df["ranking"] = np.arange(1, len(df) + 1)
    df["pct_gmv_real"] = np.round(100.0 * df["gmv_real_ipca"] / total_real, 2)
    df["pct_gmv_acumulado"] = np.round(100.0 * df["gmv_real_ipca"].cumsum() / total_real, 2)
    pct_ant = 100.0 * df["gmv_real_ipca"].cumsum().shift(1, fill_value=0.0) / total_real
    df["no_pareto_80"] = (pct_ant < 80.0).astype(int)

    cols = [
        "ranking", "categoria_codigo", "categoria_pt", "categoria_en",
        "pedidos_entregues", "itens_vendidos", "gmv_nominal", "gmv_real_ipca",
        "pct_gmv_real", "pct_gmv_acumulado", "no_pareto_80",
        "preco_medio_item", "pct_frete_gmv", "nota_media",
    ]
    return df[cols]


def calcular_06_qualidade_dados(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = d["qualidade_auditoria"].copy()
    total = float(df["linhas_afetadas"].sum())
    df["pct_das_anomalias"] = np.round(100.0 * df["linhas_afetadas"] / total, 2)
    df = df.sort_values(["linhas_afetadas", "regra_id"], ascending=[False, True]).reset_index(drop=True)
    cols = [
        "regra_id", "regra", "regra_en", "tabela_origem", "linhas_afetadas",
        "base_referencia", "pct_base", "pct_das_anomalias", "severidade", "tratamento",
    ]
    return df[cols]


CALCULADORAS = {
    "01_visao_executiva": calcular_01_visao_executiva,
    "02_serie_mensal_macro": calcular_02_serie_mensal_macro,
    "03_logistica_sla_uf": calcular_03_logistica_sla_uf,
    "04_atraso_vs_avaliacao": calcular_04_atraso_vs_avaliacao,
    "05_comercial_categorias": calcular_05_comercial_categorias,
    "06_qualidade_dados": calcular_06_qualidade_dados,
}


# ---------------------------------------------------------------------------------------------
# Testes


def test_todas_seis_consultas_e_gabaritos_presentes(execucao_gabarito):
    _, gabarito_novo = execucao_gabarito
    assert sorted(p.stem for p in (SQL_DIR / "consultas").glob("*.sql")) == CONSULTAS
    assert sorted(p.stem for p in GABARITO_DIR.glob("*.csv")) == CONSULTAS
    assert sorted(p.stem for p in gabarito_novo.glob("*.csv")) == CONSULTAS


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_gabarito_versionado_identico_a_nova_execucao_sql(execucao_gabarito, consulta):
    _, gabarito_novo = execucao_gabarito
    assert ler_csv_texto(GABARITO_DIR / f"{consulta}.csv") == ler_csv_texto(
        gabarito_novo / f"{consulta}.csv"
    ), f"rode python scripts/gerar_gabarito.py ({consulta} divergiu)"


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_sql_gabarito_bate_100_porcento_com_pandas(dados_limpos, consulta):
    sql_df = pd.read_csv(GABARITO_DIR / f"{consulta}.csv")
    pd_df = CALCULADORAS[consulta](dados_limpos)
    comparar_dataframes(sql_df, pd_df, atol=0.011)


def test_reconciliacao_cruzada_entre_consultas():
    c1 = pd.read_csv(GABARITO_DIR / "01_visao_executiva.csv").iloc[0]
    c2 = pd.read_csv(GABARITO_DIR / "02_serie_mensal_macro.csv")
    c3 = pd.read_csv(GABARITO_DIR / "03_logistica_sla_uf.csv")
    c4 = pd.read_csv(GABARITO_DIR / "04_atraso_vs_avaliacao.csv")
    c5 = pd.read_csv(GABARITO_DIR / "05_comercial_categorias.csv")

    # Série mensal soma exatamente o total executivo
    assert int(c2["pedidos_entregues"].sum()) == int(c1["pedidos_entregues"])
    assert c2["gmv_nominal"].sum() == pytest.approx(c1["gmv_nominal"], abs=0.05)
    assert c2["gmv_real_ipca"].sum() == pytest.approx(c1["gmv_real_ipca"], abs=0.05)
    assert c2["gmv_real_acumulado"].iloc[-1] == pytest.approx(c1["gmv_real_ipca"], abs=0.05)

    # 27 UFs somam exatamente o total executivo
    assert len(c3) == 27
    assert int(c3["pedidos_entregues"].sum()) == int(c1["pedidos_entregues"])
    assert c3["gmv_nominal"].sum() == pytest.approx(c1["gmv_nominal"], abs=0.05)
    assert c3["gmv_real_ipca"].sum() == pytest.approx(c1["gmv_real_ipca"], abs=0.05)

    # 5 faixas de atraso somam exatamente os pedidos entregues com data válida
    assert len(c4) == 5
    assert int(c4["pedidos"].sum()) == int(c1["pedidos_entregues_data_valida"])
    # Prova estatística central do painel: nota cai fortemente com atraso
    assert c4.loc[0, "nota_media"] > 4.2
    assert c4.loc[4, "nota_media"] < 2.0

    # Categorias somam exatamente itens e GMV dos pedidos entregues
    assert int(c5["itens_vendidos"].sum()) == int(c1["itens_vendidos_entregues"])
    assert c5["gmv_nominal"].sum() == pytest.approx(c1["gmv_nominal"], abs=0.5)
    assert c5["gmv_real_ipca"].sum() == pytest.approx(c1["gmv_real_ipca"], abs=1.5)
    assert int(c5["no_pareto_80"].sum()) == int(c1["categorias_80pct_gmv"])


def test_views_auxiliares_sqlite_coerentes_com_pandas(execucao_gabarito, dados_limpos):
    banco_path, _ = execucao_gabarito
    con = sqlite3.connect(banco_path)
    try:
        pag_sql = pd.read_sql_query("SELECT * FROM vw_pagamentos_mix ORDER BY pedidos DESC", con)
        dec_sql = pd.read_sql_query("SELECT * FROM vw_vendedores_decis ORDER BY decil_ordem", con)
        coorte_sql = pd.read_sql_query("SELECT * FROM vw_coorte_retencao", con)
    finally:
        con.close()

    ent = dados_limpos["fato_pedidos"].query("flag_entregue == 1")
    assert int(pag_sql["pedidos"].sum()) == len(ent)
    assert pag_sql["pct_pedidos"].sum() == pytest.approx(100.0, abs=0.1)

    assert len(dec_sql) == 10
    assert dec_sql["pct_gmv_acumulado"].iloc[-1] == pytest.approx(100.0, abs=0.05)

    # Coorte M+0 deve ter exatamente 100% de retenção em todo mês de coorte
    m0 = coorte_sql[coorte_sql["meses_desde_coorte"] == 0]
    assert (m0["pct_retencao"] == 100.0).all()
    assert int(m0["clientes_coorte"].sum()) == int(ent["cliente_unico_id"].nunique())


def test_gerar_gabarito_rejeita_csv_que_viola_fk_sem_deixar_banco_meio_pronto(tmp_path):
    limpa_ruim = tmp_path / "limpa"
    limpa_ruim.mkdir()
    for arq in LIMPA.glob("*.csv"):
        if arq.name in ("fato_pedidos.csv", "fato_itens_pedido.csv"):
            # Apenas cabeçalho para ser instantâneo + 1 linha inválida em fato_pedidos
            cab = arq.open(encoding="utf-8").readline()
            if arq.name == "fato_pedidos.csv":
                (limpa_ruim / arq.name).write_text(
                    cab
                    + "ord_invalido,2018-01-01,2018-01,,2018-01-10,,,,,Sem entrega,canceled,0,ZZ,"
                    "sem_categoria,,0,0,0,0,0,boleto,1,cli1,2018-01,0,0,0\n",
                    encoding="utf-8",
                )
            else:
                (limpa_ruim / arq.name).write_text(cab, encoding="utf-8")
        else:
            (limpa_ruim / arq.name).write_bytes(arq.read_bytes())

    banco = tmp_path / "painel.sqlite"
    gabarito = tmp_path / "gabarito"
    res = rodar_gerar_gabarito(limpa_ruim, banco, gabarito)
    assert res.returncode != 0
    assert "fato_pedidos.csv" in res.stderr
    assert "Traceback" not in res.stderr
    assert not banco.exists()
    assert not gabarito.exists()
