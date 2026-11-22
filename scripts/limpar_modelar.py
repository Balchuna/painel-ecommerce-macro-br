"""Limpa os dados brutos (Olist, BCB SGS e IBGE) e grava o Star Schema em data/limpa/.

Regras de negócio e transparência:
  - Nenhum pedido bruto (99.441) é apagado silenciosamente: todos entram em fato_pedidos.csv
    com coluna `status` e `flag_entregue` (1 = 'delivered', 96.478 pedidos).
  - Atraso logístico usa datas de calendário: date(entrega_real) - date(entrega_estimada),
    pois a data estimada da Olist é meia-noite (00:00:00) e entregas no mesmo dia são no prazo.
  - Deflação real pelo IPCA (BCB SGS 433) traz todos os valores nominais para reais constantes
    de outubro/2018 (fim do recorte Olist; fator_deflator = 1.000000 em 2018-10).
  - Avaliações duplicadas por pedido (551 linhas extras) são deduplicadas mantendo a avaliação
    mais recente por (review_creation_date, review_answer_timestamp, review_id).
  - Todas as anomalias reais encontradas são contabilizadas em qualidade_auditoria.csv.

Uso:
  python scripts/limpar_modelar.py
  python scripts/limpar_modelar.py --entrada data/raw --saida data/limpa
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.categorias import nome_categoria_en, nome_categoria_pt
from src.constantes import (
    ANO_MES_FIM_OLIST,
    ANO_MES_INICIO_OLIST,
    FAIXAS_ATRASO_EN,
    FAIXAS_ATRASO_ORDEM,
    LIMIAR_FRETE_EXTREMO_BRL,
    LIMIAR_RAZAO_FRETE_PRODUTO,
    MES_BASE_DEFLATOR,
    MESES_PT_ABREV,
)
from src.deflator import (
    agregar_serie_diaria_por_mes,
    calcular_deflator_ipca,
    calcular_ipca_acumulado,
    parse_data_bcb,
    parse_valor_bcb,
)

ENTRADA_PADRAO = RAIZ / "data" / "raw"
SAIDA_PADRAO = RAIZ / "data" / "limpa"


class ErroDeModelagem(Exception):
    """Falha de integridade ou ausência de arquivo na etapa de limpeza."""


def classificar_faixa_atraso(dias_atraso: float | int | None) -> str:
    if dias_atraso is None or (isinstance(dias_atraso, float) and np.isnan(dias_atraso)):
        return "Sem entrega"
    d = int(dias_atraso)
    if d <= 0:
        return "No prazo / antecipado"
    if d <= 3:
        return "1–3 dias de atraso"
    if d <= 7:
        return "4–7 dias"
    if d <= 14:
        return "8–14 dias"
    return "15+ dias"


def construir_dim_calendario(inicio: date, fim: date) -> pd.DataFrame:
    linhas = []
    atual = inicio
    while atual <= fim:
        q = (atual.month - 1) // 3 + 1
        ano_mes = atual.strftime("%Y-%m")
        dow = atual.isoweekday()
        linhas.append({
            "data": atual.isoformat(),
            "ano": atual.year,
            "trimestre": f"{atual.year}-T{q}",
            "trimestre_num": atual.year * 10 + q,
            "mes": atual.month,
            "ano_mes": ano_mes,
            "ano_mes_num": atual.year * 100 + atual.month,
            "mes_ano_pt": f"{MESES_PT_ABREV[atual.month]}/{atual.year}",
            "dia_semana": dow,
            "eh_fim_de_semana": 1 if dow >= 6 else 0,
        })
        atual += timedelta(days=1)
    return pd.DataFrame(linhas)


def construir_dim_macro_e_benchmark(entrada: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    ipca_hist = json.loads((entrada / "bcb_ipca_433_historico.json").read_text(encoding="utf-8"))
    selic_hist = json.loads((entrada / "bcb_selic_432_historico.json").read_text(encoding="utf-8"))
    ptax_hist = json.loads((entrada / "bcb_ptax_1_historico.json").read_text(encoding="utf-8"))

    deflator_rows = calcular_deflator_ipca(
        ipca_hist,
        mes_base=MES_BASE_DEFLATOR,
        ano_mes_inicio=ANO_MES_INICIO_OLIST,
        ano_mes_fim=ANO_MES_FIM_OLIST,
    )
    selic_m = agregar_serie_diaria_por_mes(selic_hist)
    ptax_m = agregar_serie_diaria_por_mes(ptax_hist)

    macro_linhas = []
    for r in deflator_rows:
        ym = r["ano_mes"]
        if ym not in selic_m or ym not in ptax_m:
            raise ErroDeModelagem(f"Selic ou PTAX ausente para o mês {ym}")
        macro_linhas.append({
            "ano_mes": ym,
            "data_mes": f"{ym}-01",
            "ipca_mensal_pct": r["ipca_mensal_pct"],
            "ipca_acum_12m_pct": r["ipca_acum_12m_pct"],
            "indice_ipca_base100": r["indice_ipca_base100"],
            "fator_deflator": r["fator_deflator"],
            "selic_media": selic_m[ym],
            "ptax_media": ptax_m[ym],
        })
    dim_macro = pd.DataFrame(macro_linhas)
    fim_row = dim_macro.loc[dim_macro["ano_mes"] == MES_BASE_DEFLATOR].iloc[0]

    # Benchmark macro recente (últimas observações oficiais da API BCB SGS)
    ipca_rec = json.loads((entrada / "bcb_ipca_433_recente.json").read_text(encoding="utf-8"))
    selic_rec = json.loads((entrada / "bcb_selic_432_recente.json").read_text(encoding="utf-8"))
    ptax_rec = json.loads((entrada / "bcb_ptax_1_recente.json").read_text(encoding="utf-8"))

    ipca_rec_data, _ = parse_data_bcb(ipca_rec[-1]["data"])
    ipca_rec_12m = calcular_ipca_acumulado(ipca_rec)
    selic_rec_data, _ = parse_data_bcb(selic_rec[-1]["data"])
    selic_rec_val = parse_valor_bcb(selic_rec[-1]["valor"])
    ptax_rec_data, _ = parse_data_bcb(ptax_rec[-1]["data"])
    ptax_rec_val = parse_valor_bcb(ptax_rec[-1]["valor"])

    benchmark = pd.DataFrame([
        {
            "indicador": "ipca_12m_pct",
            "nome_pt": "IPCA Acumulado 12 meses",
            "nome_en": "IPCA 12-Month Inflation",
            "serie_sgs": 433,
            "data_referencia": ipca_rec_data,
            "valor_recente": round(float(ipca_rec_12m), 2),
            "valor_fim_olist": round(float(fim_row["ipca_acum_12m_pct"]), 2),
            "unidade": "% 12m",
        },
        {
            "indicador": "selic_meta_aa",
            "nome_pt": "Meta Selic (Copom)",
            "nome_en": "Selic Policy Rate",
            "serie_sgs": 432,
            "data_referencia": selic_rec_data,
            "valor_recente": round(float(selic_rec_val), 2),
            "valor_fim_olist": round(float(fim_row["selic_media"]), 2),
            "unidade": "% a.a.",
        },
        {
            "indicador": "ptax_usd_venda",
            "nome_pt": "Dólar PTAX (Venda)",
            "nome_en": "USD/BRL PTAX (Sell)",
            "serie_sgs": 1,
            "data_referencia": ptax_rec_data,
            "valor_recente": round(float(ptax_rec_val), 4),
            "valor_fim_olist": round(float(fim_row["ptax_media"]), 4),
            "unidade": "R$/US$",
        },
    ])
    return dim_macro, benchmark


def construir_dim_geo_uf(entrada: Path) -> pd.DataFrame:
    estados = json.loads((entrada / "ibge_estados.json").read_text(encoding="utf-8"))
    pop18_json = json.loads((entrada / "ibge_populacao_2018.json").read_text(encoding="utf-8"))
    pop22_json = json.loads((entrada / "ibge_populacao_2022.json").read_text(encoding="utf-8"))

    pop18 = {
        int(s["localidade"]["id"]): int(s["serie"]["2018"])
        for s in pop18_json[0]["resultados"][0]["series"]
    }
    pop22 = {
        int(s["localidade"]["id"]): int(s["serie"]["2022"])
        for s in pop22_json[0]["resultados"][0]["series"]
    }

    linhas = []
    for est in sorted(estados, key=lambda e: e["sigla"]):
        cod = int(est["id"])
        if cod not in pop18 or cod not in pop22:
            raise ErroDeModelagem(f"População IBGE ausente para UF {est['sigla']} ({cod})")
        linhas.append({
            "uf": est["sigla"].strip().upper(),
            "codigo_ibge": cod,
            "nome": est["nome"].strip(),
            "regiao_sigla": est["regiao"]["sigla"].strip().upper(),
            "regiao": est["regiao"]["nome"].strip(),
            "populacao_ibge": pop18[cod],
            "populacao_censo_2022": pop22[cod],
        })
    if len(linhas) != 27:
        raise ErroDeModelagem(f"Esperadas 27 UFs do IBGE, obtidas {len(linhas)}")
    return pd.DataFrame(linhas)


def construir_dim_faixa_atraso() -> pd.DataFrame:
    linhas = []
    for faixa, ordem in sorted(FAIXAS_ATRASO_ORDEM.items(), key=lambda x: x[1]):
        linhas.append({
            "faixa_atraso": faixa,
            "faixa_atraso_en": FAIXAS_ATRASO_EN[faixa],
            "ordem": ordem,
            "eh_atrasado": 1 if 2 <= ordem <= 5 else 0,
        })
    return pd.DataFrame(linhas)


def construir_fontes_metadados(entrada: Path, contagens_arquivos: dict[str, int]) -> pd.DataFrame:
    manifesto_path = entrada / "manifesto_coleta.json"
    if not manifesto_path.is_file():
        raise ErroDeModelagem(f"Manifesto não encontrado em {manifesto_path}")
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    licencas = manifesto["licencas"]
    nomes_fonte = {
        "olist": "Olist",
        "bcb": "Banco Central (SGS)",
        "ibge": "IBGE",
    }
    linhas = []
    for item in manifesto["arquivos"]:
        arq = item["arquivo"]
        cod_fonte = item["fonte"]
        linhas.append({
            "arquivo": arq,
            "fonte": nomes_fonte.get(cod_fonte, cod_fonte),
            "endpoint": item["url"],
            "registros": contagens_arquivos.get(arq, 0),
            "bytes_total": int(item["bytes_total"]),
            "sha256": item["sha256"],
            "coletado_em_utc": item["coletado_em_utc"],
            "licenca": licencas.get(cod_fonte, ""),
        })
    return pd.DataFrame(linhas)


def gravar_csv_canonico(df: pd.DataFrame, caminho: Path) -> None:
    """Grava CSV UTF-8 com fim de linha LF e valores nulos como string vazia."""
    colunas = list(df.columns)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(colunas)
        for row in df.itertuples(index=False, name=None):
            limpa = []
            for v in row:
                if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v):
                    limpa.append("")
                else:
                    limpa.append(v)
            escritor.writerow(limpa)


def limpar_e_modelar(entrada: Path, saida: Path) -> dict[str, pd.DataFrame]:
    # 1. Carregar CSVs brutos da Olist
    orders = pd.read_csv(entrada / "olist_orders_dataset.csv", dtype=str)
    items = pd.read_csv(
        entrada / "olist_order_items_dataset.csv",
        dtype={"order_id": str, "order_item_id": int, "product_id": str, "seller_id": str},
    )
    pays = pd.read_csv(
        entrada / "olist_order_payments_dataset.csv",
        dtype={"order_id": str, "payment_sequential": int, "payment_type": str, "payment_installments": int},
    )
    revs = pd.read_csv(
        entrada / "olist_order_reviews_dataset.csv",
        dtype={"review_id": str, "order_id": str, "review_score": int},
    )
    custs = pd.read_csv(entrada / "olist_customers_dataset.csv", dtype=str)
    prods = pd.read_csv(entrada / "olist_products_dataset.csv", dtype=str)
    sellers = pd.read_csv(entrada / "olist_sellers_dataset.csv", dtype=str)
    trans = pd.read_csv(
        entrada / "product_category_name_translation.csv",
        encoding="utf-8-sig",
        dtype=str,
    )

    # 2. Dimensões de calendário, macro, geo e faixa de atraso
    dim_calendario = construir_dim_calendario(date(2016, 9, 1), date(2018, 10, 31))
    dim_macro, macro_benchmark = construir_dim_macro_e_benchmark(entrada)
    dim_geo = construir_dim_geo_uf(entrada)
    dim_faixa = construir_dim_faixa_atraso()

    mapa_deflator = dict(zip(dim_macro["ano_mes"], dim_macro["fator_deflator"]))

    # 3. Dimensão de categorias (73 reais + sem_categoria = 74)
    mapa_trad_olist = dict(
        zip(
            trans["product_category_name"].str.strip(),
            trans["product_category_name_english"].str.strip(),
        )
    )
    cats_produtos = sorted(prods["product_category_name"].dropna().str.strip().unique())
    cats_sem_traducao = [c for c in cats_produtos if c not in mapa_trad_olist]
    cat_linhas = []
    for c in [*cats_produtos, "sem_categoria"]:
        trad = mapa_trad_olist.get(c)
        cat_linhas.append({
            "categoria_codigo": c,
            "categoria_pt": nome_categoria_pt(c),
            "categoria_en": nome_categoria_en(c, trad),
            "traducao_oficial_olist": 1 if trad is not None else 0,
        })
    dim_categoria = pd.DataFrame(cat_linhas)

    # 4. Contagem exata de anomalias reais antes de transformar
    n_orders_raw = len(orders)
    n_delivered = int((orders["order_status"] == "delivered").sum())
    n_nao_entregues = int((orders["order_status"] != "delivered").sum())
    n_entregue_sem_data = int(
        ((orders["order_status"] == "delivered") & orders["order_delivered_customer_date"].isna()).sum()
    )
    n_nao_entregue_com_data = int(
        ((orders["order_status"] != "delivered") & orders["order_delivered_customer_date"].notna()).sum()
    )
    n_sem_aprovacao = int(orders["order_approved_at"].isna().sum())
    n_sem_itens = int((~orders["order_id"].isin(items["order_id"])).sum())
    n_sem_pagamento = int((~orders["order_id"].isin(pays["order_id"])).sum())
    n_sem_review = int((~orders["order_id"].isin(revs["order_id"])).sum())
    n_reviews_dup = int(len(revs) - revs["order_id"].nunique())
    n_prods_sem_cat = int(prods["product_category_name"].isna().sum())
    n_pag_not_defined = int((pays["payment_type"] == "not_defined").sum())
    n_pag_parcela_zero = int((pays["payment_installments"] == 0).sum())

    # 5. Deduplicação determinística de avaliações (mantém a mais recente por pedido)
    revs_ord = revs.sort_values(
        by=["order_id", "review_creation_date", "review_answer_timestamp", "review_id"],
        ascending=[True, True, True, True],
        na_position="first",
    )
    revs_dedup = revs_ord.drop_duplicates(subset=["order_id"], keep="last")[
        ["order_id", "review_score"]
    ].copy()

    # 6. Pagamento principal por pedido (maior payment_value; desempate pelo menor payment_sequential)
    pays_ord = pays.sort_values(
        by=["order_id", "payment_value", "payment_sequential"],
        ascending=[True, False, True],
    )
    pays_princ = pays_ord.drop_duplicates(subset=["order_id"], keep="first")[
        ["order_id", "payment_type", "payment_installments"]
    ].copy()

    # 7. Enriquecimento dos itens e identificação de outliers de frete
    prod_cat = prods[["product_id", "product_category_name"]].copy()
    prod_cat["categoria_codigo"] = prod_cat["product_category_name"].fillna("sem_categoria").str.strip()

    sel_uf = sellers[["seller_id", "seller_state", "seller_city"]].copy()
    sel_uf["uf_vendedor"] = sel_uf["seller_state"].str.strip().str.upper()
    sel_uf["cidade_vendedor"] = sel_uf["seller_city"].fillna("").str.strip()

    cust_map = custs[["customer_id", "customer_unique_id", "customer_state"]].copy()
    cust_map["uf_cliente"] = cust_map["customer_state"].str.strip().str.upper()

    ord_base = orders.merge(cust_map[["customer_id", "customer_unique_id", "uf_cliente"]], on="customer_id", how="left")
    dt_compra = pd.to_datetime(ord_base["order_purchase_timestamp"])
    dt_aprov = pd.to_datetime(ord_base["order_approved_at"])
    dt_est = pd.to_datetime(ord_base["order_estimated_delivery_date"])
    dt_real_raw = pd.to_datetime(ord_base["order_delivered_customer_date"])

    ord_base["data_compra"] = dt_compra.dt.strftime("%Y-%m-%d")
    ord_base["ano_mes"] = dt_compra.dt.strftime("%Y-%m")
    ord_base["data_aprovacao"] = dt_aprov.dt.strftime("%Y-%m-%d")
    ord_base["data_entrega_estimada"] = dt_est.dt.strftime("%Y-%m-%d")
    ord_base["flag_entregue"] = (ord_base["order_status"] == "delivered").astype(int)

    # Apenas pedidos entregues mantêm data_entrega_real e métricas de SLA logístico
    entrega_valida = (ord_base["flag_entregue"] == 1) & dt_real_raw.notna()
    ord_base["data_entrega_real"] = np.where(
        entrega_valida, dt_real_raw.dt.strftime("%Y-%m-%d"), None
    )
    dias_entrega = (dt_real_raw.dt.normalize() - dt_compra.dt.normalize()).dt.days
    dias_atraso = (dt_real_raw.dt.normalize() - dt_est.dt.normalize()).dt.days

    ord_base["dias_entrega"] = pd.array(
        np.where(entrega_valida, dias_entrega, np.nan), dtype="Int64"
    )
    ord_base["dias_atraso"] = pd.array(
        np.where(entrega_valida, dias_atraso, np.nan), dtype="Int64"
    )
    ord_base["flag_atraso"] = pd.array(
        np.where(entrega_valida, np.where(dias_atraso > 0, 1, 0), np.nan), dtype="Int64"
    )
    ord_base["faixa_atraso"] = [
        classificar_faixa_atraso(None if pd.isna(v) else int(v))
        for v in ord_base["dias_atraso"]
    ]
    ord_base["fator_deflator"] = ord_base["ano_mes"].map(mapa_deflator)
    if ord_base["fator_deflator"].isna().any():
        raise ErroDeModelagem("Pedido fora da janela do deflator IPCA")

    # Montar fato_itens_pedido
    it = items.merge(
        ord_base[["order_id", "data_compra", "ano_mes", "order_status", "flag_entregue", "uf_cliente", "fator_deflator"]],
        on="order_id",
        how="left",
    )
    it = it.merge(prod_cat[["product_id", "categoria_codigo"]], on="product_id", how="left")
    it["categoria_codigo"] = it["categoria_codigo"].fillna("sem_categoria")
    it = it.merge(sel_uf[["seller_id", "uf_vendedor"]], on="seller_id", how="left")

    it["preco"] = it["price"].round(2)
    it["frete"] = it["freight_value"].round(2)
    it["valor_item_nominal"] = (it["preco"] + it["frete"]).round(2)
    it["valor_item_real_ipca"] = (it["valor_item_nominal"] * it["fator_deflator"]).round(2)
    it["flag_frete_outlier"] = (
        (it["frete"] > LIMIAR_FRETE_EXTREMO_BRL)
        | ((it["preco"] > 0) & (it["frete"] > LIMIAR_RAZAO_FRETE_PRODUTO * it["preco"]))
    ).astype(int)

    n_itens_frete_outlier = int(it["flag_frete_outlier"].sum())
    n_meses_cauda = int(
        ord_base["ano_mes"].isin(["2016-09", "2016-12", "2018-09", "2018-10"]).sum()
    )

    fato_itens = it[[
        "order_id",
        "order_item_id",
        "data_compra",
        "ano_mes",
        "order_status",
        "flag_entregue",
        "uf_cliente",
        "categoria_codigo",
        "seller_id",
        "uf_vendedor",
        "preco",
        "frete",
        "valor_item_nominal",
        "valor_item_real_ipca",
        "flag_frete_outlier",
    ]].rename(columns={"order_status": "status"}).sort_values(
        ["order_id", "order_item_id"]
    ).reset_index(drop=True)

    # 8. Dimensão de vendedores com decil de GMV real entregue (D1 = top 10%)
    sel_gmv = (
        fato_itens[fato_itens["flag_entregue"] == 1]
        .groupby("seller_id", as_index=False)
        .agg(
            gmv_real_entregue=("valor_item_real_ipca", "sum"),
            pedidos_entregues=("order_id", "nunique"),
        )
    )
    dim_vendedor = sel_uf[["seller_id", "uf_vendedor", "cidade_vendedor"]].merge(
        sel_gmv, on="seller_id", how="left"
    )
    dim_vendedor["gmv_real_entregue"] = dim_vendedor["gmv_real_entregue"].fillna(0.0).round(2)
    dim_vendedor["pedidos_entregues"] = dim_vendedor["pedidos_entregues"].fillna(0).astype(int)

    ativos = dim_vendedor[dim_vendedor["pedidos_entregues"] > 0].sort_values(
        by=["gmv_real_entregue", "seller_id"], ascending=[False, True]
    ).copy()
    n_ativos = len(ativos)
    ativos["decil_ordem"] = ((np.arange(n_ativos) * 10) // n_ativos) + 1
    ativos["decil_gmv"] = ativos["decil_ordem"].map(lambda d: f"D{d}")

    inativos = dim_vendedor[dim_vendedor["pedidos_entregues"] == 0].copy()
    inativos["decil_ordem"] = 11
    inativos["decil_gmv"] = "Sem entrega"

    dim_vendedor = pd.concat([ativos, inativos], ignore_index=True).sort_values(
        ["decil_ordem", "gmv_real_entregue", "seller_id"], ascending=[True, False, True]
    ).reset_index(drop=True)

    # 9. Agregação dos itens para fato_pedidos + categoria principal
    it_agg = fato_itens.groupby("order_id", as_index=False).agg(
        qtd_itens=("order_item_id", "count"),
        valor_produtos=("preco", "sum"),
        valor_frete=("frete", "sum"),
        flag_frete_outlier=("flag_frete_outlier", "max"),
    )
    cat_princ = (
        fato_itens.groupby(["order_id", "categoria_codigo"], as_index=False)["valor_item_nominal"]
        .sum()
        .sort_values(["order_id", "valor_item_nominal", "categoria_codigo"], ascending=[True, False, True])
        .drop_duplicates(subset=["order_id"], keep="first")[["order_id", "categoria_codigo"]]
        .rename(columns={"categoria_codigo": "categoria_principal"})
    )

    ped = ord_base.merge(it_agg, on="order_id", how="left")
    ped = ped.merge(cat_princ, on="order_id", how="left")
    ped = ped.merge(revs_dedup, on="order_id", how="left")
    ped = ped.merge(pays_princ, on="order_id", how="left")

    ped["qtd_itens"] = ped["qtd_itens"].fillna(0).astype(int)
    ped["valor_produtos"] = ped["valor_produtos"].fillna(0.0).round(2)
    ped["valor_frete"] = ped["valor_frete"].fillna(0.0).round(2)
    ped["valor_total_nominal"] = (ped["valor_produtos"] + ped["valor_frete"]).round(2)
    ped["valor_total_real_ipca"] = (ped["valor_total_nominal"] * ped["fator_deflator"]).round(2)
    ped["categoria_principal"] = ped["categoria_principal"].fillna("sem_categoria")
    ped["tipo_pagamento_principal"] = ped["payment_type"].fillna("sem_pagamento")
    ped["parcelas"] = ped["payment_installments"].fillna(0).astype(int)
    ped["nota_review"] = ped["review_score"].astype("Int64")
    ped["flag_frete_outlier"] = ped["flag_frete_outlier"].fillna(0).astype(int)

    # Coorte e flag_recompra calculados sobre pedidos entregues por cliente único
    entregues_ord = ped[ped["flag_entregue"] == 1].sort_values(
        by=["customer_unique_id", "order_purchase_timestamp", "order_id"]
    )[["order_id", "customer_unique_id", "ano_mes"]].copy()
    entregues_ord["ordem_cli"] = entregues_ord.groupby("customer_unique_id").cumcount() + 1
    entregues_ord["flag_recompra"] = (entregues_ord["ordem_cli"] > 1).astype(int)
    coorte_cli = entregues_ord.groupby("customer_unique_id")["ano_mes"].min().rename("coorte_mes")
    entregues_ord = entregues_ord.merge(coorte_cli, on="customer_unique_id", how="left")

    ped = ped.merge(
        entregues_ord[["order_id", "coorte_mes", "flag_recompra"]],
        on="order_id",
        how="left",
    )
    ped["flag_recompra"] = ped["flag_recompra"].fillna(0).astype(int)
    ped["coorte_mes"] = ped["coorte_mes"].fillna(ped["ano_mes"])

    ym_ano = ped["ano_mes"].str.slice(0, 4).astype(int)
    ym_mes = ped["ano_mes"].str.slice(5, 7).astype(int)
    co_ano = ped["coorte_mes"].str.slice(0, 4).astype(int)
    co_mes = ped["coorte_mes"].str.slice(5, 7).astype(int)
    ped["meses_desde_coorte"] = (ym_ano - co_ano) * 12 + (ym_mes - co_mes)

    fato_pedidos = ped[[
        "order_id",
        "data_compra",
        "ano_mes",
        "data_aprovacao",
        "data_entrega_estimada",
        "data_entrega_real",
        "dias_entrega",
        "dias_atraso",
        "flag_atraso",
        "faixa_atraso",
        "order_status",
        "flag_entregue",
        "uf_cliente",
        "categoria_principal",
        "nota_review",
        "qtd_itens",
        "valor_produtos",
        "valor_frete",
        "valor_total_nominal",
        "valor_total_real_ipca",
        "tipo_pagamento_principal",
        "parcelas",
        "customer_unique_id",
        "coorte_mes",
        "meses_desde_coorte",
        "flag_recompra",
        "flag_frete_outlier",
    ]].rename(columns={
        "order_status": "status",
        "customer_unique_id": "cliente_unico_id",
    }).sort_values(["data_compra", "order_id"]).reset_index(drop=True)

    # 10. Tabela de auditoria de qualidade com anomalias reais da Olist
    def regra(rid, pt, en, tab, afetadas, base, sev, trat_pt, trat_en):
        return {
            "regra_id": rid,
            "regra": pt,
            "regra_en": en,
            "tabela_origem": tab,
            "linhas_afetadas": int(afetadas),
            "base_referencia": int(base),
            "pct_base": round(100.0 * afetadas / base, 2) if base else 0.0,
            "severidade": sev,
            "tratamento": trat_pt,
            "tratamento_en": trat_en,
        }

    qualidade_auditoria = pd.DataFrame([
        regra(
            "Q01_PEDIDOS_NAO_ENTREGUES",
            "Pedidos cancelados ou não entregues",
            "Canceled or undelivered orders",
            "olist_orders_dataset.csv",
            n_nao_entregues, n_orders_raw,
            "Exclusão analítica",
            "Mantidos em fato_pedidos com flag_entregue=0; excluídos de GMV, SLA e recompra.",
            "Retained in fato_pedidos with flag_entregue=0; excluded from GMV, SLA & retention.",
        ),
        regra(
            "Q02_ENTREGUE_SEM_DATA",
            "Pedidos entregues sem data real de entrega",
            "Delivered orders missing delivery date",
            "olist_orders_dataset.csv",
            n_entregue_sem_data, n_delivered,
            "Exclusão parcial SLA",
            "Contados no GMV entregue; faixa_atraso='Sem entrega' e excluídos do cálculo de prazo/atraso.",
            "Included in delivered GMV; labeled 'Not delivered' and excluded from SLA timing.",
        ),
        regra(
            "Q03_NAO_ENTREGUE_COM_DATA",
            "Pedidos cancelados com data de entrega preenchida",
            "Canceled orders with stray delivery timestamp",
            "olist_orders_dataset.csv",
            n_nao_entregue_com_data, n_orders_raw,
            "Ajuste / Limpeza",
            "data_entrega_real zerada para NULL em pedidos não entregues para evitar contaminação de SLA.",
            "Nulled data_entrega_real on non-delivered orders to prevent SLA contamination.",
        ),
        regra(
            "Q04_SEM_DATA_APROVACAO",
            "Pedidos sem timestamp de aprovação",
            "Orders missing approval timestamp",
            "olist_orders_dataset.csv",
            n_sem_aprovacao, n_orders_raw,
            "Sinalização / Flag",
            "Preservados com data_aprovacao=NULL sem descartar o pedido.",
            "Preserved with data_aprovacao=NULL without dropping the order.",
        ),
        regra(
            "Q05_PEDIDOS_SEM_ITENS",
            "Pedidos sem itens associados",
            "Orders with zero item records",
            "olist_order_items_dataset.csv",
            n_sem_itens, n_orders_raw,
            "Exclusão analítica",
            "Todos são não entregues; recebem qtd_itens=0, valor=0 e categoria 'sem_categoria'.",
            "All are non-delivered; assigned qtd_itens=0, value=0 and 'Uncategorized'.",
        ),
        regra(
            "Q06_PEDIDO_SEM_PAGAMENTO",
            "Pedido sem registro de pagamento",
            "Order missing payment record",
            "olist_order_payments_dataset.csv",
            n_sem_pagamento, n_orders_raw,
            "Ajuste / Fallback",
            "Classificado explicitamente como tipo_pagamento_principal='sem_pagamento' e parcelas=0.",
            "Explicitly labeled tipo_pagamento_principal='sem_pagamento' with 0 installments.",
        ),
        regra(
            "Q07_PEDIDOS_SEM_AVALIACAO",
            "Pedidos sem avaliação do cliente",
            "Orders without customer review",
            "olist_order_reviews_dataset.csv",
            n_sem_review, n_orders_raw,
            "Sinalização / Flag",
            "nota_review mantida NULL; média de notas considera apenas pedidos avaliados.",
            "nota_review kept NULL; average ratings exclude unreviewed orders.",
        ),
        regra(
            "Q08_AVALIACOES_DUPLICADAS",
            "Avaliações duplicadas para o mesmo pedido",
            "Duplicate reviews for the same order",
            "olist_order_reviews_dataset.csv",
            n_reviews_dup, len(revs),
            "Ajuste / Deduplicação",
            "Deduplicação determinística mantendo a avaliação mais recente por order_id.",
            "Deterministic deduplication keeping the latest review per order_id.",
        ),
        regra(
            "Q09_PRODUTOS_SEM_CATEGORIA",
            "Produtos sem categoria cadastrada",
            "Products missing category name",
            "olist_products_dataset.csv",
            n_prods_sem_cat, len(prods),
            "Ajuste / Fallback",
            "Mapeados para categoria_codigo='sem_categoria' ('Sem Categoria' / 'Uncategorized').",
            "Mapped to categoria_codigo='sem_categoria' ('Sem Categoria' / 'Uncategorized').",
        ),
        regra(
            "Q10_CATEGORIAS_SEM_TRADUCAO",
            "Categorias ausentes na tabela oficial de tradução EN",
            "Categories missing from Olist EN translation CSV",
            "product_category_name_translation.csv",
            len(cats_sem_traducao), len(cats_produtos),
            "Ajuste / Fallback",
            "Tradução explícita adicionada para pc_gamer e portateis_cozinha_e_preparadores_de_alimentos.",
            "Explicit fallback translation added for pc_gamer and kitchen small appliances.",
        ),
        regra(
            "Q11_FRETE_OUTLIER_EXTREMO",
            "Itens com frete extremo (>R$ 300 ou >2× preço)",
            "Items with extreme freight (>R$ 300 or >2x price)",
            "olist_order_items_dataset.csv",
            n_itens_frete_outlier, len(items),
            "Sinalização / Flag",
            "Mantidos no GMV real e sinalizados com flag_frete_outlier=1 para auditoria.",
            "Retained in real GMV and flagged with flag_frete_outlier=1 for auditability.",
        ),
        regra(
            "Q12_PAGAMENTO_ANOMALO",
            "Pagamentos 'not_defined' ou com 0 parcelas",
            "Payments typed 'not_defined' or 0 installments",
            "olist_order_payments_dataset.csv",
            n_pag_not_defined + n_pag_parcela_zero, len(pays),
            "Sinalização / Flag",
            "Preservados sem imputação artificial; 0 parcelas excluído da média de parcelas do cartão.",
            "Preserved without synthetic imputation; 0-installment rows excluded from card avg.",
        ),
        regra(
            "Q13_MESES_CAUDA_PARCIAL",
            "Pedidos em meses de cauda parcial (2016-09/12, 2018-09/10)",
            "Orders in partial tail months (2016-09/12, 2018-09/10)",
            "olist_orders_dataset.csv",
            n_meses_cauda, n_orders_raw,
            "Sinalização / Flag",
            "Preservados; YoY executivo compara também janela homogênea jan–ago 2018 vs jan–ago 2017.",
            "Preserved; executive YoY also reports like-for-like Jan–Aug 2018 vs Jan–Aug 2017.",
        ),
    ])

    # 11. Linhagem completa das 17 fontes
    contagens_arquivos = {
        "olist_orders_dataset.csv": len(orders),
        "olist_order_items_dataset.csv": len(items),
        "olist_order_payments_dataset.csv": len(pays),
        "olist_order_reviews_dataset.csv": len(revs),
        "olist_customers_dataset.csv": len(custs),
        "olist_products_dataset.csv": len(prods),
        "olist_sellers_dataset.csv": len(sellers),
        "product_category_name_translation.csv": len(trans),
        "bcb_ipca_433_historico.json": len(json.loads((entrada / "bcb_ipca_433_historico.json").read_text(encoding="utf-8"))),
        "bcb_ipca_433_recente.json": len(json.loads((entrada / "bcb_ipca_433_recente.json").read_text(encoding="utf-8"))),
        "bcb_selic_432_historico.json": len(json.loads((entrada / "bcb_selic_432_historico.json").read_text(encoding="utf-8"))),
        "bcb_selic_432_recente.json": len(json.loads((entrada / "bcb_selic_432_recente.json").read_text(encoding="utf-8"))),
        "bcb_ptax_1_historico.json": len(json.loads((entrada / "bcb_ptax_1_historico.json").read_text(encoding="utf-8"))),
        "bcb_ptax_1_recente.json": len(json.loads((entrada / "bcb_ptax_1_recente.json").read_text(encoding="utf-8"))),
        "ibge_estados.json": len(json.loads((entrada / "ibge_estados.json").read_text(encoding="utf-8"))),
        "ibge_populacao_2018.json": 27,
        "ibge_populacao_2022.json": 27,
    }
    fontes_metadados = construir_fontes_metadados(entrada, contagens_arquivos)

    tabelas = {
        "dim_macro_mensal": dim_macro,
        "dim_calendario": dim_calendario,
        "dim_geo_uf": dim_geo,
        "dim_categoria": dim_categoria,
        "dim_faixa_atraso": dim_faixa,
        "dim_vendedor": dim_vendedor,
        "fato_pedidos": fato_pedidos,
        "fato_itens_pedido": fato_itens,
        "qualidade_auditoria": qualidade_auditoria,
        "fontes_metadados": fontes_metadados,
        "macro_benchmark_atual": macro_benchmark,
    }

    saida.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        gravar_csv_canonico(df, saida / f"{nome}.csv")

    return tabelas


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Limpa dados Olist/BCB/IBGE e gera Star Schema CSV em data/limpa/."
    )
    parser.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    try:
        tabelas = limpar_e_modelar(args.entrada, args.saida)
    except (ErroDeModelagem, FileNotFoundError) as erro:
        sys.exit(f"erro de modelagem: {erro}")

    print(f"Star Schema gravado em {args.saida}:")
    total_mb = 0.0
    for nome, df in tabelas.items():
        tam_mb = (args.saida / f"{nome}.csv").stat().st_size / (1024 * 1024)
        total_mb += tam_mb
        print(f"  {nome + '.csv':28s} {len(df):8,d} linhas  ({tam_mb:5.2f} MB)")
    print(f"Total em data/limpa/: {total_mb:.2f} MB")


if __name__ == "__main__":
    main()
