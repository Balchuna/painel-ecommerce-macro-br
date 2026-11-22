"""Validação estrutural do tema (tema/tema.json) e do projeto Power BI (PBIP: TMDL + PBIR).

Confere:
  - esquema, paleta editorial e contraste WCAG AA de tema/tema.json;
  - determinismo e portabilidade de scripts/montar_pbip.py (sem vazamento de caminhos locais);
  - validação de todas as 4 páginas PBIR, esquemas JSON, ausência de placeholders ‹…›;
  - ZERO caixas delimitadoras (bounding boxes) sobrepostas e limites estritos dentro de 1280×720;
  - integridade de todos os campos (Column/Measure) usados nos visuais contra o modelo TMDL;
  - deserialização real do modelo TMDL pela biblioteca TOM oficial do Power BI Desktop
    (tests/ler_modelo_tom.ps1; pulado automaticamente em CI Linux sem Power BI instalado).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
POWERBI = RAIZ / "powerbi"
GERADOR = RAIZ / "scripts" / "montar_pbip.py"
LER_TOM = RAIZ / "tests" / "ler_modelo_tom.ps1"
TEMA_PATH = RAIZ / "tema" / "tema.json"
DAX_PATH = RAIZ / "dax" / "medidas.dax"
MODELO_MD = RAIZ / "docs" / "MODELO.md"

MODELO_PBIP = POWERBI / "PainelEcommerceMacro.SemanticModel" / "definition"
RELATORIO = POWERBI / "PainelEcommerceMacro.Report" / "definition"
TEMA_REGISTRADO = (
    POWERBI / "PainelEcommerceMacro.Report" / "StaticResources" / "RegisteredResources" / "tema.json"
)

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
LOCAIS = re.compile(r"(^|/)\.pbi/")

PAGINAS_ORDEM = ["visao_executiva", "logistica_sla", "comercial", "qualidade"]
TABELAS_ESPERADAS = {
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
}
TIPOS_MD_PARA_TOM = {
    "número inteiro": "Int64",
    "número decimal": "Double",
    "texto": "String",
    "data": "DateTime",
    "verdadeiro/falso": "Boolean",
}


def luminancia_relativa(hex_cor: str) -> float:
    r, g, b = (int(hex_cor[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    canais = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def contraste_wcag(c1: str, c2: str) -> float:
    l1, l2 = luminancia_relativa(c1), luminancia_relativa(c2)
    maior, menor = max(l1, l2), min(l1, l2)
    return (maior + 0.05) / (menor + 0.05)


def coletar_hex_json(obj) -> list[str]:
    cores = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "color" and isinstance(v, str):
                cores.append(v)
            else:
                cores.extend(coletar_hex_json(v))
    elif isinstance(obj, list):
        for item in obj:
            cores.extend(coletar_hex_json(item))
    return cores


def arquivos_pbip(pasta: Path) -> dict[str, bytes]:
    return {
        p.relative_to(pasta).as_posix(): p.read_bytes()
        for p in sorted(pasta.rglob("*"))
        if p.is_file() and not LOCAIS.search(p.relative_to(pasta).as_posix())
    }


def gerar_pbip(saida: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GERADOR), "--saida", str(saida), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def compacto(texto: str) -> str:
    return " ".join(texto.split())


def medidas_dax_arquivo() -> dict[str, str]:
    texto = DAX_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    bloco = texto.split("\nEVALUATE", 1)[0]
    partes = re.split(r"^\s*MEASURE\s+Medidas\[([^\]]+)\]\s*=", bloco, flags=re.M)
    corpos: dict[str, str] = {}
    for nome, corpo in zip(partes[1::2], partes[2::2]):
        linhas = corpo.rstrip().splitlines()
        while linhas and (not linhas[-1].strip() or linhas[-1].strip().startswith("//")):
            linhas.pop()
        corpos[nome] = compacto("\n".join(linhas))
    return corpos


def relacionamentos_modelo_md() -> list[tuple[str, str]]:
    texto = MODELO_MD.read_text(encoding="utf-8")
    secao = re.search(r"^## Relacionamentos\b(.*?)(?=^## |\Z)", texto, re.M | re.S).group(1)
    pares = re.findall(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", secao, re.M)
    return [(a, b) for a, b in pares]


def campos_do_modelo_tmdl() -> set[tuple[str, str, str]]:
    campos: set[tuple[str, str, str]] = set()
    for caminho in (MODELO_PBIP / "tables").glob("*.tmdl"):
        texto = caminho.read_text(encoding="utf-8")
        tabela = re.search(r"^table (\S+)", texto, re.M).group(1)
        for tipo, nome in re.findall(r"^\t(column|measure) ('(?:[^']|'')*'|[^\s=]+)", texto, re.M):
            if nome.startswith("'"):
                nome = nome[1:-1].replace("''", "'")
            campos.add(("Column" if tipo == "column" else "Measure", tabela, nome))
    return campos


def campos_usados_visual(objeto, apelidos=None):
    apelidos = dict(apelidos or {})
    if isinstance(objeto, dict):
        for origem in objeto.get("From", []):
            if "Entity" in origem:
                apelidos[origem["Name"]] = origem["Entity"]
        for tipo in ("Column", "Measure"):
            campo = objeto.get(tipo)
            if isinstance(campo, dict) and "Property" in campo:
                referencia = campo["Expression"]["SourceRef"]
                entidade = referencia.get("Entity") or apelidos.get(referencia.get("Source"))
                if entidade:
                    yield tipo, entidade, campo["Property"]
        for valor in objeto.values():
            yield from campos_usados_visual(valor, apelidos)
    elif isinstance(objeto, list):
        for valor in objeto:
            yield from campos_usados_visual(valor, apelidos)


def iterar_visuais():
    for caminho in sorted(RELATORIO.glob("pages/*/visuals/*/visual.json")):
        yield caminho.parts[-4], json.loads(caminho.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# 1. Tema editorial (tema/tema.json)


def test_tema_json_valido_tokens_e_contraste_wcag():
    tema = json.loads(TEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(tema["name"], str) and tema["name"].strip()
    assert len(tema["dataColors"]) >= 8
    for cor in tema["dataColors"]:
        assert HEX_RE.fullmatch(cor), f"Hex inválido em dataColors: {cor}"

    # Paleta editorial principal definida em DESIGN_SPEC.md
    assert tema["dataColors"][0].upper() == "#1E3A5F"
    assert tema["dataColors"][1].upper() == "#0D9488"
    assert tema["dataColors"][2].upper() == "#D97706"
    assert tema["background"].upper() == "#FFFFFF"
    assert tema["foreground"].upper() == "#0F172A"
    assert tema["good"].upper() == "#0D9488"
    assert tema["neutral"].upper() == "#D97706"
    assert tema["bad"].upper() == "#DC2626"

    # Todas as cores em visualStyles são hex válidos
    for cor in coletar_hex_json(tema["visualStyles"]):
        assert HEX_RE.fullmatch(cor), f"Hex inválido em visualStyles: {cor}"

    # Contraste WCAG AA mínimo sobre fundo branco #FFFFFF
    assert contraste_wcag("#0F172A", "#FFFFFF") >= 15.0
    assert contraste_wcag("#64748B", "#FFFFFF") >= 4.5
    assert contraste_wcag("#1E3A5F", "#FFFFFF") >= 10.0
    assert contraste_wcag("#DC2626", "#FFFFFF") >= 4.5

    # Cópia registrada no relatório PBIR deve ser idêntica a tema/tema.json
    assert json.loads(TEMA_REGISTRADO.read_text(encoding="utf-8")) == tema
    relatorio = json.loads((RELATORIO / "report.json").read_text(encoding="utf-8"))
    assert relatorio["themeCollection"]["customTheme"]["name"] == "tema.json"


# ---------------------------------------------------------------------------------------------
# 2. Gerador PBIP: determinismo e portabilidade


@pytest.fixture(scope="module")
def pbip_gerado(tmp_path_factory) -> Path:
    saida = tmp_path_factory.mktemp("pbip_novo")
    gerar_pbip(saida)
    return saida


def test_pbip_versionado_identico_ao_gerador(pbip_gerado):
    versionado = arquivos_pbip(POWERBI)
    novo = arquivos_pbip(pbip_gerado)
    assert sorted(versionado) == sorted(novo)
    diferentes = [k for k in novo if versionado[k] != novo[k]]
    assert not diferentes, f"powerbi/ desatualizado ({diferentes[:5]}); rode python scripts/montar_pbip.py"


def test_pbip_gerador_deterministico_e_aceita_pasta_dados(pbip_gerado, tmp_path):
    copia = tmp_path / "copia"
    gerar_pbip(copia)
    assert arquivos_pbip(copia) == arquivos_pbip(pbip_gerado)

    custom = tmp_path / "custom"
    gerar_pbip(custom, "--pasta-dados", r"E:\dados\limpa")
    expr = (custom / "PainelEcommerceMacro.SemanticModel" / "definition" / "expressions.tmdl").read_text(
        encoding="utf-8"
    )
    assert '"E:\\dados\\limpa" meta' in expr
    assert "caminho\\do\\projeto" not in expr


def test_pbip_portavel_sem_caminho_de_usuario_local():
    expr = (MODELO_PBIP / "expressions.tmdl").read_text(encoding="utf-8")
    assert '"C:\\caminho\\do\\projeto\\data\\limpa" meta' in expr
    for nome, conteudo in arquivos_pbip(POWERBI).items():
        assert not re.search(rb"[A-Za-z]:(\\){1,2}Users(\\){1,2}", conteudo), f"Caminho pessoal vazou em {nome}"


# ---------------------------------------------------------------------------------------------
# 3. Relatório PBIR: 4 páginas, esquemas JSON, ZERO sobreposição e campos válidos


def test_pbir_paginas_esquemas_e_canvas_1280x720():
    pages_meta = json.loads((RELATORIO / "pages" / "pages.json").read_text(encoding="utf-8"))
    assert pages_meta["pageOrder"] == PAGINAS_ORDEM
    assert pages_meta["$schema"].startswith("https://developer.microsoft.com/json-schemas/fabric/")

    for arq in sorted(RELATORIO.rglob("*.json")):
        dados = json.loads(arq.read_text(encoding="utf-8"))
        assert "$schema" in dados, arq
        assert dados["$schema"].startswith("https://developer.microsoft.com/json-schemas/fabric/"), arq
        texto = arq.read_text(encoding="utf-8")
        assert "‹" not in texto and "›" not in texto, f"Placeholder não resolvido em {arq.relative_to(POWERBI)}"

    for pid in PAGINAS_ORDEM:
        page = json.loads((RELATORIO / "pages" / pid / "page.json").read_text(encoding="utf-8"))
        assert (page["width"], page["height"]) == (1280, 720), pid
        vis = list((RELATORIO / "pages" / pid / "visuals").glob("*/visual.json"))
        assert len(vis) >= 10, f"Página {pid} tem poucos visuais ({len(vis)})"


def test_pbir_zero_sobreposicao_de_visuais_e_dentro_do_canvas():
    """Garante que nenhum par de visuais na mesma página se sobrepõe e todos cabem em 1280×720."""
    for pid in PAGINAS_ORDEM:
        caixas: list[tuple[str, float, float, float, float]] = []
        for caminho in sorted((RELATORIO / "pages" / pid / "visuals").glob("*/visual.json")):
            v = json.loads(caminho.read_text(encoding="utf-8"))
            pos = v["position"]
            x, y, w, h = float(pos["x"]), float(pos["y"]), float(pos["width"]), float(pos["height"])
            nome = v["name"]
            assert w > 0 and h > 0, (pid, nome, pos)
            assert x >= 0 and y >= 0, (pid, nome, pos)
            assert x + w <= 1280.0 + 1e-6 and y + h <= 720.0 + 1e-6, (
                f"Visual fora do canvas 1280x720 em {pid}/{nome}: x={x}, y={y}, w={w}, h={h}"
            )
            caixas.append((nome, x, y, x + w, y + h))

        sobreposicoes = []
        for i in range(len(caixas)):
            n1, x1a, y1a, x1b, y1b = caixas[i]
            for j in range(i + 1, len(caixas)):
                n2, x2a, y2a, x2b, y2b = caixas[j]
                if x1a < x2b and x2a < x1b and y1a < y2b and y2a < y1b:
                    sobreposicoes.append((n1, n2))
        assert not sobreposicoes, f"Visuais sobrepostos na página {pid}: {sobreposicoes}"


def test_pbir_visuais_referenciam_apenas_campos_existentes_e_sem_nativeQueryRef_duplicado():
    modelo = campos_do_modelo_tmdl()
    for pagina, visual in iterar_visuais():
        for campo in campos_usados_visual(visual):
            assert campo in modelo, f"Campo inexistente em {pagina}/{visual['name']}: {campo}"

        estado = visual["visual"].get("query", {}).get("queryState", {})
        por_nome: dict[str, set[str]] = {}
        for papel in estado.values():
            for proj in papel.get("projections", []):
                por_nome.setdefault(proj["nativeQueryRef"], set()).add(proj["queryRef"])
        repetidos = {k: v for k, v in por_nome.items() if len(v) > 1}
        assert not repetidos, f"nativeQueryRef duplicado em {pagina}/{visual['name']}: {repetidos}"


def test_tmdl_medidas_offline_batem_com_dax_arquivo():
    dax_esperado = medidas_dax_arquivo()
    assert len(dax_esperado) >= 35
    tmdl = (MODELO_PBIP / "tables" / "Medidas.tmdl").read_text(encoding="utf-8")
    nomes_tmdl = [
        n[1:-1].replace("''", "'") if n.startswith("'") else n
        for n in re.findall(r"^\tmeasure ('(?:[^']|'')*'|[^\s=]+)", tmdl, re.M)
    ]
    assert set(nomes_tmdl) == set(dax_esperado.keys())


# ---------------------------------------------------------------------------------------------
# 4. Deserialização TOM oficial do Power BI Desktop (@pytest.mark.powerbi)


@pytest.fixture(scope="module")
def tom():
    if sys.platform != "win32":
        pytest.skip("a biblioteca TOM do Power BI Desktop só existe no Windows")
    res = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(LER_TOM),
            "-Pasta",
            str(MODELO_PBIP),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 0, res.stderr
    dados = json.loads(res.stdout)
    if dados.get("ausente"):
        pytest.skip("Power BI Desktop não instalado neste ambiente")
    return dados


@pytest.mark.powerbi
def test_tom_tabelas_relacoes_e_configuracoes_calendario(tom):
    tabelas = {t["name"]: t for t in tom["tables"]}
    assert set(tabelas.keys()) == TABELAS_ESPERADAS

    # Todas as 9 relações de docs/MODELO.md presentes, ativas, *:1 e direção única
    lidas = {(r["from"], r["to"]) for r in tom["relationships"]}
    esperadas = set(relacionamentos_modelo_md())
    assert len(esperadas) == 9
    assert lidas == esperadas
    for r in tom["relationships"]:
        assert r["isActive"], r
        assert r["crossFilteringBehavior"] == "OneDirection", r
        assert (r["fromCardinality"], r["toCardinality"]) == ("Many", "One"), r

    # Calendário oficial e Time Intelligence automática desligada
    assert tom["annotations"]["__PBI_TimeIntelligenceEnabled"] == "0"
    assert tabelas["dim_calendario"]["dataCategory"] == "Time"
    cols_cal = {c["name"]: c for c in tabelas["dim_calendario"]["columns"]}
    assert cols_cal["data"]["isKey"]
    assert cols_cal["ano_mes"]["sortByColumn"] == "ano_mes_num"
    assert cols_cal["mes_ano_pt"]["sortByColumn"] == "ano_mes_num"
    assert cols_cal["trimestre"]["sortByColumn"] == "trimestre_num"

    cols_faixa = {c["name"]: c for c in tabelas["dim_faixa_atraso"]["columns"]}
    assert cols_faixa["faixa_atraso"]["sortByColumn"] == "ordem"

    cols_vend = {c["name"]: c for c in tabelas["dim_vendedor"]["columns"]}
    assert cols_vend["decil_gmv"]["sortByColumn"] == "decil_ordem"

    # Expressões Power Query não carregadas presentes e parametrizadas
    exps = {e["name"]: e for e in tom["expressions"]}
    assert {"PastaDados", "Arquivos", "fn_LerCsv"}.issubset(set(exps))
    assert "IsParameterQuery = true" in exps["PastaDados"]["expression"]


@pytest.mark.powerbi
def test_tom_todas_medidas_batem_com_dax_arquivo(tom):
    tabelas = {t["name"]: t for t in tom["tables"]}
    lidas = {m["name"]: m for m in tabelas["Medidas"]["measures"]}
    esperadas = medidas_dax_arquivo()
    assert list(lidas.keys()) == list(esperadas.keys())
    for nome, medida in lidas.items():
        assert compacto(medida["expression"]) == esperadas[nome], nome
        assert medida["description"], f"Medida sem descrição: {nome}"


@pytest.mark.powerbi
def test_tom_tipos_colunas_batem_com_modelo_md(tom):
    texto = MODELO_MD.read_text(encoding="utf-8")
    secoes = dict(re.findall(r"^###\s+`(\w+)`\n(.*?)(?=^###|^## |\Z)", texto, re.M | re.S))
    for tabela in tom["tables"]:
        nome = tabela["name"]
        tipos_doc = {
            col: tipo
            for col, tipo in re.findall(r"^\|\s*`(\w+)`\*?\s*\|\s*([^|]+?)\s*\|", secoes[nome], re.M)
        }
        for col in tabela["columns"]:
            assert col["name"] in tipos_doc, (nome, col["name"])
            assert col["dataType"] == TIPOS_MD_PARA_TOM[tipos_doc[col["name"]]], (nome, col["name"])
