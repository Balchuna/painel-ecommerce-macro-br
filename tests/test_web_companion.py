"""Testes de integridade do painel web interativo (docs/dados/resumo.json + docs/index.html).

Garante que:
  1. docs/dados/resumo.json reconcilia 100% com todos os 6 CSVs de sql/gabarito/;
  2. todas as fatias aditivas (mensal_regiao, uf_ano, faixa_atraso, categoria_ano_regiao,
     pagamento_ano_regiao, vendedores_decil, qualidade) recompõem exatamente os números do SQL;
  3. docs/index.html, docs/styles.css e docs/app.js existem, não têm placeholders soltos
     nem assets locais quebrados;
  4. (com Playwright disponível) as 4 páginas carregam em PT e EN com zero erros de console,
     zero requisições quebradas, filtros funcionais e nenhum texto 'NaN'/'undefined'.
"""
from __future__ import annotations

import functools
import http.server
import json
import math
import re
import socketserver
import threading
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
RESUMO_PATH = DOCS / "dados" / "resumo.json"
GABARITO_DIR = RAIZ / "sql" / "gabarito"


@pytest.fixture(scope="module")
def resumo() -> dict:
    assert RESUMO_PATH.is_file(), "docs/dados/resumo.json não encontrado"
    raw = RESUMO_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def _checar_sem_nan(obj, caminho="raiz") -> None:
    if isinstance(obj, float):
        assert not (math.isnan(obj) or math.isinf(obj)), f"Valor não finito em {caminho}: {obj}"
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _checar_sem_nan(v, f"{caminho}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _checar_sem_nan(v, f"{caminho}[{i}]")


def test_resumo_json_estrutura_tamanho_e_sem_nan(resumo):
    assert RESUMO_PATH.stat().st_size < 1_000_000, "resumo.json deve ficar compacto (< 1 MB)"
    chaves_obrigatorias = {
        "meta",
        "kpis_gabarito",
        "mensal_regiao",
        "macro_mensal",
        "uf_ano",
        "faixa_atraso",
        "categoria_ano_regiao",
        "pagamento_ano_regiao",
        "parcelas_ano_regiao",
        "coorte",
        "vendedores_decil",
        "qualidade",
    }
    assert chaves_obrigatorias.issubset(set(resumo.keys()))
    _checar_sem_nan(resumo)
    assert resumo["meta"]["mes_base_ipca"] == "2018-10"
    assert len(resumo["meta"]["fontes"]) == 17


def test_resumo_kpis_gabarito_bate_100_porcento_com_sql_01(resumo):
    sql01 = pd.read_csv(GABARITO_DIR / "01_visao_executiva.csv").iloc[0].to_dict()
    kpis = resumo["kpis_gabarito"]
    for chave, valor_sql in sql01.items():
        assert chave in kpis, f"KPI ausente em resumo.json: {chave}"
        assert float(kpis[chave]) == pytest.approx(float(valor_sql), abs=1e-6), (
            f"KPI {chave}: resumo={kpis[chave]} vs SQL={valor_sql}"
        )


def test_resumo_mensal_regiao_e_macro_batem_com_sql_02(resumo):
    sql02 = pd.read_csv(GABARITO_DIR / "02_serie_mensal_macro.csv")

    # Macro mensal
    macro_by_m = {r["ano_mes"]: r for r in resumo["macro_mensal"]}
    assert list(macro_by_m.keys()) == sql02["ano_mes"].tolist()
    for _, row in sql02.iterrows():
        m = macro_by_m[row["ano_mes"]]
        assert m["ipca_mensal_pct"] == pytest.approx(row["ipca_mensal_pct"], abs=0.01)
        assert m["ipca_12m_pct"] == pytest.approx(row["ipca_acum_12m_pct"], abs=0.01)
        assert m["fator_deflator"] == pytest.approx(row["fator_deflator"], abs=1e-6)
        assert m["selic_media"] == pytest.approx(row["selic_media"], abs=1e-4)
        assert m["ptax_media"] == pytest.approx(row["ptax_media"], abs=1e-4)

    # Reagregação aditiva de mensal_regiao -> mensal
    agg = defaultdict(lambda: defaultdict(float))
    for r in resumo["mensal_regiao"]:
        ym = r["ano_mes"]
        for k in (
            "pedidos", "gmv_nominal", "gmv_real", "entregues_com_data",
            "no_prazo", "soma_dias_entrega", "soma_nota", "n_nota",
        ):
            agg[ym][k] += float(r[k])

    for _, row in sql02.iterrows():
        ym = row["ano_mes"]
        a = agg[ym]
        assert int(round(a["pedidos"])) == int(row["pedidos_entregues"]), ym
        assert a["gmv_nominal"] == pytest.approx(row["gmv_nominal"], abs=0.05), ym
        assert a["gmv_real"] == pytest.approx(row["gmv_real_ipca"], abs=0.05), ym
        if a["entregues_com_data"] > 0:
            pct_np = round(100.0 * a["no_prazo"] / a["entregues_com_data"], 2)
            assert pct_np == pytest.approx(row["pct_no_prazo"], abs=0.02), ym
            prazo = round(a["soma_dias_entrega"] / a["entregues_com_data"], 2)
            assert prazo == pytest.approx(row["prazo_medio_dias"], abs=0.02), ym
        if a["n_nota"] > 0:
            nota = round(a["soma_nota"] / a["n_nota"], 2)
            assert nota == pytest.approx(row["nota_media"], abs=0.02), ym


def test_resumo_uf_ano_reagregado_bate_com_sql_03(resumo):
    sql03 = pd.read_csv(GABARITO_DIR / "03_logistica_sla_uf.csv").set_index("uf")

    agg = defaultdict(lambda: defaultdict(float))
    pop_uf = {}
    for r in resumo["uf_ano"]:
        uf = r["uf"]
        pop_uf[uf] = r["populacao"]
        for k in (
            "pedidos", "gmv_nominal", "gmv_real", "frete", "entregues_com_data",
            "no_prazo", "soma_dias_entrega", "n_atrasados", "soma_dias_atraso", "soma_nota", "n_nota",
        ):
            agg[uf][k] += float(r[k])

    assert set(agg.keys()) == set(sql03.index)
    for uf, row in sql03.iterrows():
        a = agg[uf]
        assert pop_uf[uf] == int(row["populacao_ibge"]), uf
        assert int(round(a["pedidos"])) == int(row["pedidos_entregues"]), uf
        assert a["gmv_nominal"] == pytest.approx(row["gmv_nominal"], abs=0.05), uf
        assert a["gmv_real"] == pytest.approx(row["gmv_real_ipca"], abs=0.05), uf
        gmv_100k = round(a["gmv_real"] * 100_000.0 / pop_uf[uf], 2)
        assert gmv_100k == pytest.approx(row["gmv_real_100k_hab"], abs=0.05), uf
        pct_np = round(100.0 * a["no_prazo"] / a["entregues_com_data"], 2)
        assert pct_np == pytest.approx(row["pct_no_prazo"], abs=0.02), uf
        prazo = round(a["soma_dias_entrega"] / a["entregues_com_data"], 2)
        assert prazo == pytest.approx(row["prazo_medio_dias"], abs=0.02), uf
        nota = round(a["soma_nota"] / a["n_nota"], 2)
        assert nota == pytest.approx(row["nota_media"], abs=0.02), uf


def test_resumo_faixa_atraso_reagregado_bate_com_sql_04(resumo):
    sql04 = pd.read_csv(GABARITO_DIR / "04_atraso_vs_avaliacao.csv").set_index("ordem")

    agg = defaultdict(lambda: defaultdict(float))
    nomes = {}
    for r in resumo["faixa_atraso"]:
        o = int(r["ordem"])
        nomes[o] = r["faixa"]
        for k in ("pedidos", "soma_nota", "n_nota", "notas_5", "notas_1", "soma_dias_entrega", "soma_dias_atraso"):
            agg[o][k] += float(r[k])

    assert sorted(agg.keys()) == [1, 2, 3, 4, 5]
    for ordem, row in sql04.iterrows():
        a = agg[int(ordem)]
        assert nomes[int(ordem)] == row["faixa_atraso"]
        assert int(round(a["pedidos"])) == int(row["pedidos"]), ordem
        assert int(round(a["n_nota"])) == int(row["pedidos_avaliados"]), ordem
        assert round(a["soma_nota"] / a["n_nota"], 2) == pytest.approx(row["nota_media"], abs=0.02), ordem
        assert round(100.0 * a["notas_5"] / a["n_nota"], 2) == pytest.approx(row["pct_nota_5"], abs=0.02), ordem
        assert round(100.0 * a["notas_1"] / a["n_nota"], 2) == pytest.approx(row["pct_nota_1"], abs=0.02), ordem


def test_resumo_categorias_reagregadas_batem_com_sql_05(resumo):
    sql05 = pd.read_csv(GABARITO_DIR / "05_comercial_categorias.csv").set_index("categoria_codigo")

    agg = defaultdict(lambda: defaultdict(float))
    for r in resumo["categoria_ano_regiao"]:
        c = r["categoria_codigo"]
        for k in ("itens", "gmv_nominal", "gmv_real", "frete", "soma_nota", "n_nota"):
            agg[c][k] += float(r[k])

    assert set(agg.keys()) == set(sql05.index)
    for cod, row in sql05.iterrows():
        a = agg[cod]
        assert int(round(a["itens"])) == int(row["itens_vendidos"]), cod
        assert a["gmv_nominal"] == pytest.approx(row["gmv_nominal"], abs=0.10), cod
        assert a["gmv_real"] == pytest.approx(row["gmv_real_ipca"], abs=0.10), cod
        if a["n_nota"] > 0:
            assert round(a["soma_nota"] / a["n_nota"], 2) == pytest.approx(row["nota_media"], abs=0.02), cod


def test_resumo_qualidade_e_vendedores_batem_com_sql(resumo):
    sql01 = pd.read_csv(GABARITO_DIR / "01_visao_executiva.csv").iloc[0]
    sql06 = pd.read_csv(GABARITO_DIR / "06_qualidade_dados.csv")

    q = resumo["qualidade"]
    assert q["gabarito"]["consultas"] == 6
    assert q["gabarito"]["conferem"] is True
    assert q["contagens"]["pedidos_brutos"] == int(sql01["pedidos_brutos"])
    assert q["contagens"]["pedidos_analisados"] == int(sql01["pedidos_entregues"])
    assert len(q["regras"]) == len(sql06)

    regras_json = {r["regra_id"]: r for r in q["regras"]}
    for _, row in sql06.iterrows():
        rj = regras_json[row["regra_id"]]
        assert int(rj["linhas_afetadas"]) == int(row["linhas_afetadas"])
        assert float(rj["pct"]) == pytest.approx(float(row["pct_base"]), abs=0.01)

    decis = resumo["vendedores_decil"]
    assert len(decis) == 10
    assert decis[0]["decil"] == "D1"
    assert float(decis[0]["pct_gmv"]) == pytest.approx(float(sql01["pct_gmv_top10_vendedores"]), abs=0.02)
    assert float(decis[-1]["pct_gmv_acumulado"]) == pytest.approx(100.0, abs=0.05)


def test_arquivos_web_existem_sem_assets_quebrados_nem_placeholders():
    for nome in ("index.html", "styles.css", "app.js"):
        caminho = DOCS / nome
        assert caminho.is_file(), f"docs/{nome} ausente"
        texto = caminho.read_text(encoding="utf-8")
        assert len(texto.strip()) > 0
        # Nenhum placeholder ‹...› do DESIGN_SPEC pode sobrar no código publicado
        assert "‹" not in texto and "›" not in texto, f"Placeholder não substituído em docs/{nome}"

    html = (DOCS / "index.html").read_text(encoding="utf-8")
    # Todo href/src relativo (não http/https/data/#) precisa existir em docs/
    for attr in re.findall(r'''(?:href|src)=["']([^"']+)["']''', html):
        if attr.startswith(("http://", "https://", "data:", "#", "mailto:")):
            continue
        assert (DOCS / attr).is_file(), f"Asset local quebrado em index.html: {attr}"


@pytest.mark.browser
def test_web_companion_carrega_4_paginas_pt_e_en_sem_erros():
    playwright_sync = pytest.importorskip("playwright.sync_api", reason="Playwright não instalado")

    class ServidorSilencioso(socketserver.TCPServer):
        allow_reuse_address = True

    class HandlerSilencioso(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DOCS), **kwargs)

        def log_message(self, format, *args):
            pass

    servidor = ServidorSilencioso(("127.0.0.1", 0), HandlerSilencioso)
    porta = servidor.server_address[1]
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()

    erros_console: list[str] = []
    erros_pagina: list[str] = []
    falhas_http: list[str] = []

    try:
        with playwright_sync.sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Chromium do Playwright indisponível neste ambiente: {exc}")

            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.on("console", lambda m: erros_console.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: erros_pagina.append(str(e)))
                page.on(
                    "response",
                    lambda r: falhas_http.append(f"{r.status} {r.url}") if r.status >= 400 else None,
                )

                page.goto(f"http://127.0.0.1:{porta}/index.html", wait_until="networkidle")
                page.wait_for_selector("#p1 .kpi, #p1 .card, #p1 svg", timeout=10_000)

                for lang in ("pt", "en"):
                    page.click(f'button[data-lang="{lang}"]')
                    for pid in ("p1", "p2", "p3", "p4"):
                        page.click(f"#tab-{pid}")
                        page.wait_for_selector(f"#{pid}:not([hidden])", timeout=5_000)
                        texto = page.locator(f"#{pid}").inner_text()
                        assert len(texto.strip()) > 100, f"Página {pid} ({lang}) vazia"
                        for proibido in ("NaN", "undefined", "‹", "›", "{f}", "true/6", "n/d", "n/a"):
                            assert proibido not in texto.lower() if proibido in ("n/d", "n/a") else proibido not in texto, (
                                f"Texto inválido {proibido!r} visível em {pid} ({lang})"
                            )
                        if pid == "p4":
                            assert "6/6" in texto and "✗" not in texto, f"Selo Gabarito SQL quebrado em p4 ({lang})"
                            assert "78,00%" not in texto and "78.00%" not in texto, (
                                f"Bug de 100x em % base (<1%) detectado em p4 ({lang})"
                            )

                # Testa interação de filtro na página 1 em PT
                page.click('button[data-lang="pt"]')
                page.click("#tab-p1")
                texto_antes = page.locator("#p1").inner_text()
                opcoes_ano = page.locator("#f-ano option").all_text_contents()
                assert len(opcoes_ano) >= 3
                page.select_option("#f-ano", index=1)
                texto_depois = page.locator("#p1").inner_text()
                assert texto_depois != texto_antes, "Filtro de Ano não atualizou a página 1"
                page.click("#f-reset")
            finally:
                browser.close()
    finally:
        servidor.shutdown()
        servidor.server_close()

    assert not erros_console, f"Erros de console no navegador: {erros_console}"
    assert not erros_pagina, f"Exceções JS na página: {erros_pagina}"
    assert not falhas_http, f"Requisições HTTP com erro: {falhas_http}"
