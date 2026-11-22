# Estudo para entrevista

Dez perguntas prováveis em entrevistas de **BI, Analytics e Engenharia de Dados** sobre o **Painel E-Commerce & Macroeconomia Brasil**, com respostas objetivas ancoradas nos números reais verificados pelo gabarito SQL (`sql/gabarito/*.csv`).

## 1. Qual problema de negócio o projeto resolve e por que cruzar e-commerce com BCB e IBGE?

Analisar faturamento de e-commerce isoladamente produz duas distorções clássicas:

1. **Ilusão inflacionária.** Entre setembro de 2016 e outubro de 2018, a inflação acumulada altera o poder de compra do real. Deflacionar o GMV pelo **IPCA oficial (Banco Central SGS 433)** para reais constantes de outubro de 2018 mostra quanto do crescimento foi real (**+135,87%** em Jan–Ago 2018 vs. Jan–Ago 2017) e quanto veio da inflação (**7,56 p.p.** de diferença frente aos +143,43% nominais).
2. **Viés de tamanho populacional.** São Paulo concentra 37,39% do GMV real porque tem 45,5 milhões de habitantes. Cruzar a receita com a **população oficial do IBGE** revela penetração real por 100 mil habitantes: **SP lidera com R$ 13.106,47**, seguido de **RJ (R$ 12.415,10)** e **DF (R$ 12.045,07)**, enquanto o **Amazonas registra R$ 700,71** — 18,7× menos que SP.

Ao mesmo tempo, a série da **Meta Selic (BCB SGS 432)** mostra o ciclo de queda dos juros de **14,25%** para **6,50%** no período — contexto direto para um varejo onde **78,46%** do GMV ocorre no cartão de crédito e **67,92%** das compras no cartão são parceladas (média de **3,55x**).

## 2. Por que usar duas tabelas fato (`fato_pedidos` e `fato_itens_pedido`) em vez de uma única tabela?

Porque o grão do pedido e o grão do item são diferentes. Um pedido Olist pode conter múltiplos itens de categorias e vendedores diferentes (média de **1,14 item/pedido**, 99.441 pedidos brutos para 112.650 itens).

- Se somarmos receita de pedido numa tabela no grão de item, ocorre **dupla contagem** do GMV e do frete.
- Se atribuirmos todo o valor do pedido à `categoria_principal`, distorcemos o Pareto de categorias e perdemos a atribuição correta por vendedor.

A solução é uma **constelação de fatos (*Galaxy Star Schema*)**: `fato_pedidos` responde KPIs de pedido, SLA, satisfação, pagamentos e coorte; `fato_itens_pedido` responde Pareto de categorias e concentração de vendedores. Ambas compartilham as dimensões conformadas `dim_calendario`, `dim_geo_uf` e `dim_categoria`, com **9 relacionamentos `*:1`, todos ativos e em direção única**, sem nenhuma relação bidirecional nem ambiguidade.

## 3. Como foi construído o deflator IPCA e por que escolher outubro/2018 como base?

A partir da série mensal do IPCA (BCB SGS 433), o índice acumulado cresce por juros compostos:

$$I_t = I_{t-1} \times \left(1 + \frac{\text{IPCA}_t}{100}\right)$$

Escolhendo o fim do período Olist (`2018-10`) como mês-base $B$, o fator deflator de cada mês $t$ é $I_B / I_t$. Em `2018-10` o fator vale exatamente `1,000000`; em `2016-09` vale `1,076604`. Multiplicar o valor nominal pelo fator traz todas as vendas históricas para o poder de compra do fim da série: o GMV nominal de **R$ 15,42 milhões** equivale a **R$ 15,96 milhões reais** (base out/2018).

Para que o IPCA acumulado em 12 meses (`ipca_acum_12m_pct`) já fosse exato em setembro de 2016 (**8,48%**), o pipeline coleta a série 433 retroativamente desde outubro de 2015.

## 4. Por que comparar Jan–Ago 2018 vs. Jan–Ago 2017 no YoY executivo em vez do ano inteiro?

Porque o conjunto público da Olist contém 12 meses completos em 2017, mas em 2018 as entregas regulares se encerram em agosto (setembro e outubro de 2018 têm apenas cauda residual sem pedidos entregues, auditada na regra `Q13`). Comparar 8 meses de 2018 contra 12 meses de 2017 mostraria apenas **+18,98%** de crescimento real e mascararia a expansão real do marketplace.

Na janela homogênea (*like-for-like*) **Jan–Ago 2018 vs. Jan–Ago 2017**, o GMV real cresceu **+135,87%** (R$ 3,67 mi → R$ 8,65 mi) contra **+143,43%** nominal — deixando transparente tanto o crescimento comparável quanto o efeito isolado da inflação (**7,56 p.p.**).

## 5. Como o atraso logístico afeta a nota de avaliação do cliente e que cuidado metodológico foi tomado no SLA?

Nos **96.470 pedidos entregues com data real válida**, a pontualidade geral é de **93,23%**, mas o impacto do atraso na satisfação é dramático:

- **No prazo / antecipado (89.936 pedidos):** nota média **4,29★** (62,26% notas 5★; apenas 6,62% notas 1★).
- **1–3 dias de atraso:** cai para **3,29★** (-1,00★).
- **4–7 dias:** despenca para **2,10★** (-2,19★).
- **8–14 dias:** chega ao piso de **1,67★** (-2,62★, com 70,61% de notas 1★).
- **15+ dias:** permanece em **1,72★** (-2,57★, com 69,06% de notas 1★).

Na média agregada, pedidos atrasados recebem **2,27★** contra **4,29★** no prazo (**-2,02 estrelas**).

O cuidado técnico essencial: na Olist, `order_estimated_delivery_date` vem sempre às `00:00:00`. Comparar timestamps brutos classificaria como "atrasado" qualquer pedido entregue às 14h do próprio dia prometido. Por isso o atraso é calculado em **dias civis** (`date(entrega_real) - date(estimada)`). Além disso, os 8 pedidos marcados como `delivered` mas com `data_entrega_real` nula entram no GMV entregue (`96.478`), mas ficam fora do denominador de SLA (`96.470`).

## 6. O que mostra a desigualdade regional e a penetração per capita via IBGE?

O Sudeste concentra **64,59%** do GMV real com prazo médio de **10,69 dias** (SP entrega em **8,70 dias**, com **95,51%** no prazo). Já **Norte (22,54 d)** e **Nordeste (19,95 d)** esperam em média **20,38 dias — 1,9× mais** que o Sudeste — e pagam frete próximo de 18%–22% do GMV (contra 12,20% em SP).

O ranking de penetração per capita (GMV real por 100 mil habitantes, IBGE 2018) evidencia essa assimetria e traz um destaque operacional: o **Rio de Janeiro** é o 2º maior mercado per capita do país (**R$ 12.415,10 / 100k hab.**), mas tem SLA de apenas **87,89%** no prazo e nota média de **3,97★**, sinalizando alto retorno operacional caso o prazo no RJ se aproxime de SP.

## 7. Quais anomalias reais existiam na base Olist e como foram tratadas?

Diferente de datasets "limpos de laboratório", a base real da Olist exigiu **13 regras explícitas de auditoria** (totalizando **6.420 ocorrências** rastreadas na tabela `qualidade_auditoria` e na Página 4):

- **2.963 pedidos cancelados ou não entregues (`2,98%`):** preservados em `fato_pedidos` com `flag_entregue = 0`, excluídos explicitamente nas medidas comerciais e de SLA.
- **551 avaliações duplicadas (`Q08`):** um mesmo `order_id` tinha mais de um review; deduplicamos deterministicamente mantendo a avaliação mais recente.
- **546 itens com frete extremo (`Q11`):** frete > R$ 300 ou > 2× o preço do item; mantidos no GMV real e marcados com `flag_frete_outlier = 1`.
- **8 entregues sem data real (`Q02`) e 6 cancelados com data real espúria (`Q03`):** data espúria nulificada em cancelados; entregues sem data isolados do cálculo de SLA.
- **610 produtos sem categoria (`Q09`) e 2 categorias sem tradução EN oficial (`Q10`):** mapeados explicitamente (`sem_categoria` e fallback para `pc_gamer` e portáteis de cozinha).
- **1 pedido sem registro de pagamento (`Q06`) e 5 pagamentos anômalos (`Q12`):** preservados sem imputação artificial, com `parcelas = 0` excluído da média de parcelamento.

## 8. Como você explica a baixa recompra (3,00%) e a alta concentração de vendedores (66,34%)?

- **Recompra:** apenas **2.801 de 93.358 clientes únicos entregues (3,00%)** fizeram 2+ pedidos, e só **1,36%** recompraram dentro de 6 meses (`M+1` a `M+6`). Isso reflete o modelo de negócio da Olist naquele período — um integrador de lojistas em grandes marketplaces (Mercado Livre, B2W, etc.), onde o cliente frequentemente nem percebia que comprava de uma mesma rede Olist, além do mix concentrado em itens de menor recorrência (presentes, móveis, informática).
- **Vendedores:** dos **2.970 vendedores ativos**, o decil superior (`D1`, 297 lojistas = 10%) gera **66,34%** de todo o GMV real entregue, e **18 de 74 categorias** concentram **81,34%** da receita (regra de Pareto 80/20). Estratégias de retenção de contas-chave (*key accounts*) nesses 297 vendedores protegem dois terços do faturamento.

## 9. Por que gerar o projeto Power BI (PBIP) por código Python em vez de montar clicando na tela?

O formato **PBIP** armazena o modelo semântico em texto (**TMDL**) e o relatório em JSON (**PBIR**). Gerar o `powerbi/` por script (`scripts/montar_pbip.py`) traz cinco vantagens de engenharia:

1. **Fonte única de verdade:** as 68 medidas vêm direto de `dax/medidas.dax`, as 9 relações de `docs/MODELO.md` e o tema de `tema/tema.json`. Nunca há divergência entre documentação e relatório.
2. **Reprodutibilidade determinística:** UUIDs baseados em `uuid5` garantem saída idêntica byte a byte.
3. **Portabilidade e segurança:** o `powerbi/` versionado usa um caminho de exemplo em `PastaDados` (`C:\caminho\do\projeto\data\limpa`), evitando vazar nomes de usuário locais.
4. **Validação automatizada em CI:** testes verificam sobreposição zero de *bounding boxes*, integridade de referências de colunas/medidas no PBIR e desserialização oficial via `Microsoft.PowerBI.Tabular.dll` (TOM).
5. **Reconciliação ponta a ponta:** o motor Analysis Services real do Power BI Desktop abre uma cópia local, atualiza os dados via Power Query M e executa consultas DAX exigindo igualdade contra `sql/gabarito/*.csv`.

## 10. Quais são as limitações honestas do projeto e o que evoluiria em produção?

**Limitações declaradas:**
- A base Olist é um recorte histórico (2016–2018); os indicadores recentes do BCB (`macro_benchmark_atual`) servem apenas como referência de contexto macroeconômico atual, não como projeção de vendas.
- A reconciliação de GMV real entre `fato_pedidos` (`R$ 15.964.483,56`) e `fato_itens_pedido` (`R$ 15.964.483,20`) tem diferença de **R$ 0,36** por arredondamento individual de centavos em 110.197 itens.
- A análise de atraso mede o cumprimento do prazo *prometido* pela Olist (`data_entrega_estimada`), que historicamente já embutia folga média de ~13,5 dias nos pedidos no prazo.
- No GitHub Actions (Linux/Windows sem Power BI Desktop), os testes que exigem `Microsoft.PowerBI.Tabular.dll` ou a abertura do Desktop são pulados automaticamente, rodando integralmente em máquina local com Power BI Desktop instalado.

**Evoluções naturais para um ambiente produtivo:**
- Ingestão incremental agendada (Airflow / Fabric Data Pipelines) gravando em Parquet/Delta Lake e atualizando o modelo semântico via *Incremental Refresh*.
- Adição de custos de aquisição (CAC) e margem por categoria para evoluir de GMV para margem de contribuição e LTV real das coortes.
- Segmentação logística por transportadora e rota UF origem × UF destino para atacar gargalos específicos (como o SLA de 87,89% no RJ e 78,59% em AL).
