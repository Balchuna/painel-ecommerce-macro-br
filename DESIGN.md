---
name: Padrão BI
description: "A página padrão do Power BI, bem-feita, em cinco mídias: Power BI, painel web, PDF, slides e capa."
colors:
  canvas: "#F4F5F7"
  outspace: "#ECEEF1"
  surface: "#FFFFFF"
  surface-2: "#F8F9FA"
  border: "#E1E4E8"
  border-strong: "#CDD2D8"
  grid: "#EBEDF0"
  axis: "#C4C9D0"
  mark-muted: "#C9CED5"
  ink: "#1A1D21"
  ink-2: "#4A515A"
  ink-3: "#5C636D"
  positivo: "#1A7F37"
  negativo: "#C42B3C"
  alerta: "#8F5600"
  neutro-div: "#E6E8EB"
  azul: "#2A6FD6"
  azul-ink: "#1D5BB8"
  petroleo: "#13917F"
  petroleo-ink: "#0B6F61"
  terracota: "#D2602C"
  terracota-ink: "#A8471C"
  amora: "#B5427F"
  amora-ink: "#973366"
  ocre: "#C98A00"
  ocre-ink: "#8F5F00"
  canvas-escuro: "#0F1216"
  outspace-escuro: "#0B0D10"
  surface-escuro: "#171B20"
  surface-2-escuro: "#1D2228"
  border-escuro: "#2A3038"
  border-strong-escuro: "#3A414A"
  grid-escuro: "#242A31"
  axis-escuro: "#3D444D"
  mark-muted-escuro: "#465059"
  ink-escuro: "#E8EBEE"
  ink-2-escuro: "#B4BBC4"
  ink-3-escuro: "#949CA6"
  positivo-escuro: "#4CC26B"
  negativo-escuro: "#F27782"
  alerta-escuro: "#E0A645"
  neutro-div-escuro: "#30363E"
  azul-escuro: "#4A8BEA"
  azul-ink-escuro: "#7FAEF2"
  petroleo-escuro: "#22A497"
  petroleo-ink-escuro: "#4CC3B5"
  terracota-escuro: "#E0703F"
  terracota-ink-escuro: "#F0956A"
  amora-escuro: "#D2649F"
  amora-ink-escuro: "#E58CBB"
  ocre-escuro: "#B07F10"
  ocre-ink-escuro: "#E3B24A"
typography:
  pagina:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.2
  kpi:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
  titulo:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.3
  corpo:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  rotulo:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.35
  nota:
    fontFamily: "Segoe UI, -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.35
rounded:
  cartao: "8px"
  controle: "6px"
  barra: "4px"
spacing:
  e-1: "4px"
  e-2: "8px"
  e-3: "12px"
  e-4: "16px"
  e-5: "24px"
  e-6: "32px"
  e-7: "48px"
components:
  cartao:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.cartao}"
    padding: "12px 16px"
  cartao-kpi:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.kpi}"
    rounded: "{rounded.cartao}"
    padding: "12px 16px"
    height: "80px"
  filtro:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-2}"
    typography: "{typography.rotulo}"
    rounded: "{rounded.controle}"
    padding: "2px"
  filtro-botao:
    textColor: "{colors.ink-2}"
    typography: "{typography.rotulo}"
    rounded: "{rounded.barra}"
    padding: "0 10px"
    height: "28px"
  filtro-botao-hover:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
  filtro-botao-ativo:
    backgroundColor: "color-mix(in srgb, {colors.azul} 12%, {colors.surface})"
    textColor: "{colors.azul-ink}"
  dica:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.rotulo}"
    rounded: "{rounded.controle}"
    padding: "8px 10px"
  tabela-total:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
    typography: "{typography.rotulo}"
  caixa-metodo:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.controle}"
    padding: "10px 12px"
---

# Design System: Padrão BI

Este arquivo explica o sistema e o porquê de cada decisão. O que fazer, passo a passo, e a lista "Antes de entregar" estão em `marca/REGRAS.md`. Os valores são normativos no bloco acima e, na fonte, em `marca/tokens.json`; o texto abaixo cita os tokens pelo nome e não repete valores.

## Overview

**Creative North Star: "A página padrão, bem-feita"**

O Padrão BI é a página corporativa do Power BI levada a sério: fundo cinza-frio, cartões brancos, uma linha de KPIs no topo, Segoe UI em tudo. A escolha é deliberada e sem ironia. Quem avalia um projeto de BI reconhece esse vocabulário em um segundo, e o que diferencia o trabalho é o acabamento: grade exata, números no formato brasileiro, títulos que dizem o achado, fonte e método sempre à vista. A régua é Stripe Dashboard na interface, Datawrapper no gráfico, Fluent 2 na linguagem nativa e os relatórios de exemplo do SQLBI e do Tabular Editor na página do Power BI.

A densidade é a de um painel de trabalho, não a de uma página de apresentação. A página responde em três tempos (3-30-300): a linha de KPIs em 3 s, o gráfico principal e o filtro em 30 s, a tabela e as dicas em 300 s. A cor quase não aparece: um acento por projeto pinta o dado em foco, e todo o resto fica em cinza e tinta. A assinatura é discreta, no rodapé.

O mesmo vocabulário atravessa cinco mídias: a página do Power BI de 1280×720, o painel web que a reproduz, o PDF técnico em A4, os slides do case e a capa de 1280×640. Tudo sai de um único `tokens.json`. Ficaram recusados de forma explícita o escuro-neon e o slate com azul-céu herdados do hub anterior.

**Key Characteristics:**
- Cartão branco de borda fina sobre canvas cinza-frio, sem sombra.
- Um acento por projeto; o que sai de foco vai para `mark-muted`.
- Segoe UI, dois pesos (400 e 600), caixa de frase em tudo.
- Título de gráfico é o achado, calculado dos dados, com subtítulo de unidade e período e linha de fonte embaixo.
- Variação sempre com seta desenhada e sinal, nunca só a cor.
- Tema escuro com valores próprios, validados, e não uma inversão.

## Colors

Neutros frios e quase sem matiz carregam a página; um único acento saturado pinta o dado.

### Primary
- **Acento do projeto** (`acento`, um entre `azul`, `petroleo`, `terracota` e `amora`): pinta a série principal, a barra ou região em destaque, o ponto final da linha e o trecho do período atual nos minigráficos. Cada projeto escolhe um e não repete o do projeto anterior; é isso que dá a cada projeto cor própria sem mudar o sistema.
- **Tinta do acento** (`acento-ink`, a variante `-ink` de cada matiz): a versão do acento com contraste de texto (4,5:1 ou mais). Serve a links, contorno de foco e texto do filtro ativo. Nunca pinta dado.
- **Lavagem do acento** (`acento-wash`, mistura de 12% do acento na `surface`): fundo do botão de filtro ativo e da linha de tabela em destaque.

### Secondary
- **Série categórica**: quando há mais de uma série, a ordem é a do acento escolhido em `acentos` (`serie-1` a `serie-5`), validada para daltonismo e visão normal entre vizinhos. A ordem não pula nem recicla matiz, e a cor segue a entidade: um filtro nunca repinta quem ficou.
- **Ocre** (`ocre`): só existe como quarta ou quinta série, com rótulo visível. Nunca é acento, porque no tema claro fica abaixo de 3:1 contra a superfície.

### Tertiary
- **Positivo e negativo** (`positivo`, `negativo`): só para variação boa ou ruim, sempre junto de seta desenhada e sinal.
- **Alerta** (`alerta`): estado intermediário; no Power BI é o `neutral` da formatação condicional.
- **Divergente**: negativo em `terracota`, positivo em `azul`, centro em `neutro-div`. É fixo e independe do acento do projeto.

### Neutral
- **Fora da página** (`outspace`): o fundo do navegador em volta da página, um passo mais escuro que o canvas.
- **Canvas** (`canvas`): o fundo da página do Power BI, da capa e do painel.
- **Superfície** (`surface`): o cartão, a dica e o fundo dos gráficos.
- **Superfície 2** (`surface-2`): hover discreto, linha de total da tabela, caixa de método e bloco de código no PDF.
- **Borda** (`border`) e **borda forte** (`border-strong`): o fio de 1 px do cartão e dos controles; a borda forte marca o cabeçalho da tabela, o sublinhado dos links de região e os divisores da linhagem nos slides.
- **Grade e eixo** (`grid`, `axis`): grade horizontal em fio claro; eixo e linha de base um tom acima.
- **Marca fora de foco** (`mark-muted`): o cinza do período base, das regiões não escolhidas e das demais séries nos pequenos múltiplos.
- **Tintas** (`ink`, `ink-2`, `ink-3`): `ink` para título, valor e rótulo forte; `ink-2` para subtítulo, rótulo de KPI e cabeçalho de tabela; `ink-3` para eixo, fonte, rodapé e assinatura.

### Named Rules
**A regra do acento único.** Cada projeto tem um acento e só ele pinta o dado em foco. Comparação, período base e entidades fora de foco ficam em `mark-muted`. Se a página parece colorida, há acento demais.

**A regra do cinza é o passado.** Em toda comparação no tempo, o período base fica em `mark-muted` e o atual no acento, na linha principal, nos minigráficos e na capa, e o subtítulo diz qual ano está em cinza ("2017 em cinza").

**A regra da tinta neutra.** Texto nunca usa a cor da série. Valor, rótulo e legenda ficam em `ink`, `ink-2` ou `ink-3`; a única cor em texto é `positivo` ou `negativo` numa variação com seta e sinal, e `acento-ink` em link e filtro ativo.

**A regra do escuro escolhido.** O tema escuro usa os valores de `tema.escuro`, escolhidos e validados um a um, e não uma inversão do claro. A superfície fica mais clara que o canvas para o cartão continuar subindo; cada acento ganha um `mark` mais claro e um `ink` próprio; `positivo` e `negativo` clareiam para manter 4,5:1.

## Typography

**Display Font:** Segoe UI (com a pilha `fonte.web`: -apple-system, BlinkMacSystemFont, Noto Sans, Roboto, Helvetica Neue, sans-serif)
**Body Font:** Segoe UI (mesma pilha)
**Label/Mono Font:** Cascadia Mono (com Consolas e SF Mono), só para código e caminho de arquivo

**Character:** Uma família só, a nativa do Power BI e do Fluent. A hierarquia vem de tamanho e de dois pesos, não de contraste de famílias; o resultado é sóbrio e lê como a ferramenta que o leitor já conhece. Fora do Windows a pilha cai na fonte do sistema, e a Segoe UI nunca é carregada de CDN, porque a licença é da Microsoft.

### Hierarchy
- **Página** (600, 20px, 1.2): o título da página no cabeçalho ("Visão executiva").
- **KPI** (600, 24px, 1.15, -0.01em): o valor do cartão de KPI, sem quebra de linha.
- **Título** (600, 15px, 1.3, `text-wrap: balance`): o título do cartão de gráfico, que é o achado.
- **Corpo** (400, 14px, 1.5): texto corrido do painel.
- **Rótulo** (400, 12px, 1.35): subtítulo de gráfico, rótulo de KPI, eixos, rótulos diretos, tabela, filtros e dica.
- **Nota** (400, 11px, 1.35): rodapé de fonte e assinatura.

No Power BI a escala é a mesma em pt (`largeTitle`, `callout`, `title`, `header`, `label`, `nota`), e no PDF em pt para A4 (`corpo`, `h1`, `h2`, `h3`, `legenda`, `kpi`). Números sempre em `tabular-nums`.

### Named Rules
**A regra dos dois pesos.** Só 400 e 600. O 600 marca título, valor, rótulo forte e variação; nada de 300, 500 ou 700. No Power BI o 600 é a face Segoe UI Semibold.

**A regra do 0,75.** A escala do Power BI em pt é a escala web em px vezes 0,75: página 20 px vira `largeTitle` 15 pt, KPI 24 px vira `callout` 18 pt, título 15 px vira `title` 11 pt, rótulo 12 px vira `label` 9 pt. Assim o print do Power BI e o painel web leem no mesmo tamanho.

**A regra da caixa de frase.** Caixa de frase em tudo. Sem caixa alta, sem rótulo pequeno acima do título, sem letras espaçadas; acrônimos como GMV, IPCA e KPI ficam como são.

**A regra do título-achado.** O título de cada gráfico afirma o que o dado mostra ("O GMV real cresceu 135,9% em jan–ago/2018 sobre jan–ago/2017") e é calculado dos dados: DAX fx no Power BI, JS no painel, expressão inline no Quarto. Muda com o filtro, então nunca fica falso. O subtítulo traz unidade e período, separados por " · ".

## Layout

**A página de 1280×720.** É a grade do Power BI e o gabarito do painel web: margem 24, calha 16, 12 colunas de 88. As faixas são fixas: cabeçalho em y 16 (44 de altura), KPIs em y 72 (80), linha A em y 168 (272), linha B em y 456 (224), rodapé em y 688 (16). Os quatro KPIs têm 296×80. A linha A divide 8 + 4 colunas (série mensal e barras por região); a linha B divide 6 + 6 (tabela e segundo gráfico). Filtros ficam numa linha só, no cabeçalho, à direita do título.

**Ritmo.** Os espaços vêm só da escala `espaco`. O cartão tem respiro interno de 12 por 16; o vão entre cartões é a calha de 16; o subtítulo encosta no título com 2 px.

**Responsivo.** Abaixo de 1328 px de largura a página deixa de ser o canvas fixo e vira o painel web: 12 colunas fluidas, KPIs em duas colunas, a série mensal na largura toda com 240 px de altura, os gráficos menores lado a lado com 200 px, o rodapé em pilha. Abaixo de 760 px tudo vira uma coluna; abaixo de 600 px aparece a frase que avisa que a tabela rola de lado; abaixo de 520 px os KPIs ficam em uma coluna e a página encosta nas bordas, sem raio.

### Uma página, cinco mídias
- **Power BI.** Tema JSON gerado por acento e tema (`marca/powerbi/tema-<acento>-<claro|escuro>.json`): `dataColors` na ordem do acento com `mark-muted` em sexto, página em `canvas`, todo visual com fundo `surface`, borda `border` de raio 8, sombra desligada e respiro 12 por 16; segmentação com raio 6; título em Semibold e subtítulo em `ink-2`.
- **Painel web.** HTML estático sobre `marca/tokens.css`; tema e acento trocam pelos atributos `data-theme` e `data-acento` no `<html>`, sem redesenhar nada, porque toda marca de gráfico lê variáveis.
- **PDF técnico.** Quarto com Typst em A4, margens de 22 mm nas laterais, 25 mm em cima e 22 mm embaixo. O título divide a página 1 com o resumo, sem capa vazia. Cabeçalho a partir da página 2 (título e data, com fio); rodapé com assinatura, projeto e "1 de N". A figura leva o título-achado acima ("Figura N · achado · unidade") e a linha de fonte dentro do próprio bloco, para nunca cair sozinha na página seguinte.
- **Slides do case.** Reveal.js em 1280×720, sempre no tema claro, sem transição, sem controles nem barra de progresso. Cada slide é um achado: o título afirma, o subtítulo dá unidade e período, a fonte fica embaixo, e o rodapé leva a assinatura e o número do slide. Os gráficos são os mesmos do PDF, pelo `marca.mplstyle`.
- **Capa e miniatura.** 1280×640 com 64 de respiro em cima e 72 nas laterais: à esquerda o título do projeto, uma frase e três KPIs sem cartão; à direita um cartão com a série mensal no mesmo código de cinza e acento; embaixo um fio e a assinatura. A capa é vista reduzida, então texto de gráfico fica em 15 px ou mais e a linha engrossa para 3 px. Acento e tema vêm da URL (`?acento=petroleo&tema=dark`).

### Named Rules
**A regra da grade de 88.** Todo elemento da página de 1280×720 cai nas 12 colunas de 88 com calha de 16 e numa das cinco faixas. Uma posição fora da grade é defeito, não variação.

**A regra do 3-30-300.** A ordem de cima para baixo é a ordem de leitura: resposta, explicação, detalhe. KPIs no topo, gráfico principal na linha A, tabela e dicas na linha B.

## Elevation & Depth

O sistema é plano. A profundidade vem de camadas de tom: `outspace` em volta, `canvas` na página, `surface` no cartão, cada passo separado por um fio de 1 px. No tema escuro a ordem se mantém, com a superfície mais clara que o canvas. A única sombra do sistema é a da dica flutuante, porque ela é o único elemento que de fato flutua sobre o conteúdo.

### Shadow Vocabulary
- **Sombra flutuante** (`sombra_flutuante`, em `tokens.json`): só na dica (tooltip). No Power BI, `dropShadow` fica desligado em todo visual.

### Named Rules
**A regra da sombra que flutua.** Cartão, KPI, controle e marca de gráfico não têm sombra. Se algo precisa se destacar, ganha borda, lavagem do acento ou peso 600.

## Shapes

Cantos suaves e proporcionais ao tamanho: o raio diminui do contêiner para o detalhe. Cartões e páginas usam `raio.cartao`; controles, dica, segmentação do Power BI e caixas do PDF usam `raio.controle`; a ponta da barra e o botão interno do filtro usam `raio.barra`. A barra tem no máximo 24 px de espessura, fica presa à linha de base e arredonda só a ponta do lado do dado. A linha de série tem 2 px com pontas e junções arredondadas; os marcadores têm anel de 2 px na cor da superfície, para se destacarem da linha. Seta de variação é um triângulo desenhado (SVG na web, `polygon` no Typst, ícone do próprio Power BI), nunca um caractere. Tabelas usam só fios horizontais.

### Named Rules
**A regra do raio por tamanho.** Três raios e só três: cartão, controle, barra. Nada de pílula, nada de canto vivo em cartão.

## Components

### Cartão de gráfico
Sóbrio e todo a serviço do dado.
- **Corner Style:** raio de cartão.
- **Background:** `surface`.
- **Shadow Strategy:** nenhuma (ver Elevation & Depth).
- **Border:** 1 px em `border`.
- **Internal Padding:** 12 por 16.
- **Anatomia:** título-achado (Título), subtítulo de unidade e período em `ink-2` (Rótulo), área do gráfico 8 px abaixo. Grade horizontal em `grid`, linha de base em `axis`, sem moldura. Rótulo direto seletivo: último ponto, pico e barra em destaque, nunca um número em cada ponto. Legenda sempre que houver duas séries ou mais.

### Cartão de KPI
- **Shape e cor:** o mesmo cartão, com 80 px de altura na página.
- **Anatomia:** rótulo em `ink-2` no alto à esquerda; valor em KPI embaixo à esquerda; minigráfico de 96×24 no alto à direita (período base em `mark-muted`, atual no acento, ponto final no acento); variação embaixo à direita, em 600, com seta e sinal ("+135,9%", "−4,2 p.p."). O período de comparação aparece uma vez, no subtítulo da página.
- **Nas outras mídias:** no PDF é um bloco com fundo `surface` e fio `border`; nos slides é o mesmo cartão em escala de palco (valor de 52 px); na capa os KPIs perdem o cartão e ficam soltos sobre o canvas.

### Filtro segmentado
- **Style:** grupo com fundo `surface`, borda `border`, raio de controle e 2 px de folga interna; botões transparentes de 28 px de altura em `ink-2`, com raio de barra.
- **Hover:** fundo `surface-2` e texto em `ink`.
- **Ativo:** `aria-pressed`, fundo `acento-wash`, texto em `acento-ink` e peso 600.
- **Foco:** contorno de 2 px em `acento-ink`, afastado 2 px.
- **Transição:** só cor e fundo, na duração e curva de `movimento`.

### Destaque cruzado por região
A interação-assinatura. Clicar numa região, no filtro, na barra ou no nome da tabela, mantém a região no acento e passa as demais para `mark-muted`; a linha da tabela ganha `acento-wash` e peso 600; os títulos-achado se recalculam. A troca de cor leva a duração de `movimento`. Clicar de novo limpa.

### Dica (tooltip)
- **Style:** fundo `surface`, borda `border`, raio de controle, sombra flutuante, texto em Rótulo; nome em 600 e pares rótulo e valor com o valor em `ink` e `tabular-nums`.
- **Comportamento:** aparece no ponteiro e também no foco de teclado; na série mensal as setas percorrem os meses e uma linha vertical em `ink-3` marca o mês.

### Tabela
- **Style:** fios horizontais em `grid`, cabeçalho em 600 e `ink-2` sobre fio `border-strong`, primeira coluna à esquerda e números à direita, linha de total em `surface-2` e 600.
- **Variação na célula:** seta, sinal e cor do tom, como no KPI.
- **Celular:** rola de lado dentro do cartão, com foco de teclado e uma frase curta avisando.

### Caixa de método (PDF)
Fundo `surface-2`, fio `border`, raio de controle, título em 600 e corpo em `ink-2`. É sempre cinza, nunca colorida: método é contexto, não alerta.

### Linhagem (slides)
Três colunas separadas por fio vertical em `border-strong`, sem cartão: rótulo em `ink-2` e 600, número grande em 600, frase curta. Mostra fontes, regras de qualidade e saídas.

### Estados
Carregando, vazio e erro são escritos em uma ou duas frases que dizem o que fazer ("Falta exemplos/dados/resumo.js. Gere o arquivo com ... e recarregue a página."), centrados no cartão, em `ink-2`.

## Do's and Don'ts

### Do:
- **Do** tirar toda cor, tamanho, espaço e raio de `marca/tokens.json` e rodar `python marca/gerar.py` depois de qualquer mudança.
- **Do** escolher um acento por projeto entre `azul`, `petroleo`, `terracota` e `amora`, diferente do projeto anterior.
- **Do** escrever o título de cada gráfico como o achado, calculado dos dados, com subtítulo de unidade e período e linha de fonte embaixo.
- **Do** mostrar toda variação com seta desenhada e sinal, em `positivo` ou `negativo`.
- **Do** usar `tabular-nums` e o formato brasileiro (1.234,5 · R$ 8,65 mi · 92,3%), com espaço não separável entre "R$" e o número.
- **Do** deixar foco visível em todo controle e gráfico, e oferecer os valores em texto (rótulo direto ou tabela, visível ou `sr-only`).
- **Do** manter a assinatura só no rodapé, no colofão e na capa.

### Don't:
- **Don't** pintar texto, valor ou rótulo na cor da série.
- **Don't** usar `ocre` como acento.
- **Don't** pôr sombra em cartão, KPI, controle ou marca de gráfico; sombra só na dica.
- **Don't** usar gradiente, vidro fosco, brilho ou texto em degradê.
- **Don't** pôr borda colorida grossa num lado do cartão.
- **Don't** usar caixa alta, rótulo pequeno acima do título ou letras espaçadas.
- **Don't** usar emoji ou caractere unicode como ícone; a seta é desenhada.
- **Don't** usar dois eixos y, pizza ou rosca com mais de três fatias, moldura ou 3D.
- **Don't** inverter o tema claro para obter o escuro.
- **Don't** carregar Segoe UI de CDN.
