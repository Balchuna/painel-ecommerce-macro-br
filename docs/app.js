/* Painel E-Commerce & Macroeconomia Brasil — web companion
   Sem dependências: gráficos em SVG/HTML nativos, tokens de docs/DESIGN_SPEC.md.
   Dados: docs/dados/resumo.json (gerado por scripts/exportar_web_json.py). */
(() => {
  'use strict';

  /* ------------------------------------------------------------------ tokens */
  const C = {
    ink: '#0F172A', ink2: '#334155', muted: '#64748B', faint: '#94A3B8', hair: '#E2E8F0', grid: '#EEF2F6',
    navy: '#1E3A5F', navy500: '#4F6D8F', navy300: '#A9BCD3', navy50: '#EEF3F9',
    teal: '#0D9488', teal100: '#CCFBF1', amber: '#D97706', amber100: '#FEF3C7', coral: '#DC2626', coral100: '#FEE2E2',
  };
  const DELAY = ['#0D9488', '#FCA5A5', '#F87171', '#DC2626', '#991B1B'];
  const REGIONS = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'];
  const REGION_EN = { 'Norte': 'North', 'Nordeste': 'Northeast', 'Centro-Oeste': 'Center-West', 'Sudeste': 'Southeast', 'Sul': 'South' };
  // Tile-grid cartogram of Brazil: [col, row]
  const TILES = {
    RR: [1, 0], AP: [3, 0],
    AM: [1, 1], PA: [2, 1], MA: [3, 1], CE: [4, 1], RN: [5, 1],
    AC: [0, 2], RO: [1, 2], MT: [2, 2], TO: [3, 2], PI: [4, 2], PE: [5, 2], PB: [6, 2],
    MS: [2, 3], GO: [3, 3], DF: [4, 3], BA: [5, 3], AL: [6, 3],
    SP: [3, 4], MG: [4, 4], ES: [5, 4], SE: [6, 4],
    PR: [3, 5], RJ: [4, 5],
    SC: [3, 6],
    RS: [3, 7],
  };
  const PAY = {
    credit_card: ['Cartão de crédito', 'Credit card'], boleto: ['Boleto', 'Boleto (bank slip)'],
    voucher: ['Voucher', 'Voucher'], debit_card: ['Cartão de débito', 'Debit card'], not_defined: ['Não definido', 'Not defined'],
  };

  /* ------------------------------------------------------------------ i18n */
  const I18N = {
    pt: {
      'brand.kicker': 'Portfólio · Dados & BI', 'brand.title': 'Painel E-Commerce & Macroeconomia Brasil',
      'tab.p1': 'Executivo & Macro', 'tab.p2': 'Logística & SLA', 'tab.p3': 'Comercial & Coorte', 'tab.p4': 'Qualidade & Linhagem',
      'f.ano': 'Ano', 'f.regiao': 'Região', 'f.categoria': 'Categoria', 'f.reset': 'Limpar', 'f.all': 'Todos', 'f.allf': 'Todas',
      'f.catHint': 'O filtro de categoria se aplica à página 03',
      'status.loading': 'Carregando dados…',
      'status.error': 'Não foi possível carregar <code>dados/resumo.json</code>. Rode <code>python scripts/exportar_web_json.py</code> e sirva a pasta <code>docs/</code> por HTTP (ex.: <code>python -m http.server -d docs</code>).',
      'foot.repo': 'Código, SQL e Power BI no GitHub →',
      'foot.sources': 'Fontes: Olist Brazilian E-Commerce Public Dataset (Kaggle, CC BY-NC-SA 4.0) · Banco Central do Brasil — SGS 433 (IPCA), 432 (Selic), 1 (PTAX) · IBGE — Localidades e População.',
      'foot.meta': 'Valores reais a preços de {base} (IPCA). Arquivo gerado em {gen}. Período: {ini} a {fim}.',
      'p1.eyebrow': '01 · Visão executiva & macro', 'p1.title': 'Crescimento real, não só inflação',
      'p1.sub': 'GMV nominal vs. deflacionado pelo IPCA (BCB SGS 433), com a Selic como pano de fundo do crédito ao consumo.',
      'p2.eyebrow': '02 · Logística, SLA & cliente', 'p2.title': 'Atraso é o que mais destrói a satisfação',
      'p2.sub': 'Pedidos entregues. Atraso = entrega real após a data estimada informada ao cliente no checkout.',
      'p3.eyebrow': '03 · Comercial & clientes', 'p3.title': 'Poucas categorias e poucos vendedores carregam a receita',
      'p3.sub': 'Pareto de categorias, mix de pagamento, parcelamento, recompra por coorte e concentração de vendedores.',
      'p4.eyebrow': '04 · Qualidade & linhagem', 'p4.title': 'Cada número é rastreável até a fonte',
      'p4.sub': 'Anomalias reais encontradas na base Olist, tratamento aplicado e conferência contra o gabarito SQL.',
      'k.gmvNom': 'GMV nominal', 'k.gmvReal': 'GMV real (IPCA)', 'k.orders': 'Pedidos', 'k.ticketReal': 'Ticket real',
      'k.rating': 'Nota média', 'k.onTime': 'No prazo', 'k.lead': 'Prazo médio', 'k.delayAvg': 'Atraso médio (atrasados)',
      'k.ratingOn': 'Nota — no prazo', 'k.ratingLate': 'Nota — com atraso', 'k.freight': 'Frete / GMV',
      'k.items': 'Itens por pedido', 'k.card': 'Pedidos no cartão', 'k.inst': 'Parcelas médias (cartão)', 'k.repeat': 'Clientes que recompram',
      'k.top10': 'Top 10% vendedores', 'k.raw': 'Pedidos brutos', 'k.valid': 'Pedidos analisados', 'k.excl': 'Excluídos da análise',
      'k.anom': 'Registros com anomalia', 'k.dupRev': 'Reviews duplicadas', 'k.check': 'Gabarito SQL',
      'd.vs': 'vs {p}', 'd.same': 'mesmo período', 'd.na': 'sem base de comparação', 'd.stable': '● estável',
      'd.delivered': 'pedidos entregues', 'd.scale': 'escala 1–5', 'd.late': 'dias após o prometido', 'd.share': 'participação no total',
      'd.checkOk': 'consultas SQL conferidas', 'd.ofRaw': 'do total bruto',
      'c.trend.t': 'GMV real {dir} <em>{v}</em> {cmp}', 'c.trend.tNo': 'GMV real de <em>{v}</em> no período',
      'c.trend.up': 'cresce', 'c.trend.down': 'recua', 'c.trend.s': 'R$ a preços de {base}. A distância entre as linhas é o efeito da inflação.',
      'c.trend.cmp': '({y} vs {p}, mesmo período)',
      'c.macro.t': 'Selic {dir} de <em class="mac">{a}</em> para <em class="mac">{b}</em>', 'c.macro.down': 'cai', 'c.macro.up': 'sobe', 'c.macro.flat': 'estável em',
      'c.macro.s': 'Selic meta (% a.a., média mensal) e IPCA acumulado em 12 meses — BCB SGS 432/433.',
      'c.region.t': '{r} concentra <em>{v}</em> do GMV real', 'c.region.s': 'Clique numa região para filtrar o painel.',
      'c.ticket.t': 'Ticket médio real {dir} <em>{v}</em> no período', 'c.ticket.up': 'sobe', 'c.ticket.down': 'cai', 'c.ticket.flat': 'estável:',
      'c.ticket.s': 'Por trimestre. Trimestres com menos de 200 pedidos omitidos.',
      'c.read.t': 'Leitura executiva', 'c.read.s': 'Calculada a partir dos filtros ativos.',
      'c.read.1': '<b>Volume:</b> {gmv} em GMV real, {n} pedidos, ticket médio de {tk}.',
      'c.read.2': '<b>Macro:</b> IPCA 12m foi de {i0} a {i1}; Selic de {s0} a {s1} no mesmo intervalo.',
      'c.read.3': '<b>Risco:</b> pedidos atrasados recebem nota {late}, contra {on} quando chegam no prazo.',
      'c.hero.t': 'Com 15+ dias de atraso, a nota despenca de <em>{a}</em> para <em class="neg">{b}</em>',
      'c.hero.s': 'Nota média da avaliação (1–5) por faixa de atraso na entrega. Abaixo de cada barra: pedidos avaliados.',
      'c.lead.t': '{a} espera <em class="neg">{x}×</em> o prazo do {b}', 'c.lead.s': 'Prazo médio entre compra e entrega, em dias. Clique para filtrar.',
      'c.map.t': '{best} lidera; {worst} fica por último', 'c.map.s': 'Por UF do cliente. População: IBGE. Passe o mouse para detalhes.',
      'c.map.top': 'Melhores 5', 'c.map.bot': 'Piores 5', 'c.map.vMap': 'Mapa', 'c.map.vTbl': 'Tabela 27 UFs',
      'm.gmv100k': 'GMV/100 mil hab.', 'm.onTime': '% no prazo', 'm.lead': 'Prazo médio', 'm.rating': 'Nota',
      'bench.label': 'Referência macro atual (BCB):',
      'c.pareto.t': '<em>{n}</em> de {tot} categorias somam 80% do GMV real', 'c.pareto.s': 'Top 15 categorias por GMV real; linha = % acumulado do total.',
      'c.pareto.cat': '{c}: {v} · #{r} · {p} do GMV', 'c.pareto.l1': 'GMV real', 'c.pareto.l2': '% acumulado', 'c.pareto.l3': 'Referência 80%',
      'c.pay.t': '{m} domina: <em>{v}</em> do valor pago', 'c.pay.s': 'Participação no valor total pago, por meio de pagamento principal.',
      'c.inst.t': '<em>{v}</em> dos pedidos no cartão são parcelados', 'c.inst.s': 'Pedidos no cartão por número de parcelas (10+ agrupa 10 a 24x).',
      'c.sel.t': 'Top 10% dos vendedores = <em class="neg">{v}</em> do GMV', 'c.sel.s': 'Participação no GMV real por decil de vendedores (D1 = 10% que mais vendem).',
      'c.coh.t': 'Recompra é rara: <em class="neg">{v}</em> voltam no mês seguinte', 'c.coh.s': '% de clientes da coorte (mês da 1ª compra) que compram de novo no mês M+n.',
      'c.coh.cohort': 'Coorte', 'c.coh.n': 'Clientes',
      'c.audit.t': '<em>{n}</em> regras de qualidade — nada é descartado em silêncio', 'c.audit.s': 'Cada exclusão ou correção fica registrada na tabela qualidade_auditoria.',
      'c.types.t': '{r} é a maior fonte de anomalia', 'c.types.s': 'Registros afetados por regra.',
      'c.lin.t': '<em>{n}</em> fontes públicas ({f} arquivos), sem chave de API', 'c.lin.s': 'Coleta reprodutível com timestamps UTC e SHA-256 em scripts/coletar_dados.py.',
      'c.lin.vSum': 'Resumo (3)', 'c.lin.vAll': 'Arquivos ({f})', 'th.files': 'Arquivos',
      'th.rule': 'Regra', 'th.table': 'Tabela', 'th.rows': 'Registros', 'th.pct': '% base', 'th.action': 'Tratamento',
      'th.source': 'Fonte', 'th.endpoint': 'Endpoint / arquivo', 'th.records': 'Registros', 'th.when': 'Coletado em', 'th.license': 'Licença',
      't.orders': 'Pedidos', 't.rated': 'Avaliados', 't.pop': 'População', 't.share': 'Participação',
      'faixa.0': 'No prazo', 'faixa.1': '1–3 dias', 'faixa.2': '4–7 dias', 'faixa.3': '8–14 dias', 'faixa.4': '15+ dias',
      'empty': 'Sem dados para os filtros selecionados.', 'na': 'n/d',
    },
    en: {
      'brand.kicker': 'Portfolio · Data & BI', 'brand.title': 'Brazil E-Commerce & Macroeconomics Dashboard',
      'tab.p1': 'Executive & Macro', 'tab.p2': 'Logistics & SLA', 'tab.p3': 'Commercial & Cohorts', 'tab.p4': 'Data Quality & Lineage',
      'f.ano': 'Year', 'f.regiao': 'Region', 'f.categoria': 'Category', 'f.reset': 'Clear', 'f.all': 'All', 'f.allf': 'All',
      'f.catHint': 'The category filter applies to page 03',
      'status.loading': 'Loading data…',
      'status.error': 'Could not load <code>dados/resumo.json</code>. Run <code>python scripts/exportar_web_json.py</code> and serve <code>docs/</code> over HTTP (e.g. <code>python -m http.server -d docs</code>).',
      'foot.repo': 'Code, SQL and Power BI on GitHub →',
      'foot.sources': 'Sources: Olist Brazilian E-Commerce Public Dataset (Kaggle, CC BY-NC-SA 4.0) · Central Bank of Brazil — SGS 433 (IPCA), 432 (Selic), 1 (PTAX) · IBGE — Localities & Population.',
      'foot.meta': 'Real values at {base} prices (IPCA). File generated on {gen}. Period: {ini} to {fim}.',
      'p1.eyebrow': '01 · Executive & macro view', 'p1.title': 'Real growth, not just inflation',
      'p1.sub': 'Nominal GMV vs. GMV deflated by IPCA (BCB SGS 433), with the Selic rate as the consumer-credit backdrop.',
      'p2.eyebrow': '02 · Logistics, SLA & customer', 'p2.title': 'Late delivery is what destroys satisfaction',
      'p2.sub': 'Delivered orders. Late = actual delivery after the estimated date promised to the customer at checkout.',
      'p3.eyebrow': '03 · Commercial & customers', 'p3.title': 'A few categories and sellers carry the revenue',
      'p3.sub': 'Category Pareto, payment mix, installments, cohort repurchase and seller concentration.',
      'p4.eyebrow': '04 · Data quality & lineage', 'p4.title': 'Every number traces back to its source',
      'p4.sub': 'Real anomalies found in the Olist data, how each was handled, and reconciliation against the SQL answer key.',
      'k.gmvNom': 'Nominal GMV', 'k.gmvReal': 'Real GMV (IPCA)', 'k.orders': 'Orders', 'k.ticketReal': 'Real avg. ticket',
      'k.rating': 'Avg. score', 'k.onTime': 'On-time SLA', 'k.lead': 'Avg. delivery', 'k.delayAvg': 'Avg. delay (when late)',
      'k.ratingOn': 'Score — on time', 'k.ratingLate': 'Score — late', 'k.freight': 'Freight / GMV',
      'k.items': 'Items per order', 'k.card': 'Orders by card', 'k.inst': 'Avg. installments (card)', 'k.repeat': 'Repeat customers',
      'k.top10': 'Top 10% sellers', 'k.raw': 'Raw orders', 'k.valid': 'Orders analysed', 'k.excl': 'Excluded from analysis',
      'k.anom': 'Records with anomalies', 'k.dupRev': 'Duplicate reviews', 'k.check': 'SQL answer key',
      'd.vs': 'vs {p}', 'd.same': 'same period', 'd.na': 'no comparison base', 'd.stable': '● flat',
      'd.delivered': 'delivered orders', 'd.scale': '1–5 scale', 'd.late': 'days past promise', 'd.share': 'share of total',
      'd.checkOk': 'SQL queries verified', 'd.ofRaw': 'of raw total',
      'c.trend.t': 'Real GMV {dir} <em>{v}</em> {cmp}', 'c.trend.tNo': 'Real GMV of <em>{v}</em> in the period',
      'c.trend.up': 'grows', 'c.trend.down': 'falls', 'c.trend.s': 'BRL at {base} prices. The gap between the lines is inflation.',
      'c.trend.cmp': '({y} vs {p}, same period)',
      'c.macro.t': 'Selic {dir} from <em class="mac">{a}</em> to <em class="mac">{b}</em>', 'c.macro.down': 'falls', 'c.macro.up': 'rises', 'c.macro.flat': 'flat at',
      'c.macro.s': 'Selic target (% p.a., monthly average) and 12-month IPCA inflation — BCB SGS 432/433.',
      'c.region.t': '{r} holds <em>{v}</em> of real GMV', 'c.region.s': 'Click a region to filter the dashboard.',
      'c.ticket.t': 'Real avg. ticket {dir} <em>{v}</em> over the period', 'c.ticket.up': 'rises', 'c.ticket.down': 'falls', 'c.ticket.flat': 'flat:',
      'c.ticket.s': 'By quarter. Quarters with fewer than 200 orders omitted.',
      'c.read.t': 'Executive readout', 'c.read.s': 'Computed from the active filters.',
      'c.read.1': '<b>Volume:</b> {gmv} real GMV, {n} orders, average ticket {tk}.',
      'c.read.2': '<b>Macro:</b> 12-month IPCA moved from {i0} to {i1}; Selic from {s0} to {s1} over the same window.',
      'c.read.3': '<b>Risk:</b> late orders score {late} on average, versus {on} when delivered on time.',
      'c.hero.t': 'At 15+ days late, the review score collapses from <em>{a}</em> to <em class="neg">{b}</em>',
      'c.hero.s': 'Average review score (1–5) by delivery-delay bucket. Below each bar: reviewed orders.',
      'c.lead.t': '{a} waits <em class="neg">{x}×</em> as long as the {b}', 'c.lead.s': 'Average days from purchase to delivery. Click to filter.',
      'c.map.t': '{best} leads; {worst} ranks last', 'c.map.s': 'By customer state. Population: IBGE. Hover for details.',
      'c.map.top': 'Top 5', 'c.map.bot': 'Bottom 5', 'c.map.vMap': 'Map', 'c.map.vTbl': '27-State Table',
      'm.gmv100k': 'GMV / 100k pop.', 'm.onTime': '% on time', 'm.lead': 'Avg. delivery', 'm.rating': 'Score',
      'bench.label': 'Current macro reference (BCB):',
      'c.pareto.t': '<em>{n}</em> of {tot} categories make up 80% of real GMV', 'c.pareto.s': 'Top 15 categories by real GMV; line = cumulative % of total.',
      'c.pareto.cat': '{c}: {v} · #{r} · {p} of GMV', 'c.pareto.l1': 'Real GMV', 'c.pareto.l2': 'Cumulative %', 'c.pareto.l3': '80% reference',
      'c.pay.t': '{m} dominates: <em>{v}</em> of value paid', 'c.pay.s': 'Share of total value paid, by main payment method.',
      'c.inst.t': '<em>{v}</em> of card orders are paid in installments', 'c.inst.s': 'Credit-card orders by installment count (10+ groups 10–24x).',
      'c.sel.t': 'Top 10% of sellers = <em class="neg">{v}</em> of GMV', 'c.sel.s': 'Share of real GMV by seller decile (D1 = top-selling 10%).',
      'c.coh.t': 'Repurchase is rare: <em class="neg">{v}</em> come back the next month', 'c.coh.s': '% of cohort customers (first-purchase month) buying again in month M+n.',
      'c.coh.cohort': 'Cohort', 'c.coh.n': 'Customers',
      'c.audit.t': '<em>{n}</em> data-quality rules — nothing is dropped silently', 'c.audit.s': 'Every exclusion or fix is logged in the qualidade_auditoria table.',
      'c.types.t': '{r} is the largest anomaly source', 'c.types.s': 'Records affected per rule.',
      'c.lin.t': '<em>{n}</em> public sources ({f} files), zero API keys', 'c.lin.s': 'Reproducible collection with UTC timestamps and SHA-256 in scripts/coletar_dados.py.',
      'c.lin.vSum': 'Summary (3)', 'c.lin.vAll': 'Files ({f})', 'th.files': 'Files',
      'th.rule': 'Rule', 'th.table': 'Table', 'th.rows': 'Records', 'th.pct': '% base', 'th.action': 'Treatment',
      'th.source': 'Source', 'th.endpoint': 'Endpoint / file', 'th.records': 'Records', 'th.when': 'Collected at', 'th.license': 'License',
      't.orders': 'Orders', 't.rated': 'Reviewed', 't.pop': 'Population', 't.share': 'Share',
      'faixa.0': 'On time', 'faixa.1': '1–3 days', 'faixa.2': '4–7 days', 'faixa.3': '8–14 days', 'faixa.4': '15+ days',
      'empty': 'No data for the selected filters.', 'na': 'n/a',
    },
  };

  /* ------------------------------------------------------------------ state */
  const state = { lang: 'pt', page: 'p1', ano: 'all', regiao: 'all', categoria: 'all', mapMetric: 'gmv100k', mapView: 'map', linView: 'summary', D: null };
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const t = (k, v) => { let s = (I18N[state.lang][k] ?? I18N.pt[k] ?? k); if (v) for (const [a, b] of Object.entries(v)) s = s.split(`{${a}}`).join(b); return s; };
  const sum = (arr, f) => arr.reduce((a, r) => a + (+(typeof f === 'function' ? f(r) : r[f]) || 0), 0);
  const groupBy = (arr, f) => arr.reduce((m, r) => { const k = f(r); (m.get(k) || m.set(k, []).get(k)).push(r); return m; }, new Map());
  const div = (a, b) => (b ? a / b : null);
  const isEN = () => state.lang === 'en';

  /* ------------------------------------------------------------------ formatting */
  const nf = (v, d = 0) => (v == null || !isFinite(v)) ? t('na')
    : new Intl.NumberFormat(isEN() ? 'en-US' : 'pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  const F = {
    int: (v) => nf(v, 0),
    money: (v, d = 1) => {
      if (v == null || !isFinite(v)) return t('na');
      const a = Math.abs(v), sp = isEN() ? '' : ' ';
      if (a === 0) return `R$${sp}0`;
      if (a >= 1e9) return `R$${sp}${nf(v / 1e9, d)}${isEN() ? 'B' : ' bi'}`;
      if (a >= 1e6) return `R$${sp}${nf(v / 1e6, d)}${isEN() ? 'M' : ' mi'}`;
      if (a >= 1e3) return `R$${sp}${nf(v / 1e3, d)}${isEN() ? 'K' : ' mil'}`;
      return `R$${sp}${nf(v, d)}`;
    },
    moneyFull: (v) => (v == null ? t('na') : `R$${isEN() ? '' : ' '}${nf(v, 2)}`),
    pct: (v, d = 1) => (v == null || !isFinite(v) ? t('na') : `${nf(v * 100, d)}%`),
    pctRaw: (v, d = 2) => (v == null || !isFinite(v) ? t('na') : `${nf(v, d)}%`),
    star: (v, d = 2) => (v == null ? t('na') : `${nf(v, d)}★`),
    days: (v, d = 1) => (v == null ? t('na') : `${nf(v, d)} ${isEN() ? 'd' : 'd'}`),
    x: (v) => nf(v, 1),
  };
  const MONTHS = {
    pt: ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'],
    en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  };
  const fmtMonth = (ym, long) => {
    if (!ym) return '';
    const [y, m] = String(ym).split('-');
    const n = MONTHS[state.lang][+m - 1];
    return isEN() ? `${n} ${long ? y : y.slice(2)}` : `${n}/${long ? y : y.slice(2)}`;
  };
  const regionName = (r) => (isEN() ? (REGION_EN[r] || r) : r);
  const payName = (p) => (PAY[p] ? PAY[p][isEN() ? 1 : 0] : String(p).replace(/_/g, ' '));
  const catName = (r) => (isEN() ? (r.categoria_en || r.categoria_pt) : (r.categoria_pt || r.categoria_en)) || '—';
  const prettyCat = (s) => String(s || '').replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());

  /* ------------------------------------------------------------------ data access */
  const D = () => state.D;
  const yearOf = (r) => String(r.ano ?? String(r.ano_mes || '').slice(0, 4));
  const okYear = (r) => state.ano === 'all' || yearOf(r) === state.ano;
  const okRegion = (r) => state.regiao === 'all' || r.regiao === state.regiao;
  const okCat = (r) => state.categoria === 'all' || r.categoria_pt === state.categoria;
  const filt = (arr, { year = true, region = true } = {}) => (arr || []).filter((r) => (!year || okYear(r)) && (!region || okRegion(r)));

  function aggMonthly(rows) {
    const a = {
      pedidos: sum(rows, 'pedidos'), gmvNom: sum(rows, 'gmv_nominal'), gmvReal: sum(rows, 'gmv_real'), frete: sum(rows, 'frete'),
      entregues: sum(rows, 'entregues'),
      entreguesData: sum(rows, (r) => r.entregues_com_data ?? r.entregues),
      noPrazo: sum(rows, 'no_prazo'), diasEnt: sum(rows, 'soma_dias_entrega'),
      nAtr: sum(rows, 'n_atrasados'), diasAtr: sum(rows, 'soma_dias_atraso'), somaNota: sum(rows, 'soma_nota'), nNota: sum(rows, 'n_nota'),
    };
    a.ticketReal = div(a.gmvReal, a.pedidos);
    a.pctNoPrazo = div(a.noPrazo, a.entreguesData);
    a.prazo = div(a.diasEnt, a.entreguesData);
    a.atraso = div(a.diasAtr, a.nAtr);
    a.nota = div(a.somaNota, a.nNota);
    a.fretePct = div(a.frete, a.gmvNom);
    return a;
  }

  /** Same-period YoY: latest year in the filtered set vs. previous year, same months. */
  function yoy() {
    const all = filt(D().mensal_regiao, { year: false });
    const scoped = filt(D().mensal_regiao);
    const years = [...new Set(scoped.filter((r) => r.pedidos > 0).map(yearOf))].sort();
    if (!years.length) return null;
    const y = years[years.length - 1], p = String(+y - 1);
    const monthsArr = [...new Set(scoped.filter((r) => yearOf(r) === y && r.pedidos > 0).map((r) => String(r.ano_mes).slice(5, 7)))].sort();
    const months = new Set(monthsArr);
    const cur = aggMonthly(all.filter((r) => yearOf(r) === y && months.has(String(r.ano_mes).slice(5, 7))));
    const prev = aggMonthly(all.filter((r) => yearOf(r) === p && months.has(String(r.ano_mes).slice(5, 7))));
    if (prev.pedidos < 500) return null;
    const mNames = MONTHS[state.lang];
    const span = monthsArr.length < 12 ? `${mNames[+monthsArr[0] - 1]}–${mNames[+monthsArr[monthsArr.length - 1] - 1]}` : '';
    return { y, p, cur, prev, partial: months.size < 12, span };
  }

  function monthlySeries(rows) {
    const g = groupBy(rows, (r) => r.ano_mes);
    return [...g.keys()].sort().map((k) => ({ ym: k, ...aggMonthly(g.get(k)) }));
  }

  function delayRows() {
    const raw = filt(D().faixa_atraso).filter((r) => +r.ordem >= 0 && +r.ordem <= 4);
    const g = groupBy(raw, (r) => +r.ordem);
    return [0, 1, 2, 3, 4].map((o) => {
      const rows = g.get(o) || [];
      return {
        ordem: o,
        faixa: rows[0]?.faixa,
        faixa_en: rows[0]?.faixa_en,
        pedidos: sum(rows, 'pedidos'), nNota: sum(rows, 'n_nota'), somaNota: sum(rows, 'soma_nota'),
        nota: div(sum(rows, 'soma_nota'), sum(rows, 'n_nota')),
      };
    });
  }

  /* ------------------------------------------------------------------ tooltip */
  const tip = () => $('#tip');
  function showTip(html, ev) {
    const el = tip(); el.innerHTML = html; el.classList.add('on');
    const pad = 14, w = el.offsetWidth, h = el.offsetHeight;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + w > innerWidth - 8) x = ev.clientX - w - pad;
    if (y + h > innerHeight - 8) y = ev.clientY - h - pad;
    el.style.left = `${Math.max(8, x)}px`; el.style.top = `${Math.max(8, y)}px`;
  }
  const hideTip = () => tip().classList.remove('on');
  const tipRow = (label, value, color) => `<div class="t-r"><span>${color ? `<i style="background:${color}"></i>` : ''}${label}</span><b>${value}</b></div>`;

  /* ------------------------------------------------------------------ SVG helpers */
  const NS = 'http://www.w3.org/2000/svg';
  function niceScale(min, max, count = 4) {
    if (!isFinite(min) || !isFinite(max)) { min = 0; max = 1; }
    if (max === min) { max = min + (min === 0 ? 1 : Math.abs(min) * 0.1); }
    const step0 = (max - min) / count, mag = Math.pow(10, Math.floor(Math.log10(step0))), n = step0 / mag;
    const step = (n < 1.5 ? 1 : n < 3 ? 2 : n < 7 ? 5 : 10) * mag;
    const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, ticks = [];
    for (let v = lo; v <= hi + step / 2; v += step) ticks.push(+v.toFixed(10));
    return { lo, hi, ticks };
  }
  function svg(w, h) {
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('class', 'chart'); s.setAttribute('viewBox', `0 0 ${w} ${h}`); s.setAttribute('height', h); s.setAttribute('role', 'img');
    return s;
  }
  function add(parent, tag, attrs = {}, text) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) if (v != null) e.setAttribute(k, v);
    if (text != null) e.textContent = text;
    parent.appendChild(e); return e;
  }
  const widthOf = (el) => Math.max(260, Math.floor(el.clientWidth || el.parentElement.clientWidth || 600));
  const empty = (el) => { el.innerHTML = `<div class="empty">${t('empty')}</div>`; };

  /** Multi-series line chart with optional secondary axis and hover crosshair. */
  function lineChart(el, o) {
    el.innerHTML = '';
    const labels = o.labels; if (!labels.length) return empty(el);
    const W = widthOf(el), H = o.height || 240;
    const hasY2 = o.series.some((s) => s.axis === 2);
    const m = { t: 10, r: hasY2 ? 46 : (o.endLabels ? 80 : 14), b: 24, l: 50 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const vals = (ax) => o.series.filter((s) => (s.axis || 1) === ax).flatMap((s) => s.values).filter((v) => v != null && isFinite(v));
    const v1 = vals(1), v2 = vals(2);
    const s1 = niceScale(o.yZero ? Math.min(0, ...v1) : Math.min(...v1), Math.max(...v1));
    const s2 = hasY2 ? niceScale(o.y2Zero ? Math.min(0, ...v2) : Math.min(...v2), Math.max(...v2)) : null;
    const x = (i) => m.l + (labels.length === 1 ? iw / 2 : (i * iw) / (labels.length - 1));
    const y = (v, ax = 1) => { const s = ax === 2 ? s2 : s1; return m.t + ih - ((v - s.lo) / (s.hi - s.lo)) * ih; };
    const S = svg(W, H);
    const g = add(S, 'g', { class: 'grid' }), ay = add(S, 'g', { class: 'ax-y' });
    s1.ticks.forEach((v) => { add(g, 'line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }); add(ay, 'text', { x: m.l - 8, y: y(v) + 4, 'text-anchor': 'end' }, o.yFmt(v)); });
    if (s2) s2.ticks.forEach((v) => add(ay, 'text', { x: W - m.r + 8, y: y(v, 2) + 4 }, o.y2Fmt(v)));
    add(S, 'line', { class: 'base', x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih });
    const every = Math.max(1, Math.ceil(labels.length / Math.max(2, Math.floor(iw / 62))));
    labels.forEach((l, i) => { if (i % every === 0 || i === labels.length - 1 && labels.length - 1 - (Math.floor((labels.length - 1) / every) * every) > every / 2) add(S, 'text', { x: x(i), y: H - 6, 'text-anchor': 'middle' }, o.xFmt ? o.xFmt(l) : l); });
    o.series.forEach((s) => {
      let d = '', pen = false;
      s.values.forEach((v, i) => { if (v == null || !isFinite(v)) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${y(v, s.axis).toFixed(1)}`; pen = true; });
      if (s.area) {
        const idx = s.values.map((v, i) => (v == null ? null : i)).filter((i) => i != null);
        if (idx.length > 1) add(S, 'path', { d: `${d}L${x(idx[idx.length - 1])},${m.t + ih}L${x(idx[0])},${m.t + ih}Z`, fill: s.color, opacity: 0.07 });
      }
      add(S, 'path', { d, fill: 'none', stroke: s.color, 'stroke-width': s.width || 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', 'stroke-dasharray': s.dash || null });
      if (o.endLabels && (s.axis || 1) === 1) {
        let li = s.values.length - 1; while (li >= 0 && s.values[li] == null) li--;
        if (li >= 0) {
          add(S, 'circle', { cx: x(li), cy: y(s.values[li], s.axis), r: 3, fill: s.color });
          s._end = { x: x(li) + 8, y: y(s.values[li], s.axis), text: s.endFmt ? s.endFmt(s.values[li]) : o.yFmt(s.values[li]), color: s.color };
        }
      }
    });
    // de-collide end labels
    const ends = o.series.map((s) => s._end).filter(Boolean).sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
    ends.forEach((e) => add(S, 'text', { x: e.x, y: e.y + 4, class: 'lbl', style: `fill:${e.color}` }, e.text));
    // hover
    const xh = add(S, 'line', { class: 'xhair', y1: m.t, y2: m.t + ih, x1: m.l, x2: m.l, opacity: 0 });
    const dots = o.series.map((s) => add(S, 'circle', { r: 4, fill: '#fff', stroke: s.color, 'stroke-width': 2, cx: m.l, cy: m.t, opacity: 0 }));
    const hit = add(S, 'rect', { class: 'hit', x: m.l, y: m.t, width: iw, height: ih });
    hit.addEventListener('mousemove', (ev) => {
      const r = S.getBoundingClientRect(), px = ((ev.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(labels.length - 1, Math.round(((px - m.l) / iw) * (labels.length - 1))));
      xh.setAttribute('x1', x(i)); xh.setAttribute('x2', x(i)); xh.setAttribute('opacity', 1);
      o.series.forEach((s, k) => {
        const v = s.values[i];
        dots[k].setAttribute('cx', v == null ? m.l : x(i));
        dots[k].setAttribute('cy', v == null ? m.t : y(v, s.axis));
        dots[k].setAttribute('opacity', v == null ? 0 : 1);
      });
      showTip(`<div class="t-h">${o.xTipFmt ? o.xTipFmt(labels[i]) : labels[i]}</div>${o.series.map((s) => tipRow(s.name, s.values[i] == null ? t('na') : (s.tipFmt || o.yFmt)(s.values[i]), s.color)).join('')}`, ev);
    });
    hit.addEventListener('mouseleave', () => { hideTip(); xh.setAttribute('opacity', 0); dots.forEach((d) => d.setAttribute('opacity', 0)); });
    el.appendChild(S);
  }

  /** Vertical columns with per-bar colours, value labels and optional sub-labels / secondary line. */
  function columnChart(el, o) {
    el.innerHTML = '';
    const items = o.items; if (!items.length) return empty(el);
    const W = widthOf(el), H = o.height || 220;
    const m = { t: o.labels === false ? 10 : 22, r: o.line ? 44 : 8, b: (o.sub ? 36 : 22) + (o.rotate ? 34 : 0), l: o.yAxis === false ? 8 : 46 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const vmax = Math.max(...items.map((d) => d.value || 0));
    const sc = o.yRange ? { lo: o.yRange[0], hi: o.yRange[1], ticks: o.yTicks || niceScale(o.yRange[0], o.yRange[1]).ticks } : niceScale(0, vmax);
    const y = (v) => m.t + ih - ((Math.max(sc.lo, v) - sc.lo) / (sc.hi - sc.lo)) * ih;
    const S = svg(W, H);
    if (o.yAxis !== false) {
      const g = add(S, 'g', { class: 'grid' }), ay = add(S, 'g', { class: 'ax-y' });
      sc.ticks.forEach((v) => { add(g, 'line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }); add(ay, 'text', { x: m.l - 8, y: y(v) + 4, 'text-anchor': 'end' }, o.yFmt(v)); });
    }
    const band = iw / items.length, bw = Math.min(o.maxBar || 56, band * (o.gap ?? 0.62));
    items.forEach((d, i) => {
      const cx = m.l + band * i + band / 2, top = y(d.value || 0), bh = m.t + ih - top;
      const r = add(S, 'rect', { class: `bar${d.dim ? ' dim' : ''}${o.onClick ? ' clickable' : ''}`, x: cx - bw / 2, y: top, width: bw, height: Math.max(0, bh), rx: 2, fill: d.color || C.navy });
      if (o.labels !== false && d.value != null) add(S, 'text', { x: cx, y: top - 6, 'text-anchor': 'middle', class: o.bigLabels ? 'lbl-big' : 'lbl' }, o.labelFmt ? o.labelFmt(d.value) : o.yFmt(d.value));
      const lx = add(S, 'text', o.rotate
        ? { x: cx, y: m.t + ih + 12, 'text-anchor': 'end', transform: `rotate(-38 ${cx} ${m.t + ih + 12})` }
        : { x: cx, y: m.t + ih + 15, 'text-anchor': 'middle', style: d.strong ? `fill:${C.ink};font-weight:600` : null },
      o.rotate && d.label.length > 18 ? `${d.label.slice(0, 17)}…` : d.label);
      if (o.sub && d.sub) add(S, 'text', { x: cx, y: m.t + ih + 30, 'text-anchor': 'middle', style: `fill:${C.faint};font-size:10.5px` }, d.sub);
      const hb = add(S, 'rect', { class: 'hit', x: m.l + band * i, y: m.t, width: band, height: ih + 4 });
      if (o.onClick) { hb.classList.add('clickable'); hb.addEventListener('click', () => o.onClick(d)); }
      hb.addEventListener('mousemove', (ev) => { r.style.opacity = 0.85; showTip(d.tip || `<div class="t-h">${esc(d.label)}</div>${tipRow('', o.yFmt(d.value))}`, ev); });
      hb.addEventListener('mouseleave', () => { r.style.opacity = ''; hideTip(); });
      void lx;
    });
    add(S, 'line', { class: 'base', x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih });
    if (o.line) {
      const y2 = (v) => m.t + ih - v * ih; // 0..1
      const ay2 = add(S, 'g', { class: 'ax-y' });
      [0, 0.25, 0.5, 0.75, 1].forEach((v) => add(ay2, 'text', { x: W - m.r + 8, y: y2(v) + 4 }, `${Math.round(v * 100)}%`));
      if (o.line.ref != null) {
        add(S, 'line', { x1: m.l, x2: W - m.r, y1: y2(o.line.ref), y2: y2(o.line.ref), stroke: C.faint, 'stroke-dasharray': '4 4', 'stroke-width': 1 });
      }
      let d = '';
      o.line.values.forEach((v, i) => { d += `${i ? 'L' : 'M'}${(m.l + band * i + band / 2).toFixed(1)},${y2(v).toFixed(1)}`; });
      add(S, 'path', { d, fill: 'none', stroke: o.line.color, 'stroke-width': 2, 'stroke-linejoin': 'round' });
      o.line.values.forEach((v, i) => add(S, 'circle', { cx: m.l + band * i + band / 2, cy: y2(v), r: 2.6, fill: '#fff', stroke: o.line.color, 'stroke-width': 1.6, 'pointer-events': 'none' }));
    }
    el.appendChild(S);
  }

  /** HTML horizontal bars. */
  function hbars(el, o) {
    if (!o.items.length) return empty(el);
    const max = Math.max(...o.items.map((d) => d.value || 0)) || 1;
    el.innerHTML = `<div class="hbars" style="--lw:${o.labelWidth || 104}px">${o.items.map((d, i) => `
      <${o.onClick ? 'button type="button"' : 'div'} class="hbar${o.onClick ? ' clickable' : ''}${d.dim ? ' is-dim' : ''}" data-i="${i}">
        <span class="hbar__label" title="${esc(d.label)}">${esc(d.label)}</span>
        <span class="hbar__track"><span class="hbar__fill" style="width:0;background:${d.color || C.navy}" data-w="${((d.value || 0) / max) * 100}"></span></span>
        <span class="hbar__val">${o.fmt(d.value)}</span>
      </${o.onClick ? 'button' : 'div'}>`).join('')}</div>`;
    $$('.hbar', el).forEach((b) => {
      const d = o.items[+b.dataset.i];
      if (o.onClick) b.addEventListener('click', () => o.onClick(d));
      if (d.tip) { b.addEventListener('mousemove', (ev) => showTip(d.tip, ev)); b.addEventListener('mouseleave', hideTip); }
    });
    requestAnimationFrame(() => $$('.hbar__fill', el).forEach((f) => { f.style.width = `${f.dataset.w}%`; }));
  }

  function sparkline(values, color) {
    const v = values.filter((x) => x != null && isFinite(x));
    if (v.length < 3) return '';
    const min = Math.min(...v), max = Math.max(...v), w = 64, h = 22;
    const pts = values.map((x, i) => (x == null ? null : [(i / (values.length - 1)) * w, h - 2 - ((x - min) / ((max - min) || 1)) * (h - 4)])).filter(Boolean);
    const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join('');
    const last = pts[pts.length - 1];
    return `<svg class="kpi__spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${d}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round" opacity=".55"/><circle cx="${last[0]}" cy="${last[1]}" r="2.2" fill="${color}"/></svg>`;
  }

  const lerp = (a, b, k) => Math.round(a + (b - a) * k);
  function mix(c1, c2, k) {
    const p = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
    const a = p(c1), b = p(c2);
    return `#${a.map((v, i) => lerp(v, b[i], Math.max(0, Math.min(1, k))).toString(16).padStart(2, '0')).join('')}`;
  }

  /* ------------------------------------------------------------------ building blocks */
  function kpiHTML(k) {
    const dcls = k.deltaClass ? ` ${k.deltaClass}` : '';
    const sp = k.spark ? sparkline(k.spark, k.accent || C.navy) : '';
    return `<div class="kpi${k.badge ? ' kpi--badge' : ''}${sp ? ' kpi--spark' : ''}" style="--accent:${k.accent || C.navy}">
      <div class="kpi__label" title="${esc(k.label)}">${k.label}</div>
      <div class="kpi__value">${k.value}</div>
      <div class="kpi__delta${dcls}">${k.delta || ''}</div>
      ${sp}
    </div>`;
  }
  function deltaOf(cur, prev, { lowerIsBetter = false, pp = false, label } = {}) {
    if (cur == null || prev == null || !isFinite(cur) || !isFinite(prev) || (!pp && prev === 0)) return { html: `<span>${t('d.na')}</span>`, cls: '' };
    const ch = pp ? (cur - prev) * 100 : (cur / prev - 1) * 100;
    if (Math.abs(ch) < 0.05) return { html: `${t('d.stable')} <span>${label}</span>`, cls: '' };
    const good = lowerIsBetter ? ch < 0 : ch > 0;
    const val = pp ? `${nf(Math.abs(ch), 1)} p.p.` : `${nf(Math.abs(ch), 1)}%`;
    return { html: `${ch > 0 ? '▲' : '▼'} ${val} <span>${label}</span>`, cls: good ? 'is-good' : 'is-bad' };
  }
  function card({ area, id, title, sub, hero, extra = '', legend = '' }) {
    return `<article class="card${hero ? ' card--hero' : ''}" style="grid-area:${area}">
      <div class="card__head"><div><h2 class="card__title" id="${id}-t">${title}</h2>${sub ? `<p class="card__sub">${sub}</p>` : ''}</div>${extra}</div>
      ${legend}
      <div class="card__body" id="${id}"></div>
    </article>`;
  }
  const legendHTML = (items) => `<div class="legend">${items.map((i) => `<span><i class="${i.cls || ''}" style="background:${i.color};color:${i.color}"></i>${i.label}</span>`).join('')}</div>`;

  function toggleRegion(r) { state.regiao = state.regiao === r ? 'all' : r; syncFilters(); render(); }

  /* ------------------------------------------------------------------ page 1 */
  function renderP1(root) {
    const rows = filt(D().mensal_regiao), a = aggMonthly(rows), Y = yoy();
    const ms = monthlySeries(rows).filter((r) => r.pedidos > 0);
    const msSpark = ms.filter((r) => r.pedidos >= 50);
    const spSrc = msSpark.length >= 3 ? msSpark : ms;
    const lbl = Y ? t('d.vs', { p: Y.p }) + (Y.span ? ` (${Y.span})` : '') : '';
    const dl = (k, opt = {}) => (Y ? deltaOf(Y.cur[k], Y.prev[k], { label: lbl, ...opt }) : { html: `<span>${t('d.na')}</span>`, cls: '' });
    const kpis = [
      { label: t('k.gmvNom'), value: F.money(a.gmvNom), accent: C.navy, d: dl('gmvNom'), spark: spSrc.map((r) => r.gmvNom) },
      { label: t('k.gmvReal'), value: F.money(a.gmvReal), accent: C.teal, d: dl('gmvReal'), spark: spSrc.map((r) => r.gmvReal) },
      { label: t('k.orders'), value: F.int(a.pedidos), accent: C.navy, d: dl('pedidos'), spark: spSrc.map((r) => r.pedidos) },
      { label: t('k.ticketReal'), value: F.moneyFull(a.ticketReal), accent: C.teal, d: dl('ticketReal'), spark: spSrc.map((r) => r.ticketReal) },
      { label: t('k.rating'), value: F.star(a.nota), accent: C.teal, d: dl('nota'), spark: spSrc.map((r) => r.nota) },
      { label: t('k.onTime'), value: F.pct(a.pctNoPrazo), accent: (a.pctNoPrazo ?? 1) < 0.9 ? C.coral : C.teal, d: dl('pctNoPrazo', { pp: true }), spark: spSrc.map((r) => r.pctNoPrazo) },
    ].map((k) => ({ ...k, delta: k.d.html, deltaClass: k.d.cls }));

    // insight titles
    let trendT = t('c.trend.tNo', { v: F.money(a.gmvReal) });
    if (Y) {
      const g = Y.cur.gmvReal / Y.prev.gmvReal - 1;
      trendT = t('c.trend.t', { dir: t(g >= 0 ? 'c.trend.up' : 'c.trend.down'), v: `${nf(Math.abs(g) * 100, 1)}%`, cmp: t('c.trend.cmp', { y: Y.y, p: Y.p }) });
    }
    const macro = (D().macro_mensal || []).filter(okYear).filter((r) => !ms.length || (r.ano_mes >= ms[0].ym && r.ano_mes <= ms[ms.length - 1].ym));
    const macroSelic = macro.filter((r) => r.selic_media != null && isFinite(r.selic_media));
    let macroT = '';
    if (macroSelic.length) {
      const s0 = macroSelic[0].selic_media, s1 = macroSelic[macroSelic.length - 1].selic_media;
      macroT = Math.abs(s1 - s0) < 0.05 ? `Selic ${t('c.macro.flat')} <em class="mac">${F.pctRaw(s1)}</em>`
        : t('c.macro.t', { dir: t(s1 < s0 ? 'c.macro.down' : 'c.macro.up'), a: F.pctRaw(s0), b: F.pctRaw(s1) });
    }
    const byReg = groupBy(filt(D().mensal_regiao, { region: false }), (r) => r.regiao);
    const regTot = sum([...byReg.values()].flat(), 'gmv_real');
    const regItems = REGIONS.filter((r) => byReg.has(r)).map((r) => ({ key: r, label: regionName(r), value: sum(byReg.get(r), 'gmv_real') }))
      .sort((p, q) => q.value - p.value)
      .map((d) => ({ ...d, dim: state.regiao !== 'all' && state.regiao !== d.key, tip: `<div class="t-h">${esc(d.label)}</div>${tipRow(t('k.gmvReal'), F.money(d.value))}${tipRow(t('t.share'), F.pct(d.value / regTot))}` }));
    const regT = regItems.length ? t('c.region.t', { r: regItems[0].label, v: F.pct(regItems[0].value / regTot, 0) }) : '';

    const qg = groupBy(rows.filter((r) => r.pedidos > 0), (r) => `${r.ano_mes.slice(0, 4)}-T${Math.ceil(+r.ano_mes.slice(5, 7) / 3)}`);
    const quarters = [...qg.keys()].sort().map((k) => { const x = aggMonthly(qg.get(k)); return { k, label: `${isEN() ? 'Q' : 'T'}${k.slice(-1)}/${k.slice(2, 4)}`, value: x.ticketReal, pedidos: x.pedidos }; }).filter((q) => q.pedidos >= 200);
    let tkT = t('c.ticket.t', { dir: t('c.ticket.flat'), v: F.moneyFull(a.ticketReal) });
    if (quarters.length >= 2) {
      const ch = quarters[quarters.length - 1].value / quarters[0].value - 1;
      tkT = Math.abs(ch) < 0.02 ? t('c.ticket.t', { dir: t('c.ticket.flat'), v: F.moneyFull(a.ticketReal) }) : t('c.ticket.t', { dir: t(ch > 0 ? 'c.ticket.up' : 'c.ticket.down'), v: `${nf(Math.abs(ch) * 100, 1)}%` });
    }
    const dr = delayRows(), on = dr[0], lateAgg = { s: sum(dr.slice(1), 'somaNota'), n: sum(dr.slice(1), 'nNota') };

    root.innerHTML = `<div class="kpis">${kpis.map(kpiHTML).join('')}</div>
      <div class="grid grid--p1">
        ${card({ area: 'trend', id: 'c-trend', title: trendT, sub: t('c.trend.s', { base: fmtMonth(D().meta?.mes_base_ipca, true) }),
    legend: legendHTML([{ color: C.navy, label: t('k.gmvNom') }, { color: C.teal, label: t('k.gmvReal') }]) })}
        ${card({ area: 'macro', id: 'c-macro', title: macroT, sub: t('c.macro.s'),
    legend: legendHTML([{ color: C.amber, label: isEN() ? 'IPCA 12m' : 'IPCA 12m' }, { color: C.faint, label: isEN() ? 'Selic (target)' : 'Selic meta' }]) })}
        ${card({ area: 'region', id: 'c-region', title: regT, sub: t('c.region.s') })}
        ${card({ area: 'ticket', id: 'c-ticket', title: tkT, sub: t('c.ticket.s') })}
        ${card({ area: 'read', id: 'c-read', title: t('c.read.t'), sub: t('c.read.s') })}
      </div>`;

    lineChart($('#c-trend'), {
      labels: ms.map((r) => r.ym), xFmt: (l) => fmtMonth(l), xTipFmt: (l) => fmtMonth(l, true), height: 252, yZero: true, endLabels: true,
      yFmt: (v) => F.money(v, v >= 1e6 ? 1 : 0),
      series: [
        { name: t('k.gmvNom'), values: ms.map((r) => r.gmvNom), color: C.navy, width: 2 },
        { name: t('k.gmvReal'), values: ms.map((r) => r.gmvReal), color: C.teal, width: 2.5, area: true },
      ],
    });
    lineChart($('#c-macro'), {
      labels: macro.map((r) => r.ano_mes), xFmt: (l) => fmtMonth(l), xTipFmt: (l) => fmtMonth(l, true), height: 252, yZero: true, endLabels: true,
      yFmt: (v) => `${nf(v, v % 1 ? 1 : 0)}%`, endFmt: null,
      series: [
        { name: 'IPCA 12m', values: macro.map((r) => r.ipca_12m_pct), color: C.amber, width: 2, tipFmt: (v) => F.pctRaw(v), endFmt: (v) => F.pctRaw(v) },
        { name: isEN() ? 'Selic (target)' : 'Selic meta', values: macro.map((r) => r.selic_media), color: C.faint, width: 2, dash: '5 4', tipFmt: (v) => F.pctRaw(v), endFmt: (v) => F.pctRaw(v) },
      ],
    });
    hbars($('#c-region'), { items: regItems, fmt: (v) => F.money(v), labelWidth: 92, onClick: (d) => toggleRegion(d.key) });
    columnChart($('#c-ticket'), {
      items: quarters.map((q) => ({ label: q.label, value: q.value, color: C.teal, tip: `<div class="t-h">${q.label}</div>${tipRow(t('k.ticketReal'), F.moneyFull(q.value))}${tipRow(t('t.orders'), F.int(q.pedidos))}` })),
      height: 150, yAxis: false, yFmt: (v) => F.moneyFull(v), labelFmt: (v) => nf(v, 0), maxBar: 34,
    });
    const macroIpca = macro.filter((r) => r.ipca_12m_pct != null && isFinite(r.ipca_12m_pct));
    const i0 = macroIpca[0], i1 = macroIpca[macroIpca.length - 1];
    const s0 = macroSelic[0], s1 = macroSelic[macroSelic.length - 1];
    const bm = D().meta?.benchmark_macro_atual;
    const bmParts = [];
    if (Array.isArray(bm)) {
      const order = { selic_meta_aa: 0, ipca_12m_pct: 1, ptax_usd_venda: 2 };
      bm.slice().sort((p, q) => (order[p.indicador] ?? 9) - (order[q.indicador] ?? 9)).forEach((b) => {
        if (b.valor_recente == null) return;
        const lbl = b.indicador === 'selic_meta_aa' ? 'Selic' : b.indicador === 'ipca_12m_pct' ? 'IPCA 12m' : 'PTAX';
        const val = b.indicador === 'ptax_usd_venda' ? `R$ ${nf(b.valor_recente, 2)}` : F.pctRaw(b.valor_recente);
        bmParts.push(`${lbl} <b>${val}</b>`);
      });
    } else if (bm) {
      if (bm.selic_pct != null || bm.selic != null) bmParts.push(`Selic <b>${F.pctRaw(bm.selic_pct ?? bm.selic)}</b>`);
      if (bm.ipca_12m_pct != null || bm.ipca_acum_12m_pct != null) bmParts.push(`IPCA 12m <b>${F.pctRaw(bm.ipca_12m_pct ?? bm.ipca_acum_12m_pct)}</b>`);
      if (bm.ptax != null || bm.ptax_usd != null) bmParts.push(`PTAX <b>R$ ${nf(bm.ptax ?? bm.ptax_usd, 2)}</b>`);
    }
    const bmRef = Array.isArray(bm) && bm.length ? String(bm[0].data_referencia || '').slice(0, 7) : bm?.referencia;
    $('#c-read').innerHTML = `<ul class="read">
      <li><span class="ic ic--up">▲</span><span>${t('c.read.1', { gmv: `<b>${F.money(a.gmvReal)}</b>`, n: F.int(a.pedidos), tk: F.moneyFull(a.ticketReal) })}</span></li>
      ${(i0 && s0) ? `<li><span class="ic ic--mac">●</span><span>${t('c.read.2', { i0: F.pctRaw(i0.ipca_12m_pct), i1: `<b>${F.pctRaw(i1.ipca_12m_pct)}</b>`, s0: F.pctRaw(s0.selic_media), s1: `<b>${F.pctRaw(s1.selic_media)}</b>` })}</span></li>` : ''}
      <li><span class="ic ic--down">▼</span><span>${t('c.read.3', { late: `<b style="color:${C.coral}">${F.star(div(lateAgg.s, lateAgg.n))}</b>`, on: `<b style="color:${C.teal}">${F.star(on.nota)}</b>` })}</span></li>
    </ul>${bmParts.length ? `<div class="bench-note"><span>${t('bench.label')}</span><span>${bmParts.join(' · ')}${bmRef ? ` (${esc(fmtMonth(bmRef, true))})` : ''}</span></div>` : ''}`;
  }

  /* ------------------------------------------------------------------ page 2 */
  function ufStats() {
    const g = groupBy(filt(D().uf_ano, { region: false }), (r) => r.uf);
    return [...g.entries()].map(([uf, rs]) => {
      const pop = rs[0].populacao, gmv = sum(rs, 'gmv_real');
      const ent = sum(rs, (r) => r.entregues_com_data ?? r.entregues);
      return {
        uf, nome: rs[0].nome, regiao: rs[0].regiao, pop, pedidos: sum(rs, 'pedidos'), gmv,
        gmv100k: div(gmv, pop) != null ? (gmv / pop) * 1e5 : null,
        onTime: div(sum(rs, 'no_prazo'), ent), lead: div(sum(rs, 'soma_dias_entrega'), ent), rating: div(sum(rs, 'soma_nota'), sum(rs, 'n_nota')),
      };
    });
  }
  const MAP_METRICS = {
    gmv100k: { key: 'gmv100k', lab: 'm.gmv100k', fmt: (v) => F.money(v, 0), color: C.navy, better: 'high' },
    onTime: { key: 'onTime', lab: 'm.onTime', fmt: (v) => F.pct(v), color: C.teal, better: 'high' },
    lead: { key: 'lead', lab: 'm.lead', fmt: (v) => F.days(v), color: C.coral, better: 'low' },
    rating: { key: 'rating', lab: 'm.rating', fmt: (v) => F.star(v), color: C.teal, better: 'high' },
  };

  function renderP2(root) {
    const rows = filt(D().mensal_regiao), a = aggMonthly(rows), Y = yoy(), dr = delayRows();
    const ms = monthlySeries(rows).filter((r) => r.pedidos > 0);
    const msSpark = ms.filter((r) => r.pedidos >= 50);
    const spSrc = msSpark.length >= 3 ? msSpark : ms;
    const lbl = Y ? t('d.vs', { p: Y.p }) + (Y.span ? ` (${Y.span})` : '') : '';
    const dl = (k, opt = {}) => (Y ? deltaOf(Y.cur[k], Y.prev[k], { label: lbl, ...opt }) : { html: `<span>${t('d.na')}</span>`, cls: '' });
    const late = { s: sum(dr.slice(1), 'somaNota'), n: sum(dr.slice(1), 'nNota') };
    const kpis = [
      { label: t('k.lead'), value: F.days(a.prazo), accent: C.navy, d: dl('prazo', { lowerIsBetter: true }), spark: spSrc.map((r) => r.prazo) },
      { label: t('k.onTime'), value: F.pct(a.pctNoPrazo), accent: C.teal, d: dl('pctNoPrazo', { pp: true }), spark: spSrc.map((r) => r.pctNoPrazo) },
      { label: t('k.delayAvg'), value: F.days(a.atraso), accent: C.coral, d: { html: `<span>${t('d.late')}</span>`, cls: '' } },
      { label: t('k.ratingOn'), value: F.star(dr[0].nota), accent: C.teal, d: { html: `<span>${F.int(dr[0].nNota)} ${isEN() ? 'reviews' : 'avaliações'}</span>`, cls: '' } },
      { label: t('k.ratingLate'), value: F.star(div(late.s, late.n)), accent: C.coral, d: { html: `<span>${F.int(late.n)} ${isEN() ? 'reviews' : 'avaliações'}</span>`, cls: '' } },
      { label: t('k.freight'), value: F.pct(a.fretePct), accent: C.amber, d: dl('fretePct', { lowerIsBetter: true, pp: true }), spark: spSrc.map((r) => r.fretePct) },
    ].map((k) => ({ ...k, delta: k.d.html, deltaClass: k.d.cls }));

    const heroT = (dr[0].nota != null && dr[4].nota != null) ? t('c.hero.t', { a: F.star(dr[0].nota, 1), b: F.star(dr[4].nota, 1) }) : '';
    const regG = groupBy(filt(D().mensal_regiao, { region: false }), (r) => r.regiao);
    const leadItems = REGIONS.filter((r) => regG.has(r)).map((r) => { const x = aggMonthly(regG.get(r)); return { key: r, label: regionName(r), value: x.prazo, x }; })
      .filter((d) => d.value != null).sort((p, q) => q.value - p.value)
      .map((d) => ({ ...d, color: C.navy, dim: state.regiao !== 'all' && state.regiao !== d.key, tip: `<div class="t-h">${esc(d.label)}</div>${tipRow(t('k.lead'), F.days(d.value))}${tipRow(t('k.onTime'), F.pct(d.x.pctNoPrazo))}${tipRow(t('t.orders'), F.int(d.x.pedidos))}` }));
    const leadT = leadItems.length >= 2 ? t('c.lead.t', { a: leadItems[0].label, b: leadItems[leadItems.length - 1].label, x: nf(leadItems[0].value / leadItems[leadItems.length - 1].value, 1) }) : '';

    const mm = MAP_METRICS[state.mapMetric];
    const ufs = ufStats().filter((u) => u[mm.key] != null);
    const ranked = [...ufs].sort((p, q) => (mm.better === 'high' ? q[mm.key] - p[mm.key] : p[mm.key] - q[mm.key]));
    const mapT = ranked.length ? t('c.map.t', { best: `<em>${ranked[0].uf}</em>`, worst: `<em class="neg">${ranked[ranked.length - 1].uf}</em>` }) + ` <span style="color:${C.muted};font-weight:500">· ${t(mm.lab)}</span>` : '';
    const seg = `<div class="seg" role="group">${Object.values(MAP_METRICS).map((m) => `<button type="button" data-metric="${m.key}" aria-pressed="${m.key === state.mapMetric}">${t(m.lab)}</button>`).join('')}</div>`;
    const vseg = `<div class="seg" role="group"><button type="button" data-mapview="map" aria-pressed="${state.mapView === 'map'}">${t('c.map.vMap')}</button><button type="button" data-mapview="table" aria-pressed="${state.mapView === 'table'}">${t('c.map.vTbl')}</button></div>`;

    root.innerHTML = `<div class="kpis">${kpis.map(kpiHTML).join('')}</div>
      <div class="grid grid--p2">
        ${card({ area: 'hero', id: 'c-hero', title: heroT, sub: t('c.hero.s'), hero: true })}
        ${card({ area: 'lead', id: 'c-lead', title: leadT, sub: t('c.lead.s') })}
        ${card({ area: 'map', id: 'c-map', title: mapT, sub: t('c.map.s') })}
      </div>`;
    $('#c-map').insertAdjacentHTML('beforebegin', `<div class="maptools">${seg}${vseg}</div>`);
    $$('.seg button[data-metric]', root).forEach((b) => b.addEventListener('click', () => { state.mapMetric = b.dataset.metric; render(); }));
    $$('.seg button[data-mapview]', root).forEach((b) => b.addEventListener('click', () => { state.mapView = b.dataset.mapview; render(); }));

    const totRated = sum(dr, 'nNota');
    columnChart($('#c-hero'), {
      items: dr.map((d, i) => ({
        label: t(`faixa.${i}`), value: d.nota, color: DELAY[i], strong: true,
        sub: `${F.int(d.nNota)} · ${F.pct(div(d.nNota, totRated), 1)}`,
        tip: `<div class="t-h">${t(`faixa.${i}`)}</div>${tipRow(t('k.rating'), F.star(d.nota))}${tipRow(t('t.rated'), F.int(d.nNota))}${tipRow(t('t.share'), F.pct(div(d.nNota, totRated)))}`,
      })),
      height: 268, yRange: [1, 5], yTicks: [1, 2, 3, 4, 5], yFmt: (v) => `${nf(v, 0)}★`, labelFmt: (v) => F.star(v, 1), bigLabels: true, sub: true, maxBar: 72, gap: 0.6,
    });
    hbars($('#c-lead'), { items: leadItems, fmt: (v) => F.days(v), labelWidth: 92, onClick: (d) => toggleRegion(d.key) });
    if (state.mapView === 'table') renderUfTable($('#c-map'), ranked, mm);
    else renderMap($('#c-map'), ufs, ranked, mm);
  }

  function renderUfTable(el, ranked, mm) {
    if (!ranked.length) return empty(el);
    const maxGmv = Math.max(1, ...ranked.map((u) => u.gmv100k || 0));
    el.innerHTML = `<div class="scroll" style="max-height:430px"><table class="tbl"><thead><tr>
      <th>UF</th><th>${t('f.regiao')}</th><th class="num">${t('t.orders')}</th><th class="num">${t('m.gmv100k')}</th>
      <th class="num">${t('m.lead')}</th><th class="num">${t('m.onTime')}</th><th class="num">${t('m.rating')}</th>
    </tr></thead><tbody>${ranked.map((u) => {
      const dim = state.regiao !== 'all' && u.regiao !== state.regiao;
      const slaCls = u.onTime >= 0.92 ? 'pill--ok' : (u.onTime < 0.85 ? 'pill--bad' : 'pill--warn');
      return `<tr style="${dim ? 'opacity:.4' : ''};cursor:pointer" data-reg="${esc(u.regiao)}">
        <td class="strong">${esc(u.uf)}</td><td>${esc(regionName(u.regiao))}</td>
        <td class="num">${F.int(u.pedidos)}</td>
        <td class="num"><span class="databar"><i style="width:${((u.gmv100k || 0) / maxGmv) * 100}%;background:${C.teal100}"></i><b>${F.money(u.gmv100k, 0)}</b></span></td>
        <td class="num">${F.days(u.lead)}</td>
        <td class="num"><span class="pill ${slaCls}">${F.pct(u.onTime)}</span></td>
        <td class="num">${F.star(u.rating)}</td>
      </tr>`;
    }).join('')}</tbody></table></div>`;
    $$('tr[data-reg]', el).forEach((tr) => tr.addEventListener('click', () => toggleRegion(tr.dataset.reg)));
    void mm;
  }

  function renderMap(el, ufs, ranked, mm) {
    if (!ufs.length) return empty(el);
    el.innerHTML = '<div class="mapwrap"><div class="mapsvg"></div><div class="rank"></div></div>';
    const host = $('.mapsvg', el), W = Math.max(240, host.clientWidth || 340);
    const cell = Math.min(50, Math.floor((W - 4) / 7)), gap = 3, H = cell * 8 + 4;
    const vals = ufs.map((u) => u[mm.key]), lo = Math.min(...vals), hi = Math.max(...vals);
    const kOf = (v) => (hi === lo ? 0.5 : (v - lo) / (hi - lo));
    const colorOf = (v) => { const k = kOf(v); return mix('#F1F5F9', mm.color, mm.better === 'low' ? 0.12 + 0.88 * k : 0.12 + 0.88 * k); };
    const S = svg(cell * 7 + 4, H); S.removeAttribute('height'); S.style.maxWidth = `${cell * 7 + 4}px`;
    const byUf = new Map(ufs.map((u) => [u.uf, u]));
    Object.entries(TILES).forEach(([uf, [c, r]]) => {
      const u = byUf.get(uf), g = add(S, 'g', { class: `tile${u && state.regiao !== 'all' && u.regiao !== state.regiao ? ' dim' : ''}` });
      const fill = u ? colorOf(u[mm.key]) : '#F1F5F9', dark = u ? kOf(u[mm.key]) > 0.45 : false;
      add(g, 'rect', { x: 2 + c * cell, y: 2 + r * cell, width: cell - gap, height: cell - gap, rx: 5, fill });
      add(g, 'text', { x: 2 + c * cell + (cell - gap) / 2, y: 2 + r * cell + (cell - gap) / 2 - 2, 'text-anchor': 'middle', class: dark ? '' : 'dark' }, uf);
      if (u && cell >= 42) add(g, 'text', { x: 2 + c * cell + (cell - gap) / 2, y: 2 + r * cell + (cell - gap) / 2 + 11, 'text-anchor': 'middle', class: dark ? '' : 'dark', style: 'font-size:9px;font-weight:500;opacity:.9' }, shortMetric(mm, u[mm.key]));
      if (u) {
        g.style.cursor = 'pointer';
        g.addEventListener('mousemove', (ev) => showTip(`<div class="t-h">${esc(u.nome)} · ${uf}</div>${tipRow(regionName(u.regiao), '')}${tipRow(t('m.gmv100k'), F.money(u.gmv100k, 0))}${tipRow(t('m.onTime'), F.pct(u.onTime))}${tipRow(t('m.lead'), F.days(u.lead))}${tipRow(t('m.rating'), F.star(u.rating))}${tipRow(t('t.orders'), F.int(u.pedidos))}${tipRow(t('t.pop'), F.int(u.pop))}`, ev));
        g.addEventListener('mouseleave', hideTip);
        g.addEventListener('click', () => toggleRegion(u.regiao));
      }
    });
    host.appendChild(S);
    host.insertAdjacentHTML('beforeend', `<div class="ramp"><span>${mm.fmt(lo)}</span><span class="ramp__bar" style="background:linear-gradient(90deg,${colorOf(lo)},${colorOf(hi)})"></span><span>${mm.fmt(hi)}</span></div>`);
    const li = (u, i) => `<li><b>${i}. ${u.uf}</b><span>${esc(u.nome)}</span><em>${mm.fmt(u[mm.key])}</em></li>`;
    $('.rank', el).innerHTML = `<h4>${t('c.map.top')}</h4><ol>${ranked.slice(0, 5).map((u, i) => li(u, i + 1)).join('')}</ol>
      <h4>${t('c.map.bot')}</h4><ol>${ranked.slice(-5).reverse().map((u, i) => li(u, ranked.length - i)).join('')}</ol>`;
  }
  function shortMetric(mm, v) {
    if (mm.key === 'gmv100k') return v >= 1e6 ? `${nf(v / 1e6, 1)}${isEN() ? 'M' : 'mi'}` : `${nf(v / 1e3, 0)}${isEN() ? 'K' : 'mil'}`;
    if (mm.key === 'onTime') return `${nf(v * 100, 0)}%`;
    if (mm.key === 'lead') return `${nf(v, 0)}d`;
    return nf(v, 1);
  }

  /* ------------------------------------------------------------------ page 3 */
  function renderP3(root) {
    const rows = filt(D().mensal_regiao), a = aggMonthly(rows), d = D();
    const cats = filt(d.categoria_ano_regiao);
    const itens = sum(cats, 'itens');
    const pays = filt(d.pagamento_ano_regiao), payTot = sum(pays, 'valor'), payOrd = sum(pays, 'pedidos');
    const payG = groupBy(pays, (r) => r.tipo);
    const card$ = payG.get('credit_card') || [];
    const inst = filt(d.parcelas_ano_regiao), instOrd = sum(inst, 'pedidos');
    const decNum = (x) => +String(x.decil_ordem ?? x.decil ?? '').replace(/\D/g, '') || 0;
    const dec = (d.vendedores_decil || []).filter((x) => decNum(x) >= 1 && decNum(x) <= 10).slice().sort((p, q) => decNum(p) - decNum(q)), decTot = sum(dec, 'gmv_real');
    const kg = d.kpis_gabarito || {};
    const repPctRaw = kg.pct_clientes_recompra ?? kg.pct_recompra;
    const rep = d.recompra || (repPctRaw != null || kg.clientes_recompra != null
      ? { pct: repPctRaw > 1 ? repPctRaw / 100 : repPctRaw, recompraram: kg.clientes_recompra, clientes: kg.clientes_unicos_entregues ?? kg.clientes_unicos }
      : null);
    const kpis = [
      { label: t('k.ticketReal'), value: F.moneyFull(a.ticketReal), accent: C.navy, delta: `<span>${F.int(a.pedidos)} ${isEN() ? 'orders' : 'pedidos'}</span>` },
      { label: t('k.items'), value: nf(div(itens, a.pedidos), 2), accent: C.navy, delta: `<span>${F.int(itens)} ${isEN() ? 'items' : 'itens'}</span>` },
      { label: t('k.card'), value: F.pct(div(sum(card$, 'pedidos'), payOrd)), accent: C.navy, delta: `<span>${F.pct(div(sum(card$, 'valor'), payTot))} ${isEN() ? 'of value' : 'do valor'}</span>` },
      { label: t('k.inst'), value: nf(div(sum(inst, (r) => r.parcelas * r.pedidos), instOrd), 1), accent: C.amber, delta: `<span>${isEN() ? 'per order' : 'por pedido'}</span>` },
      { label: t('k.repeat'), value: rep ? F.pct(rep.pct ?? div(rep.recompraram, rep.clientes)) : t('na'), accent: C.teal, delta: rep ? `<span>${F.int(rep.recompraram)} ${isEN() ? 'of' : 'de'} ${F.int(rep.clientes)}</span>` : '' },
      { label: t('k.top10'), value: dec.length ? F.pct(div(dec[0].gmv_real, decTot)) : t('na'), accent: C.coral, delta: dec.length ? `<span>${F.int(dec[0].vendedores)} ${isEN() ? 'sellers' : 'vendedores'}</span>` : '' },
    ];

    // Pareto
    const cg = groupBy(cats, (r) => r.categoria_pt);
    const catTot = sum(cats, 'gmv_real');
    const catList = [...cg.entries()].map(([k, rs]) => ({ key: k, label: prettyCat(catName(rs[0])), value: sum(rs, 'gmv_real'), pedidos: sum(rs, 'pedidos') })).sort((p, q) => q.value - p.value);
    let cum = 0; catList.forEach((c, i) => { cum += c.value; c.cum = cum / catTot; c.rank = i + 1; });
    const n80 = catList.findIndex((c) => c.cum >= 0.8) + 1;
    const top = catList.slice(0, 15);
    const sel = state.categoria !== 'all' ? catList.find((c) => c.key === state.categoria) : null;
    const paretoSub = sel ? `<b style="color:${C.ink}">${t('c.pareto.cat', { c: esc(sel.label), v: F.money(sel.value), r: sel.rank, p: F.pct(sel.value / catTot) })}</b>` : t('c.pareto.s');

    const payItems = [...payG.entries()].map(([k, rs]) => ({
      key: k,
      label: (isEN() ? rs[0]?.tipo_en : rs[0]?.tipo_pt) || payName(k),
      value: div(sum(rs, 'valor'), payTot),
    })).filter((p) => p.value > 0).sort((p, q) => q.value - p.value)
      .map((p, i) => ({ ...p, color: i === 0 ? C.navy : C.navy500 }));
    const ig = groupBy(inst, (r) => Math.min(10, Math.max(1, +r.parcelas || 1)));
    const instItems = [...Array(10)].map((_, i) => { const k = i + 1, v = sum(ig.get(k) || [], 'pedidos'); return { label: k === 10 ? '10+' : `${k}x`, value: v, color: k === 1 ? C.navy : C.navy300, tip: `<div class="t-h">${k === 10 ? '10+' : `${k}x`}</div>${tipRow(t('t.orders'), F.int(v))}${tipRow(t('t.share'), F.pct(div(v, instOrd)))}` }; });
    const pctInst = div(instOrd - sum(ig.get(1) || [], 'pedidos'), instOrd);

    root.innerHTML = `<div class="kpis">${kpis.map(kpiHTML).join('')}</div>
      <div class="grid grid--p3">
        ${card({ area: 'pareto', id: 'c-pareto', title: n80 ? t('c.pareto.t', { n: n80, tot: catList.length }) : '', sub: paretoSub,
    legend: legendHTML([{ color: C.navy, label: t('c.pareto.l1'), cls: 'sq' }, { color: C.amber, label: t('c.pareto.l2') }, { color: C.faint, label: t('c.pareto.l3'), cls: 'dash' }]) })}
        ${card({ area: 'cohort', id: 'c-cohort', title: '', sub: t('c.coh.s') })}
        ${card({ area: 'pay', id: 'c-pay', title: payItems.length ? t('c.pay.t', { m: payItems[0].label, v: F.pct(payItems[0].value, 0) }) : '', sub: t('c.pay.s') })}
        ${card({ area: 'inst', id: 'c-inst', title: pctInst != null ? t('c.inst.t', { v: F.pct(pctInst, 0) }) : '', sub: t('c.inst.s') })}
        ${card({ area: 'sellers', id: 'c-sellers', title: dec.length ? t('c.sel.t', { v: F.pct(div(dec[0].gmv_real, decTot), 0) }) : '', sub: t('c.sel.s') })}
      </div>`;

    columnChart($('#c-pareto'), {
      items: top.map((c) => ({
        label: c.label, value: c.value, color: !sel || sel.key === c.key ? C.navy : C.navy300,
        tip: `<div class="t-h">#${c.rank} ${esc(c.label)}</div>${tipRow(t('k.gmvReal'), F.money(c.value))}${tipRow(t('t.share'), F.pct(c.value / catTot))}${tipRow(t('c.pareto.l2'), F.pct(c.cum))}`,
      })),
      onClick: (c) => { const hit = top.find((x) => x.label === c.label); state.categoria = state.categoria === hit.key ? 'all' : hit.key; syncFilters(); render(); },
      height: 268, rotate: true, labels: false, yFmt: (v) => F.money(v, 0), gap: 0.7, line: { values: top.map((c) => c.cum), color: C.amber, ref: 0.8 },
    });
    hbars($('#c-pay'), { items: payItems, fmt: (v) => F.pct(v), labelWidth: 140 });
    columnChart($('#c-inst'), { items: instItems, height: 132, yAxis: false, yFmt: (v) => F.int(v), labelFmt: (v) => (v >= 1000 ? `${nf(v / 1000, 1)}${isEN() ? 'k' : ' mil'}` : nf(v, 0)), maxBar: 26 });
    columnChart($('#c-sellers'), {
      items: dec.map((x, i) => {
        const lbl = `D${decNum(x)}`;
        return { label: lbl, value: div(x.gmv_real, decTot), color: i === 0 ? C.coral : C.navy300, tip: `<div class="t-h">${lbl}</div>${tipRow(t('t.share'), F.pct(div(x.gmv_real, decTot)))}${tipRow(isEN() ? 'Sellers' : 'Vendedores', F.int(x.vendedores))}${tipRow(t('k.gmvReal'), F.money(x.gmv_real))}` };
      }),
      height: 224, yAxis: false, yFmt: (v) => F.pct(v, 0), labelFmt: (v) => F.pct(v, v < 0.1 ? 1 : 0), maxBar: 28,
    });
    renderCohort($('#c-cohort'), $('#c-cohort-t'));
  }

  function renderCohort(el, titleEl) {
    const co = (D().coorte || []).filter((c) => c.clientes > 0);
    if (!co.length) return empty(el);
    const nM = Math.max(...co.map((c) => (c.retidos || []).length));
    const rates = co.map((c) => (c.retidos || []).map((v) => div(v, c.clientes)));
    const maxR = Math.max(...rates.flat().filter((v) => v != null)) || 1;
    const m1 = div(sum(co, (c) => (c.retidos || [])[0] || 0), sum(co, 'clientes'));
    titleEl.innerHTML = t('c.coh.t', { v: F.pct(m1, m1 < 0.01 ? 2 : 1) });
    el.innerHTML = `<div class="scroll" style="max-height:310px"><table class="cohort"><thead><tr><th class="row">${t('c.coh.cohort')}</th><th>${t('c.coh.n')}</th>${[...Array(nM)].map((_, i) => `<th>M+${i + 1}</th>`).join('')}</tr></thead><tbody>
      ${co.map((c, ri) => `<tr><th class="row">${fmtMonth(c.coorte)}</th><td class="n">${F.int(c.clientes)}</td>${[...Array(nM)].map((_, i) => {
    const v = rates[ri][i];
    if (v == null) return '<td></td>';
    const k = Math.sqrt(v / maxR), bg = mix('#FFFFFF', C.teal, 0.08 + 0.85 * k), fg = k > 0.62 ? '#fff' : C.ink2;
    return `<td style="background:${bg};color:${fg}" title="${F.int(c.retidos[i])} / ${F.int(c.clientes)}">${F.pct(v, v > 0 && v < 0.01 ? 2 : 1)}</td>`;
  }).join('')}</tr>`).join('')}
    </tbody></table></div>`;
  }

  /* ------------------------------------------------------------------ page 4 */
  function renderP4(root) {
    const q = D().qualidade || {}, ct = q.contagens || {}, rules = (q.regras || []).slice(), gab = q.gabarito || {};
    const raw = ct.pedidos_brutos, valid = ct.pedidos_analisados;
    const anom = ct.total_anomalias ?? ct.registros_com_anomalia ?? sum(rules, 'linhas_afetadas');
    const dup = ct.reviews_duplicadas ?? (rules.find((r) => /dupl/i.test(r.regra) && /review|avalia/i.test(`${r.regra} ${r.tabela}`)) || {}).linhas_afetadas;
    const ok = gab.conferem === true || (gab.conferem != null && gab.consultas != null && gab.conferem === gab.consultas);
    const okNum = gab.conferem === true ? gab.consultas : gab.conferem;
    const kpis = [
      { label: t('k.raw'), value: F.int(raw), accent: C.faint, delta: `<span>${isEN() ? 'Olist orders dataset' : 'base Olist de pedidos'}</span>` },
      { label: t('k.valid'), value: F.int(valid), accent: C.teal, delta: `<span>${F.pct(div(valid, raw))} ${t('d.ofRaw')}</span>` },
      { label: t('k.excl'), value: F.pct(div(raw - valid, raw)), accent: C.amber, delta: `<span>${F.int(raw - valid)} ${isEN() ? 'orders' : 'pedidos'}</span>` },
      { label: t('k.anom'), value: F.int(anom), accent: C.amber, delta: `<span>${rules.length} ${isEN() ? 'rules' : 'regras'}</span>` },
      { label: t('k.dupRev'), value: F.int(dup), accent: C.amber, delta: `<span>order_reviews</span>` },
      { label: t('k.check'), value: gab.consultas != null ? `${ok ? '✓' : '✗'} ${okNum}/${gab.consultas}` : t('na'), accent: ok ? C.teal : C.coral, badge: ok, delta: `<span style="color:${ok ? C.teal : C.coral}">${t('d.checkOk')}</span>` },
    ];
    const sorted = rules.slice().sort((p, q2) => (q2.linhas_afetadas || 0) - (p.linhas_afetadas || 0));
    const maxL = Math.max(1, ...rules.map((r) => r.linhas_afetadas || 0));
    const fontes = D().meta?.fontes || [];
    const fontesRes = D().meta?.fontes_resumo || [];
    const nSources = fontesRes.length || fontes.length;
    const tx = (r, k) => (isEN() && r[`${k}_en`]) ? r[`${k}_en`] : r[k];
    const linToggle = fontesRes.length && fontes.length
      ? `<div class="seg" role="group"><button type="button" data-linview="summary" aria-pressed="${state.linView === 'summary'}">${t('c.lin.vSum')}</button><button type="button" data-linview="all" aria-pressed="${state.linView === 'all'}">${t('c.lin.vAll', { f: fontes.length })}</button></div>`
      : '';

    root.innerHTML = `<div class="kpis">${kpis.map(kpiHTML).join('')}</div>
      <div class="grid grid--p4">
        ${card({ area: 'audit', id: 'c-audit', title: t('c.audit.t', { n: rules.length }), sub: t('c.audit.s') })}
        ${card({ area: 'types', id: 'c-types', title: sorted.length ? t('c.types.t', { r: esc(tx(sorted[0], 'regra')) }) : '', sub: t('c.types.s') })}
        ${card({ area: 'lineage', id: 'c-lin', title: t('c.lin.t', { n: nSources, f: fontes.length }), sub: t('c.lin.s'), extra: linToggle })}
      </div>`;
    $$('button[data-linview]', root).forEach((b) => b.addEventListener('click', () => { state.linView = b.dataset.linview; render(); }));
    const shortTbl = (s) => String(s || '').replace(/^olist_/, '').replace(/_dataset\.csv$/, '.csv');
    const shortLic = (s) => {
      const m = String(s || '');
      if (/CC BY/i.test(m)) return 'CC BY-NC-SA 4.0';
      if (/Banco Central/i.test(m)) return isEN() ? 'BCB Public Data' : 'BCB · Dados Públicos';
      if (/IBGE/i.test(m)) return isEN() ? 'IBGE Public Data' : 'IBGE · Dados Públicos';
      return m.split('(')[0].trim().slice(0, 26);
    };
    $('#c-audit').innerHTML = rules.length ? `<div class="scroll" style="max-height:540px"><table class="tbl tbl--fixed"><thead><tr><th style="width:32%">${t('th.rule')}</th><th class="num" style="width:16%">${t('th.rows')}</th><th class="num" style="width:12%">${t('th.pct')}</th><th style="width:40%">${t('th.action')}</th></tr></thead><tbody>
      ${rules.map((r) => `<tr><td class="strong">${esc(tx(r, 'regra'))}<div style="margin-top:4px"><code title="${esc(r.tabela)}">${esc(shortTbl(r.tabela))}</code></div></td>
        <td class="num"><span class="databar"><i style="width:${((r.linhas_afetadas || 0) / maxL) * 100}%"></i><b>${F.int(r.linhas_afetadas)}</b></span></td>
        <td class="num">${r.pct != null ? F.pctRaw(r.pct, 2) : t('na')}</td><td>${esc(tx(r, 'tratamento'))}</td></tr>`).join('')}
    </tbody></table></div>` : `<div class="empty">${t('empty')}</div>`;
    hbars($('#c-types'), { items: sorted.slice(0, 8).map((r) => ({ label: tx(r, 'regra'), value: r.linhas_afetadas, color: C.amber })), fmt: (v) => F.int(v), labelWidth: 235 });
    const showSum = fontesRes.length && state.linView === 'summary';
    $('#c-lin').innerHTML = showSum
      ? `<div class="scroll"><table class="tbl"><thead><tr><th>${t('th.source')}</th><th class="num">${t('th.files')}</th><th class="num">${t('th.records')}</th><th>${t('th.when')}</th><th>${t('th.license')}</th></tr></thead><tbody>
          ${fontesRes.map((f) => `<tr><td class="strong">${esc(f.fonte)}</td><td class="num">${F.int(f.arquivos)}</td><td class="num">${F.int(f.registros)}</td><td style="white-space:nowrap">${esc(fmtStamp(f.coletado_em))}</td><td><span class="pill pill--ok" title="${esc(f.licenca)}">${esc(shortLic(f.licenca))}</span></td></tr>`).join('')}
        </tbody></table></div>`
      : (fontes.length ? `<div class="scroll" style="max-height:260px"><table class="tbl"><thead><tr><th>${t('th.source')}</th><th>${t('th.endpoint')}</th><th class="num">${t('th.records')}</th><th>${t('th.when')}</th></tr></thead><tbody>
          ${fontes.map((f) => `<tr><td class="strong" style="white-space:nowrap">${esc(f.fonte || f.nome)}<br><span style="font-weight:400;color:${C.muted};font-size:11px">${esc(f.nome)}</span></td><td><code class="url" title="${esc(f.endpoint)}">${esc(f.endpoint)}</code></td><td class="num">${F.int(f.registros)}</td><td style="white-space:nowrap">${esc(fmtStamp(f.coletado_em))}</td></tr>`).join('')}
        </tbody></table></div>` : `<div class="empty">${t('empty')}</div>`);
  }
  function fmtStamp(s) {
    if (!s) return t('na');
    const d = new Date(s); if (isNaN(d)) return s;
    return d.toLocaleString(isEN() ? 'en-US' : 'pt-BR', { dateStyle: 'medium', timeStyle: 'short' });
  }

  /* ------------------------------------------------------------------ chrome */
  const PAGES = { p1: renderP1, p2: renderP2, p3: renderP3, p4: renderP4 };
  function render() {
    if (!state.D) return;
    const p = state.page;
    $$('.page').forEach((s) => { s.hidden = s.id !== p; });
    $$('.tab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.page === p)));
    $('#ph-eyebrow').textContent = t(`${p}.eyebrow`);
    $('#ph-title').textContent = t(`${p}.title`);
    $('#ph-sub').textContent = t(`${p}.sub`);
    document.title = `${t(`${p}.title`)} · ${t('brand.title')}`;
    const catSel = $('#f-categoria');
    catSel.disabled = p !== 'p3';
    catSel.closest('.filter').style.opacity = p === 'p3' ? '' : '.45';
    catSel.title = p === 'p3' ? '' : t('f.catHint');
    $('#f-regiao').disabled = p === 'p4'; $('#f-ano').disabled = p === 'p4';
    $$('#f-regiao, #f-ano').forEach((s) => { s.closest('.filter').style.opacity = p === 'p4' ? '.45' : ''; });
    hideTip();
    PAGES[p]($(`#${p}`));
    writeHash();
  }

  function applyI18n() {
    document.documentElement.lang = isEN() ? 'en' : 'pt-BR';
    $$('[data-i18n]').forEach((e) => { e.textContent = t(e.dataset.i18n); });
    $$('.lang button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)));
    const m = D()?.meta || {};
    $('#foot-sources').textContent = t('foot.sources');
    $('#foot-meta').textContent = state.D ? t('foot.meta', {
      base: fmtMonth(m.mes_base_ipca, true) || t('na'), gen: fmtStamp(m.gerado_em),
      ini: fmtMonth(m.periodo?.inicio, true) || t('na'), fim: fmtMonth(m.periodo?.fim, true) || t('na'),
    }) : '';
    buildFilters();
  }

  function buildFilters() {
    if (!state.D) return;
    const years = [...new Set((D().mensal_regiao || []).filter((r) => r.pedidos > 0).map(yearOf))].sort();
    const regs = REGIONS.filter((r) => (D().mensal_regiao || []).some((x) => x.regiao === r));
    const cg = groupBy(D().categoria_ano_regiao || [], (r) => r.categoria_pt);
    const cats = [...cg.entries()].map(([k, rs]) => ({ k, label: prettyCat(catName(rs[0])), v: sum(rs, 'gmv_real') })).sort((a, b) => b.v - a.v);
    const opt = (v, l) => `<option value="${esc(v)}">${esc(l)}</option>`;
    $('#f-ano').innerHTML = opt('all', t('f.all')) + years.map((y) => opt(y, y)).join('');
    $('#f-regiao').innerHTML = opt('all', t('f.allf')) + regs.map((r) => opt(r, regionName(r))).join('');
    $('#f-categoria').innerHTML = opt('all', t('f.allf')) + cats.map((c) => opt(c.k, c.label)).join('');
    syncFilters();
  }
  function syncFilters() {
    const set = (id, v) => { const s = $(id); if (![...s.options].some((o) => o.value === v)) v = 'all'; s.value = v; s.classList.toggle('is-active', v !== 'all'); return v; };
    state.ano = set('#f-ano', state.ano); state.regiao = set('#f-regiao', state.regiao); state.categoria = set('#f-categoria', state.categoria);
    $('#f-reset').hidden = state.ano === 'all' && state.regiao === 'all' && state.categoria === 'all';
  }

  function readHash() {
    const [p, qs] = location.hash.replace(/^#/, '').split('?');
    if (PAGES[p]) state.page = p;
    const q = new URLSearchParams(qs || '');
    ['ano', 'regiao', 'categoria'].forEach((k) => { if (q.get(k)) state[k] = q.get(k); });
    const sp = new URLSearchParams(location.search);
    const lang = sp.get('lang') || q.get('lang') || localStorage.getItem('painel.lang');
    if (lang === 'en' || lang === 'pt') state.lang = lang;
  }
  function writeHash() {
    const q = new URLSearchParams();
    ['ano', 'regiao', 'categoria'].forEach((k) => { if (state[k] !== 'all') q.set(k, state[k]); });
    const h = `#${state.page}${q.toString() ? `?${q}` : ''}`;
    if (location.hash !== h) history.replaceState(null, '', h);
  }

  function bind() {
    $$('.tab').forEach((b) => b.addEventListener('click', () => { state.page = b.dataset.page; render(); window.scrollTo({ top: 0, behavior: 'smooth' }); }));
    $('.tabs').addEventListener('keydown', (e) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
      const ids = Object.keys(PAGES), i = ids.indexOf(state.page) + (e.key === 'ArrowRight' ? 1 : -1);
      state.page = ids[(i + ids.length) % ids.length]; render(); $(`#tab-${state.page}`).focus();
    });
    $$('.lang button').forEach((b) => b.addEventListener('click', () => { state.lang = b.dataset.lang; try { localStorage.setItem('painel.lang', state.lang); } catch (e) { /* private mode */ } applyI18n(); render(); }));
    $('#f-ano').addEventListener('change', (e) => { state.ano = e.target.value; syncFilters(); render(); });
    $('#f-regiao').addEventListener('change', (e) => { state.regiao = e.target.value; syncFilters(); render(); });
    $('#f-categoria').addEventListener('change', (e) => { state.categoria = e.target.value; syncFilters(); render(); });
    $('#f-reset').addEventListener('click', () => { state.ano = state.regiao = state.categoria = 'all'; syncFilters(); render(); });
    let rt; let lastW = innerWidth;
    addEventListener('resize', () => { if (innerWidth === lastW) return; lastW = innerWidth; clearTimeout(rt); rt = setTimeout(render, 160); });
    addEventListener('hashchange', () => { readHash(); syncFilters(); render(); });
  }

  async function boot() {
    readHash(); bind();
    $$('[data-i18n]').forEach((e) => { e.textContent = t(e.dataset.i18n); });
    try {
      const res = await fetch('dados/resumo.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.D = normalize(await res.json());
      $('#status').hidden = true;
      applyI18n(); render();
    } catch (err) {
      const s = $('#status'); s.className = 'error'; s.innerHTML = t('status.error');
      console.warn('[painel] resumo.json indisponível:', err.message);
    }
  }

  /** Adapter: tolerate minor naming differences in resumo.json. */
  function normalize(raw) {
    const d = { ...raw };
    d.meta = d.meta || {};
    ['mensal_regiao', 'macro_mensal', 'uf_ano', 'faixa_atraso', 'categoria_ano_regiao', 'pagamento_ano_regiao', 'parcelas_ano_regiao', 'coorte', 'vendedores_decil']
      .forEach((k) => { if (!Array.isArray(d[k])) d[k] = []; });
    d.macro_mensal = d.macro_mensal.map((r) => ({
      ...r,
      ipca_12m_pct: r.ipca_12m_pct ?? r.ipca_acum_12m_pct,
    }));
    const ords = d.faixa_atraso.map((r) => +r.ordem).filter((n) => isFinite(n));
    const shift = ords.length && Math.min(...ords) === 1 ? -1 : 0;
    d.faixa_atraso = d.faixa_atraso
      .map((r) => ({ ...r, ordem: +r.ordem + shift }))
      .filter((r) => r.ordem >= 0 && r.ordem <= 4);
    if (d.qualidade && Array.isArray(d.qualidade.regras)) {
      d.qualidade = {
        ...d.qualidade,
        regras: d.qualidade.regras.map((r) => ({
          ...r,
          tabela: r.tabela ?? r.tabela_origem,
          pct: r.pct ?? r.pct_base,
        })),
      };
    }
    return d;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
