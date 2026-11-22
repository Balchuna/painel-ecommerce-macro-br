# Design Spec — Painel E-Commerce & Macroeconomia Brasil

> Fonte única de verdade visual para o relatório Power BI (`powerbi/`) **e** para o painel web (`docs/index.html`).
> Tema Power BI: [`tema/tema.json`](../tema/tema.json). Os tokens abaixo são idênticos nos dois.
> Dono: `designer`. Alterações de layout → combinar no board antes.

---

## 1. Princípios (editorial executivo)

1. **Insight primeiro.** Todo título de visual é uma frase que *afirma* algo verificável ("Atraso derruba a nota de 4,3★ para 1,7★"), não um rótulo ("Nota por faixa"). O subtítulo diz *como ler*.
2. **Cor = significado, nunca decoração.** Navy = nominal/base, Teal = real/positivo, Amber = macro (IPCA, Selic, câmbio), Vermelho = **somente** atraso / impacto negativo. Todo o resto é cinza ardósia.
3. **Zero ruído.** Sem bordas grossas, sem sombras, sem eixo X com gridlines, sem títulos de eixo redundantes, sem legendas quando a cor já está no título, sem rótulos de dados em todas as barras de séries longas.
4. **Uma hierarquia por página:** cabeçalho → faixa de KPIs → visual-herói (o argumento) → visuais de apoio → rodapé de fontes.
5. **Honestidade:** números nos títulos vêm do gabarito SQL (`sql/gabarito/*.csv`) ou de medidas DAX dinâmicas. Placeholders `‹…›` neste documento **devem** ser substituídos pelo valor verificado, nunca inventados.

---

## 2. Tokens

### 2.1 Cores

| Token | Hex | Uso |
|---|---|---|
| `canvas` | `#F8FAFC` | fundo da página (Power BI: page background) |
| `outspace` | `#F1F5F9` | área fora da página |
| `surface` | `#FFFFFF` | cartões / visuais |
| `hairline` | `#E2E8F0` | borda 1px dos cartões, divisórias |
| `grid` | `#EEF2F6` | gridlines do eixo de valores (só horizontais) |
| `ink` | `#0F172A` | títulos, valores de KPI |
| `ink-2` | `#334155` | rótulos de dados, texto de corpo |
| `muted` | `#64748B` | subtítulos, rótulos de KPI, eixo de categorias |
| `faint` | `#94A3B8` | eixo de valores, rodapé, séries de referência |
| `navy` (primária) | `#1E3A5F` | GMV **nominal**, séries base, barras padrão |
| `navy-300` | `#A9BCD3` | navy em segundo plano (ex.: barras fora do top) |
| `teal` (acento) | `#0D9488` | GMV **real (deflacionado IPCA)**, "no prazo", deltas positivos, selo ✓ |
| `teal-100` | `#CCFBF1` | fundo de selos/badges positivos |
| `amber` (macro) | `#D97706` | IPCA, Selic, PTAX, avisos de qualidade |
| `amber-100` | `#FEF3C7` | fundo de avisos |
| `coral` (negativo) | `#DC2626` | **somente** atraso de entrega, nota baixa, deltas negativos |
| `coral-100` | `#FEE2E2` | fundo de alertas |

**Escala ordinal de atraso** (página 2, visual-herói — do bom ao pior):

| Faixa | Cor |
|---|---|
| No prazo / antecipado | `#0D9488` |
| 1–3 dias de atraso | `#FCA5A5` |
| 4–7 dias | `#F87171` |
| 8–14 dias | `#DC2626` |
| 15+ dias | `#991B1B` |

**Regiões IBGE** (só quando a região for a série — senão use navy): Norte `#0D9488`, Nordeste `#D97706`, Centro-Oeste `#94A3B8`, Sudeste `#1E3A5F`, Sul `#4F6D8F`.

Acessibilidade: `ink`/`surface` 17,9:1; `muted`/`surface` 4,8:1; `navy`/`surface` 11,6:1; `teal`/`surface` 3,7:1 (usar teal em texto só ≥ 12pt semibold ou em gráficos); `coral`/`surface` 4,8:1. Navy × teal × amber são distinguíveis em deuteranopia/protanopia por luminância; vermelho nunca aparece ao lado de verde.

### 2.2 Tipografia

Power BI: **Segoe UI / Segoe UI Semibold** (disponível em qualquer Windows). Web: `Inter` → fallback `"Segoe UI", system-ui`; números com `font-variant-numeric: tabular-nums`.

| Papel | Power BI | Web | Cor |
|---|---|---|---|
| Eyebrow (kicker da página) | Segoe UI Semibold 8pt, CAIXA ALTA | 11px/600, `letter-spacing:.08em` | `teal` |
| Título da página | Segoe UI Semibold 18pt | 24px/650 | `ink` |
| Subtítulo da página | Segoe UI 9pt | 13px/400 | `muted` |
| Título do visual (insight) | Segoe UI Semibold 12pt | 15px/600 | `ink` |
| Subtítulo do visual | Segoe UI 9pt | 12px/400 | `muted` |
| Valor do KPI | Segoe UI Semibold 24pt | 28px/650 tabular | `ink` |
| Rótulo do KPI | Segoe UI 9pt | 12px/500 | `muted` |
| Delta do KPI | Segoe UI Semibold 9pt | 12px/600 | teal ▲ / coral ▼ / muted ● |
| Eixos | Segoe UI 9pt | 11px | categorias `muted`, valores `faint` |
| Rótulos de dados | Segoe UI 9pt | 11px | `ink-2` |
| Rodapé de fontes | Segoe UI 8pt | 11px | `faint` |

### 2.3 Formatação de números (pt-BR)

| Grandeza | Formato | Exemplo |
|---|---|---|
| Moeda grande | `R$ #,0,,.0 "mi"` | R$ 15,4 mi |
| Moeda média | `R$ #,0,.0 "mil"` | R$ 842,1 mil |
| Ticket | `R$ #,0.00` | R$ 154,10 |
| Contagem | `#,0` | 96.478 |
| Percentual | `0.0%` | 91,9% |
| Nota | `0.00 "★"` | 4,09★ |
| Dias | `0.0 "d"` | 12,5 d |
| Variação de % | `+0.0 "p.p."` | +1,2 p.p. |
| Delta KPI | `▲ 12,4% vs ano ant.` / `▼ 3,1% vs ano ant.` / `● estável` | — |

Regra do delta: teal quando a variação é **boa para o negócio**, coral quando é **ruim**. Métricas "quanto menor melhor" (prazo, atraso, % atraso, % anomalias) invertem a cor, não a seta.

### 2.4 Espaçamento e grade (canvas 1280 × 720)

- Margem externa: **24 px** (conteúdo de x=24 a x=1256, y=16 a y=684).
- Gutter entre cartões: **16 px**.
- Raio dos cartões: **8 px**; slicers **6 px**. Borda 1px `hairline`. Sem sombra.
- Padding interno dos visuais: 12–14 px (Power BI: padding do container).
- Faixas verticais fixas (todas as páginas):

| Faixa | y | altura | conteúdo |
|---|---|---|---|
| Cabeçalho | 16 | 60 | eyebrow + título + subtítulo (x=24, w=720) e 3 slicers à direita |
| Régua | 84 | 1 | `basicShape` linha `hairline`, x=24, w=1232 |
| KPIs | 96 | 96 | 6 cartões de w=192 (ou 4 de w=296) |
| Conteúdo | 208 | 476 | visuais (termina em y=684) |
| Rodapé | 694 | 18 | fontes + data de coleta das APIs (x=24, w=1232) |

**Colunas de KPI** (6): x = 24, 232, 440, 648, 856, 1064 — w=192, h=96.
**Colunas de KPI** (4, se preferir): x = 24, 336, 648, 960 — w=296, h=96.

**Slicers do cabeçalho** (todas as páginas, sincronizados por `syncGroup`): w=150, h=52, y=20, modo Dropdown:

| Nome | x | Campo |
|---|---|---|
| `filtro_ano` | 782 | `dim_calendario[ano]` |
| `filtro_regiao` | 944 | `dim_geo_uf[regiao]` |
| `filtro_categoria` | 1106 | `dim_categoria[categoria_pt]` |

(Página 4 pode omitir slicers — auditoria é sobre a base inteira.)

### 2.5 Anatomia do cartão KPI

```
┌──────────────────────────────┐  ← surface #FFF, borda 1px #E2E8F0, raio 8
│ GMV REAL (IPCA)              │  ← título do container: rótulo 9pt Semibold muted
│ ▲ 21,4% vs 2017              │  ← subtítulo do container: delta 9pt Semibold (fx)
│ R$ 15,9 mi                   │  ← valor (callout) 24pt Semibold ink
└──────────────────────────────┘
```

**Um único visual `card` por KPI** (sem sobreposição de caixas — o teste de layout do `verifier` exige zero overlap):
- `visualContainerObjects.title.text` = rótulo estático (ex.: "GMV real (IPCA)").
- `visualContainerObjects.subTitle.text` = **expressão** ligada a uma medida de texto (`[Delta GMV Real Texto]` → `"▲ 21,4% vs 2017"`); `subTitle.fontColor` = expressão ligada a uma medida de cor (`[Delta GMV Real Cor]` → `"#0D9488"` / `"#DC2626"` / `"#64748B"`). Se o fx de cor der trabalho, deixe `muted` — a seta já comunica.
- `categoryLabels` desligado (já está no tema). Sem delta? Use o subtítulo para contexto curto ("pedidos entregues", "média 1–5").

Cor semântica do delta: teal (bom), coral (ruim), muted (estável / sem comparação).

### 2.6 Rodapé (todas as páginas)

`textbox` x=24 y=694 w=1232 h=18, 8pt `faint`:

> Fontes: Olist Brazilian E-Commerce Public Dataset (Kaggle, CC BY-NC-SA 4.0) · Banco Central do Brasil — SGS 433 (IPCA), 432 (Selic), 1 (PTAX) · IBGE — Localidades e População · Valores reais a preços de ‹mês-base› (IPCA) · APIs coletadas em ‹data›

---

## 3. Páginas

Convenção das tabelas: `nome_visual` (use como `name` no PBIR) · tipo PBIR · x · y · w · h · conteúdo. Nomes de medidas são sugestões — `bi-eng` é dono do DAX.

### Cabeçalho comum (`titulo`, textbox, x=24 y=16 w=720 h=60)

Três parágrafos: eyebrow (8pt Semibold teal, caixa alta) · título (18pt Semibold ink) · subtítulo (9pt muted).

---

### Página 1 — Visão Executiva & Macro (`visao_executiva`)

- Eyebrow: `01 · VISÃO EXECUTIVA & MACRO`
- Título: **Crescimento real, não só inflação**
- Subtítulo: *GMV nominal vs. deflacionado pelo IPCA (BCB SGS 433), com Selic como pano de fundo do crédito ao consumo.*

| nome_visual | tipo | x | y | w | h | conteúdo |
|---|---|---|---|---|---|---|
| `kpi_gmv_nominal` | card | 24 | 96 | 192 | 96 | `[GMV Nominal]` · acento navy · delta YoY |
| `kpi_gmv_real` | card | 232 | 96 | 192 | 96 | `[GMV Real IPCA]` · acento teal · delta YoY |
| `kpi_pedidos` | card | 440 | 96 | 192 | 96 | `[Pedidos]` · acento navy · delta YoY |
| `kpi_ticket_real` | card | 648 | 96 | 192 | 96 | `[Ticket Médio Real]` · acento teal |
| `kpi_nota` | card | 856 | 96 | 192 | 96 | `[Nota Média]` (0.00★) · acento teal |
| `kpi_no_prazo` | card | 1064 | 96 | 192 | 96 | `[% Entregas no Prazo]` · acento teal (coral se < 90%) |
| `tendencia_gmv` | lineChart | 24 | 208 | 816 | 316 | Eixo: `dim_calendario[ano_mes]`; séries `[GMV Nominal]` navy 2px e `[GMV Real IPCA]` teal 2.5px; legenda TopLeft; sem marcadores; rótulo só no último ponto |
| `macro_ipca_selic` | lineChart | 856 | 208 | 400 | 316 | `[IPCA 12m %]` amber 2px e `[Selic Média %]` `faint` 2px tracejada; mesmo eixo mensal |
| `gmv_regiao` | clusteredBarChart | 24 | 540 | 400 | 144 | `[GMV Real IPCA]` por `dim_geo_uf[regiao]`, ordenado desc, navy, rótulos de dados ligados |
| `ticket_trimestre` | clusteredColumnChart | 440 | 540 | 400 | 144 | `[Ticket Médio Real]` por trimestre, teal |
| `leitura_executiva` | textbox | 856 | 540 | 400 | 144 | Cartão branco com borda (ligar background/border no textbox) — 3 bullets de leitura, ver abaixo |
| `rodape` | textbox | 24 | 694 | 1232 | 18 | fontes |

Títulos dos visuais (insight-first):
- `tendencia_gmv`: **"GMV real cresce ‹x›% em 2018 vs 2017 — inflação explica só ‹y› p.p."** · sub: *R$ a preços de ‹mês-base›. Navy = nominal, teal = real.*
- `macro_ipca_selic`: **"Juros em queda de ‹14,25%› para ‹6,50%› no período"** · sub: *Selic meta média mensal e IPCA acumulado 12m (BCB SGS 432/433).*
- `gmv_regiao`: **"Sudeste concentra ‹x›% do GMV"**
- `ticket_trimestre`: **"Ticket médio real ‹estável/cai› ao longo do período"**
- `leitura_executiva` (título 12pt Semibold "Leitura executiva", corpo 9pt ink-2):
  - ▲ Volume: ‹…›
  - ● Macro: ‹…›
  - ▼ Risco: atraso é o maior detrator de nota (ver pág. 2).

---

### Página 2 — Logística, SLA & Impacto no Cliente (`logistica_sla`)

- Eyebrow: `02 · LOGÍSTICA, SLA & CLIENTE`
- Título: **Atraso é o que mais destrói a satisfação**
- Subtítulo: *Pedidos entregues. Atraso = entrega real após a data estimada informada ao cliente.*

| nome_visual | tipo | x | y | w | h | conteúdo |
|---|---|---|---|---|---|---|
| `kpi_prazo_medio` | card | 24 | 96 | 192 | 96 | `[Prazo Médio Entrega (d)]` · acento navy |
| `kpi_no_prazo` | card | 232 | 96 | 192 | 96 | `[% Entregas no Prazo]` · acento teal |
| `kpi_atraso_medio` | card | 440 | 96 | 192 | 96 | `[Atraso Médio quando Atrasa (d)]` · acento coral |
| `kpi_nota_no_prazo` | card | 648 | 96 | 192 | 96 | `[Nota Média no Prazo]` · acento teal |
| `kpi_nota_atrasado` | card | 856 | 96 | 192 | 96 | `[Nota Média Atrasado]` · acento coral |
| `kpi_frete_pct` | card | 1064 | 96 | 192 | 96 | `[Frete % do GMV]` · acento amber |
| `nota_por_atraso` | clusteredColumnChart | 24 | 208 | 600 | 316 | **Visual-herói.** Eixo: faixa de atraso (5 faixas, ordem fixa por coluna de ordenação); valor `[Nota Média]`; cores = escala ordinal §2.1 (data colors por ponto); rótulos de dados `0.0★` ligados, 10pt Semibold; eixo Y 1–5 fixo |
| `prazo_regiao` | clusteredBarChart | 24 | 540 | 600 | 144 | `[Prazo Médio Entrega (d)]` por região, desc, navy; rótulos ligados |
| `tabela_uf` | tableEx | 640 | 208 | 616 | 476 | Colunas: UF · Região · Pedidos · GMV/100 mil hab. (barra de dados teal) · Prazo médio (d) · % no prazo (cor de fonte: ≥ 92% teal, < 85% coral) · Nota. Ordenar por GMV/100 mil hab. desc. Linha 9pt, rowPadding 4 → 27 UFs cabem sem rolagem |
| `rodape` | textbox | 24 | 694 | 1232 | 18 | fontes + "População: IBGE" |

Títulos:
- `nota_por_atraso`: **"Com 15+ dias de atraso, a nota despenca de ‹4,3›★ para ‹1,7›★"** · sub: *Nota média da avaliação (1–5) por faixa de atraso na entrega.*
- `prazo_regiao`: **"Norte e Nordeste esperam ‹x›× mais que o Sudeste"**
- `tabela_uf`: **"Onde o e-commerce penetra mais — e onde entrega pior"** · sub: *GMV por 100 mil habitantes (IBGE) e SLA por UF do cliente.*

---

### Página 3 — Comercial, Categorias, Pagamentos & Coorte (`comercial`)

- Eyebrow: `03 · COMERCIAL & CLIENTES`
- Título: **Poucas categorias e poucos vendedores carregam a receita**
- Subtítulo: *Pareto de categorias, mix de pagamento, parcelamento, recompra por coorte e concentração de vendedores.*

| nome_visual | tipo | x | y | w | h | conteúdo |
|---|---|---|---|---|---|---|
| `kpi_ticket` | card | 24 | 96 | 192 | 96 | `[Ticket Médio Real]` · navy |
| `kpi_itens_pedido` | card | 232 | 96 | 192 | 96 | `[Itens por Pedido]` · navy |
| `kpi_pct_cartao` | card | 440 | 96 | 192 | 96 | `[% Pedidos Cartão]` · navy |
| `kpi_parcelas` | card | 648 | 96 | 192 | 96 | `[Parcelas Médias (Cartão)]` · amber |
| `kpi_recompra` | card | 856 | 96 | 192 | 96 | `[% Clientes Recompra]` · teal |
| `kpi_top_vendedores` | card | 1064 | 96 | 192 | 96 | `[% GMV Top 10% Vendedores]` · coral (risco de concentração) |
| `pareto_categorias` | lineClusteredColumnComboChart | 24 | 208 | 744 | 260 | Colunas `[GMV Real IPCA]` por categoria (top 15, desc) navy; linha `[% Acumulado GMV]` amber em eixo secundário 0–100%; linha de referência 80% `faint` tracejada; rótulos de categoria rotacionados no máximo 45° |
| `coorte_recompra` | pivotTable | 24 | 484 | 744 | 200 | Linhas: mês da 1ª compra (coorte); colunas: meses desde a 1ª compra (0–6… quantos couberem); valor `[% Retenção Coorte]`; **escala de cor de fundo** branco → teal (`#FFFFFF` → `#0D9488`), texto 8pt |
| `mix_pagamento` | clusteredBarChart | 784 | 208 | 472 | 148 | `[% GMV]` por tipo de pagamento, desc, navy; rótulos 0.0% |
| `parcelas` | clusteredColumnChart | 784 | 372 | 472 | 148 | `[Pedidos]` por nº de parcelas (1…10+), navy-300 com 1x destacada navy |
| `concentracao_vendedores` | clusteredColumnChart | 784 | 536 | 472 | 148 | `[% GMV]` por decil de vendedor (D1 = top 10%), D1 coral, demais `navy-300` |
| `rodape` | textbox | 24 | 694 | 1232 | 18 | fontes |

Títulos:
- `pareto_categorias`: **"‹n› categorias somam 80% do GMV"**
- `coorte_recompra`: **"Recompra é rara: ‹x›% voltam em até 6 meses"** · sub: *% de clientes únicos da coorte que compram de novo no mês M+n.*
- `mix_pagamento`: **"Cartão domina: ‹x›% do GMV"**
- `parcelas`: **"‹x›% dos pedidos no cartão são parcelados"**
- `concentracao_vendedores`: **"Top 10% dos vendedores = ‹x›% do GMV"**

---

### Página 4 — Qualidade, Linhagem & Auditoria (`qualidade`)

- Eyebrow: `04 · QUALIDADE & LINHAGEM`
- Título: **Cada número é rastreável até a fonte**
- Subtítulo: *Anomalias reais encontradas na base Olist, tratamento aplicado e conferência contra o gabarito SQL.*

| nome_visual | tipo | x | y | w | h | conteúdo |
|---|---|---|---|---|---|---|
| `kpi_pedidos_brutos` | card | 24 | 96 | 192 | 96 | `[Pedidos Brutos]` · faint |
| `kpi_pedidos_validos` | card | 232 | 96 | 192 | 96 | `[Pedidos Entregues Analisados]` · teal |
| `kpi_pct_excluidos` | card | 440 | 96 | 192 | 96 | `[% Excluídos da Análise]` · amber |
| `kpi_anomalias` | card | 648 | 96 | 192 | 96 | `[Anomalias Detectadas]` · amber |
| `kpi_reviews_dup` | card | 856 | 96 | 192 | 96 | `[Reviews Duplicadas]` · amber |
| `kpi_gabarito` | card | 1064 | 96 | 192 | 96 | **Selo de verificação**: valor `✓ ‹6/6›` teal, rótulo "consultas SQL conferem com o DAX"; fundo `teal-100` (`#CCFBF1`), borda teal |
| `tabela_auditoria` | tableEx | 24 | 208 | 600 | 476 | `qualidade_auditoria`: Regra · Tabela · Linhas afetadas · % da base · Tratamento. Linhas afetadas com barra de dados amber |
| `anomalias_tipo` | clusteredBarChart | 640 | 208 | 616 | 230 | Linhas afetadas por tipo de anomalia, desc, amber |
| `linhagem_fontes` | tableEx | 640 | 454 | 616 | 230 | Fonte · Endpoint/arquivo · Registros · Coletado em (timestamp) · Licença |
| `rodape` | textbox | 24 | 694 | 1232 | 18 | fontes |

Títulos:
- `tabela_auditoria`: **"‹n› regras de qualidade aplicadas — nada é descartado em silêncio"**
- `anomalias_tipo`: **"Pedidos cancelados/não entregues são a maior exclusão"**
- `linhagem_fontes`: **"3 fontes públicas, sem chave de API, coleta reprodutível"**

---

## 4. Regras de acabamento (checklist para `bi-eng`)

- [ ] Page background `#F8FAFC` (vem do tema); nenhum visual com fundo cinza.
- [ ] Todo visual de dados: título (insight) + subtítulo ligados; borda hairline; raio 8; **sem** sombra.
- [ ] Eixo X sem gridlines; eixo Y com gridlines `#EEF2F6`; títulos de eixo desligados.
- [ ] Séries mensais: sem marcadores, linhas 2–2,5 px, sem rótulos em todos os pontos.
- [ ] Barras horizontais sempre ordenadas desc; nunca pizza/rosca; nunca 3D.
- [ ] Vermelho aparece **apenas** em atraso/nota baixa/concentração de risco/deltas negativos.
- [ ] Nenhum visual encosta em outro: verifique gutters de 16 px e margem de 24 px.
- [ ] Textos não truncados em 1280×720 (testar títulos longos; abreviar se precisar, mantendo o número).
- [ ] Ordem de tabulação: cabeçalho → slicers → KPIs (esq→dir) → herói → apoio.

---

## 5. Painel web (`docs/index.html`)

Espelha 1-para-1 as 4 páginas acima com os mesmos tokens (`docs/styles.css` → variáveis CSS com os hex desta seção), alimentado por `docs/dados/resumo.json`.

- Barra superior: marca + título, abas das 4 páginas, alternador **PT / EN**.
- Barra de filtros: Ano · Região · Categoria (quando o dado agregado permitir).
- Grade CSS de 12 colunas, largura máx. 1280 px; ≤1024 px → 2 colunas; ≤640 px → 1 coluna.
- Gráficos: SVG/HTML nativos sem dependências externas (100% offline-safe, nítidos em qualquer DPI, tooltips em pt-BR/en-US), incluindo cartograma de UFs do Brasil + tabela ranqueada e matriz de coorte.
- Rodapé com fontes e data de coleta, idêntico ao Power BI.
