"""Gera o projeto do Power BI (PBIP) do Painel E-Commerce & Macroeconomia Brasil.

Um projeto PBIP é uma pasta de arquivos de texto que o Power BI Desktop abre como um .pbix:
o modelo semântico fica em TMDL e o relatório em PBIR. Este script gera tudo a partir das
peças versionadas do repositório:

- as medidas DAX e suas descrições de dax/medidas.dax (incluindo títulos dinâmicos fx);
- as 9 relações do modelo estrela de docs/MODELO.md;
- os tokens e a grade 1280x720 de marca/tokens.json;
- o tema Power BI gerado em marca/powerbi/tema-azul-claro.json (espelhado em tema/tema.json);
- as consultas Power Query M lendo data/limpa/*.csv via parâmetro portável PastaDados.

Sem argumentos, grava powerbi/ com um caminho de exemplo em PastaDados (sem vazar caminhos
locais do computador). Para abrir e atualizar no Power BI Desktop localmente, gere uma cópia
fora do repositório apontando para a sua pasta data/limpa:

    python scripts/montar_pbip.py --pasta-dados "D:/Repos/painel-ecommerce-macro-br/data/limpa" --saida ../painel-ecommerce-local
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import textwrap
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MEDIDAS_ARQ = RAIZ / "dax" / "medidas.dax"
MODELO_MD = RAIZ / "docs" / "MODELO.md"
TOKENS_ARQ = RAIZ / "marca" / "tokens.json"
TEMA_ARQ = RAIZ / "marca" / "powerbi" / "tema-azul-claro.json"
SAIDA_PADRAO = RAIZ / "powerbi"

NOME = "PainelEcommerceMacro"
CAMINHO_DE_EXEMPLO = r"C:\caminho\do\projeto\data\limpa"
# UUID determinístico para que execuções repetidas produzam arquivos idênticos byte a byte.
ESPACO = uuid.uuid5(uuid.NAMESPACE_URL, "painel-ecommerce-macro-br")

ESQUEMAS = "https://developer.microsoft.com/json-schemas/fabric/"
VERSOES = {"report": "3.0.0", "page": "2.0.0", "visual": "2.4.0"}

# Tokens e grade carregados diretamente de marca/tokens.json (zero hex escrito à mão).
TOKENS = json.loads(TOKENS_ARQ.read_text(encoding="utf-8"))
TEMA_CLARO = TOKENS["tema"]["claro"]
ACENTO_NOME = "azul"
CORES_SERIE = [TOKENS["cores"][n]["claro"]["mark"] for n in TOKENS["acentos"][ACENTO_NOME]]
COR_ACENTO = CORES_SERIE[0]
COR_SERIE_2 = CORES_SERIE[1]
TIPO_PBI = TOKENS["tipo"]["powerbi_pt"]
GRADE = TOKENS["grade_powerbi"]
PAGINA_LARGURA, PAGINA_ALTURA = GRADE["pagina"]
MARGEM = GRADE["margem"]
CALHA = GRADE["calha"]
LARGURA_COL = GRADE["largura_coluna"]
FAIXAS = GRADE["faixas"]

TEXTO, INTEIRO, DECIMAL, DATA = "string", "int64", "double", "dateTime"
M_TIPO = {
    TEXTO: "type text",
    INTEIRO: "Int64.Type",
    DECIMAL: "type number",
    DATA: "type date",
}

# Colunas de cada tabela na ordem de docs/MODELO.md (nome, tipo TMDL, presente no CSV?).
TABELAS_SCHEMA: dict[str, dict] = {
    "dim_calendario": {
        "csv": "dim_calendario.csv",
        "descricao": "Dimensão calendário diária (2016-09-01 a 2018-10-31), marcada como tabela de datas.",
        "colunas": [
            ("data", DATA, True),
            ("ano", INTEIRO, True),
            ("trimestre", TEXTO, True),
            ("trimestre_num", INTEIRO, True),
            ("mes", INTEIRO, True),
            ("ano_mes", TEXTO, True),
            ("ano_mes_num", INTEIRO, True),
            ("mes_ano_pt", TEXTO, True),
            ("dia_semana", INTEIRO, True),
            ("eh_fim_de_semana", INTEIRO, True),
            ("trimestre_curto", TEXTO, False),
        ],
    },
    "dim_macro_mensal": {
        "csv": "dim_macro_mensal.csv",
        "descricao": "Série mensal do Banco Central SGS: IPCA (433), Selic meta (432) e Dólar PTAX (1).",
        "colunas": [
            ("ano_mes", TEXTO, True),
            ("data_mes", DATA, True),
            ("ipca_mensal_pct", DECIMAL, True),
            ("ipca_acum_12m_pct", DECIMAL, True),
            ("indice_ipca_base100", DECIMAL, True),
            ("fator_deflator", DECIMAL, True),
            ("selic_media", DECIMAL, True),
            ("ptax_media", DECIMAL, True),
        ],
    },
    "dim_geo_uf": {
        "csv": "dim_geo_uf.csv",
        "descricao": "27 Unidades da Federação (IBGE Localidades + população estimada 2018 e Censo 2022).",
        "colunas": [
            ("uf", TEXTO, True),
            ("codigo_ibge", INTEIRO, True),
            ("nome", TEXTO, True),
            ("regiao_sigla", TEXTO, True),
            ("regiao", TEXTO, True),
            ("populacao_ibge", INTEIRO, True),
            ("populacao_censo_2022", INTEIRO, True),
        ],
    },
    "dim_categoria": {
        "csv": "dim_categoria.csv",
        "descricao": "Categorias de produtos Olist com nomes padronizados em PT-BR e EN.",
        "colunas": [
            ("categoria_codigo", TEXTO, True),
            ("categoria_pt", TEXTO, True),
            ("categoria_en", TEXTO, True),
            ("traducao_oficial_olist", INTEIRO, True),
        ],
    },
    "dim_faixa_atraso": {
        "csv": "dim_faixa_atraso.csv",
        "descricao": "Faixas ordinais de atraso logístico (5 faixas entregues + Sem entrega).",
        "colunas": [
            ("faixa_atraso", TEXTO, True),
            ("faixa_atraso_en", TEXTO, True),
            ("ordem", INTEIRO, True),
            ("eh_atrasado", INTEIRO, True),
        ],
    },
    "dim_vendedor": {
        "csv": "dim_vendedor.csv",
        "descricao": "Vendedores Olist classificados em decis de concentração de GMV real entregue (D1..D10).",
        "colunas": [
            ("seller_id", TEXTO, True),
            ("uf_vendedor", TEXTO, True),
            ("cidade_vendedor", TEXTO, True),
            ("gmv_real_entregue", DECIMAL, True),
            ("pedidos_entregues", INTEIRO, True),
            ("decil_ordem", INTEIRO, True),
            ("decil_gmv", TEXTO, True),
        ],
    },
    "fato_pedidos": {
        "csv": "fato_pedidos.csv",
        "descricao": "Fato de pedidos Olist (99.441 linhas). Pedidos entregues têm flag_entregue = 1.",
        "colunas": [
            ("order_id", TEXTO, True),
            ("data_compra", DATA, True),
            ("ano_mes", TEXTO, True),
            ("data_aprovacao", DATA, True),
            ("data_entrega_estimada", DATA, True),
            ("data_entrega_real", DATA, True),
            ("dias_entrega", INTEIRO, True),
            ("dias_atraso", INTEIRO, True),
            ("flag_atraso", INTEIRO, True),
            ("faixa_atraso", TEXTO, True),
            ("status", TEXTO, True),
            ("flag_entregue", INTEIRO, True),
            ("uf_cliente", TEXTO, True),
            ("categoria_principal", TEXTO, True),
            ("nota_review", INTEIRO, True),
            ("qtd_itens", INTEIRO, True),
            ("valor_produtos", DECIMAL, True),
            ("valor_frete", DECIMAL, True),
            ("valor_total_nominal", DECIMAL, True),
            ("valor_total_real_ipca", DECIMAL, True),
            ("tipo_pagamento_principal", TEXTO, True),
            ("parcelas", INTEIRO, True),
            ("cliente_unico_id", TEXTO, True),
            ("coorte_mes", TEXTO, True),
            ("meses_desde_coorte", INTEIRO, True),
            ("flag_recompra", INTEIRO, True),
            ("flag_frete_outlier", INTEIRO, True),
            ("tipo_pagamento_pt", TEXTO, False),
            ("faixa_parcelas", TEXTO, False),
            ("faixa_parcelas_ordem", INTEIRO, False),
            ("mes_coorte_label", TEXTO, False),
            ("coorte_mes_num", INTEIRO, False),
        ],
    },
    "fato_itens_pedido": {
        "csv": "fato_itens_pedido.csv",
        "descricao": "Fato no grão de item vendido (112.650 linhas) para Pareto de categorias e vendedores.",
        "colunas": [
            ("order_id", TEXTO, True),
            ("order_item_id", INTEIRO, True),
            ("data_compra", DATA, True),
            ("ano_mes", TEXTO, True),
            ("status", TEXTO, True),
            ("flag_entregue", INTEIRO, True),
            ("uf_cliente", TEXTO, True),
            ("categoria_codigo", TEXTO, True),
            ("seller_id", TEXTO, True),
            ("uf_vendedor", TEXTO, True),
            ("preco", DECIMAL, True),
            ("frete", DECIMAL, True),
            ("valor_item_nominal", DECIMAL, True),
            ("valor_item_real_ipca", DECIMAL, True),
            ("flag_frete_outlier", INTEIRO, True),
        ],
    },
    "qualidade_auditoria": {
        "csv": "qualidade_auditoria.csv",
        "descricao": "Auditoria das 13 anomalias reais detectadas na base Olist e seu tratamento.",
        "colunas": [
            ("regra_id", TEXTO, True),
            ("regra", TEXTO, True),
            ("regra_en", TEXTO, True),
            ("tabela_origem", TEXTO, True),
            ("linhas_afetadas", INTEIRO, True),
            ("base_referencia", INTEIRO, True),
            ("pct_base", DECIMAL, True),
            ("severidade", TEXTO, True),
            ("tratamento", TEXTO, True),
            ("tratamento_en", TEXTO, True),
            ("pct_base_frac", DECIMAL, False),
            ("tabela_curta", TEXTO, False),
            ("tipo_curto", TEXTO, False),
        ],
    },
    "fontes_metadados": {
        "csv": "fontes_metadados.csv",
        "descricao": "Linhagem completa dos arquivos e endpoints públicos (Olist, BCB SGS e IBGE).",
        "colunas": [
            ("arquivo", TEXTO, True),
            ("fonte", TEXTO, True),
            ("endpoint", TEXTO, True),
            ("registros", INTEIRO, True),
            ("bytes_total", INTEIRO, True),
            ("sha256", TEXTO, True),
            ("coletado_em_utc", TEXTO, True),
            ("licenca", TEXTO, True),
            ("coletado_data", TEXTO, False),
            ("licenca_curta", TEXTO, False),
            ("arquivo_curto", TEXTO, False),
        ],
    },
    "macro_benchmark_atual": {
        "csv": "macro_benchmark_atual.csv",
        "descricao": "Retrato macro recente (IPCA 12m, Selic e PTAX) frente ao fim do recorte Olist.",
        "colunas": [
            ("indicador", TEXTO, True),
            ("nome_pt", TEXTO, True),
            ("nome_en", TEXTO, True),
            ("serie_sgs", INTEIRO, True),
            ("data_referencia", DATA, True),
            ("valor_recente", DECIMAL, True),
            ("valor_fim_olist", DECIMAL, True),
            ("unidade", TEXTO, True),
        ],
    },
    "Medidas": {
        "csv": None,
        "descricao": "Tabela técnica vazia que centraliza todas as medidas DAX do painel.",
        "colunas": [("oculta", TEXTO, False)],
    },
}

CLASSIFICAR_POR = {
    ("dim_calendario", "trimestre"): "trimestre_num",
    ("dim_calendario", "trimestre_curto"): "trimestre_num",
    ("dim_calendario", "ano_mes"): "ano_mes_num",
    ("dim_calendario", "mes_ano_pt"): "ano_mes_num",
    ("dim_faixa_atraso", "faixa_atraso"): "ordem",
    ("dim_vendedor", "decil_gmv"): "decil_ordem",
    ("fato_pedidos", "faixa_parcelas"): "faixa_parcelas_ordem",
    ("fato_pedidos", "mes_coorte_label"): "meses_desde_coorte",
}

ESCONDIDAS = {
    ("Medidas", "oculta"),
    ("dim_calendario", "trimestre_num"),
    ("dim_calendario", "ano_mes_num"),
    ("dim_faixa_atraso", "ordem"),
    ("dim_vendedor", "decil_ordem"),
    ("fato_pedidos", "faixa_parcelas_ordem"),
    ("fato_pedidos", "coorte_mes_num"),
}

FORMATOS_COLUNA = {
    ("qualidade_auditoria", "pct_base_frac"): "0.00%",
    ("qualidade_auditoria", "linhas_afetadas"): "#,0",
    ("fontes_metadados", "registros"): "#,0",
}

TABELA_DE_DATAS = ("dim_calendario", "data")

# Formatação das medidas DAX seguindo marca/REGRAS.md (sem símbolos unicode de ícone).
FORMATO_MOEDA_GRANDE = {
    "GMV Nominal",
    "GMV Real IPCA",
    "Receita Produtos Nominal",
    "Frete Nominal",
    "GMV Real Mês Anterior",
    "GMV Real Ano Anterior",
    "GMV Real Média Móvel 3m",
    "GMV Real Acumulado",
    "GMV Itens Real IPCA",
}
FORMATO_MOEDA_EXATA = {
    "Ticket Médio Nominal",
    "Ticket Médio Real",
    "GMV Real / 100 mil hab.",
    "Dólar PTAX Médio",
}
FORMATO_PCT_1 = {
    "% Excluídos da Análise",
    "Frete % do GMV",
    "GMV Real MoM %",
    "GMV Real YoY %",
    "GMV Nominal YoY Jan-Ago %",
    "GMV Real YoY Jan-Ago %",
    "Pedidos YoY Jan-Ago %",
    "% Entregas no Prazo",
    "% GMV Categorias",
    "% Acumulado GMV Categorias",
    "% Pedidos Cartão",
    "% GMV Pagamento",
    "% Cartão Parcelado",
    "% Clientes Recompra",
    "% GMV Vendedores",
    "% GMV Top 10% Vendedores",
}
FORMATO_PCT_2 = {
    "IPCA Mensal %",
    "IPCA 12m %",
    "Selic Média %",
    "% Retenção Coorte",
}
FORMATO_NOTA = {"Nota Média", "Nota Média no Prazo", "Nota Média Atrasado"}
FORMATO_DIAS = {"Prazo Médio Entrega (d)", "Atraso Médio quando Atrasa (d)"}
FORMATO_TEXTO_COR = {"Selo Gabarito SQL"}
FORMATO_ESPECIFICO = {
    "Itens por Pedido": "0.00",
    "Parcelas Médias (Cartão)": '0.00"x"',
    "Fator Deflator Médio": "0.0000",
    "Efeito Inflação YoY (p.p.)": '+0.0 "p.p.";−0.0 "p.p.";0.0 "p.p."',
    "Impacto Atraso na Nota": '+0.00 "pts";−0.00 "pts";0.00 "pts"',
}

RELACAO_RE = re.compile(r"^\|\s*`(\w+)\[(\w+)\]`\s*\|\s*`(\w+)\[(\w+)\]`\s*\|", re.M)
NOME_SIMPLES = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

RODAPE_FONTES = (
    "Fontes: Olist (CC BY-NC-SA 4.0) · BCB SGS 433 (IPCA), 432 (Selic), 1 (PTAX) · "
    "IBGE População 2018 · Valores reais out/2018 (IPCA) · Coleta: 22/11/2026"
)
RODAPE_ASSINATURA = f"{TOKENS['assinatura']} · Power BI · SQL · Python"


# ---------------------------------------------------------------------------------------------
# Grade 1280x720 (marca/tokens.json > grade_powerbi)


def col_x(col_inicio: int) -> int:
    """Retorna x inicial de uma coluna 1-based (1..12) na grade de 88 px com calha de 16 px."""
    return MARGEM + (col_inicio - 1) * (LARGURA_COL + CALHA)


def col_w(qtd_cols: int) -> int:
    """Retorna a largura em px de um bloco abrangendo `qtd_cols` colunas da grade."""
    return qtd_cols * LARGURA_COL + (qtd_cols - 1) * CALHA


def faixa(nome: str) -> tuple[int, int]:
    """Retorna (y, h) de uma das cinco faixas normativas de marca/tokens.json."""
    y, h = FAIXAS[nome]
    return int(y), int(h)


# ---------------------------------------------------------------------------------------------
# Leitura do pacote (DAX e relacionamentos)


def ler_medidas() -> list[dict]:
    """Lê as medidas do bloco DEFINE de dax/medidas.dax com descrição e pasta de exibição."""
    texto = MEDIDAS_ARQ.read_text(encoding="utf-8").replace("\r\n", "\n")
    inicio = re.search(r"^DEFINE\b", texto, re.M)
    fim = re.search(r"^EVALUATE\b", texto, re.M)
    if not inicio or not fim:
        sys.exit("dax/medidas.dax precisa conter blocos DEFINE e EVALUATE")
    linhas = texto[inicio.end():fim.start()].splitlines()
    medidas: list[dict] = []
    comentario: list[str] = []
    pasta_atual = ""
    atual: dict | None = None
    for linha in linhas:
        cabecalho = re.match(r"^\s*MEASURE\s+Medidas\[([^\]]+)\]\s*=\s*(.*)$", linha)
        if cabecalho:
            atual = {
                "nome": cabecalho.group(1),
                "descricao": "\n".join(comentario),
                "pasta": pasta_atual,
                "corpo": [cabecalho.group(2)],
            }
            medidas.append(atual)
            comentario = []
        elif linha.strip().startswith("//"):
            conteudo = re.sub(r"^\s*// ?", "", linha).strip()
            if set(conteudo) <= {"-"} and conteudo:
                comentario = []
            elif re.match(r"^0\d\.\s+", conteudo):
                pasta_atual = conteudo
                comentario = []
            else:
                comentario.append(conteudo)
        elif not linha.strip():
            comentario = []
            if atual:
                atual["corpo"].append("")
        elif atual:
            atual["corpo"].append(linha)
    for m in medidas:
        corpo = "\n".join(m.pop("corpo")).strip("\n")
        m["expressao"] = textwrap.dedent(corpo).strip()
        m["descricao"] = m["descricao"].strip()
    return medidas


def ler_relacoes() -> list[tuple[str, str, str, str]]:
    return RELACAO_RE.findall(MODELO_MD.read_text(encoding="utf-8"))


def formato_da_medida(nome: str) -> str | None:
    if nome in FORMATO_TEXTO_COR or nome.startswith(("Título ", "Subtítulo ", "Cor ", "Delta ")):
        return None
    if nome in FORMATO_ESPECIFICO:
        return FORMATO_ESPECIFICO[nome]
    if nome in FORMATO_MOEDA_GRANDE:
        return "R$ #,0.00"
    if nome in FORMATO_MOEDA_EXATA:
        return "R$ #,0.00"
    if nome in FORMATO_PCT_1:
        return "0.0%"
    if nome in FORMATO_PCT_2:
        return "0.00%"
    if nome in FORMATO_NOTA:
        return "0.00"
    if nome in FORMATO_DIAS:
        return '0.0 "d"'
    return "#,0"


# ---------------------------------------------------------------------------------------------
# Power Query M (gerado a partir de TABELAS_SCHEMA)


def m_para_tabela(nome: str, spec: dict) -> str:
    if nome == "Medidas":
        return "let\n    Medidas = #table(type table [oculta = text], {})\nin\n    Medidas"

    csv_nome = spec["csv"]
    cols_csv = [(c, t) for c, t, do_csv in spec["colunas"] if do_csv]
    pares_tipo = ", ".join(f'{{"{c}", {M_TIPO[t]}}}' for c, t in cols_csv)
    lista_nomes = ", ".join(f'"{c}"' for c, _ in cols_csv)

    etapas = [
        f'Fonte = fn_LerCsv("{csv_nome}")',
        f"Selecionadas = Table.SelectColumns(Fonte, {{{lista_nomes}}})",
        f'Nulos = Table.ReplaceValue(Selecionadas, "", null, Replacer.ReplaceValue, {{{lista_nomes}}})',
        f'Tipada = Table.TransformColumnTypes(Nulos, {{{pares_tipo}}}, "en-US")',
    ]
    ultima = "Tipada"

    if nome == "dim_calendario":
        etapas += [
            'ComTriCurto = Table.AddColumn(Tipada, "trimestre_curto", each Text.End([trimestre], 2) & "/" & Text.Middle([trimestre], 2, 2), type text)'
        ]
        ultima = "ComTriCurto"
    elif nome == "fato_pedidos":
        etapas += [
            (
                'ComPagamentoPt = Table.AddColumn(Tipada, "tipo_pagamento_pt", each '
                'if [tipo_pagamento_principal] = "credit_card" then "Cartão de crédito" '
                'else if [tipo_pagamento_principal] = "boleto" then "Boleto bancário" '
                'else if [tipo_pagamento_principal] = "voucher" then "Voucher e cupom" '
                'else if [tipo_pagamento_principal] = "debit_card" then "Cartão de débito" '
                'else if [tipo_pagamento_principal] = "not_defined" then "Não definido" '
                'else "Sem registro", type text)'
            ),
            (
                'ComParcelasOrdem = Table.AddColumn(ComPagamentoPt, "faixa_parcelas_ordem", each '
                "if [parcelas] = null or [parcelas] <= 0 then 0 "
                "else if [parcelas] >= 10 then 10 else [parcelas], Int64.Type)"
            ),
            (
                'ComFaixaParcelas = Table.AddColumn(ComParcelasOrdem, "faixa_parcelas", each '
                'if [faixa_parcelas_ordem] = 0 then "Sem info" '
                'else if [faixa_parcelas_ordem] = 10 then "10x+" '
                'else Text.From([faixa_parcelas_ordem]) & "x", type text)'
            ),
            (
                'ComCoorteLabel = Table.AddColumn(ComFaixaParcelas, "mes_coorte_label", each '
                'if [meses_desde_coorte] = 0 then "M0" '
                'else "M+" & Text.From([meses_desde_coorte]), type text)'
            ),
            (
                'ComCoorteNum = Table.AddColumn(ComCoorteLabel, "coorte_mes_num", each '
                'Int64.From(Text.Replace([coorte_mes], "-", "")), Int64.Type)'
            ),
        ]
        ultima = "ComCoorteNum"
    elif nome == "qualidade_auditoria":
        etapas += [
            'ComPctFrac = Table.AddColumn(Tipada, "pct_base_frac", each [pct_base] / 100.0, type number)',
            (
                'ComTabelaCurta = Table.AddColumn(ComPctFrac, "tabela_curta", each '
                'Text.Replace(Text.Replace(Text.Replace([tabela_origem], "olist_", ""), "_dataset", ""), "product_category_name_translation.csv", "cat_translation.csv"), type text)'
            ),
            (
                'ComTipoCurto = Table.AddColumn(ComTabelaCurta, "tipo_curto", each '
                'if Text.Contains([severidade], "parcial") then "Exclusão SLA" '
                'else if Text.Contains([severidade], "Exclus") then "Exclusão" '
                'else if Text.Contains([severidade], "Deduplic") then "Deduplicação" '
                'else if Text.Contains([severidade], "Fallback") then "Fallback" '
                'else if Text.Contains([severidade], "Limpeza") then "Limpeza" '
                'else "Sinalização", type text)'
            ),
        ]
        ultima = "ComTipoCurto"
    elif nome == "fontes_metadados":
        etapas += [
            'ComData = Table.AddColumn(Tipada, "coletado_data", each Text.Start([coletado_em_utc], 10), type text)',
            (
                'ComLicenca = Table.AddColumn(ComData, "licenca_curta", each '
                'if Text.Contains([licenca], "CC BY-NC-SA") then "CC BY-NC-SA 4.0" '
                'else if Text.Contains([licenca], "Banco Central") then "BCB Público" '
                'else "IBGE Público", type text)'
            ),
            (
                'ComArqCurto = Table.AddColumn(ComLicenca, "arquivo_curto", each '
                'Text.Replace(Text.Replace(Text.Replace([arquivo], "olist_", ""), "_dataset", ""), "product_category_name_translation.csv", "cat_translation.csv"), type text)'
            ),
        ]
        ultima = "ComArqCurto"

    corpo = ",\n    ".join(etapas)
    return f"let\n    {corpo}\nin\n    {ultima}"


def expressoes_m(pasta_dados: str) -> list[dict]:
    pasta_segura = pasta_dados.replace('"', '""')
    return [
        {
            "nome": "PastaDados",
            "tipo": "Text",
            "descricao": (
                "Caminho absoluto da pasta data\\limpa deste projeto, onde estão os CSVs do modelo estrela.\n"
                "Troque o caminho no Power BI Desktop ou regenere localmente com --pasta-dados."
            ),
            "m": f'"{pasta_segura}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
        },
        {
            "nome": "Arquivos",
            "tipo": "Table",
            "descricao": (
                "Fonte única de dados do painel: lista os arquivos CSV da pasta PastaDados.\n"
                "Usar uma fonte única evita alertas de privacidade do Power Query entre tabelas."
            ),
            "m": (
                "let\n"
                "    Fonte = Folder.Contents(PastaDados),\n"
                '    Csvs = Table.SelectRows(Fonte, each Text.EndsWith([Name], ".csv")),\n'
                '    Arquivos = Table.SelectColumns(Csvs, {"Name", "Content"})\n'
                "in\n"
                "    Arquivos"
            ),
        },
        {
            "nome": "fn_LerCsv",
            "tipo": "Function",
            "descricao": (
                "Lê um CSV UTF-8 da pasta PastaDados via Binary.Buffer para reportar erros de caminho "
                "imediatamente e promove o cabeçalho."
            ),
            "m": (
                "(arquivo as text) as table =>\n"
                "let\n"
                "    Lido = try Binary.Buffer(Arquivos{[Name = arquivo]}[Content]),\n"
                "    Conteudo =\n"
                "        if Lido[HasError]\n"
                '        then error Error.Record("Arquivo não encontrado",\n'
                '            "Não consegui ler " & arquivo & " na pasta " & PastaDados & ". " & Lido[Error][Message])\n'
                "        else Lido[Value],\n"
                '    Tabela = Csv.Document(Conteudo, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),\n'
                "    ComCabecalho = Table.PromoteHeaders(Tabela, [PromoteAllScalars = true])\n"
                "in\n"
                "    ComCabecalho"
            ),
        },
    ]


# ---------------------------------------------------------------------------------------------
# Modelo Semântico (TMDL)


def etiqueta(*partes: str) -> str:
    return str(uuid.uuid5(ESPACO, "/".join(partes)))


def nome_tmdl(nome: str) -> str:
    return nome if NOME_SIMPLES.fullmatch(nome) else "'" + nome.replace("'", "''") + "'"


def descricao_tmdl(texto: str, recuo: int) -> list[str]:
    if not texto:
        return []
    return ["\t" * recuo + "/// " + linha if linha else "\t" * recuo + "///" for linha in texto.splitlines()]


def expressao_tmdl(cabecalho: str, expressao: str, recuo: int) -> list[str]:
    if "\n" not in expressao:
        return [f"{cabecalho} = {expressao}"]
    corpo = ["\t" * recuo + linha if linha.strip() else "" for linha in expressao.splitlines()]
    return [f"{cabecalho} =", *corpo]


def tabela_tmdl(nome: str, spec: dict, medidas: list[dict]) -> str:
    linhas = [*descricao_tmdl(spec["descricao"], 0), f"table {nome_tmdl(nome)}"]
    if TABELA_DE_DATAS[0] == nome:
        linhas.append("\tdataCategory: Time")
    linhas += [f"\tlineageTag: {etiqueta('tabela', nome)}", ""]

    if nome == "Medidas":
        for m in medidas:
            linhas += descricao_tmdl(m["descricao"], 1)
            linhas += expressao_tmdl(f"\tmeasure {nome_tmdl(m['nome'])}", m["expressao"], 3)
            formato = formato_da_medida(m["nome"])
            if formato:
                linhas.append(f"\t\tformatString: {formato}")
            if m["pasta"]:
                linhas.append(f"\t\tdisplayFolder: {m['pasta']}")
            linhas += [f"\t\tlineageTag: {etiqueta('medida', m['nome'])}", ""]

    for coluna_nome, tipo, _ in spec["colunas"]:
        linhas += [f"\tcolumn {nome_tmdl(coluna_nome)}", f"\t\tdataType: {tipo}"]
        if (nome, coluna_nome) in ESCONDIDAS:
            linhas.append("\t\tisHidden")
        if (nome, coluna_nome) == TABELA_DE_DATAS:
            linhas.append("\t\tisKey")
        formato_col = FORMATOS_COLUNA.get((nome, coluna_nome))
        if formato_col:
            linhas.append(f"\t\tformatString: {formato_col}")
        elif tipo == DATA:
            linhas.append("\t\tformatString: dd/MM/yyyy")
        elif tipo == INTEIRO:
            linhas.append("\t\tformatString: 0")
        linhas += [
            f"\t\tlineageTag: {etiqueta('coluna', nome, coluna_nome)}",
            "\t\tsummarizeBy: none",
            f"\t\tsourceColumn: {coluna_nome}",
        ]
        if (nome, coluna_nome) in CLASSIFICAR_POR:
            linhas.append(f"\t\tsortByColumn: {CLASSIFICAR_POR[(nome, coluna_nome)]}")
        linhas.append("")
        if tipo == DATA:
            linhas += ["\t\tannotation UnderlyingDateTimeDataType = Date", ""]
        linhas += ["\t\tannotation SummarizationSetBy = User", ""]

    linhas += [f"\tpartition {nome_tmdl(nome)} = m", "\t\tmode: import"]
    linhas += expressao_tmdl("\t\tsource", m_para_tabela(nome, spec), 4)
    linhas += ["", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(linhas)


def expressoes_tmdl(pasta_dados: str) -> str:
    linhas: list[str] = []
    for expr in expressoes_m(pasta_dados):
        linhas += descricao_tmdl(expr["descricao"], 0)
        linhas += expressao_tmdl(f"expression {nome_tmdl(expr['nome'])}", expr["m"], 2)
        linhas += [
            f"\tlineageTag: {etiqueta('expressao', expr['nome'])}",
            "",
            f"\tannotation PBI_ResultType = {expr['tipo']}",
            "",
        ]
    return "\n".join(linhas)


def modelo_tmdl(pasta_dados: str) -> str:
    ordem_nomes = [e["nome"] for e in expressoes_m(pasta_dados)] + list(TABELAS_SCHEMA.keys())
    ordem = json.dumps(ordem_nomes, ensure_ascii=False)
    linhas = [
        "model Model",
        "\tculture: pt-BR",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: pt-BR",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        f"annotation PBI_QueryOrder = {ordem}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        'annotation PBI_ProTooling = ["DevMode"]',
        "",
    ]
    linhas += [f"ref table {nome_tmdl(nome)}" for nome in TABELAS_SCHEMA]
    return "\n".join(linhas) + "\n"


def relacoes_tmdl(relacoes: list[tuple[str, str, str, str]]) -> str:
    linhas: list[str] = []
    for muitos, col_muitos, um, col_um in relacoes:
        linhas.append(f"relationship {etiqueta('relacao', muitos, col_muitos, um, col_um)}")
        if (um, col_um) == TABELA_DE_DATAS:
            linhas.append("\tjoinOnDateBehavior: datePartOnly")
        linhas += [f"\tfromColumn: {muitos}.{col_muitos}", f"\ttoColumn: {um}.{col_um}", ""]
    return "\n".join(linhas)


def escrever_modelo(pasta: Path, pasta_dados: str) -> None:
    medidas = ler_medidas()
    relacoes = ler_relacoes()
    if len(relacoes) != 9:
        sys.exit(f"Esperava 9 relacionamentos em docs/MODELO.md, encontrei {len(relacoes)}")
    escrever_json(
        pasta / "definition.pbism",
        {
            "$schema": ESQUEMAS + "item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.2",
            "settings": {},
        },
    )
    definicao = pasta / "definition"
    escrever(definicao / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    escrever(definicao / "model.tmdl", modelo_tmdl(pasta_dados))
    escrever(definicao / "expressions.tmdl", expressoes_tmdl(pasta_dados))
    escrever(definicao / "relationships.tmdl", relacoes_tmdl(relacoes))
    for nome, spec in TABELAS_SCHEMA.items():
        escrever(definicao / "tables" / f"{nome}.tmdl", tabela_tmdl(nome, spec, medidas))


# ---------------------------------------------------------------------------------------------
# Relatório (PBIR v2.4.0 · grade exata 1280x720 de marca/REGRAS.md e títulos DAX fx)


def coluna(tabela: str, nome: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}}


def medida(nome: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": nome}}


def referencia(campo: dict) -> str:
    dados = next(iter(campo.values()))
    return f"{dados['Expression']['SourceRef']['Entity']}.{dados['Property']}"


def projecao(campo: dict, rotulo: str | None = None) -> dict:
    nome = rotulo or next(iter(campo.values()))["Property"]
    resultado = {"field": campo, "queryRef": referencia(campo), "nativeQueryRef": nome}
    if rotulo:
        resultado["displayName"] = rotulo
    return resultado


def literal(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def texto_literal(texto: str) -> dict:
    return literal("'" + texto.replace("'", "''") + "'")


def cor_solida(hex_cor: str) -> dict:
    return {"solid": {"color": texto_literal(hex_cor)}}


def cor_medida(nome_medida: str) -> dict:
    return {"solid": {"color": {"expr": medida(nome_medida)}}}


def padding_container(top: int, bottom: int, left: int, right: int) -> list[dict]:
    return [
        {
            "properties": {
                "top": literal(f"{top}D"),
                "bottom": literal(f"{bottom}D"),
                "left": literal(f"{left}D"),
                "right": literal(f"{right}D"),
            }
        }
    ]


def cabecalho_visual_fx(titulo_medida: str, subtitulo_txt: str | None = None) -> dict:
    """Liga o título do visual a uma medida DAX dinâmica (fx) com subtítulo de unidade e período."""
    container: dict = {
        "title": [
            {
                "properties": {
                    "show": literal("true"),
                    "text": {"expr": medida(titulo_medida)},
                }
            }
        ],
    }
    if subtitulo_txt:
        container["subTitle"] = [
            {"properties": {"show": literal("true"), "text": texto_literal(subtitulo_txt)}}
        ]
    else:
        container["subTitle"] = [{"properties": {"show": literal("false")}}]
    return container


def fonte_do_filtro(campo: dict, apelido: str) -> tuple[list[dict], dict]:
    tipo, dados = next(iter(campo.items()))
    origem = [{"Name": apelido, "Entity": dados["Expression"]["SourceRef"]["Entity"], "Type": 0}]
    local = {tipo: {"Expression": {"SourceRef": {"Source": apelido}}, "Property": dados["Property"]}}
    return origem, local


def filtro_entre(nome: str, campo: dict, minimo: str, maximo: str) -> dict:
    origem, local = fonte_do_filtro(campo, "f")
    condicao = {
        "And": {
            "Left": {"Comparison": {"ComparisonKind": 2, "Left": local, "Right": {"Literal": {"Value": minimo}}}},
            "Right": {"Comparison": {"ComparisonKind": 4, "Left": local, "Right": {"Literal": {"Value": maximo}}}},
        }
    }
    return {
        "name": nome,
        "field": campo,
        "type": "Advanced",
        "filter": {"Version": 2, "From": origem, "Where": [{"Condition": condicao}]},
        "howCreated": "User",
    }


def filtro_em(nome: str, campo: dict, valores: list[str]) -> dict:
    origem, local = fonte_do_filtro(campo, "f")
    condicao = {
        "In": {
            "Expressions": [local],
            "Values": [[{"Literal": {"Value": v}}] for v in valores],
        }
    }
    return {
        "name": nome,
        "field": campo,
        "type": "Categorical",
        "filter": {"Version": 2, "From": origem, "Where": [{"Condition": condicao}]},
        "howCreated": "User",
    }


def filtro_top_n(nome: str, campo_cat: dict, campo_valor: dict, n: int) -> dict:
    origem_cat, local_cat = fonte_do_filtro(campo_cat, "c")
    origem_val, local_val = fonte_do_filtro(campo_valor, "m")
    return {
        "name": nome,
        "field": campo_cat,
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {
                    "Name": "subquery",
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": origem_cat + origem_val,
                                "Select": [{"Column": local_cat["Column"], "Name": "field"}],
                                "OrderBy": [{"Direction": 2, "Expression": local_val}],
                                "Top": n,
                            }
                        }
                    },
                    "Type": 2,
                },
                *origem_cat,
            ],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [local_cat],
                            "Table": {"SourceRef": {"Source": "subquery"}},
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


class Pagina:
    def __init__(self, nome: str, display_name: str, titulo: str, subtitulo: str):
        self.nome = nome
        self.display_name = display_name
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.visuais: list[dict] = []

    def adicionar(
        self,
        nome: str,
        x: int,
        y: int,
        largura: int,
        altura: int,
        tipo: str,
        *,
        papeis: dict | None = None,
        ordem: list | None = None,
        objetos: dict | None = None,
        container: dict | None = None,
        filtros: list[dict] | None = None,
        sincronia: str | None = None,
    ) -> None:
        visual: dict = {"visualType": tipo}
        if papeis:
            visual["query"] = {
                "queryState": {papel: {"projections": lista} for papel, lista in papeis.items()}
            }
            if ordem:
                visual["query"]["sortDefinition"] = {
                    "sort": [{"field": campo, "direction": direcao} for campo, direcao in ordem],
                    "isDefaultSort": False,
                }
        if objetos:
            visual["objects"] = objetos
        if container:
            visual["visualContainerObjects"] = container
        if sincronia:
            visual["syncGroup"] = {
                "groupName": sincronia,
                "fieldChanges": True,
                "filterChanges": True,
            }
        visual["drillFilterOtherVisuals"] = True
        pos = len(self.visuais)
        conteudo: dict = {
            "$schema": f"{ESQUEMAS}item/report/definition/visualContainer/{VERSOES['visual']}/schema.json",
            "name": nome,
            "position": {
                "x": x,
                "y": y,
                "z": pos,
                "height": altura,
                "width": largura,
                "tabOrder": pos,
            },
            "visual": visual,
        }
        if filtros:
            conteudo["filterConfig"] = {"filters": filtros}
        self.visuais.append(conteudo)

    def texto(
        self,
        nome: str,
        x: int,
        y: int,
        largura: int,
        altura: int,
        paragrafos: list[dict],
        *,
        container: dict | None = None,
    ) -> None:
        self.adicionar(
            nome,
            x,
            y,
            largura,
            altura,
            "textbox",
            objetos={"general": [{"properties": {"paragraphs": paragrafos}}]},
            container=container,
        )

    def cabecalho(self, com_slicers: bool = True) -> None:
        y_cab, h_cab = faixa("cabecalho")
        largura_header = col_w(6) if com_slicers else col_w(12)
        self.texto(
            "titulo",
            col_x(1),
            y_cab,
            largura_header,
            h_cab,
            [
                {
                    "textRuns": [
                        {
                            "value": self.titulo,
                            "textStyle": {
                                "fontFamily": TOKENS["fonte"]["powerbi_forte"],
                                "fontWeight": "bold",
                                "fontSize": f"{TIPO_PBI['largeTitle']}pt",
                                "color": TEMA_CLARO["ink"],
                            },
                        }
                    ]
                },
                {
                    "textRuns": [
                        {
                            "value": self.subtitulo,
                            "textStyle": {
                                "fontFamily": TOKENS["fonte"]["powerbi"],
                                "fontSize": f"{TIPO_PBI['label']}pt",
                                "color": TEMA_CLARO["ink_2"],
                            },
                        }
                    ]
                },
            ],
        )
        if com_slicers:
            for nome_slicer, col_ini, campo, rotulo in (
                ("filtro_ano", 7, coluna("dim_calendario", "ano"), "Ano"),
                ("filtro_regiao", 9, coluna("dim_geo_uf", "regiao"), "Região"),
                ("filtro_categoria", 11, coluna("dim_categoria", "categoria_pt"), "Categoria"),
            ):
                self.adicionar(
                    nome_slicer,
                    col_x(col_ini),
                    y_cab,
                    col_w(2),
                    h_cab,
                    "slicer",
                    papeis={"Values": [projecao(campo, rotulo)]},
                    objetos={
                        "data": [{"properties": {"mode": texto_literal("Dropdown")}}],
                        "header": [{"properties": {"textSize": literal("7D")}}],
                        "items": [{"properties": {"textSize": literal("8D")}}],
                    },
                    container={"padding": padding_container(0, 0, 8, 8)},
                    sincronia=nome_slicer,
                )

    def rodape(self, texto_extra: str = "") -> None:
        y_rod, h_rod = faixa("rodape")
        texto_fontes = f"{RODAPE_FONTES}{texto_extra}"
        self.texto(
            "rodape_fontes",
            col_x(1),
            y_rod,
            col_w(9),
            h_rod,
            [
                {
                    "textRuns": [
                        {
                            "value": texto_fontes,
                            "textStyle": {
                                "fontFamily": TOKENS["fonte"]["powerbi"],
                                "fontSize": f"{TIPO_PBI['nota']}pt",
                                "color": TEMA_CLARO["ink_3"],
                            },
                        }
                    ]
                }
            ],
        )
        self.texto(
            "rodape_assinatura",
            col_x(10),
            y_rod,
            col_w(3),
            h_rod,
            [
                {
                    "horizontalTextAlignment": "right",
                    "textRuns": [
                        {
                            "value": RODAPE_ASSINATURA,
                            "textStyle": {
                                "fontFamily": TOKENS["fonte"]["powerbi"],
                                "fontSize": f"{TIPO_PBI['nota']}pt",
                                "color": TEMA_CLARO["ink_3"],
                            },
                        }
                    ],
                }
            ],
        )


def kpi_card(
    pagina: Pagina,
    nome: str,
    col_inicio: int,
    medida_nome: str,
    rotulo: str,
    *,
    subtitulo: str | None = None,
    subtitulo_medida: str | None = None,
    subtitulo_cor_medida: str | None = None,
    subtitulo_cor_hex: str | None = None,
    unidades: str | None = None,
) -> None:
    """Cartão de KPI 296x80 (3 colunas) na faixa kpis (y=72, h=80), sempre com valor em ink."""
    y_kpi, h_kpi = faixa("kpis")
    lbl_props: dict = {"fontSize": literal(f"{TIPO_PBI['callout']}D")}
    if unidades is not None:
        lbl_props["labelDisplayUnits"] = literal(unidades)
    objetos = {"labels": [{"properties": lbl_props}]}

    sub_props: dict = {"show": literal("true"), "fontSize": literal(f"{TIPO_PBI['nota']}D")}
    if subtitulo_medida:
        sub_props["text"] = {"expr": medida(subtitulo_medida)}
    elif subtitulo:
        sub_props["text"] = texto_literal(subtitulo)
    else:
        sub_props["show"] = literal("false")

    if subtitulo_cor_medida:
        sub_props["fontColor"] = cor_medida(subtitulo_cor_medida)
    elif subtitulo_cor_hex:
        sub_props["fontColor"] = cor_solida(subtitulo_cor_hex)

    container: dict = {
        "padding": padding_container(6, 6, 14, 14),
        "title": [{"properties": {"show": literal("true"), "text": texto_literal(rotulo)}}],
        "subTitle": [{"properties": sub_props}],
    }

    pagina.adicionar(
        nome,
        col_x(col_inicio),
        y_kpi,
        col_w(3),
        h_kpi,
        "card",
        papeis={"Values": [projecao(medida(medida_nome))]},
        objetos=objetos,
        container=container,
    )


# ---------------------------------------------------------------------------------------------
# As 4 páginas (grade exata 1280x720 de marca/REGRAS.md e títulos dinâmicos DAX fx)


def pagina_visao_executiva() -> Pagina:
    p = Pagina(
        "visao_executiva",
        "Visão executiva",
        "Visão executiva e macroeconomia",
        "GMV real a preços de out/2018 (IPCA BCB SGS 433) · comparação jan–ago/2018 vs. 2017",
    )
    p.cabecalho(com_slicers=True)

    # Faixa KPIs (y=72, h=80): 4 cartões de 3 colunas (296x80)
    kpi_card(
        p, "kpi_gmv_real", 1, "GMV Real IPCA", "GMV real (IPCA)",
        subtitulo_medida="Delta GMV Real Texto", subtitulo_cor_medida="Cor Delta GMV Real",
    )
    kpi_card(
        p, "kpi_pedidos", 4, "Pedidos Entregues", "Pedidos entregues",
        subtitulo_medida="Delta Pedidos Texto", subtitulo_cor_medida="Cor Delta Pedidos",
        unidades="1D",
    )
    kpi_card(
        p, "kpi_ticket_real", 7, "Ticket Médio Real", "Ticket médio real",
        subtitulo_medida="Subtítulo Ticket Real", unidades="1D",
    )
    kpi_card(
        p, "kpi_no_prazo", 10, "% Entregas no Prazo", "Entregas no prazo",
        subtitulo_medida="Subtítulo SLA Nota",
    )

    y_a, h_a = faixa("linha_a")
    y_b, h_b = faixa("linha_b")

    # Linha A (8 + 4 colunas): Tendência mensal GMV Real vs. Nominal + Selic & IPCA 12m
    p.adicionar(
        "tendencia_gmv",
        col_x(1),
        y_a,
        col_w(8),
        h_a,
        "lineChart",
        papeis={
            "Category": [projecao(coluna("dim_calendario", "mes_ano_pt"), "Mês")],
            "Y": [
                projecao(medida("GMV Real IPCA"), "GMV real (IPCA)"),
                projecao(medida("GMV Nominal"), "GMV nominal"),
            ],
        },
        ordem=[(coluna("dim_calendario", "mes_ano_pt"), "Ascending")],
        objetos={
            "dataPoint": [
                {"properties": {"fill": cor_solida(COR_ACENTO)}, "selector": {"metadata": "Medidas.GMV Real IPCA"}},
                {"properties": {"fill": cor_solida(TEMA_CLARO["mark_muted"])}, "selector": {"metadata": "Medidas.GMV Nominal"}},
            ],
            "labels": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Tendência GMV",
            "R$ milhões por mês · real a preços de out/2018 em azul, nominal em cinza",
        ),
    )

    p.adicionar(
        "macro_ipca_selic",
        col_x(9),
        y_a,
        col_w(4),
        h_a,
        "lineChart",
        papeis={
            "Category": [projecao(coluna("dim_macro_mensal", "data_mes"), "Mês")],
            "Y": [
                projecao(medida("Selic Média %"), "Selic meta"),
                projecao(medida("IPCA 12m %"), "IPCA 12m"),
            ],
        },
        objetos={
            "dataPoint": [
                {"properties": {"fill": cor_solida(COR_ACENTO)}, "selector": {"metadata": "Medidas.Selic Média %"}},
                {"properties": {"fill": cor_solida(COR_SERIE_2)}, "selector": {"metadata": "Medidas.IPCA 12m %"}},
            ],
            "categoryAxis": [{"properties": {"axisType": texto_literal("Scalar")}}],
            "labels": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Macro IPCA Selic",
            "% a.a. e acumulado 12m · BCB SGS 432 e 433",
        ),
    )

    # Linha B (6 + 6 colunas): GMV Real por Região + Ticket Médio Real por Trimestre
    p.adicionar(
        "gmv_regiao",
        col_x(1),
        y_b,
        col_w(6),
        h_b,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("dim_geo_uf", "regiao"), "Região")],
            "Y": [projecao(medida("GMV Real IPCA"), "GMV real")],
        },
        ordem=[(medida("GMV Real IPCA"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Região Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "categoryAxis": [{"properties": {"innerPadding": literal("12L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título GMV Região",
            "R$ milhões a preços de out/2018 · líder destacada em azul",
        ),
    )

    p.adicionar(
        "ticket_trimestre",
        col_x(7),
        y_b,
        col_w(6),
        h_b,
        "clusteredColumnChart",
        papeis={
            "Category": [projecao(coluna("dim_calendario", "trimestre_curto"), "Trimestre")],
            "Y": [projecao(medida("Ticket Médio Real"), "Ticket real")],
        },
        ordem=[(coluna("dim_calendario", "trimestre_curto"), "Ascending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Trimestre Período")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Ticket Trimestre",
            "R$ de out/2018 por pedido entregue · 2017 em cinza, 2018 em azul",
        ),
        filtros=[filtro_entre("trimestres_cheios", coluna("dim_calendario", "trimestre_num"), "20171L", "20183L")],
    )

    p.rodape()
    return p


def pagina_logistica_sla() -> Pagina:
    p = Pagina(
        "logistica_sla",
        "Logística e SLA",
        "Logística, SLA e avaliação do cliente",
        "Pedidos entregues com data real válida (96.470) · atraso = entrega após a data estimada",
    )
    p.cabecalho(com_slicers=True)

    # Faixa KPIs (y=72, h=80): 4 cartões de 3 colunas (296x80)
    kpi_card(
        p, "kpi_prazo_medio", 1, "Prazo Médio Entrega (d)", "Prazo médio de entrega",
        subtitulo_medida="Subtítulo Prazo Médio", unidades="1D",
    )
    kpi_card(
        p, "kpi_no_prazo", 4, "% Entregas no Prazo", "Entregas no prazo",
        subtitulo_medida="Subtítulo SLA Contagem",
    )
    kpi_card(
        p, "kpi_nota_no_prazo", 7, "Nota Média no Prazo", "Nota média no prazo",
        subtitulo="escala 1 a 5 · entregas até o prazo", unidades="1D",
    )
    kpi_card(
        p, "kpi_nota_atrasado", 10, "Nota Média Atrasado", "Nota média com atraso",
        subtitulo_medida="Subtítulo Nota Atraso", subtitulo_cor_medida="Cor Impacto Atraso",
        unidades="1D",
    )

    y_a, h_a = faixa("linha_a")
    y_b, h_b = faixa("linha_b")

    # Linha A (6 + 6 colunas): Nota por Faixa de Atraso + Top 8 UFs por Penetração per capita
    p.adicionar(
        "nota_por_atraso",
        col_x(1),
        y_a,
        col_w(6),
        h_a,
        "clusteredColumnChart",
        papeis={
            "Category": [projecao(coluna("dim_faixa_atraso", "faixa_atraso"), "Faixa de atraso")],
            "Y": [projecao(medida("Nota Média"), "Nota média")],
        },
        ordem=[(coluna("dim_faixa_atraso", "faixa_atraso"), "Ascending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Faixa Atraso")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "labels": [{"properties": {"show": literal("true")}}],
            "valueAxis": [{"properties": {"start": literal("1D"), "end": literal("5D")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Nota Atraso",
            "Nota média de 1 a 5 por faixa ordinal de atraso na entrega",
        ),
        filtros=[filtro_entre("cinco_faixas", coluna("dim_faixa_atraso", "ordem"), "1L", "5L")],
    )

    p.adicionar(
        "penetracao_uf",
        col_x(7),
        y_a,
        col_w(6),
        h_a,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("dim_geo_uf", "uf"), "UF")],
            "Y": [projecao(medida("GMV Real / 100 mil hab."), "GMV/100 mil hab.")],
            "Tooltips": [
                projecao(medida("Pedidos Entregues"), "Pedidos"),
                projecao(medida("% Entregas no Prazo"), "% no prazo"),
                projecao(medida("Prazo Médio Entrega (d)"), "Prazo (d)"),
            ],
        },
        ordem=[(medida("GMV Real / 100 mil hab."), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor UF Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "categoryAxis": [{"properties": {"innerPadding": literal("10L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [
                {
                    "properties": {
                        "show": literal("true"),
                        "fontSize": literal("8D"),
                        "labelDisplayUnits": literal("1D"),
                        "labelPosition": texto_literal("OutsideEnd"),
                    }
                }
            ],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Penetração UF",
            "Top 8 UFs por GMV real a cada 100 mil hab. · IBGE 2018",
        ),
        filtros=[
            filtro_top_n(
                "top8_ufs",
                coluna("dim_geo_uf", "uf"),
                medida("GMV Real / 100 mil hab."),
                8,
            )
        ],
    )

    # Linha B (6 + 6 colunas): Prazo Médio por Região + Tabela detalhada das 27 UFs
    p.adicionar(
        "prazo_regiao",
        col_x(1),
        y_b,
        col_w(6),
        h_b,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("dim_geo_uf", "regiao"), "Região")],
            "Y": [projecao(medida("Prazo Médio Entrega (d)"), "Prazo (d)")],
        },
        ordem=[(medida("Prazo Médio Entrega (d)"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Prazo Região Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "categoryAxis": [{"properties": {"innerPadding": literal("12L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Prazo Região",
            "Dias corridos entre compra e entrega real · média por região",
        ),
    )

    colunas_uf = [
        (coluna("dim_geo_uf", "uf"), "UF"),
        (coluna("dim_geo_uf", "regiao"), "Região"),
        (medida("Pedidos Entregues"), "Pedidos"),
        (medida("GMV Real / 100 mil hab."), "GMV/100k hab."),
        (medida("Prazo Médio Entrega (d)"), "Prazo (d)"),
        (medida("% Entregas no Prazo"), "% no prazo"),
        (medida("Nota Média"), "Nota"),
    ]
    p.adicionar(
        "tabela_uf",
        col_x(7),
        y_b,
        col_w(6),
        h_b,
        "tableEx",
        papeis={"Values": [projecao(campo, rotulo) for campo, rotulo in colunas_uf]},
        ordem=[(medida("GMV Real / 100 mil hab."), "Descending")],
        objetos={
            "grid": [{"properties": {"textSize": literal("8D"), "rowPadding": literal("2L")}}],
            "total": [{"properties": {"totals": literal("true")}}],
            "values": [
                {
                    "properties": {"fontColor": cor_medida("Cor SLA UF")},
                    "selector": {
                        "data": [{"dataViewWildcard": {"matchingOption": 1}}],
                        "metadata": "Medidas.% Entregas no Prazo",
                    },
                }
            ],
        },
        container=cabecalho_visual_fx(
            "Título Tabela UF",
            "GMV real por 100 mil hab. e SLA · verde ≥ 92%, vermelho < 85%",
        ),
    )

    p.rodape()
    return p


def pagina_comercial() -> Pagina:
    p = Pagina(
        "comercial",
        "Comercial e clientes",
        "Comercial, categorias e clientes",
        "Concentração de categorias e vendedores no grão de item · pagamentos, parcelas e retenção por coorte",
    )
    p.cabecalho(com_slicers=True)

    # Faixa KPIs (y=72, h=80): 4 cartões de 3 colunas (296x80)
    kpi_card(
        p, "kpi_ticket", 1, "Ticket Médio Real", "Ticket médio real",
        subtitulo_medida="Subtítulo Ticket Itens", unidades="1D",
    )
    kpi_card(
        p, "kpi_pct_cartao", 4, "% Pedidos Cartão", "Pedidos no cartão",
        subtitulo_medida="Subtítulo Cartão Parcelas",
    )
    kpi_card(
        p, "kpi_recompra", 7, "% Clientes Recompra", "Clientes com recompra",
        subtitulo_medida="Subtítulo Recompra",
    )
    kpi_card(
        p, "kpi_top_vendedores", 10, "% GMV Top 10% Vendedores", "GMV no top 10% vendedores",
        subtitulo_medida="Subtítulo Top Vendedores",
    )

    y_a, h_a = faixa("linha_a")
    y_b, h_b = faixa("linha_b")

    # Linha A (8 + 4 colunas): Top 8 Categorias (eixo único, sem eixo Y duplo!) + Decis de Vendedores
    p.adicionar(
        "pareto_categorias",
        col_x(1),
        y_a,
        col_w(8),
        h_a,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("dim_categoria", "categoria_pt"), "Categoria")],
            "Y": [projecao(medida("GMV Itens Real IPCA"), "GMV real")],
            "Tooltips": [
                projecao(medida("% GMV Categorias"), "% do GMV"),
                projecao(medida("% Acumulado GMV Categorias"), "% acumulado"),
            ],
        },
        ordem=[(medida("GMV Itens Real IPCA"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Categoria Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "categoryAxis": [{"properties": {"maxMarginFactor": literal("36L"), "innerPadding": literal("10L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "fontSize": literal("8D"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Pareto Categorias",
            "Top 8 por GMV real de itens (R$ de out/2018) · % acumulado na dica",
        ),
        filtros=[
            filtro_top_n(
                "top8_categorias",
                coluna("dim_categoria", "categoria_pt"),
                medida("GMV Itens Real IPCA"),
                8,
            )
        ],
    )

    p.adicionar(
        "concentracao_vendedores",
        col_x(9),
        y_a,
        col_w(4),
        h_a,
        "clusteredColumnChart",
        papeis={
            "Category": [projecao(coluna("dim_vendedor", "decil_gmv"), "Decil")],
            "Y": [projecao(medida("% GMV Vendedores"), "% GMV")],
        },
        ordem=[(coluna("dim_vendedor", "decil_gmv"), "Ascending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Decil Vendedores")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "fontSize": literal("8D"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Concentração Vendedores",
            "% do GMV real por decil de vendedores (D1 = top 10%)",
        ),
        filtros=[filtro_entre("decis_1_10", coluna("dim_vendedor", "decil_ordem"), "1L", "10L")],
    )

    # Linha B (4 + 4 + 4 colunas): Mix de Pagamento + Parcelas no Cartão + Coorte de Recompra
    p.adicionar(
        "mix_pagamento",
        col_x(1),
        y_b,
        col_w(4),
        h_b,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("fato_pedidos", "tipo_pagamento_pt"), "Pagamento")],
            "Y": [projecao(medida("% GMV Pagamento"), "% GMV")],
        },
        ordem=[(medida("% GMV Pagamento"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Pagamento Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "categoryAxis": [{"properties": {"maxMarginFactor": literal("36L"), "innerPadding": literal("14L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "labels": [{"properties": {"show": literal("true"), "fontSize": literal("8D"), "labelPosition": texto_literal("OutsideEnd")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Mix Pagamento",
            "% do GMV real entregue · 4 meios principais",
        ),
        filtros=[
            filtro_em(
                "pagamentos_validos",
                coluna("fato_pedidos", "tipo_pagamento_principal"),
                ["'credit_card'", "'boleto'", "'voucher'", "'debit_card'"],
            )
        ],
    )

    p.adicionar(
        "parcelas",
        col_x(5),
        y_b,
        col_w(4),
        h_b,
        "clusteredColumnChart",
        papeis={
            "Category": [projecao(coluna("fato_pedidos", "faixa_parcelas"), "Parcelas")],
            "Y": [projecao(medida("Pedidos Cartão"), "Pedidos")],
        },
        ordem=[(coluna("fato_pedidos", "faixa_parcelas"), "Ascending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Parcelas")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "labels": [{"properties": {"show": literal("false")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Parcelas",
            "Pedidos no cartão · 1x à vista em cinza, parcelados em azul",
        ),
        filtros=[filtro_entre("parcelas_1_10", coluna("fato_pedidos", "faixa_parcelas_ordem"), "1L", "10L")],
    )

    p.adicionar(
        "coorte_recompra",
        col_x(9),
        y_b,
        col_w(4),
        h_b,
        "pivotTable",
        papeis={
            "Rows": [projecao(coluna("fato_pedidos", "coorte_mes"), "Coorte")],
            "Columns": [projecao(coluna("fato_pedidos", "mes_coorte_label"), "Mês")],
            "Values": [projecao(medida("% Retenção Coorte"), "Retenção")],
        },
        objetos={
            "grid": [{"properties": {"textSize": literal("8D"), "rowPadding": literal("1L")}}],
            "subTotals": [
                {"properties": {"rowSubtotals": literal("false"), "columnSubtotals": literal("false")}}
            ],
            "values": [
                {
                    "properties": {"backColor": cor_medida("Cor Retenção Coorte")},
                    "selector": {
                        "data": [{"dataViewWildcard": {"matchingOption": 1}}],
                        "metadata": "Medidas.% Retenção Coorte",
                    },
                }
            ],
        },
        container=cabecalho_visual_fx(
            "Título Coorte Recompra",
            "% da coorte que compra de novo em M+1 a M+6",
        ),
        filtros=[
            filtro_entre("meses_1_a_6", coluna("fato_pedidos", "meses_desde_coorte"), "1L", "6L"),
            filtro_entre("coortes_cheias", coluna("fato_pedidos", "coorte_mes_num"), "201701L", "201807L"),
        ],
    )

    p.rodape()
    return p


def pagina_qualidade() -> Pagina:
    p = Pagina(
        "qualidade",
        "Qualidade e linhagem",
        "Qualidade de dados e linhagem",
        "Anomalias reais encontradas na base Olist (99.441 pedidos brutos), tratamento determinístico e conferência SQL",
    )
    # Auditoria cobre a base inteira (sem slicers no cabeçalho).
    p.cabecalho(com_slicers=False)

    # Faixa KPIs (y=72, h=80): 4 cartões de 3 colunas (296x80)
    kpi_card(
        p, "kpi_pedidos_brutos", 1, "Pedidos Brutos", "Pedidos brutos (Olist)",
        subtitulo_medida="Subtítulo Pedidos Brutos", unidades="1D",
    )
    kpi_card(
        p, "kpi_pct_excluidos", 4, "% Excluídos da Análise", "Pedidos excluídos",
        subtitulo_medida="Subtítulo Excluídos",
    )
    kpi_card(
        p, "kpi_anomalias", 7, "Anomalias Detectadas", "Ocorrências auditadas",
        subtitulo_medida="Subtítulo Anomalias", unidades="1D",
    )
    kpi_card(
        p, "kpi_gabarito", 10, "Selo Gabarito SQL", "Conferência SQL e DAX",
        subtitulo="consultas do gabarito conferem",
    )

    y_a, h_a = faixa("linha_a")
    y_b, h_b = faixa("linha_b")

    # Linha A (6 + 6 colunas): Top 7 Regras de Auditoria + Ocorrências por Tipo de Tratamento
    p.adicionar(
        "anomalias_tipo",
        col_x(1),
        y_a,
        col_w(6),
        h_a,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("qualidade_auditoria", "regra"), "Regra")],
            "Y": [projecao(medida("Anomalias Detectadas"), "Registros")],
        },
        ordem=[(medida("Anomalias Detectadas"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Anomalia Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "labels": [
                {
                    "properties": {
                        "show": literal("true"),
                        "fontSize": literal("8D"),
                        "labelDisplayUnits": literal("1D"),
                        "labelPosition": texto_literal("OutsideEnd"),
                    }
                }
            ],
            "categoryAxis": [{"properties": {"maxMarginFactor": literal("48L"), "fontSize": literal("8D"), "innerPadding": literal("10L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Anomalias Tipo",
            "Top 7 regras por registros afetados · base bruta Olist",
        ),
        filtros=[
            filtro_top_n(
                "top7_regras",
                coluna("qualidade_auditoria", "regra"),
                medida("Anomalias Detectadas"),
                7,
            )
        ],
    )

    p.adicionar(
        "tratamento_anomalias",
        col_x(7),
        y_a,
        col_w(6),
        h_a,
        "clusteredBarChart",
        papeis={
            "Category": [projecao(coluna("qualidade_auditoria", "tipo_curto"), "Tratamento")],
            "Y": [projecao(medida("Anomalias Detectadas"), "Registros")],
        },
        ordem=[(medida("Anomalias Detectadas"), "Descending")],
        objetos={
            "dataPoint": [
                {
                    "properties": {"fill": cor_medida("Cor Tratamento Destaque")},
                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]},
                }
            ],
            "labels": [
                {
                    "properties": {
                        "show": literal("true"),
                        "fontSize": literal("8D"),
                        "labelDisplayUnits": literal("1D"),
                        "labelPosition": texto_literal("OutsideEnd"),
                    }
                }
            ],
            "categoryAxis": [{"properties": {"innerPadding": literal("12L")}}],
            "valueAxis": [{"properties": {"show": literal("false")}}],
            "legend": [{"properties": {"show": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Tratamento Anomalias",
            "Registros auditados por tipo de ação determinística",
        ),
    )

    # Linha B (6 + 6 colunas): Tabela Completa de Auditoria + Linhagem das Fontes Públicas
    colunas_aud = [
        (coluna("qualidade_auditoria", "regra"), "Regra"),
        (coluna("qualidade_auditoria", "tabela_curta"), "Origem"),
        (coluna("qualidade_auditoria", "linhas_afetadas"), "Linhas"),
        (coluna("qualidade_auditoria", "pct_base_frac"), "% base"),
        (coluna("qualidade_auditoria", "tipo_curto"), "Tipo"),
    ]
    p.adicionar(
        "tabela_auditoria",
        col_x(1),
        y_b,
        col_w(6),
        h_b,
        "tableEx",
        papeis={"Values": [projecao(campo, rotulo) for campo, rotulo in colunas_aud]},
        ordem=[(coluna("qualidade_auditoria", "linhas_afetadas"), "Descending")],
        objetos={
            "grid": [{"properties": {"textSize": literal("7.5D"), "rowPadding": literal("2L")}}],
            "total": [{"properties": {"totals": literal("false")}}],
        },
        container={
            **cabecalho_visual_fx(
                "Título Tabela Auditoria",
                "13 regras da base pública Olist com tratamento documentado",
            ),
            "padding": padding_container(10, 10, 10, 10),
        },
    )

    colunas_fontes = [
        (coluna("fontes_metadados", "fonte"), "Fonte"),
        (coluna("fontes_metadados", "arquivo_curto"), "Arquivo"),
        (coluna("fontes_metadados", "registros"), "Registros"),
        (coluna("fontes_metadados", "coletado_data"), "Coletado"),
        (coluna("fontes_metadados", "licenca_curta"), "Licença"),
    ]
    p.adicionar(
        "linhagem_fontes",
        col_x(7),
        y_b,
        col_w(6),
        h_b,
        "tableEx",
        papeis={"Values": [projecao(campo, rotulo) for campo, rotulo in colunas_fontes]},
        ordem=[(coluna("fontes_metadados", "registros"), "Descending")],
        objetos={
            "grid": [{"properties": {"textSize": literal("8D"), "rowPadding": literal("2L")}}],
            "total": [{"properties": {"totals": literal("false")}}],
        },
        container=cabecalho_visual_fx(
            "Título Linhagem Fontes",
            "Manifesto com hash SHA-256 e timestamp UTC em data/raw/manifesto_coleta.json",
        ),
    )

    p.rodape()
    return p


def escrever_relatorio(pasta: Path) -> None:
    escrever_json(
        pasta / "definition.pbir",
        {
            "$schema": ESQUEMAS + "item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}},
        },
    )
    definicao = pasta / "definition"
    escrever_json(
        definicao / "version.json",
        {
            "$schema": ESQUEMAS + "item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0",
        },
    )
    escrever_json(
        definicao / "report.json",
        {
            "$schema": f"{ESQUEMAS}item/report/definition/report/{VERSOES['report']}/schema.json",
            "themeCollection": {
                "customTheme": {
                    "name": "tema.json",
                    "reportVersionAtImport": VERSOES,
                    "type": "RegisteredResources",
                }
            },
            "resourcePackages": [
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [{"name": "tema.json", "path": "tema.json", "type": "CustomTheme"}],
                }
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultDrillFilterOtherVisuals": True,
                "useEnhancedTooltips": True,
            },
        },
    )
    tema_dest = pasta / "StaticResources" / "RegisteredResources" / "tema.json"
    tema_dest.parent.mkdir(parents=True, exist_ok=True)
    escrever(tema_dest, TEMA_ARQ.read_text(encoding="utf-8").replace("\r\n", "\n"))

    paginas = [
        pagina_visao_executiva(),
        pagina_logistica_sla(),
        pagina_comercial(),
        pagina_qualidade(),
    ]
    escrever_json(
        definicao / "pages" / "pages.json",
        {
            "$schema": ESQUEMAS + "item/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [pag.nome for pag in paginas],
            "activePageName": paginas[0].nome,
        },
    )
    for pag in paginas:
        pasta_pag = definicao / "pages" / pag.nome
        escrever_json(
            pasta_pag / "page.json",
            {
                "$schema": f"{ESQUEMAS}item/report/definition/page/{VERSOES['page']}/schema.json",
                "name": pag.nome,
                "displayName": pag.display_name,
                "displayOption": "FitToPage",
                "height": PAGINA_ALTURA,
                "width": PAGINA_LARGURA,
            },
        )
        for visual in pag.visuais:
            escrever_json(pasta_pag / "visuals" / visual["name"] / "visual.json", visual)


# ---------------------------------------------------------------------------------------------
# Escrita e CLI


def escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8", newline="\n")


def escrever_json(caminho: Path, dados) -> None:
    escrever(caminho, json.dumps(dados, ensure_ascii=False, indent=2) + "\n")


def montar(saida: Path, pasta_dados: str) -> None:
    for parte in (
        f"{NOME}.SemanticModel/definition",
        f"{NOME}.Report/definition",
        f"{NOME}.Report/StaticResources",
    ):
        if (saida / parte).exists():
            shutil.rmtree(saida / parte)
    escrever_json(
        saida / f"{NOME}.pbip",
        {
            "$schema": ESQUEMAS + "pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{NOME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    escrever(
        saida / ".gitignore",
        "# O Power BI Desktop guarda aqui o cache dos dados e as preferências locais.\n**/.pbi/\n",
    )
    escrever_modelo(saida / f"{NOME}.SemanticModel", pasta_dados)
    escrever_relatorio(saida / f"{NOME}.Report")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--saida",
        type=Path,
        default=SAIDA_PADRAO,
        help="pasta de saída do projeto PBIP (padrão: powerbi/)",
    )
    parser.add_argument(
        "--pasta-dados",
        "--pasta-entrada",
        dest="pasta_dados",
        default=CAMINHO_DE_EXEMPLO,
        help="caminho absoluto da pasta data/limpa, gravado no parâmetro PastaDados",
    )
    opcoes = parser.parse_args()
    montar(opcoes.saida.resolve(), opcoes.pasta_dados)
    print(f"Projeto gravado em {opcoes.saida}. Abra {NOME}.pbip no Power BI Desktop.")


if __name__ == "__main__":
    main()
