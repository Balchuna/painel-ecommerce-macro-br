# Decisões técnicas e metodológicas

Este documento registra as principais escolhas de dados, modelagem, DAX, Power BI e visualização do projeto — e os *trade-offs* aceitos em cada uma.

## 1. Dados públicos, reprodutibilidade e higiene do Git

### Fontes oficiais sem chave privada
As três fontes são 100% públicas e acessíveis sem token nem credencial:
- **Olist** (`olist/work-at-olist-data`, espelho oficial do dataset publicado no Kaggle sob licença **CC BY-NC-SA 4.0**).
- **Banco Central do Brasil (SGS)**: séries `433` (IPCA mensal), `432` (Meta Selic diária) e `1` (Dólar PTAX venda diário).
- **IBGE**: API de Localidades (`/v1/localidades/estados`) e SIDRA Agregados (`6579` População Estimada 2018 e `4714` Censo 2022).

Todas as requisições respeitam *rate limit* explícito (`0,35 s` entre chamadas), `User-Agent` identificável e registro de URL, timestamp UTC e hash SHA-256 em `data/raw/manifesto_coleta.json` e `data/limpa/fontes_metadados.csv`.

### Por que `data/raw/` e `data/painel.sqlite` ficam fora do Git
Os arquivos brutos da Olist somam ~61 MB e o banco SQLite é derivado de `data/limpa/`. Mantê-los no `.gitignore` preserva o repositório leve e rápido para clonar. Em contrapartida, os CSVs modelados de `data/limpa/` (todos abaixo de 23 MB), os gabaritos `sql/gabarito/*.csv` e o `docs/dados/resumo.json` (289 KB) ficam versionados para que o CI rode 100% offline e sem dependência de rede.

## 2. Metodologia econômica e de negócio

### Deflator acumulado pelo IPCA com base `2018-10`
Cada mês $t$ recebe variação mensal $r_t$ da série BCB SGS 433. O índice encadeado cresce por $I_t = I_{t-1} \cdot (1 + r_t / 100)$. Escolhendo outubro de 2018 ($B = \text{2018-10}$, último mês da janela Olist) como mês-base:

$$\text{fator\_deflator}_t = \frac{I_B}{I_t}, \qquad \text{GMV Real}_t = \text{GMV Nominal}_t \times \text{fator\_deflator}_t$$

Com isso, `fator_deflator = 1,000000` em `2018-10`, e meses anteriores (como `2016-09`, com fator `1,076604`) são trazidos para o poder de compra de outubro de 2018. O IPCA acumulado em 12 meses (`ipca_acum_12m_pct`) usa janela móvel composta exata de 12 meses — por isso a coleta começa em `2015-10`.

### Comparativo YoY homogêneo (Jan–Ago 2018 vs. Jan–Ago 2017)
A base pública da Olist contém 12 meses cheios em 2017, mas em 2018 encerra as entregas regulares em agosto (setembro e outubro de 2018 têm apenas cauda residual sem entregas concluídas, registrada na regra `Q13_MESES_CAUDA_PARCIAL`). Comparar apenas o total anual de 2018 contra 2017 subestimaria o crescimento real (+18,98% vs. ano cheio). Por isso, o gabarito SQL (`01_visao_executiva.sql`) e as medidas DAX reportam explicitamente a janela homogênea **Jan–Ago 2018 vs. Jan–Ago 2017**: **+143,43% nominal**, **+135,87% real**, isolando **7,56 p.p.** de efeito inflacionário.

### População IBGE 2018 para penetração per capita (com Censo 2022 na dimensão)
Para calcular `GMV Real / 100 mil hab.` sobre pedidos de 2016–2018, usar a **Estimativa Populacional IBGE de 2018** (SIDRA 6579) mantém coerência temporal entre numerador e denominador. A coluna `populacao_censo_2022` (SIDRA 4714) também é preservada em `dim_geo_uf` como referência demográfica atualizada.

### Cálculo de atraso em dias corridos (data civil)
O atraso logístico é definido como `date(data_entrega_real) - date(data_entrega_estimada)` em dias corridos. A data estimada informada pela Olist ao consumidor vem sempre à meia-noite (`00:00:00`); comparar timestamps brutos marcaria entregas feitas no próprio dia prometido (às 14h, por exemplo) como "atrasadas". Comparar datas civis elimina esse falso positivo e produz **93,23%** de entregas no prazo (`89.936` de `96.470`).

### Diferença de arredondamento de R$ 0,36 entre `fato_pedidos` e `fato_itens_pedido`
Em `fato_pedidos`, `valor_total_real_ipca` aplica o deflator sobre o total do pedido e arredonda para 2 casas decimais (`R$ 15.964.483,56`). Em `fato_itens_pedido`, `valor_item_real_ipca` aplica o deflator em cada um dos 110.197 itens entregues individualmente (`R$ 15.964.483,20`). A diferença acumulada de **R$ 0,36** (0,000002%) é efeito normal de arredondamento de centavos no grão de item e é documentada explicitamente em vez de maquiada.

## 3. Qualidade de dados — nada descartado em silêncio

Todos os **99.441 pedidos brutos** entram em `fato_pedidos` com `flag_entregue` (`0` ou `1`). Nenhuma anomalia é escondida:
- **2.963 pedidos não entregues** (`Q01`) permanecem auditáveis e são filtrados explicitamente nas medidas comerciais e de SLA.
- **8 pedidos entregues sem data real** (`Q02`) entram no GMV entregue (`96.478`), mas ficam fora do denominador de SLA (`96.470`) e recebem faixa `'Sem entrega'`.
- **6 pedidos cancelados com data real preenchida** (`Q03`) têm `data_entrega_real` zerada para `NULL` para não contaminar prazos.
- **551 avaliações duplicadas** (`Q08`) são deduplicadas deterministicamente mantendo a avaliação mais recente por `order_id`.
- **546 itens com frete extremo** (`Q11`, frete > R$ 300 ou > 2× preço) são preservados no GMV real e marcados com `flag_frete_outlier = 1`.

## 4. Modelagem Semântica, DAX e PBIP gerado por script

### Constelação de fatos (*Galaxy Star Schema*) com direção única
Em vez de ligar `fato_itens_pedido` diretamente a `fato_pedidos` (o que criaria caminhos ambíguos com `dim_calendario`, `dim_geo_uf` e `dim_categoria`), ambas as fatos ligam-se apenas às dimensões conformadas em **9 relacionamentos `*:1`, todos ativos e em direção única**.

### Projeto Power BI (PBIP) 100% gerado por código
Assim como no projeto anterior (`painel-certificacoes-sst`), `scripts/montar_pbip.py` gera todo o `powerbi/` (TMDL + PBIR) a partir de:
- `dax/medidas.dax` (fonte única das 68 medidas e suas descrições);
- `docs/MODELO.md` (fonte única dos 9 relacionamentos);
- `tema/tema.json` (tema editorial criado pelo designer);
- `docs/DESIGN_SPEC.md` (grade 1280×720, margem 24 px, gutter 16 px, zero sobreposição de caixas).

### Portabilidade e proteção de privacidade no `powerbi/` versionado
O Power Query exige caminho absoluto para ler arquivos locais. No `powerbi/` versionado, o parâmetro `PastaDados` aponta para `C:\caminho\do\projeto\data\limpa`. Para abrir no Power BI Desktop localmente, gera-se uma cópia fora do repositório com `--pasta-dados`. Um teste automatizado garante que nenhum caminho pessoal (`C:\Users\...`) vaze para o repositório.

### Um único `card` por KPI (sem caixas sobrepostas)
Para garantir zero sobreposição de *bounding boxes* no PBIR (validado por teste automatizado), cada KPI usa um único visual `card` de 192×96 px: o título do container exibe o rótulo do indicador, o subtítulo do container recebe a medida dinâmica de delta (e cor semântica) e o *callout* exibe o valor principal.

### Cultura `"en-US"` na tipagem dos CSVs no Power Query
Embora o modelo use `culture: pt-BR` para exibir números com vírgula decimal e datas `dd/MM/aaaa`, os CSVs em `data/limpa/` seguem o padrão universal UTF-8 com ponto decimal e datas ISO (`AAAA-MM-DD`). Cada consulta M substitui `""` por `null` antes de chamar `Table.TransformColumnTypes(..., "en-US")`, impedindo que um Windows em português leia `123.45` como `12345` ou gere erros em campos nulos.

### Igualdade estrita (`== 0`) em `flag_atraso` no DAX
Na verificação ao vivo dentro do motor Analysis Services do Power BI Desktop, a comparação `fato_pedidos[flag_atraso] = 0` inicialmente elevou o SLA de SP de `95,51%` (SQL) para `95,52%`: em DAX, o operador `=` trata `BLANK() = 0` como verdadeiro, puxando para "no prazo" os 8 pedidos entregues sem data real (`Q02`). Trocar para `NOT ISBLANK ( fato_pedidos[flag_atraso] )` combinado com igualdade estrita `== 0` zerou a divergência para **89.936** entregas no prazo exatas em todas as UFs.

### Ajustes capturados na inspeção visual no Power BI Desktop
A abertura e captura real das 4 páginas no Power BI Desktop 2.159 identificou quatro ajustes que testes puramente textuais não pegam:
1. **Matriz de coorte (`coorte_recompra`):** `REMOVEFILTERS` em DAX não aceita misturar uma tabela inteira (`dim_calendario`) e colunas de outra tabela (`fato_pedidos[...]`) na mesma chamada; separar em dois argumentos distintos de `CALCULATE` + filtrar `coorte_mes_num` como inteiro (`201701..201807`) eliminou o erro do visual.
2. **Eixo macro (`macro_ipca_selic`):** trocar o eixo de texto mensal para `dim_macro_mensal[data_mes]` em modo contínuo (`Continuous`) eliminou a barra de rolagem horizontal e exibiu a queda completa da Selic (14,25% → 6,50%).
3. **Cabeçalho, rodapé e trimestres:** ajuste fino de altura do cabeçalho (`h=76`), rodapé (`y=688, h=28`) e rótulo curto `trimestre_curto` (`T1/17`..`T3/18`) eliminou cortes verticais e reticências (`...`).
4. **Tabelas da página 4:** colunas derivadas no Power Query (`tabela_curta`, `coletado_data`, `licenca_curta`) garantiram que todas as colunas de auditoria e linhagem ficassem legíveis sem corte horizontal.
