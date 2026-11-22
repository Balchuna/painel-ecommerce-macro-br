# Especificação visual do projeto · Painel E-Commerce & Macroeconomia Brasil

Este documento registra apenas as decisões específicas deste projeto: narrativa das 4 páginas, mapa de visuais na grade de 1280×720, mapeamento das medidas DAX de títulos dinâmicos (`fx`) e regras de cor por série.

O sistema visual completo (paleta, tipografia, escala de espaços, raios, contraste mínimo e proibições) não é repetido aqui: ele vive em fonte única em [`DESIGN.md`](../DESIGN.md), [`marca/REGRAS.md`](../marca/REGRAS.md) e [`marca/tokens.json`](../marca/tokens.json).

---

## 1. Configuração da marca neste projeto

- **Acento escolhido:** `azul` (`python marca/gerar.py --acento azul --dados docs/dados/resumo.json --saida-dados docs/dados`).
- **Tema do Power BI:** [`marca/powerbi/tema-azul-claro.json`](../marca/powerbi/tema-azul-claro.json), copiado integralmente para [`tema/tema.json`](../tema/tema.json) e embutido em `powerbi/` por [`scripts/montar_pbip.py`](../scripts/montar_pbip.py).
- **Variáveis CSS do painel web:** [`marca/tokens.css`](../marca/tokens.css), copiado integralmente para [`docs/marca/tokens.css`](marca/tokens.css) para servir sem 404 no GitHub Pages (claro e escuro).
- **Tipografia, espaços e raios:** herdados diretamente de [`marca/tokens.json`](../marca/tokens.json) (`Segoe UI` 400 e 600, caixa de frase em todo texto, números tabulares no formato brasileiro, cartões em `surface` com borda de 1 px em `border`, raio `cartao`, sem sombra).

### Semântica de cor específica do domínio

| Papel no painel | Token em `marca/tokens.json` | Onde entra |
|---|---|---|
| Série principal e entidade líder | `cores.azul.claro.mark` | GMV real (IPCA), Selic meta, 2018 nos trimestres, líder regional, UF líder, categoria líder, decil D1, pedidos parcelados (2x–10x+) |
| Comparação, base histórica e demais entidades | `tema.claro.mark_muted` | GMV nominal, período base 2017, regiões/UFs/categorias/decis fora do destaque, compras à vista (1x) |
| Segunda série categórica | `cores.terracota.claro.mark` | IPCA 12m no gráfico macro (ordem oficial de `acentos.azul`), faixa intermediária de atraso (4–7 d) |
| Variação favorável / SLA alto | `tema.claro.positivo` | Deltas positivos com sinal (`+`) de GMV e pedidos, SLA ≥ 92% na tabela de UFs |
| Variação desfavorável / degradação crítica | `tema.claro.negativo` | Queda de nota por atraso, SLA < 85% na tabela de UFs, faixas severas de atraso (8–14 d e 15+ d) |
| Mapa de calor da retenção por coorte | Lavagens graduais de `azul` sobre `surface` | Matriz `coorte_recompra` com contraste acima de 10:1 para texto em `ink` |
| Texto, valores de KPI e rótulos | `ink`, `ink_2`, `ink_3` | Valores de KPI sempre em `ink`; rótulos e subtítulos em `ink_2`; eixos e rodapé em `ink_3` |

---

## 2. Grade 1280×720 e anatomia das faixas

Todas as 4 páginas seguem sem exceção a grade normativa de `marca/tokens.json > grade_powerbi`: margem externa de 24 px, calha de 16 px e 12 colunas de 88 px (`x(c) = 24 + (c − 1) × 104`, `w(k) = k × 104 − 16`).

| Faixa | `y` | `h` | Conteúdo padrão |
|---|---:|---:|---|
| `cabecalho` | 16 | 44 | Título da página em `largeTitle` + subtítulo em `label` (colunas 1–6 nas páginas 1–3; colunas 1–12 na página 4) e 3 filtros sincronizados em lista suspensa (`filtro_ano`, `filtro_regiao`, `filtro_categoria`, colunas 7–8, 9–10 e 11–12) |
| `kpis` | 72 | 80 | 4 cartões de KPI com 3 colunas cada (296×80, `x = 24, 336, 648, 960`), valor em `callout` (`ink`), rótulo em caixa de frase e subtítulo dinâmico por medida DAX (`fx`) |
| `linha_a` | 168 | 272 | Visuais principais da narrativa (leitura em 30 s): 8 + 4 colunas nas páginas 1 e 3; 6 + 6 colunas nas páginas 2 e 4 |
| `linha_b` | 456 | 224 | Detalhamento e tabelas (leitura em 300 s): 6 + 6 colunas nas páginas 1, 2 e 4; 4 + 4 + 4 colunas na página 3 |
| `rodape` | 688 | 16 | Fontes, deflator e data de coleta à esquerda (`rodape_fontes`, colunas 1–9) e assinatura `Rafael Balchuna · Power BI · SQL · Python` à direita (`rodape_assinatura`, colunas 10–12) |

### Eliminação de eixos duplos

Seguindo `marca/REGRAS.md`, nenhum visual do relatório usa eixo Y secundário. O ranking de categorias da página 3 (`pareto_categorias`), que anteriormente combinava colunas de GMV e linha acumulada em dois eixos, foi convertido para gráfico de barras horizontais de eixo único (top 8 categorias por GMV real de itens, com nomes completos sem rotação), preservando `[% GMV Categorias]` e `[% Acumulado GMV Categorias]` na dica interativa e o número exato de categorias que somam 80% do GMV no título dinâmico `[Título Pareto Categorias]`.

---

## 3. Páginas, visuais e mapeamento DAX `fx`

Todos os títulos de gráficos e tabelas são vinculados via expressão `Measure` em `visualContainerObjects.title[0].properties.text` às medidas da pasta `07. Títulos Dinâmicos (fx)` de [`dax/medidas.dax`](../dax/medidas.dax). Quando qualquer filtro (ano, região, categoria ou destaque cruzado) é aplicado, os títulos e os subtítulos de KPI se recalculam no contexto ativo.

### Página 1 · Visão executiva (`visao_executiva`)

- **Título da página:** Visão executiva e macroeconomia
- **Subtítulo:** GMV real a preços de out/2018 (IPCA BCB SGS 433) · comparação jan–ago/2018 vs. 2017
- **Pergunta respondida:** Quanto do crescimento do e-commerce foi expansão real de volume e não inflação, diante do ciclo de queda da Selic?

| Visual | Tipo PBIR | Colunas / faixa (`x, y, w, h`) | Medida(s) principal(is) | Título / subtítulo dinâmico (`fx`) | Cor condicional (`fx`) |
|---|---|---|---|---|---|
| `kpi_gmv_real` | `card` | 1–3 · `kpis` (24, 72, 296, 80) | `[GMV Real IPCA]` | Subtítulo: `[Delta GMV Real Texto]` | `[Cor Delta GMV Real]` |
| `kpi_pedidos` | `card` | 4–6 · `kpis` (336, 72, 296, 80) | `[Pedidos Entregues]` | Subtítulo: `[Delta Pedidos Texto]` | `[Cor Delta Pedidos]` |
| `kpi_ticket_real` | `card` | 7–9 · `kpis` (648, 72, 296, 80) | `[Ticket Médio Real]` | Subtítulo: `[Subtítulo Ticket Real]` | Neutra (`ink_2`) |
| `kpi_no_prazo` | `card` | 10–12 · `kpis` (960, 72, 296, 80) | `[% Entregas no Prazo]` | Subtítulo: `[Subtítulo SLA Nota]` | Neutra (`ink_2`) |
| `tendencia_gmv` | `lineChart` | 1–8 · `linha_a` (24, 168, 816, 272) | `[GMV Real IPCA]`, `[GMV Nominal]` | `[Título Tendência GMV]` | `azul` (real) e `mark_muted` (nominal) |
| `macro_ipca_selic` | `lineChart` | 9–12 · `linha_a` (856, 168, 400, 272) | `[Selic Média %]`, `[IPCA 12m %]` | `[Título Macro IPCA Selic]` | `azul` (Selic) e `terracota` (IPCA 12m) |
| `gmv_regiao` | `clusteredBarChart` | 1–6 · `linha_b` (24, 456, 608, 224) | `[GMV Real IPCA]` por `regiao` | `[Título GMV Região]` | `[Cor Região Destaque]` |
| `ticket_trimestre` | `clusteredColumnChart` | 7–12 · `linha_b` (648, 456, 608, 224) | `[Ticket Médio Real]` por `trimestre_curto` | `[Título Ticket Trimestre]` | `[Cor Trimestre Período]` (2017 em cinza) |

### Página 2 · Logística e SLA (`logistica_sla`)

- **Título da página:** Logística, SLA e avaliação do cliente
- **Subtítulo:** Pedidos entregues com data real válida (96.470) · atraso = entrega após a data estimada
- **Pergunta respondida:** Quanto o atraso logístico penaliza a nota do cliente, onde o e-commerce penetra mais per capita (IBGE) e onde a entrega demora mais?

| Visual | Tipo PBIR | Colunas / faixa (`x, y, w, h`) | Medida(s) principal(is) | Título / subtítulo dinâmico (`fx`) | Cor condicional (`fx`) |
|---|---|---|---|---|---|
| `kpi_prazo_medio` | `card` | 1–3 · `kpis` (24, 72, 296, 80) | `[Prazo Médio Entrega (d)]` | Subtítulo: `[Subtítulo Prazo Médio]` | Neutra (`ink_2`) |
| `kpi_no_prazo` | `card` | 4–6 · `kpis` (336, 72, 296, 80) | `[% Entregas no Prazo]` | Subtítulo: `[Subtítulo SLA Contagem]` | Neutra (`ink_2`) |
| `kpi_nota_no_prazo` | `card` | 7–9 · `kpis` (648, 72, 296, 80) | `[Nota Média no Prazo]` | Subtítulo estático de escala | Neutra (`ink_2`) |
| `kpi_nota_atrasado` | `card` | 10–12 · `kpis` (960, 72, 296, 80) | `[Nota Média Atrasado]` | Subtítulo: `[Subtítulo Nota Atraso]` | `[Cor Impacto Atraso]` |
| `nota_por_atraso` | `clusteredColumnChart` | 1–6 · `linha_a` (24, 168, 608, 272) | `[Nota Média]` por `faixa_atraso` (ordens 1–5) | `[Título Nota Atraso]` | `[Cor Faixa Atraso]` |
| `penetracao_uf` | `clusteredBarChart` | 7–12 · `linha_a` (648, 168, 608, 272) | `[GMV Real / 100 mil hab.]` (top 8 UFs) | `[Título Penetração UF]` | `[Cor UF Destaque]` |
| `prazo_regiao` | `clusteredBarChart` | 1–6 · `linha_b` (24, 456, 608, 224) | `[Prazo Médio Entrega (d)]` por `regiao` | `[Título Prazo Região]` | `[Cor Prazo Região Destaque]` |
| `tabela_uf` | `tableEx` | 7–12 · `linha_b` (648, 456, 608, 224) | UF, Região, Pedidos, GMV/100k, Prazo, % no prazo, Nota | `[Título Tabela UF]` | `[Cor SLA UF]` na coluna `% no prazo` |

### Página 3 · Comercial e clientes (`comercial`)

- **Título da página:** Comercial, categorias e clientes
- **Subtítulo:** Concentração de categorias e vendedores no grão de item · pagamentos, parcelas e retenção por coorte
- **Pergunta respondida:** Qual o grau de concentração da receita em categorias e vendedores, como o cliente paga e qual a retenção recorrente?

| Visual | Tipo PBIR | Colunas / faixa (`x, y, w, h`) | Medida(s) principal(is) | Título / subtítulo dinâmico (`fx`) | Cor condicional (`fx`) |
|---|---|---|---|---|---|
| `kpi_ticket` | `card` | 1–3 · `kpis` (24, 72, 296, 80) | `[Ticket Médio Real]` | Subtítulo: `[Subtítulo Ticket Itens]` | Neutra (`ink_2`) |
| `kpi_pct_cartao` | `card` | 4–6 · `kpis` (336, 72, 296, 80) | `[% Pedidos Cartão]` | Subtítulo: `[Subtítulo Cartão Parcelas]` | Neutra (`ink_2`) |
| `kpi_recompra` | `card` | 7–9 · `kpis` (648, 72, 296, 80) | `[% Clientes Recompra]` | Subtítulo: `[Subtítulo Recompra]` | Neutra (`ink_2`) |
| `kpi_top_vendedores` | `card` | 10–12 · `kpis` (960, 72, 296, 80) | `[% GMV Top 10% Vendedores]` | Subtítulo: `[Subtítulo Top Vendedores]` | Neutra (`ink_2`) |
| `pareto_categorias` | `clusteredBarChart` | 1–8 · `linha_a` (24, 168, 816, 272) | `[GMV Itens Real IPCA]` (top 8; `% GMV` e `% Acumulado` na dica) | `[Título Pareto Categorias]` | `[Cor Categoria Destaque]` |
| `concentracao_vendedores` | `clusteredColumnChart` | 9–12 · `linha_a` (856, 168, 400, 272) | `[% GMV Vendedores]` por decil D1–D10 | `[Título Concentração Vendedores]` | `[Cor Decil Vendedores]` |
| `mix_pagamento` | `clusteredBarChart` | 1–4 · `linha_b` (24, 456, 400, 224) | `[% GMV Pagamento]` (4 meios principais) | `[Título Mix Pagamento]` | `[Cor Pagamento Destaque]` |
| `parcelas` | `clusteredColumnChart` | 5–8 · `linha_b` (440, 456, 400, 224) | `[Pedidos Cartão]` por `faixa_parcelas` (1x–10x+) | `[Título Parcelas]` | `[Cor Parcelas]` (1x em cinza) |
| `coorte_recompra` | `pivotTable` | 9–12 · `linha_b` (856, 456, 400, 224) | `[% Retenção Coorte]` (`coorte_mes` × `M+1..M+6`) | `[Título Coorte Recompra]` | `[Cor Retenção Coorte]` |

### Página 4 · Qualidade e linhagem (`qualidade`)

- **Título da página:** Qualidade de dados e linhagem
- **Subtítulo:** Anomalias reais encontradas na base Olist (99.441 pedidos brutos), tratamento determinístico e conferência SQL
- **Pergunta respondida:** Quais anomalias reais existem na base pública, como cada uma foi tratada sem descarte silencioso e qual a rastreabilidade dos arquivos?
- **Filtros:** omitidos no cabeçalho porque a auditoria e a linhagem descrevem a base completa.

| Visual | Tipo PBIR | Colunas / faixa (`x, y, w, h`) | Medida(s) principal(is) | Título / subtítulo dinâmico (`fx`) | Cor condicional (`fx`) |
|---|---|---|---|---|---|
| `kpi_pedidos_brutos` | `card` | 1–3 · `kpis` (24, 72, 296, 80) | `[Pedidos Brutos]` | Subtítulo: `[Subtítulo Pedidos Brutos]` | Neutra (`ink_2`) |
| `kpi_pct_excluidos` | `card` | 4–6 · `kpis` (336, 72, 296, 80) | `[% Excluídos da Análise]` | Subtítulo: `[Subtítulo Excluídos]` | Neutra (`ink_2`) |
| `kpi_anomalias` | `card` | 7–9 · `kpis` (648, 72, 296, 80) | `[Anomalias Detectadas]` | Subtítulo: `[Subtítulo Anomalias]` | Neutra (`ink_2`) |
| `kpi_gabarito` | `card` | 10–12 · `kpis` (960, 72, 296, 80) | `[Selo Gabarito SQL]` (`6/6`) | Subtítulo estático de conferência | Neutra (`ink_2`) |
| `anomalias_tipo` | `clusteredBarChart` | 1–6 · `linha_a` (24, 168, 608, 272) | `[Anomalias Detectadas]` (top 7 regras) | `[Título Anomalias Tipo]` | `[Cor Anomalia Destaque]` |
| `tratamento_anomalias` | `clusteredBarChart` | 7–12 · `linha_a` (648, 168, 608, 272) | `[Anomalias Detectadas]` por `tipo_curto` | `[Título Tratamento Anomalias]` | `[Cor Tratamento Destaque]` |
| `tabela_auditoria` | `tableEx` | 1–6 · `linha_b` (24, 456, 608, 224) | Regra, Origem, Linhas, % base, Tipo | `[Título Tabela Auditoria]` | Tema padrão |
| `linhagem_fontes` | `tableEx` | 7–12 · `linha_b` (648, 456, 608, 224) | Fonte, Arquivo, Registros, Coletado, Licença | `[Título Linhagem Fontes]` | Tema padrão |

---

## 4. Alinhamento com o painel web (`docs/`)

O painel web em [`docs/index.html`](index.html) espelha as mesmas 4 páginas, os mesmos números reconciliados do gabarito SQL (via `docs/dados/resumo.js` gerado por `marca/gerar.py`) e os mesmos tokens de [`docs/marca/tokens.css`](marca/tokens.css), com alternância entre tema claro e tema escuro, idioma PT/EN, destaque cruzado por região e adaptação responsiva abaixo de 1328 px até celular (390 px).
