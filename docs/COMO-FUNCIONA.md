# Como funciona

Este texto explica o **Painel E-Commerce & Macroeconomia Brasil** sem jargão técnico. Os detalhes de execução estão no [README](../README.md), o modelo de dados em [MODELO.md](MODELO.md) e as escolhas de engenharia em [DECISOES.md](DECISOES.md).

## O problema

Analisar vendas de e-commerce olhando apenas o faturamento nominal engana em dois sentidos:

1. **Inflação distorce o crescimento.** Um real de setembro de 2016 não compra o mesmo que um real de outubro de 2018. Sem corrigir pela inflação oficial (IPCA), parte do crescimento aparente é só alta de preços.
2. **Volume sem população esconde onde há espaço.** São Paulo sempre lidera em vendas absolutas por ter 45,5 milhões de habitantes. Dividir a receita pela população oficial de cada estado (IBGE) mostra onde o e-commerce realmente penetra — e onde o frete e o prazo travam a demanda.

O painel cruza **99.441 pedidos reais** do conjunto público da Olist (2016–2018) com **séries oficiais do Banco Central** (IPCA, Selic e Dólar PTAX) e **dados demográficos do IBGE** para responder quatro perguntas executivas:

1. Quanto do crescimento do e-commerce foi **real** (acima da inflação) enquanto os juros (Selic) caíam de 14,25% para 6,50%?
2. Quanto o **atraso na entrega** derruba a nota de satisfação do cliente (1 a 5 estrelas) e qual a desigualdade logística entre regiões?
3. Como a receita se concentra em **categorias, meios de pagamento, parcelamento, recompra e vendedores**?
4. Quais **defeitos reais** existem na base pública da Olist e como garantir que nenhum número foi distorcido ou inventado?

## O caminho dos dados

```
fontes públicas reais  ->  limpeza & modelagem  ->  banco SQLite  ->  gabarito SQL  ->  Power BI + Web
(Olist, BCB SGS, IBGE)     scripts/                 data/             sql/gabarito/     powerbi/ & docs/
data/raw/                  limpar_modelar.py        painel.sqlite                       index.html
```

1. **Coleta pública e reproduzível (`scripts/coletar_dados.py`).** Baixa os 8 arquivos oficiais da Olist (licença CC BY-NC-SA 4.0) e consulta diretamente, sem chave privada, as APIs públicas do Banco Central (SGS 433 IPCA, 432 Selic, 1 PTAX) e do IBGE (Localidades, População 2018 e Censo 2022). Cada arquivo recebe hash SHA-256 e carimbo de data/hora UTC no manifesto `data/raw/manifesto_coleta.json`.
2. **Limpeza, deflação e modelo estrela (`scripts/limpar_modelar.py`).** Constrói o deflator acumulado do IPCA trazendo todos os valores para **reais constantes de outubro de 2018**, aplica 13 regras de qualidade (deduplicando avaliações repetidas, zerando datas espúrias em cancelados, sinalizando fretes extremos) e grava os CSVs limpos em `data/limpa/`.
3. **Banco relacional e gabarito (`scripts/gerar_gabarito.py`).** Carrega os CSVs no SQLite com chaves estrangeiras e restrições `CHECK` ativas (`sql/01_tabelas.sql`) e executa 6 consultas analíticas (`sql/consultas/01..06.sql`), salvando as respostas oficiais em `sql/gabarito/*.csv`.
4. **Conferência independente (`tests/`).** Um cálculo separado em pandas refaz todas as métricas diretamente a partir dos dados, sem reutilizar o SQL, exigindo concordância exata.
5. **Painel Power BI e versão interativa web (`powerbi/` e `docs/index.html`).** O script `scripts/montar_pbip.py` gera o projeto completo do Power BI (TMDL + PBIR, 4 páginas e 68 medidas DAX) a partir dos arquivos versionados, e `scripts/exportar_web_json.py` gera o resumo agregado (`docs/dados/resumo.json`) que alimenta o painel interativo publicado no GitHub Pages — espelhando as mesmas 4 páginas, cores e números.

## O que os dados reais revelam

| Pergunta | Achado verificado no gabarito SQL |
|---|---|
| Pedidos analisados | **96.478 entregues** de 99.441 brutos (2.963 cancelados/não entregues = 2,98%) |
| GMV nominal vs. real (out/2018) | **R$ 15,42 mi nominais** → **R$ 15,96 mi reais** (+R$ 540 mil em poder de compra) |
| Crescimento real (Jan–Ago 18 vs 17) | **+135,87% real** contra +143,43% nominal — inflação explica apenas **7,56 p.p.** |
| Pano de fundo macro (BCB SGS) | **Selic** caiu de **14,25%** (set/2016) para **6,50%** (out/2018); **IPCA 12m** de **8,48%** para **4,56%** |
| Impacto do atraso na nota | Entrega no prazo: **4,29★** (93,23% dos pedidos). Atrasada: **2,27★** (**-2,02★**). Com 8+ dias de atraso cai para **1,67★–1,72★** |
| Desigualdade regional (IBGE) | Sudeste concentra **64,59%** do GMV; **Norte e Nordeste esperam 1,9× mais** que o Sudeste (20,4 d vs 10,7 d). Líder per capita: **SP (R$ 13.106 / 100 mil hab.)**, 18,7× acima do **AM (R$ 701 / 100 mil hab.)** |
| Concentração comercial | **18 de 74 categorias** somam 80% do GMV; **top 10% dos vendedores** (297 de 2.970) concentram **66,34%** da receita |
| Crédito e recompra | Cartão de crédito responde por **78,46% do GMV** (**67,92%** parcelados, média de **3,55x**). Recompra é rara: apenas **3,00%** dos clientes voltam (**1,36%** em até 6 meses) |
| Auditoria de qualidade | **13 regras** mapearam **6.420 ocorrências** reais (incluindo 551 reviews duplicadas e 546 fretes extremos), todas rastreadas na página 4 |
