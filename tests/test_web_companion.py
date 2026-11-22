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
    assert 'data-acento="azul"' in html, "docs/index.html deve declarar data-acento=\"azul\""
    # Todo href/src relativo (não http/https/data/#) precisa existir em docs/
    for attr in re.findall(r'''(?:href|src)=["']([^"']+)["']''', html):
        if attr.startswith(("http://", "https://", "data:", "#", "mailto:")):
            continue
        assert (DOCS / attr).is_file(), f"Asset local quebrado em index.html: {attr}"


def test_padrao_bi_tokens_css_identico_e_resumo_js_presente():
    tokens_raiz = RAIZ / "marca" / "tokens.css"
    tokens_docs = DOCS / "marca" / "tokens.css"
    assert tokens_raiz.is_file(), "marca/tokens.css ausente"
    assert tokens_docs.is_file(), "docs/marca/tokens.css ausente"
    assert tokens_docs.read_bytes() == tokens_raiz.read_bytes(), (
        "docs/marca/tokens.css diverge de marca/tokens.css"
    )

    resumo_js = DOCS / "dados" / "resumo.js"
    assert resumo_js.is_file(), "docs/dados/resumo.js ausente"
    conteudo_js = resumo_js.read_text(encoding="utf-8")
    assert conteudo_js.startswith("window.RESUMO = "), "docs/dados/resumo.js inválido"
    embutido = json.loads(conteudo_js.removeprefix("window.RESUMO = ").rstrip().rstrip(";"))
    original = json.loads(RESUMO_PATH.read_text(encoding="utf-8"))
    assert embutido == original, "docs/dados/resumo.js desatualizado em relação a docs/dados/resumo.json"


def test_padrao_bi_zero_hex_escrito_a_mao_em_docs_web():
    hex6 = re.compile(r"#[0-9a-fA-F]{6}\b")
    hex3 = re.compile(r"(?<![&\w])#[0-9a-fA-F]{3}\b")
    for caminho in sorted(
        list(DOCS.glob("*.html")) + list(DOCS.glob("*.css")) + list(DOCS.glob("*.js"))
    ):
        texto = caminho.read_text(encoding="utf-8")
        assert not hex6.findall(texto), f"Cor hex #RRGGBB fora de marca/ em docs/{caminho.name}: {hex6.findall(texto)}"
        assert not hex3.findall(texto), f"Cor hex #RGB fora de marca/ em docs/{caminho.name}: {hex3.findall(texto)}"


def test_padrao_bi_conformidade_taste_md_e_regras_web():
    css = (DOCS / "styles.css").read_text(encoding="utf-8")
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    js = (DOCS / "app.js").read_text(encoding="utf-8")

    # Proibições de CSS (REGRAS.md + .unslop-ui/taste.md)
    assert not re.search(r"text-transform\s*:\s*uppercase", css, re.I), "uppercase proibido em styles.css"
    assert not re.search(r"(linear|radial|conic)-gradient", css, re.I), "gradiente proibido em styles.css"
    assert not re.search(r"backdrop-filter", css, re.I), "vidro fosco (backdrop-filter) proibido em styles.css"
    assert not re.search(r"font-weight\s*:\s*(300|500|700|800|900|bold)\b", css, re.I), (
        "somente pesos 400 e 600 são permitidos em styles.css"
    )
    sombras = re.findall(r"box-shadow\s*:\s*([^;]+);", css, re.I)
    for s in sombras:
        assert s.strip() in ("none", "var(--sombra-flutuante)"), f"box-shadow não autorizado: {s}"

    # Zero CDN Google Fonts ou Segoe UI externa
    for nome, texto in (("index.html", html), ("styles.css", css), ("app.js", js)):
        assert not re.search(r"fonts\.googleapis\.com|fonts\.gstatic\.com", texto, re.I), (
            f"Google Fonts CDN proibido em docs/{nome}"
        )

    # Zero ícones unicode, travessão em texto UI, palavras proibidas e exclamação em strings UI
    icones_unicode = re.compile(r"[▲▼→●✓★]")
    palavras_proibidas = re.compile(r"\b(insights?|jornada|potencializar|alavancar|storytelling)\b", re.I)
    for nome, texto in (("index.html", html), ("styles.css", css), ("app.js", js)):
        assert not icones_unicode.search(texto), f"Ícone unicode proibido em docs/{nome}"
        assert "—" not in texto, f"Travessão (—) proibido em docs/{nome}"
        assert not palavras_proibidas.search(texto), (
            f"Palavra proibida pelo taste.md em docs/{nome}: {palavras_proibidas.findall(texto)}"
        )

    # Zero '!' em texto visível do HTML (ignora <!doctype> e comentários <!-- -->)
    html_sem_tags = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html_sem_tags = re.sub(r"<[^>]+>", " ", html_sem_tags)
    assert "!" not in html_sem_tags, "Ponto de exclamação (!) proibido no texto de docs/index.html"

    # Zero '!' em literais de string de UI em docs/app.js (ignora comentários e regex /!/g)
    js_sem_coment = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js_sem_coment = re.sub(r"//[^\n]*", "", js_sem_coment)
    js_sem_coment = re.sub(r"/!/[gimsuy]*", "", js_sem_coment)
    for linha in js_sem_coment.splitlines():
        if "!" not in linha:
            continue
        for m in re.finditer(r'"([^"\\\n]*(?:\\.[^"\\\n]*)*)"|\'([^\'\\\n]*(?:\\.[^\'\\\n]*)*)\'', linha):
            valor = m.group(1) if m.group(1) is not None else m.group(2)
            assert "!" not in valor, f"Ponto de exclamação (!) em string de UI em docs/app.js: {valor!r}"


@pytest.mark.browser
def test_web_companion_carrega_4_paginas_claro_escuro_mobile_pt_en_e_filtros():
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
    urls_ok: set[str] = set()

    def registrar_resposta(r):
        if r.status >= 400:
            falhas_http.append(f"{r.status} {r.url}")
        else:
            urls_ok.add(r.url)

    def checar_texto_limpo(texto: str, contexto: str):
        assert len(texto.strip()) > 100, f"Página vazia em {contexto}"
        for proibido in ("NaN", "undefined", "‹", "›", "{f}", "true/6", "!", "—", "▲", "▼", "→", "●", "✓", "★"):
            assert proibido not in texto, f"Texto proibido {proibido!r} visível em {contexto}"
        for palavra in ("n/d", "n/a", "insights", "insight", "jornada", "potencializar", "alavancar", "storytelling"):
            assert not re.search(rf"\b{re.escape(palavra)}\b", texto, re.I), (
                f"Palavra proibida {palavra!r} visível em {contexto}"
            )

    try:
        with playwright_sync.sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Chromium do Playwright indisponível neste ambiente: {exc}")

            try:
                # 1. Desktop 1280x720: Light e Dark, PT e EN, todas as 4 páginas + filtros
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.on("console", lambda m: erros_console.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: erros_pagina.append(str(e)))
                page.on("response", registrar_resposta)

                page.goto(f"http://127.0.0.1:{porta}/index.html", wait_until="networkidle")
                page.wait_for_selector("#p1 .kpi, #p1 .cartao, #p1 svg", timeout=10_000)

                assert any(u.endswith("/marca/tokens.css") for u in urls_ok), "marca/tokens.css não carregou (200)"
                assert any(u.endswith("/dados/resumo.js") for u in urls_ok), "dados/resumo.js não carregou (200)"

                for tema in ("light", "dark"):
                    page.click(f'button[data-tema="{tema}"]')
                    assert page.evaluate("document.documentElement.dataset.theme") == tema
                    for lang in ("pt", "en"):
                        page.click(f'button[data-lang="{lang}"]')
                        for pid in ("p1", "p2", "p3", "p4"):
                            page.click(f"#tab-{pid}")
                            page.wait_for_selector(f"#{pid}:not([hidden])", timeout=5_000)
                            texto = page.locator(f"#{pid}").inner_text()
                            checar_texto_limpo(texto, f"desktop-{tema}-{lang}-{pid}")
                            if pid == "p4":
                                assert "6/6" in texto and "✗" not in texto, (
                                    f"Selo Gabarito SQL quebrado em p4 ({tema}/{lang})"
                                )
                                assert "78,00%" not in texto and "78.00%" not in texto, (
                                    f"Bug de 100x em % base (<1%) detectado em p4 ({tema}/{lang})"
                                )

                # Interações: filtro de ano, destaque cruzado por região e filtro de categoria
                page.click('button[data-tema="light"]')
                page.click('button[data-lang="pt"]')
                page.click("#tab-p1")
                texto_base = page.locator("#p1").inner_text()

                page.click('#filtro-ano button[data-ano="2017"]')
                texto_ano = page.locator("#p1").inner_text()
                assert texto_ano != texto_base, "Filtro de Ano (2017) não atualizou a página 1"
                page.click("#f-reset")

                page.click('#filtro-regiao button[data-regiao="Norte"]')
                texto_reg = page.locator("#p1").inner_text()
                assert texto_reg != texto_base and "Norte" in texto_reg, (
                    "Destaque cruzado por região (Norte) não atualizou a página 1"
                )
                page.click('#filtro-regiao button[data-regiao=""]')

                page.click("#tab-p3")
                texto_p3_antes = page.locator("#p3").inner_text()
                assert page.locator("#f-categoria option").count() > 5
                page.select_option("#f-categoria", index=1)
                texto_p3_depois = page.locator("#p3").inner_text()
                assert texto_p3_depois != texto_p3_antes, "Filtro de Categoria não atualizou a página 3"
                page.click("#f-reset")
                page.close()

                # 2. Mobile 390x844: Light e Dark, todas as 4 páginas, ZERO overflow horizontal
                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                mobile.on("console", lambda m: erros_console.append(m.text) if m.type == "error" else None)
                mobile.on("pageerror", lambda e: erros_pagina.append(str(e)))
                mobile.on("response", registrar_resposta)
                mobile.goto(f"http://127.0.0.1:{porta}/index.html", wait_until="networkidle")
                mobile.wait_for_selector("#p1 .kpi", timeout=10_000)

                for tema in ("light", "dark"):
                    mobile.click(f'button[data-tema="{tema}"]')
                    for pid in ("p1", "p2", "p3", "p4"):
                        mobile.click(f"#tab-{pid}")
                        mobile.wait_for_selector(f"#{pid}:not([hidden])", timeout=5_000)
                        overflow = mobile.evaluate(
                            "document.documentElement.scrollWidth - window.innerWidth"
                        )
                        assert overflow <= 1, f"Overflow horizontal no celular 390px ({tema}/{pid}): +{overflow}px"
                        checar_texto_limpo(mobile.locator(f"#{pid}").inner_text(), f"mobile-{tema}-{pid}")
                mobile.close()
            finally:
                browser.close()
    finally:
        servidor.shutdown()
        servidor.server_close()

    assert not erros_console, f"Erros de console no navegador: {erros_console}"
    assert not erros_pagina, f"Exceções JS na página: {erros_pagina}"
    assert not falhas_http, f"Requisições HTTP com erro: {falhas_http}"
