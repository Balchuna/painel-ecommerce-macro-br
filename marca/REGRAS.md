# Padrão BI · regras para qualquer agente

Estas regras valem para Claude, Gemini ou qualquer outro agente que construa um projeto de BI do portfólio de Rafael Balchuna. Elas cobrem o Power BI, o painel web, o PDF técnico, os slides do case e a capa. O porquê de cada decisão está em `DESIGN.md`. Aqui está o que fazer e como conferir.

## Onde está cada coisa

| Arquivo | Papel | Edite? |
|---|---|---|
| `marca/tokens.json` | Fonte única: cores (claro e escuro), acentos, tipos, espaços, raios, grade do Power BI | Sim, só aqui |
| `marca/gerar.py` | Gera tudo abaixo e confere contraste (falha se algum texto ficar abaixo de 4,5:1) | Raramente |
| `marca/tokens.css` | Variáveis CSS do painel web, da capa e dos slides | Não, é gerado |
| `marca/powerbi/tema-<acento>-<claro\|escuro>.json` | 8 temas do Power BI | Não, é gerado |
| `marca/quarto/_brand.yml`, `typst-template.typ` | Marca do Quarto e parcial do Typst | Não, é gerado |
| `marca/quarto/modelo.typ` | Layout do PDF: página, cabeçalho, KPI, nota, fonte, tabela | Sim |
| `marca/quarto/typst-show.typ`, `slides.scss` | Ligação do Quarto com o modelo; tema dos slides | Sim |
| `marca/marca.mplstyle` | Estilo dos gráficos do matplotlib | Não, é gerado |
| `exemplos/painel.html` | Página de referência 1280×720 (web, e gabarito do Power BI) | Copie e adapte |
| `exemplos/relatorio.qmd`, `slides.qmd`, `analise.py` | PDF e slides lendo os mesmos dados | Copie e adapte |
| `exemplos/capa.html` | Capa e miniatura 1280×640 | Copie e adapte |

## Projeto novo, passo a passo

1. Copie `marca/`, `DESIGN.md` e `.unslop-ui/` para a raiz do repositório do projeto.
2. Escolha um acento que o projeto anterior não usou: `azul`, `petroleo`, `terracota` ou `amora`. Ocre nunca é acento.
3. Gere os arquivos do projeto:

   ```
   python marca/gerar.py --acento petroleo --dados docs/dados/resumo.json --saida-dados docs/dados
   ```

4. **Power BI.** Exibir > Temas > Procurar temas > `marca/powerbi/tema-<acento>-claro.json`. Monte a página na grade abaixo. Todo título de visual afetado por filtro usa medida DAX (fx).
5. **Painel web.** Parta de `exemplos/painel.html`. Troque `data-acento` no `<html>` e o caminho de `tokens.css` e `resumo.js`.
6. **PDF e slides.** Parta de `relatorio.qmd`, `slides.qmd` e `analise.py`. Rode `quarto render relatorio.qmd` e `quarto render slides.qmd`.
7. **Capa.** Abra `capa.html?acento=<acento>` num servidor local e capture 1280×640 (`&tema=dark` para a versão escura).

## Regras

### Cor

- Toda cor vem de `tokens.json`. Fora dos arquivos gerados, não existe hex escrito à mão.
- Um acento por projeto. Ele pinta a série principal ou a entidade em destaque. A comparação (ano anterior, outras regiões) fica no cinza `mark_muted`.
- Comparação no tempo: o período base fica em `mark_muted` e o atual no acento, na linha principal, nos minigráficos e na capa. O subtítulo diz qual ano está em cinza ("2017 em cinza").
- Mais de uma série segue a ordem do acento em `tokens.json > acentos`, sem pular nem reciclar matiz. A cor segue a entidade: um filtro nunca repinta quem ficou.
- `positivo` e `negativo` servem só para variação boa ou ruim. Sempre com seta desenhada e sinal (+4,2%, −0,09), nunca a cor sozinha.
- Texto nunca usa a cor da série. Valores, rótulos e legendas ficam em `ink`, `ink_2` ou `ink_3`.
- Tema escuro é escolhido, não invertido: use os valores de `tema.escuro`, já validados.

### Tipo

- Segoe UI no Power BI e no PDF; a pilha `fonte.web` no navegador. Dois pesos: 400 e 600.
- Fora do Windows a pilha web cai para a fonte do sistema (San Francisco no macOS, Noto Sans ou Roboto no Linux). Não carregue a Segoe UI de CDN: a licença é da Microsoft.
- Tamanhos só de `tipo` (web em px, Power BI e PDF em pt). A capa, os slides e o título do PDF são vistos de longe ou reduzidos e têm escala própria, fixa em `capa.html`, `slides.scss` e `modelo.typ`; não crie tamanho fora desses lugares. Números em `font-variant-numeric: tabular-nums`.
- Caixa de frase em tudo. Sem caixa alta, sem rótulo pequeno acima do título (eyebrow), sem letras espaçadas.

### Página do Power BI e painel web (1280×720)

- Margem 24, calha 16, 12 colunas de 88. Faixas: cabeçalho y 16 (44 de altura), KPIs y 72 (80), linha A y 168 (272), linha B y 456 (224), rodapé y 688 (16).
- Leitura 3-30-300: a linha de KPIs responde em 3 s, o gráfico principal e o filtro em 30 s, a tabela e as dicas em 300 s.
- Cartão de KPI: rótulo, valor, variação com seta e sinal, minigráfico. O período de comparação fica escrito uma vez, no subtítulo da página.
- Cartões com fundo `surface`, borda de 1px `border`, raio 8, sem sombra. Sombra só na dica flutuante.
- Filtros numa linha, acima dos gráficos, no cabeçalho.

### Gráficos

- O título é o achado, calculado dos dados ("O GMV real cresceu 135,9% em jan–ago/2018"). Ele muda com o filtro: DAX fx no Power BI, JS no painel, expressão inline no Quarto.
- Subtítulo com unidade e período. Linha de fonte embaixo, sempre; no PDF ela fica dentro do bloco da figura, para nunca cair sozinha na página seguinte.
- Barras com até 24px de espessura e ponta arredondada de 4px no lado do dado, presas à linha de base.
- Linhas de 2px com pontas arredondadas. Marcadores de 8px ou mais, com anel de 2px da cor da superfície.
- Grade em fio claro (`grid`), eixo em `axis`. Sem moldura, sem 3D, sem sombra em marca.
- Rótulo direto seletivo: último ponto, pico, a barra em destaque. Nunca um número em cada ponto.
- Legenda sempre que houver 2 séries ou mais. Uma série dividida em período base e atual continua sendo uma série: o subtítulo faz o papel da legenda ("2017 em cinza").
- Nunca dois eixos y. Duas medidas de escala diferente viram dois gráficos ou pequenos múltiplos.
- Dica (tooltip) em todo gráfico interativo. Os valores também existem em texto: rótulo direto em cada barra, ou tabela para séries longas (visível, ou só para leitor de tela com a classe `sr-only`).
- Tabela larga no celular rola de lado dentro do cartão, com uma frase curta avisando que dá para deslizar.

### Texto

- pt-BR (e EN no painel web bilíngue). Números no formato brasileiro: 1.234,5 · R$ 8,65 mi · 92,3%.
- "R$" e o número nunca quebram de linha (espaço não separável).
- Mês abreviado "ago/18"; intervalo com meia-risca "jan–ago/2018".
- Sem ponto de exclamação, sem travessão, sem "insights", "jornada" ou "potencializar".
- Assinatura só no rodapé, no colofão e na capa do PDF: "Rafael Balchuna".

### Acessibilidade

- Texto com contraste de 4,5:1 ou mais (o `gerar.py` confere).
- Foco visível em todo controle e gráfico; gráficos de linha navegáveis pelas setas do teclado.
- Estados de carregando, vazio e erro escritos em uma ou duas frases que dizem o que fazer.

### Proibido

- Gradiente, vidro fosco, brilho, texto em degradê.
- Borda colorida grossa num lado do cartão.
- Emoji ou caractere unicode (▲ ▼ → ●) como ícone. Setas são desenhadas: SVG na web, `polygon` no Typst, ícone do próprio Power BI.
- Pizza ou rosca com mais de três fatias.

## Antes de entregar

- [ ] `python marca/gerar.py --acento <acento>` roda sem erro de contraste.
- [ ] Os `assert` do `analise.py` passam (os números do texto batem com o gabarito do projeto).
- [ ] Prints conferidos: claro e escuro, 1280×720 e celular (390 de largura).
- [ ] Nenhum hex fora de `marca/`: `grep -rnE "#[0-9a-fA-F]{6}" --include=*.html --include=*.css --include=*.qmd . | grep -v _files/` só acha arquivos gerados.
- [ ] Passada do unslop-ui com `.unslop-ui/taste.md`.
