"""Testes de integridade do Star Schema (data/limpa/), deflator e auditoria de anomalias Olist.

Verifica chaves primárias, chaves estrangeiras, ausência de chaves nulas, consistência
aritmética do deflator IPCA em todas as linhas de fato, consistência de SLA/faixas de atraso,
contabilização fiel das anomalias reais da base Olist e restrições do DDL SQLite.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
LIMPA = RAIZ / "data" / "limpa"
RAW = RAIZ / "data" / "raw"
SQL_DIR = RAIZ / "sql"

ARQUIVOS_ESPERADOS = {
    "dim_calendario.csv",
    "dim_macro_mensal.csv",
    "dim_geo_uf.csv",
    "dim_categoria.csv",
    "dim_faixa_atraso.csv",
    "dim_vendedor.csv",
    "fato_pedidos.csv",
    "fato_itens_pedido.csv",
    "qualidade_auditoria.csv",
    "fontes_metadados.csv",
    "macro_benchmark_atual.csv",
}

ISO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_MES = re.compile(r"^\d{4}-\d{2}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@pytest.fixture(scope="module")
def tabelas() -> dict[str, pd.DataFrame]:
    return {
        nome[:-4]: pd.read_csv(LIMPA / nome, keep_default_na=True, low_memory=False)
        for nome in sorted(ARQUIVOS_ESPERADOS)
    }


def test_todos_arquivos_star_schema_existem():
    encontrados = {p.name for p in LIMPA.glob("*.csv")}
    assert encontrados == ARQUIVOS_ESPERADOS


def test_chaves_primarias_unicas_e_sem_nulos(tabelas):
    chaves_simples = {
        "dim_calendario": "data",
        "dim_macro_mensal": "ano_mes",
        "dim_geo_uf": "uf",
        "dim_categoria": "categoria_codigo",
        "dim_faixa_atraso": "faixa_atraso",
        "dim_vendedor": "seller_id",
        "fato_pedidos": "order_id",
        "qualidade_auditoria": "regra_id",
        "fontes_metadados": "arquivo",
        "macro_benchmark_atual": "indicador",
    }
    for nome, pk in chaves_simples.items():
        df = tabelas[nome]
        assert len(df) > 0, nome
        assert df[pk].notna().all(), f"PK nula em {nome}.{pk}"
        assert df[pk].is_unique, f"PK duplicada em {nome}.{pk}"

    itens = tabelas["fato_itens_pedido"]
    assert itens["order_id"].notna().all()
    assert itens["order_item_id"].notna().all()
    assert not itens.duplicated(subset=["order_id", "order_item_id"]).any()


def test_dimensoes_cobertura_e_dominios(tabelas):
    # Calendário diário contínuo de 2016-09-01 a 2018-10-31 sem buracos
    cal = tabelas["dim_calendario"]
    datas = [date.fromisoformat(d) for d in cal["data"]]
    assert datas[0] == date(2016, 9, 1)
    assert datas[-1] == date(2018, 10, 31)
    assert datas == [datas[0] + timedelta(days=i) for i in range(len(datas))]

    # Macro mensal: 26 meses contínuos, base 2018-10 com fator == 1.0 e índice == 100.0
    macro = tabelas["dim_macro_mensal"]
    assert len(macro) == 26
    assert macro["ano_mes"].iloc[0] == "2016-09"
    assert macro["ano_mes"].iloc[-1] == "2018-10"
    base = macro.loc[macro["ano_mes"] == "2018-10"].iloc[0]
    assert base["fator_deflator"] == pytest.approx(1.0, abs=1e-6)
    assert base["indice_ipca_base100"] == pytest.approx(100.0, abs=1e-4)
    assert (macro["fator_deflator"] > 0).all()
    assert (macro["selic_media"] > 0).all()
    assert (macro["ptax_media"] > 0).all()

    # IBGE: 27 UFs e 5 macrorregiões com populações positivas
    uf = tabelas["dim_geo_uf"]
    assert len(uf) == 27
    assert set(uf["regiao"]) == {"Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"}
    assert (uf["populacao_ibge"] > 500_000).all()
    assert (uf["populacao_censo_2022"] > 500_000).all()
    assert uf["codigo_ibge"].is_unique

    # Faixas de atraso canônicas (1..5 entregues, 6 sem entrega)
    faixas = tabelas["dim_faixa_atraso"].sort_values("ordem")
    assert faixas["ordem"].tolist() == [1, 2, 3, 4, 5, 6]
    assert faixas["faixa_atraso"].tolist() == [
        "No prazo / antecipado",
        "1–3 dias de atraso",
        "4–7 dias",
        "8–14 dias",
        "15+ dias",
        "Sem entrega",
    ]

    # Categorias sem rótulos vazios e com traduções de fallback presentes
    cat = tabelas["dim_categoria"]
    assert cat["categoria_pt"].notna().all() and (cat["categoria_pt"].str.strip() != "").all()
    assert cat["categoria_en"].notna().all() and (cat["categoria_en"].str.strip() != "").all()
    assert {"sem_categoria", "pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"}.issubset(
        set(cat["categoria_codigo"])
    )


def test_integridade_referencial_chaves_estrangeiras(tabelas):
    cal_datas = set(tabelas["dim_calendario"]["data"])
    macro_meses = set(tabelas["dim_macro_mensal"]["ano_mes"])
    ufs = set(tabelas["dim_geo_uf"]["uf"])
    cats = set(tabelas["dim_categoria"]["categoria_codigo"])
    faixas = set(tabelas["dim_faixa_atraso"]["faixa_atraso"])
    vendedores = set(tabelas["dim_vendedor"]["seller_id"])
    pedidos_ids = set(tabelas["fato_pedidos"]["order_id"])

    assert set(tabelas["dim_calendario"]["ano_mes"]).issubset(macro_meses)
    assert set(tabelas["dim_macro_mensal"]["data_mes"]).issubset(cal_datas)
    assert set(tabelas["dim_vendedor"]["uf_vendedor"]).issubset(ufs)

    fp = tabelas["fato_pedidos"]
    for col, dominio in [
        ("data_compra", cal_datas),
        ("ano_mes", macro_meses),
        ("uf_cliente", ufs),
        ("categoria_principal", cats),
        ("faixa_atraso", faixas),
    ]:
        assert fp[col].notna().all(), f"FK nula em fato_pedidos.{col}"
        assert set(fp[col]).issubset(dominio), f"FK órfã em fato_pedidos.{col}"

    fi = tabelas["fato_itens_pedido"]
    for col, dominio in [
        ("order_id", pedidos_ids),
        ("data_compra", cal_datas),
        ("ano_mes", macro_meses),
        ("uf_cliente", ufs),
        ("uf_vendedor", ufs),
        ("categoria_codigo", cats),
        ("seller_id", vendedores),
    ]:
        assert fi[col].notna().all(), f"FK nula em fato_itens_pedido.{col}"
        assert set(fi[col]).issubset(dominio), f"FK órfã em fato_itens_pedido.{col}"


def test_consistencia_deflator_e_reconciliacao_pedidos_vs_itens(tabelas):
    macro = tabelas["dim_macro_mensal"].set_index("ano_mes")["fator_deflator"]
    fp = tabelas["fato_pedidos"]
    fi = tabelas["fato_itens_pedido"]

    # Volumetria real Olist (sem descarte silencioso)
    assert len(fp) == 99_441
    assert int((fp["flag_entregue"] == 1).sum()) == 96_478
    assert len(fi) == 112_650

    # Consistência nominal e deflator IPCA em cada linha de fato_pedidos
    soma_nom = (fp["valor_produtos"] + fp["valor_frete"]).round(2)
    assert np.allclose(fp["valor_total_nominal"], soma_nom, atol=0.011)

    esperado_real_fp = (fp["valor_total_nominal"] * fp["ano_mes"].map(macro)).round(2)
    assert np.allclose(fp["valor_total_real_ipca"], esperado_real_fp, atol=0.011)

    # Consistência nominal e deflator IPCA em cada linha de fato_itens_pedido
    soma_item = (fi["preco"] + fi["frete"]).round(2)
    assert np.allclose(fi["valor_item_nominal"], soma_item, atol=0.011)

    esperado_real_fi = (fi["valor_item_nominal"] * fi["ano_mes"].map(macro)).round(2)
    assert np.allclose(fi["valor_item_real_ipca"], esperado_real_fi, atol=0.011)

    # Reconciliação exata item -> pedido (produtos, frete, total e qtd_itens)
    agg_itens = fi.groupby("order_id").agg(
        qtd_itens=("order_item_id", "count"),
        valor_produtos=("preco", "sum"),
        valor_frete=("frete", "sum"),
        valor_total_nominal=("valor_item_nominal", "sum"),
    )
    comp = fp.set_index("order_id")[["qtd_itens", "valor_produtos", "valor_frete", "valor_total_nominal"]].merge(
        agg_itens, left_index=True, right_index=True, suffixes=("", "_itens"), how="left"
    ).fillna(0.0)
    assert (comp["qtd_itens"] == comp["qtd_itens_itens"]).all()
    assert np.allclose(comp["valor_produtos"], comp["valor_produtos_itens"], atol=0.011)
    assert np.allclose(comp["valor_frete"], comp["valor_frete_itens"], atol=0.011)
    assert np.allclose(comp["valor_total_nominal"], comp["valor_total_nominal_itens"], atol=0.011)


def test_consistencia_datas_sla_e_faixas_de_atraso(tabelas):
    fp = tabelas["fato_pedidos"]

    # Pedidos não entregues nunca podem carregar data de entrega ou atraso
    nao_entregues = fp[fp["flag_entregue"] == 0]
    assert nao_entregues["data_entrega_real"].isna().all()
    assert nao_entregues["dias_entrega"].isna().all()
    assert nao_entregues["dias_atraso"].isna().all()
    assert nao_entregues["flag_atraso"].isna().all()
    assert (nao_entregues["faixa_atraso"] == "Sem entrega").all()

    # Pedidos entregues com data real obedecem aritmética exata de calendário
    com_data = fp[(fp["flag_entregue"] == 1) & fp["data_entrega_real"].notna()].copy()
    dt_compra = pd.to_datetime(com_data["data_compra"])
    dt_estimada = pd.to_datetime(com_data["data_entrega_estimada"])
    dt_real = pd.to_datetime(com_data["data_entrega_real"])

    dias_ent = (dt_real - dt_compra).dt.days
    dias_atr = (dt_real - dt_estimada).dt.days
    assert (com_data["dias_entrega"].astype(int) == dias_ent).all()
    assert (com_data["dias_entrega"] >= 0).all()
    assert (com_data["dias_atraso"].astype(int) == dias_atr).all()
    assert (com_data["flag_atraso"].astype(int) == (dias_atr > 0).astype(int)).all()

    # Verifica fronteiras exatas das 5 faixas de atraso
    def faixa_independente(d: int) -> str:
        if d <= 0:
            return "No prazo / antecipado"
        if d <= 3:
            return "1–3 dias de atraso"
        if d <= 7:
            return "4–7 dias"
        if d <= 14:
            return "8–14 dias"
        return "15+ dias"

    esperado_faixa = dias_atr.map(faixa_independente)
    assert (com_data["faixa_atraso"] == esperado_faixa).all()


def test_auditoria_anomalias_bate_com_tabelas_limpas(tabelas):
    fp = tabelas["fato_pedidos"]
    fi = tabelas["fato_itens_pedido"]
    cat = tabelas["dim_categoria"]
    aud = tabelas["qualidade_auditoria"].set_index("regra_id")

    assert len(aud) >= 10
    assert int(aud.loc["Q01_PEDIDOS_NAO_ENTREGUES", "linhas_afetadas"]) == int((fp["flag_entregue"] == 0).sum())
    assert int(aud.loc["Q02_ENTREGUE_SEM_DATA", "linhas_afetadas"]) == int(
        ((fp["flag_entregue"] == 1) & fp["data_entrega_real"].isna()).sum()
    )
    assert int(aud.loc["Q04_SEM_DATA_APROVACAO", "linhas_afetadas"]) == int(fp["data_aprovacao"].isna().sum())
    assert int(aud.loc["Q05_PEDIDOS_SEM_ITENS", "linhas_afetadas"]) == int((fp["qtd_itens"] == 0).sum())
    assert int(aud.loc["Q06_PEDIDO_SEM_PAGAMENTO", "linhas_afetadas"]) == int(
        (fp["tipo_pagamento_principal"] == "sem_pagamento").sum()
    )
    assert int(aud.loc["Q07_PEDIDOS_SEM_AVALIACAO", "linhas_afetadas"]) == int(fp["nota_review"].isna().sum())
    assert int(aud.loc["Q10_CATEGORIAS_SEM_TRADUCAO", "linhas_afetadas"]) == int(
        ((cat["traducao_oficial_olist"] == 0) & (cat["categoria_codigo"] != "sem_categoria")).sum()
    )
    assert int(aud.loc["Q11_FRETE_OUTLIER_EXTREMO", "linhas_afetadas"]) == int((fi["flag_frete_outlier"] == 1).sum())

    # Percentuais de auditoria coerentes com linhas_afetadas / base_referencia
    for regra_id, row in aud.iterrows():
        esperado_pct = round(100.0 * row["linhas_afetadas"] / row["base_referencia"], 2)
        assert row["pct_base"] == pytest.approx(esperado_pct, abs=0.011), regra_id


def test_auditoria_anomalias_bate_com_brutos_olist_quando_presentes(tabelas):
    """Quando data/raw/ está presente localmente, valida as contagens direto nos CSVs brutos da Olist."""
    if not (RAW / "olist_orders_dataset.csv").is_file():
        pytest.skip("data/raw/ não versionado no git; verificação local apenas quando coletado")

    aud = tabelas["qualidade_auditoria"].set_index("regra_id")
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")
    reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")

    assert len(orders) == 99_441
    assert int(aud.loc["Q01_PEDIDOS_NAO_ENTREGUES", "linhas_afetadas"]) == int(
        (orders["order_status"] != "delivered").sum()
    )
    assert int(aud.loc["Q03_NAO_ENTREGUE_COM_DATA", "linhas_afetadas"]) == int(
        ((orders["order_status"] != "delivered") & orders["order_delivered_customer_date"].notna()).sum()
    )
    assert int(aud.loc["Q08_AVALIACOES_DUPLICADAS", "linhas_afetadas"]) == int(
        len(reviews) - reviews["order_id"].nunique()
    )
    assert int(aud.loc["Q09_PRODUTOS_SEM_CATEGORIA", "linhas_afetadas"]) == int(
        products["product_category_name"].isna().sum()
    )
    assert int(aud.loc["Q12_PAGAMENTO_ANOMALO", "linhas_afetadas"]) == int(
        ((payments["payment_type"] == "not_defined") | (payments["payment_installments"] == 0)).sum()
    )


def test_consistencia_coorte_e_recompra(tabelas):
    entregues = tabelas["fato_pedidos"].query("flag_entregue == 1").copy()
    primeira = entregues.groupby("cliente_unico_id")["ano_mes"].min()
    esperado_coorte = entregues["cliente_unico_id"].map(primeira)
    assert (entregues["coorte_mes"] == esperado_coorte).all()

    ano_p = entregues["ano_mes"].str.slice(0, 4).astype(int)
    mes_p = entregues["ano_mes"].str.slice(5, 7).astype(int)
    ano_c = entregues["coorte_mes"].str.slice(0, 4).astype(int)
    mes_c = entregues["coorte_mes"].str.slice(5, 7).astype(int)
    esperado_delta = (ano_p - ano_c) * 12 + (mes_p - mes_c)
    assert (entregues["meses_desde_coorte"] == esperado_delta).all()
    assert (entregues["meses_desde_coorte"] >= 0).all()

    # flag_recompra == 1 se e somente se o cliente único tem >= 2 pedidos entregues
    pedidos_por_cliente = entregues.groupby("cliente_unico_id")["order_id"].count()
    esperado_recompra = (entregues["cliente_unico_id"].map(pedidos_por_cliente) >= 2).astype(int)
    # Pode ser flag a nível de cliente (todos os pedidos do cliente) ou a partir do 2º pedido;
    # verificar qual convenção é consistente com a consulta SQL 01 (COUNT DISTINCT cliente WHERE flag_recompra=1)
    clientes_flag = set(entregues.loc[entregues["flag_recompra"] == 1, "cliente_unico_id"])
    clientes_multi = set(pedidos_por_cliente[pedidos_por_cliente >= 2].index)
    assert clientes_flag == clientes_multi


def test_metadados_fontes_tem_checksums_e_licencas(tabelas):
    meta = tabelas["fontes_metadados"]
    assert set(meta["fonte"]) == {"Olist", "Banco Central (SGS)", "IBGE"}
    assert len(meta) == 17
    for _, row in meta.iterrows():
        assert SHA256_RE.fullmatch(str(row["sha256"])), row["arquivo"]
        assert str(row["endpoint"]).startswith("https://"), row["arquivo"]
        assert int(row["bytes_total"]) > 0
        assert str(row["licenca"]).strip() != ""


def test_ddl_sqlite_recusa_chaves_estrangeiras_e_dominios_invalidos():
    banco = sqlite3.connect(":memory:")
    try:
        banco.execute("PRAGMA foreign_keys = ON")
        banco.executescript((SQL_DIR / "01_tabelas.sql").read_text(encoding="utf-8"))
        banco.executescript((SQL_DIR / "02_views.sql").read_text(encoding="utf-8"))

        # UF inválida precisa falhar CHECK
        with pytest.raises(sqlite3.IntegrityError):
            banco.execute(
                "INSERT INTO dim_geo_uf VALUES ('SPX', 35, 'Sao Paulo', 'SE', 'Sudeste', 1000, 1000)"
            )
        # Pedido com UF inexistente precisa falhar FK
        with pytest.raises(sqlite3.IntegrityError):
            banco.execute(
                "INSERT INTO fato_pedidos (order_id, data_compra, ano_mes, data_entrega_estimada, "
                "faixa_atraso, status, flag_entregue, uf_cliente, categoria_principal, qtd_itens, "
                "valor_produtos, valor_frete, valor_total_nominal, valor_total_real_ipca, "
                "tipo_pagamento_principal, parcelas, cliente_unico_id, coorte_mes, meses_desde_coorte, "
                "flag_recompra, flag_frete_outlier) VALUES ("
                "'x', '2018-01-01', '2018-01', '2018-01-10', 'Sem entrega', 'canceled', 0, 'ZZ', "
                "'sem_categoria', 0, 0, 0, 0, 0, 'boleto', 1, 'c1', '2018-01', 0, 0, 0)"
            )
    finally:
        banco.close()
