"""Gera todos os arquivos derivados do padrão visual a partir de marca/tokens.json.

Uso:
    python marca/gerar.py                       # acento azul
    python marca/gerar.py --acento petroleo     # acento do projeto
    python marca/gerar.py --dados caminho/resumo.json --saida-dados exemplos/dados

Saídas (não edite à mão):
    marca/tokens.css                      variáveis CSS (claro, escuro, 4 acentos) + superfícies do navegador
    marca/powerbi/tema-<acento>-<modo>.json   8 temas do Power BI
    marca/quarto/_brand.yml               marca do Quarto (HTML, revealjs, Typst)
    marca/quarto/typst-template.typ       cores + modelo.typ, parcial do Typst
    marca/marca.mplstyle                  estilo do matplotlib
"""
import argparse
import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
T = json.loads((RAIZ / "tokens.json").read_text(encoding="utf-8"))
MODOS = ("claro", "escuro")


def lum(hexa):
    r, g, b = (int(hexa.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mistura(frente, fundo, alfa):
    """Cor sólida de `frente` com opacidade `alfa` sobre `fundo` (o Power BI não aceita alfa)."""
    f = [int(frente.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(fundo.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x * alfa + y * (1 - alfa)):02X}" for x, y in zip(f, b))


def verificar():
    """Autoteste: falha a geração se algum par de texto ficar abaixo de AA."""
    erros = []
    for m in MODOS:
        t = T["tema"][m]
        for fundo in ("surface", "surface_2", "canvas"):
            for tinta in ("ink", "ink_2", "ink_3", "positivo", "negativo", "alerta"):
                c = contraste(t[tinta], t[fundo])
                if c < 4.5:
                    erros.append(f"{m}: {tinta} sobre {fundo} = {c:.2f}")
            for nome, cor in T["cores"].items():
                if nome.startswith("_"):
                    continue
                c = contraste(cor[m]["ink"], t[fundo])
                if c < 4.5:
                    erros.append(f"{m}: {nome}.ink sobre {fundo} = {c:.2f}")
        for acento in T["acentos"]:
            if acento.startswith("_"):
                continue
            c = contraste(T["cores"][acento][m]["mark"], t["surface"])
            if c < 3:
                erros.append(f"{m}: acento {acento}.mark sobre surface = {c:.2f} (< 3:1)")
    assert not erros, "Contraste insuficiente:\n  " + "\n  ".join(erros)


def paleta(acento, modo):
    return [T["cores"][n][modo]["mark"] for n in T["acentos"][acento]]


def acentos():
    return [a for a in T["acentos"] if not a.startswith("_")]


# ---------- CSS ----------
def vars_tema(modo):
    t = T["tema"][modo]
    return "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in t.items())


def vars_acento(acento, modo):
    c = T["cores"][acento][modo]
    linhas = [f"  --acento: {c['mark']};", f"  --acento-ink: {c['ink']};"]
    linhas += [f"  --serie-{i}: {cor};" for i, cor in enumerate(paleta(acento, modo), 1)]
    return "\n".join(linhas)


def css():
    tipo = T["tipo"]["web_px"]
    estat = [
        f"  --fonte: {T['fonte']['web']};",
        f"  --fonte-mono: {T['fonte']['mono_web']};",
        *[f"  --t-{k}: {s}px;\n  --t-{k}-peso: {p};\n  --t-{k}-altura: {a};" for k, (s, p, a) in tipo.items()],
        *[f"  --e-{i}: {v}px;" for i, v in enumerate(T["espaco"], 1)],
        *[f"  --raio-{k}: {v}px;" for k, v in T["raio"].items()],
        f"  --mov-duracao: {T['movimento']['duracao_ms']}ms;",
        f"  --mov-curva: {T['movimento']['curva']};",
        f"  --sombra-flutuante: {T['sombra_flutuante']};",
        "  --acento-wash: color-mix(in srgb, var(--acento) 12%, var(--surface));",
        f"  --div-neg: var(--{T['divergente']['negativo']});",
        f"  --div-pos: var(--{T['divergente']['positivo']});",
    ]
    cores_nome = lambda m: "\n".join(
        f"  --{n}: {c[m]['mark']};" for n, c in T["cores"].items() if not n.startswith("_"))
    escuro = ':root[data-theme="dark"]'
    partes = [
        "/* Gerado por marca/gerar.py a partir de tokens.json. Não edite à mão. */",
        ":root {\n  color-scheme: light;\n" + "\n".join(estat) + "\n" + vars_tema("claro") + "\n"
        + cores_nome("claro") + "\n" + vars_acento("azul", "claro") + "\n}",
    ]
    for a in acentos():
        partes.append(f':root[data-acento="{a}"] {{\n{vars_acento(a, "claro")}\n}}')
    bloco_escuro = vars_tema("escuro") + "\n" + cores_nome("escuro") + "\n" + vars_acento("azul", "escuro")
    partes.append(f'{escuro} {{\n  color-scheme: dark;\n{bloco_escuro}\n}}')
    for a in acentos():
        partes.append(f'{escuro}[data-acento="{a}"] {{\n{vars_acento(a, "escuro")}\n}}')
    media = [f':root:not([data-theme="light"]) {{\n  color-scheme: dark;\n{bloco_escuro}\n}}']
    media += [f':root:not([data-theme="light"])[data-acento="{a}"] {{\n{vars_acento(a, "escuro")}\n}}' for a in acentos()]
    partes.append("@media (prefers-color-scheme: dark) {\n" + "\n".join(media) + "\n}")
    partes.append(SUPERFICIES)
    return "\n\n".join(partes) + "\n"


SUPERFICIES = """/* Superfícies do navegador: o que não desenhamos também veste o padrão. */
::selection { background: color-mix(in srgb, var(--acento) 24%, transparent); color: var(--ink); }
:root { accent-color: var(--acento); caret-color: var(--acento-ink); scrollbar-color: var(--border-strong) transparent; }
:focus-visible { outline: 2px solid var(--acento-ink); outline-offset: 2px; border-radius: var(--raio-controle); }
a { color: var(--acento-ink); text-underline-offset: 0.2em; text-decoration-thickness: 1px; }
table, .num { font-variant-numeric: tabular-nums; }
@media (prefers-reduced-motion: reduce) { * { transition-duration: 0ms !important; animation: none !important; } }"""


# ---------- Power BI ----------
def solido(c):
    return {"solid": {"color": c}}


def tema_powerbi(acento, modo):
    t = T["tema"][modo]
    c = T["cores"][acento][modo]
    f, ff = T["fonte"]["powerbi"], T["fonte"]["powerbi_forte"]
    pt = T["tipo"]["powerbi_pt"]
    neg = T["cores"][T["divergente"]["negativo"]][modo]["mark"]
    pos = T["cores"][T["divergente"]["positivo"]][modo]["mark"]
    grade = {"gridVertical": False, "gridHorizontal": True, "gridHorizontalColor": solido(t["grid"]),
             "gridHorizontalWeight": 1, "outlineColor": solido(t["border"]), "rowPadding": 4, "textSize": pt["label"]}
    cabec = {"fontFamily": ff, "fontColor": solido(t["ink_2"]), "backColor": solido(t["surface_2"]), "outline": "BottomOnly"}
    return {
        "name": f"{T['nome']} · {acento} · {modo}",
        "dataColors": paleta(acento, modo) + [t["mark_muted"]],
        "background": t["surface"], "foreground": t["ink"], "tableAccent": c["mark"],
        "good": t["positivo"], "neutral": t["alerta"], "bad": t["negativo"],
        "maximum": pos, "center": t["neutro_div"], "minimum": neg, "null": t["mark_muted"],
        "hyperlink": c["ink"], "visitedHyperlink": c["ink"],
        "textClasses": {
            "largeTitle": {"fontFace": ff, "fontSize": pt["largeTitle"], "color": t["ink"]},
            "callout": {"fontFace": ff, "fontSize": pt["callout"], "color": t["ink"]},
            "title": {"fontFace": ff, "fontSize": pt["title"], "color": t["ink"]},
            "header": {"fontFace": ff, "fontSize": pt["header"], "color": t["ink_2"]},
            "label": {"fontFace": f, "fontSize": pt["label"], "color": t["ink_3"]},
        },
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": solido(t["surface"]), "transparency": 0}],
                "border": [{"show": True, "color": solido(t["border"]), "radius": T["raio"]["cartao"]}],
                "dropShadow": [{"show": False}],
                "padding": [{"top": 12, "bottom": 12, "left": 16, "right": 16}],
                "title": [{"show": True, "fontFamily": ff, "fontSize": pt["title"], "fontColor": solido(t["ink"]), "alignment": "left"}],
                "subTitle": [{"show": True, "fontFamily": f, "fontSize": pt["label"], "fontColor": solido(t["ink_2"]), "alignment": "left"}],
                "categoryAxis": [{"show": True, "fontFamily": f, "fontSize": pt["label"], "labelColor": solido(t["ink_3"]),
                                  "showAxisTitle": False, "gridlineShow": False, "axisLine": False}],
                "valueAxis": [{"show": True, "fontFamily": f, "fontSize": pt["label"], "labelColor": solido(t["ink_3"]),
                               "showAxisTitle": False, "gridlineShow": True, "gridlineColor": solido(t["grid"]),
                               "gridlineThickness": 1, "gridlineStyle": "solid", "axisLine": False}],
                "legend": [{"show": True, "position": "TopLeft", "fontFamily": f, "fontSize": pt["label"],
                            "labelColor": solido(t["ink_2"]), "showTitle": False}],
                "labels": [{"fontFamily": f, "fontSize": pt["label"], "color": solido(t["ink_2"])}],
            }},
            "page": {"*": {
                "background": [{"color": solido(t["canvas"]), "transparency": 0}],
                "outspace": [{"color": solido(t["outspace"]), "transparency": 0}],
            }},
            "card": {"*": {
                "labels": [{"fontFamily": ff, "fontSize": pt["callout"], "color": solido(t["ink"])}],
                "categoryLabels": [{"show": False}],
                "title": [{"show": True, "fontFamily": f, "fontSize": pt["label"], "fontColor": solido(t["ink_2"]), "alignment": "left"}],
            }},
            "slicer": {"*": {
                "background": [{"show": True, "color": solido(t["surface"]), "transparency": 0}],
                "border": [{"show": True, "color": solido(t["border"]), "radius": T["raio"]["controle"]}],
                "title": [{"show": False}],
                "header": [{"show": True, "fontFamily": ff, "textSize": pt["nota"], "fontColor": solido(t["ink_2"])}],
                "items": [{"fontFamily": f, "textSize": pt["header"], "fontColor": solido(t["ink"])}],
            }},
            "tableEx": {"*": {
                "grid": [grade], "columnHeaders": [cabec],
                "values": [{"fontFamily": f, "fontColorPrimary": solido(t["ink"]), "backColorPrimary": solido(t["surface"]),
                            "fontColorSecondary": solido(t["ink"]), "backColorSecondary": solido(t["surface"])}],
                "total": [{"fontFamily": ff, "fontColor": solido(t["ink"]), "backColor": solido(t["surface_2"])}],
            }},
            "pivotTable": {"*": {
                "grid": [grade], "columnHeaders": [cabec],
                "rowHeaders": [{"fontFamily": ff, "fontColor": solido(t["ink"]), "backColor": solido(t["surface"])}],
                "values": [{"fontFamily": f, "fontColorPrimary": solido(t["ink"]), "backColorPrimary": solido(t["surface"])}],
            }},
            "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}],
                              "title": [{"show": False}], "subTitle": [{"show": False}], "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}]}},
            "basicShape": {"*": {"background": [{"show": False}], "border": [{"show": False}], "title": [{"show": False}]}},
            "lineChart": {"*": {"lineStyles": [{"strokeWidth": 2, "showMarker": False}]}},
            "lineClusteredColumnComboChart": {"*": {"lineStyles": [{"strokeWidth": 2, "showMarker": False}]}},
        },
    }


# ---------- Quarto / Typst / matplotlib ----------
def brand(acento):
    t, c = T["tema"]["claro"], T["cores"][acento]["claro"]
    paleta_nomes = {n: v["claro"]["mark"] for n, v in T["cores"].items() if not n.startswith("_")}
    linhas = [
        "# Gerado por marca/gerar.py. Não edite à mão.",
        "meta:", f"  name: \"{T['nome']}\"",
        "color:", "  palette:", *[f"    {n}: \"{v}\"" for n, v in paleta_nomes.items()],
        f"    tinta: \"{t['ink']}\"", f"    tinta-2: \"{t['ink_2']}\"", f"    canvas: \"{t['canvas']}\"",
        f"  background: \"{t['surface']}\"", f"  foreground: \"{t['ink']}\"",
        f"  primary: \"{c['ink']}\"", f"  secondary: \"{t['ink_2']}\"",
        f"  light: \"{t['canvas']}\"", f"  dark: \"{t['ink']}\"",
        f"  success: \"{t['positivo']}\"", f"  danger: \"{t['negativo']}\"", f"  warning: \"{t['alerta']}\"",
        "typography:", "  fonts:", *[f"    - family: \"{n}\"\n      source: system" for n in T["fonte"]["typst"]],
        f"  base:\n    family: \"{T['fonte']['typst'][0]}\"\n    line-height: 1.45",
        f"  headings:\n    family: \"{T['fonte']['typst'][0]}\"\n    weight: 600\n    color: \"{t['ink']}\"",
        "  link:\n    color: primary",
    ]
    return "\n".join(linhas) + "\n"


def typst_cores(acento):
    t, c = T["tema"]["claro"], T["cores"][acento]["claro"]
    pares = {k.replace("_", "-"): v for k, v in t.items()}
    pares.update({"acento": c["mark"], "acento-ink": c["ink"]})
    corpo = ",\n".join(f"  {k}: rgb(\"{v}\")" for k, v in pares.items())
    series = ", ".join(f"rgb(\"{h}\")" for h in paleta(acento, "claro"))
    fontes = ", ".join(f"\"{n}\"" for n in T["fonte"]["typst"])
    pt = T["tipo"]["pdf_pt"]
    return (f"// Gerado por marca/gerar.py (acento {acento}). Edite modelo.typ, não este bloco.\n"
            f"#let marca = (\n{corpo},\n  series: ({series}),\n)\n"
            f"#let marca-fontes = ({fontes})\n"
            f"#let marca-assinatura = \"{T['assinatura']}\"\n"
            f"#let marca-pt = ({', '.join(f'{k}: {v}pt' for k, v in pt.items())})\n\n")


def mplstyle(acento):
    t = T["tema"]["claro"]
    cyc = ", ".join(f"'{h.lstrip('#')}'" for h in paleta(acento, "claro"))
    fam = ", ".join(T["fonte"]["typst"] + ["DejaVu Sans"])
    sem = lambda h: h.lstrip("#")
    return f"""# Gerado por marca/gerar.py (acento {acento}). Não edite à mão.
font.family: sans-serif
font.sans-serif: {fam}
font.size: 9
text.color: {sem(t['ink'])}
axes.prop_cycle: cycler('color', [{cyc}])
axes.facecolor: {sem(t['surface'])}
axes.edgecolor: {sem(t['axis'])}
axes.labelcolor: {sem(t['ink_2'])}
axes.titlesize: 11
axes.titleweight: 600
axes.titlelocation: left
axes.titlepad: 10
axes.titlecolor: {sem(t['ink'])}
axes.spines.top: False
axes.spines.right: False
axes.spines.left: False
axes.spines.bottom: True
axes.linewidth: 1
axes.grid: True
axes.grid.axis: y
axes.axisbelow: True
grid.color: {sem(t['grid'])}
grid.linewidth: 1
grid.linestyle: -
xtick.color: {sem(t['ink_3'])}
ytick.color: {sem(t['ink_3'])}
xtick.labelcolor: {sem(t['ink_3'])}
ytick.labelcolor: {sem(t['ink_3'])}
xtick.major.size: 0
ytick.major.size: 0
xtick.major.pad: 6
ytick.major.pad: 6
lines.linewidth: 2
lines.solid_capstyle: round
lines.solid_joinstyle: round
legend.frameon: False
legend.fontsize: 9
figure.facecolor: {sem(t['surface'])}
figure.dpi: 150
savefig.dpi: 200
savefig.facecolor: {sem(t['surface'])}
savefig.bbox: tight
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acento", default="azul", choices=acentos())
    ap.add_argument("--dados", type=Path, help="resumo.json do projeto, copiado para --saida-dados")
    ap.add_argument("--saida-dados", type=Path, default=RAIZ.parent / "exemplos" / "dados")
    a = ap.parse_args()
    verificar()

    (RAIZ / "tokens.css").write_text(css(), encoding="utf-8")
    pbi = RAIZ / "powerbi"
    pbi.mkdir(exist_ok=True)
    for ac in acentos():
        for m in MODOS:
            (pbi / f"tema-{ac}-{m}.json").write_text(
                json.dumps(tema_powerbi(ac, m), ensure_ascii=False, indent=2), encoding="utf-8")
    q = RAIZ / "quarto"
    q.mkdir(exist_ok=True)
    (q / "_brand.yml").write_text(brand(a.acento), encoding="utf-8")
    (q / "typst-template.typ").write_text(
        typst_cores(a.acento) + (q / "modelo.typ").read_text(encoding="utf-8"), encoding="utf-8")
    (RAIZ / "marca.mplstyle").write_text(mplstyle(a.acento), encoding="utf-8")

    if a.dados:
        a.saida_dados.mkdir(parents=True, exist_ok=True)
        destino_json = a.saida_dados / "resumo.json"
        if a.dados.resolve() != destino_json.resolve():
            shutil.copyfile(a.dados, destino_json)
        bruto = a.dados.read_text(encoding="utf-8")
        json.loads(bruto)  # valida antes de embutir
        # resumo.js deixa o painel abrir com duplo clique (file:// bloqueia fetch).
        (a.saida_dados / "resumo.js").write_text(f"window.RESUMO = {bruto};\n", encoding="utf-8")
    print(f"ok: tokens.css, {len(acentos()) * 2} temas Power BI, _brand.yml, typst-template.typ, marca.mplstyle (acento {a.acento})")


if __name__ == "__main__":
    main()
