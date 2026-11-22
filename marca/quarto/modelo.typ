// modelo.typ: layout do relatório técnico em A4.
// Este arquivo passa pelo motor de templates do Pandoc: não use cifrão aqui.
// As variáveis `marca`, `marca-fontes`, `marca-pt` e `marca-assinatura` vêm do bloco gerado acima.

// Cor de um tom de variação: "bom", "ruim" ou "neutro".
#let cor-tom(tom) = if tom == "bom" { marca.positivo } else if tom == "ruim" { marca.negativo } else { marca.ink-2 }

// Triângulo desenhado (nunca um caractere): "sobe" ou "desce".
#let seta(direcao, cor) = box(baseline: -0.05em, if direcao == "sobe" {
  polygon(fill: cor, (0pt, 5pt), (3pt, 0pt), (6pt, 5pt))
} else {
  polygon(fill: cor, (0pt, 0pt), (6pt, 0pt), (3pt, 5pt))
})

// Variação com sinal, seta e cor do tom; o sinal no texto garante leitura sem cor.
#let variacao(texto, direcao: none, tom: "neutro") = box(text(weight: 600, fill: cor-tom(tom), {
  if direcao != none { seta(direcao, cor-tom(tom)); h(3pt) }
  texto
}))

// Cartão de KPI, o mesmo vocabulário da linha de KPIs do painel.
#let kpi(rotulo, valor, delta: none, direcao: none, tom: "neutro", base: none) = block(
  width: 100%, inset: (x: 10pt, y: 9pt), radius: 6pt,
  stroke: 0.75pt + marca.border, fill: marca.surface,
  {
    text(size: 8pt, fill: marca.ink-2, rotulo)
    v(6pt, weak: true)
    block(text(size: marca-pt.kpi, weight: 600, fill: marca.ink, box(valor)))
    if delta != none {
      v(7pt, weak: true)
      text(size: 8pt, variacao(delta, direcao: direcao, tom: tom))
      if base != none { text(size: 8pt, fill: marca.ink-3, [ #base]) }
    }
  },
)
#let kpis(..itens) = grid(
  columns: (1fr,) * itens.pos().len(), column-gutter: 8pt, ..itens.pos(),
)

// Linha de fonte embaixo de cada figura ou tabela.
#let fonte(corpo) = block(above: 5pt, below: 16pt, text(size: marca-pt.legenda, fill: marca.ink-3, corpo))

// Caixa de método: cinza neutro, nunca colorida.
#let nota(titulo: none, corpo) = block(
  width: 100%, inset: (x: 12pt, y: 10pt), radius: 6pt, above: 14pt, below: 14pt,
  fill: marca.surface-2, stroke: 0.75pt + marca.border,
  {
    if titulo != none { block(below: 5pt, text(size: 9pt, weight: 600, titulo)) }
    text(size: 9pt, fill: marca.ink-2, corpo)
  },
)

#let relatorio(title: none, subtitle: none, date: none, projeto: none, fontes: none, doc) = {
  set document(title: title, author: marca-assinatura)
  set text(font: marca-fontes, size: marca-pt.corpo, fill: marca.ink, lang: "pt", region: "BR")
  set par(leading: 0.7em, spacing: 1em, justify: false)
  set page(
    paper: "a4",
    margin: (x: 22mm, top: 25mm, bottom: 22mm),
    header: context {
      if counter(page).get().first() > 1 {
        set text(size: 8pt, fill: marca.ink-3)
        grid(columns: (1fr, auto), title, date)
        v(-5pt)
        line(length: 100%, stroke: 0.5pt + marca.border)
      }
    },
    footer: context {
      set text(size: 8pt, fill: marca.ink-3)
      grid(
        columns: (1fr, auto),
        [#marca-assinatura#if projeto != none [ · #projeto]],
        counter(page).display("1 de 1", both: true),
      )
    },
  )

  set heading(numbering: "1.1")
  show heading: set text(weight: 600, fill: marca.ink)
  show heading.where(level: 1): it => block(above: 24pt, below: 10pt, text(size: marca-pt.h1, it))
  show heading.where(level: 2): it => block(above: 18pt, below: 8pt, text(size: marca-pt.h2, it))
  show heading.where(level: 3): it => block(above: 14pt, below: 6pt, text(size: marca-pt.h3, it))

  show link: set text(fill: marca.acento-ink)
  show raw: set text(font: ("Cascadia Mono", "Consolas"), size: 8.5pt)
  show raw.where(block: true): it => block(
    width: 100%, inset: 9pt, radius: 6pt, fill: marca.surface-2, stroke: 0.75pt + marca.border, it,
  )

  // Figura: título acima (achado + unidade), fonte abaixo pela função `fonte`.
  show figure: set align(left)
  set figure.caption(position: top)
  // A fonte mora dentro da figura (que não quebra página), então o respiro vem depois da figura.
  show figure: set block(above: 16pt, below: 16pt)
  show figure.caption: it => {
    set align(left)
    block(below: 6pt, text(size: 9.5pt, weight: 600, fill: marca.ink)[#it.supplement #context it.counter.display(it.numbering) · #it.body])
  }

  // Tabela: só linhas horizontais, cabeçalho em tinta 2, números tabulares.
  set table(
    stroke: (x, y) => (bottom: if y == 0 { 0.75pt + marca.ink-3 } else { 0.5pt + marca.border }),
    inset: (x: 6pt, y: 5pt),
    align: (x, y) => if x == 0 { left } else { right },
  )
  show table: set text(size: 9pt, number-width: "tabular")
  show table.cell.where(y: 0): set text(size: 8.5pt, weight: 600, fill: marca.ink-2)

  // Folha de rosto: o título divide a página 1 com o resumo, sem capa vazia.
  block(below: 20pt, {
    block(below: 6pt, text(size: 24pt, weight: 600, fill: marca.ink, title))
    if subtitle != none { block(below: 12pt, text(size: 12pt, fill: marca.ink-2, subtitle)) }
    text(size: 8.5pt, fill: marca.ink-3)[#marca-assinatura#if date != none [ · #date]#if fontes != none [ · Dados: #fontes]]
    v(10pt)
    line(length: 100%, stroke: 0.5pt + marca.border)
  })

  doc
}
