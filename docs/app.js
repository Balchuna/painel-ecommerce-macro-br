/* Painel E-Commerce e Macroeconomia Brasil · Padrão BI
   Sem dependências externas e sem hex escrito à mão: cores vêm de marca/tokens.css.
   Carrega dados/resumo.js (funciona em file://) com fallback para fetch('dados/resumo.json'). */
(() => {
  "use strict";

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const raiz = document.documentElement;
  const MENOS = "\u2212";
  const NBSP = "\u00A0";

  const REGIOES = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"];
  const REGIAO_EN = {
    Sudeste: "Southeast",
    Sul: "South",
    Nordeste: "Northeast",
    "Centro-Oeste": "Center-West",
    Norte: "North",
  };
  const REGRA_CURTA = {
    Q01_PEDIDOS_NAO_ENTREGUES: ["Não entregues", "Undelivered"],
    Q05_PEDIDOS_SEM_ITENS: ["Sem itens", "No order items"],
    Q07_PEDIDOS_SEM_AVALIACAO: ["Sem avaliação", "No review score"],
    Q09_PRODUTOS_SEM_CATEGORIA: ["Sem categoria", "Missing category"],
    Q08_AVALIACOES_DUPLICADAS: ["Avaliações dup.", "Duplicate reviews"],
    Q11_FRETE_OUTLIER_EXTREMO: ["Frete extremo", "Extreme freight"],
    Q04_SEM_DATA_APROVACAO: ["Sem aprovação", "No approval date"],
    Q13_MESES_CAUDA_PARCIAL: ["Cauda parcial", "Partial tail months"],
  };
  const PAG_NOME = {
    credit_card: ["Cartão de crédito", "Credit card"],
    boleto: ["Boleto", "Bank slip (boleto)"],
    voucher: ["Voucher", "Voucher"],
    debit_card: ["Cartão de débito", "Debit card"],
    not_defined: ["Não definido", "Not defined"],
  };
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

  const MESES = {
    pt: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  };
  const MESES_LONGOS = {
    pt: ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  };

  const I18N = {
    pt: {
      "brand.title": "Painel E-Commerce · Brasil",
      "tab.p1": "Visão executiva",
      "tab.p2": "Logística e SLA",
      "tab.p3": "Comercial e coorte",
      "tab.p4": "Qualidade e linhagem",
      "theme.light": "Claro",
      "theme.dark": "Escuro",
      "f.todos": "Todos",
      "f.brasil": "Brasil",
      "f.categoria": "Categoria",
      "f.todasCat": "Todas as categorias",
      "f.reset": "Limpar",
      "status.loading": "Carregando dados do painel…",
      "status.errTitle": "Os dados do painel não carregaram",
      "status.errBody": "Falta <code>dados/resumo.js</code> ou <code>dados/resumo.json</code>. Gere os arquivos com <code>python scripts/exportar_web_json.py</code> e <code>python marca/gerar.py --acento azul --dados docs/dados/resumo.json --saida-dados docs/dados</code> e recarregue a página.",
      "foot.source": "Fonte: Olist (CC BY-NC-SA 4.0), IBGE e BCB/SGS. Valores reais em R$ de {base}, deflacionados pelo IPCA. Só pedidos entregues com data válida.",
      "foot.updated": "Rafael Balchuna · dados atualizados em {data}",
      "foot.repo": "Código, SQL e Power BI no GitHub",
      "dica.rolagem": "Deslize a tabela para o lado para ver todas as colunas.",
      "vazio": "Sem pedidos entregues para esta seleção.",
      "semBase": "sem base",
      "estavel": "estável",
      "p1.title": "Visão executiva",
      "p1.subBase": "E-commerce Olist cruzado com IPCA, IBGE e BCB · variações de {atual} sobre {base}",
      "p1.subAno": "E-commerce Olist cruzado com IPCA, IBGE e BCB · recorte de {ano}",
      "p2.title": "Logística e SLA",
      "p2.subBase": "Pedidos entregues · atraso após estimativa do checkout · Δ {atual} sobre {base}",
      "p2.subAno": "Pedidos entregues · atraso após estimativa do checkout · recorte de {ano}",
      "p3.title": "Comercial e coorte",
      "p3.sub": "Categorias, pagamentos, coorte e vendedores",
      "p4.title": "Qualidade e linhagem",
      "p4.sub": "Auditoria das anomalias reais na base Olist, tratamento aplicado e conferência contra o gabarito SQL",
      "k.gmvReal": "GMV real (IPCA)",
      "k.gmvNom": "GMV nominal",
      "k.pedidos": "Pedidos entregues",
      "k.noPrazo": "Entregas no prazo",
      "k.nota": "Nota média (1 a 5)",
      "k.prazo": "Prazo médio",
      "k.notaAtraso": "Nota com atraso",
      "k.frete": "Frete sobre GMV",
      "k.ticket": "Ticket médio real",
      "k.cartao": "Pedidos no cartão",
      "k.recompra": "Clientes que recompram",
      "k.top10": "Top 10% vendedores",
      "k.brutos": "Pedidos brutos",
      "k.analisados": "Pedidos analisados",
      "k.anomalias": "Registros com anomalia",
      "k.gabarito": "Gabarito SQL",
      "m.gmv100k": "GMV/100 mil hab.",
      "m.onTime": "No prazo",
      "m.lead": "Prazo médio",
      "m.rating": "Nota",
      "map.mapa": "Mapa",
      "map.tabela": "Tabela 27 UFs",
      "map.top": "Melhores 5",
      "map.bot": "Piores 5",
      "pag.meios": "Meios",
      "pag.parcelas": "Parcelas",
      "lin.resumo": "Resumo ({n})",
      "lin.arquivos": "Arquivos ({n})",
      "faixa.0": "No prazo",
      "faixa.1": "1–3 dias",
      "faixa.2": "4–7 dias",
      "faixa.3": "8–14 dias",
      "faixa.4": "15+ dias",
    },
    en: {
      "brand.title": "Brazil E-Commerce · Dashboard",
      "tab.p1": "Executive view",
      "tab.p2": "Logistics and SLA",
      "tab.p3": "Commercial and cohorts",
      "tab.p4": "Quality and lineage",
      "theme.light": "Light",
      "theme.dark": "Dark",
      "f.todos": "All",
      "f.brasil": "Brazil",
      "f.categoria": "Category",
      "f.todasCat": "All categories",
      "f.reset": "Clear",
      "status.loading": "Loading dashboard data…",
      "status.errTitle": "Dashboard data failed to load",
      "status.errBody": "Missing <code>dados/resumo.js</code> or <code>dados/resumo.json</code>. Generate them with <code>python scripts/exportar_web_json.py</code> and <code>python marca/gerar.py --acento azul --dados docs/dados/resumo.json --saida-dados docs/dados</code> and reload.",
      "foot.source": "Sources: Olist (CC BY-NC-SA 4.0), IBGE and BCB/SGS. Real values in {base} BRL deflated by IPCA. Delivered orders with valid dates only.",
      "foot.updated": "Rafael Balchuna · data updated on {data}",
      "foot.repo": "Code, SQL and Power BI on GitHub",
      "dica.rolagem": "Swipe the table sideways to see all columns.",
      "vazio": "No delivered orders for this selection.",
      "semBase": "no base",
      "estavel": "flat",
      "p1.title": "Executive view",
      "p1.subBase": "Olist e-commerce joined with IPCA, IBGE and BCB · changes compare {atual} vs {base}",
      "p1.subAno": "Olist e-commerce joined with IPCA, IBGE and BCB · {ano} slice",
      "p2.title": "Logistics and SLA",
      "p2.subBase": "Delivered orders · delay past checkout estimate · Δ {atual} vs {base}",
      "p2.subAno": "Delivered orders · delay past checkout estimate · {ano} slice",
      "p3.title": "Commercial and cohorts",
      "p3.sub": "Categories, payments, cohorts and sellers",
      "p4.title": "Quality and lineage",
      "p4.sub": "Real Olist data anomalies, applied treatments and SQL answer-key verification",
      "k.gmvReal": "Real GMV (IPCA)",
      "k.gmvNom": "Nominal GMV",
      "k.pedidos": "Delivered orders",
      "k.noPrazo": "On-time deliveries",
      "k.nota": "Avg. score (1 to 5)",
      "k.prazo": "Avg. lead time",
      "k.notaAtraso": "Score when late",
      "k.frete": "Freight / GMV",
      "k.ticket": "Real avg. ticket",
      "k.cartao": "Orders by card",
      "k.recompra": "Repeat customers",
      "k.top10": "Top 10% sellers",
      "k.brutos": "Raw orders",
      "k.analisados": "Analysed orders",
      "k.anomalias": "Anomaly records",
      "k.gabarito": "SQL answer key",
      "m.gmv100k": "GMV/100k pop.",
      "m.onTime": "On time",
      "m.lead": "Lead time",
      "m.rating": "Score",
      "map.mapa": "Map",
      "map.tabela": "27-state table",
      "map.top": "Top 5",
      "map.bot": "Bottom 5",
      "pag.meios": "Methods",
      "pag.parcelas": "Installments",
      "lin.resumo": "Summary ({n})",
      "lin.arquivos": "Files ({n})",
      "faixa.0": "On time",
      "faixa.1": "1–3 days",
      "faixa.2": "4–7 days",
      "faixa.3": "8–14 days",
      "faixa.4": "15+ days",
    },
  };

  const state = {
    lang: "pt",
    page: "p1",
    ano: "all",
    regiao: null,
    categoria: "all",
    mapMetric: "gmv100k",
    mapView: "map",
    pagView: "meios",
    linView: "summary",
    D: null,
  };

  const isEN = () => state.lang === "en";
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const limparTexto = (s) => String(s ?? "").replace(/\s*\u2014\s*/g, " · ").replace(/!/g, "");
  const t = (k, vars) => {
    let s = I18N[state.lang][k] ?? I18N.pt[k] ?? k;
    if (vars) for (const [a, b] of Object.entries(vars)) s = s.split(`{${a}}`).join(b);
    return s;
  };
  const ler = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
  const gravar = (k, v) => { try { localStorage.setItem(k, v); } catch { /* privado */ } };

  /* ---------- Formatação numérica (pt-BR e en-US, NBSP em R$ e unidades) ---------- */
  const nfCache = {};
  function num(v, d = 0) {
    if (v == null || !isFinite(v)) return "–";
    const loc = isEN() ? "en-US" : "pt-BR";
    const key = `${loc}:${d}`;
    nfCache[key] ??= new Intl.NumberFormat(loc, { minimumFractionDigits: d, maximumFractionDigits: d });
    return nfCache[key].format(v).replace("-", MENOS);
  }
  const fmt = {
    int: (v) => num(v, 0),
    dec: (v, d = 1) => num(v, d),
    brl: (v, d = 2) => {
      if (v == null || !isFinite(v)) return "–";
      const a = Math.abs(v);
      if (a >= 1e9) return `R$${NBSP}${num(v / 1e9, d)}${isEN() ? "B" : `${NBSP}bi`}`;
      if (a >= 1e6) return `R$${NBSP}${num(v / 1e6, d)}${isEN() ? "M" : `${NBSP}mi`}`;
      if (a >= 1e3) return `R$${NBSP}${num(v / 1e3, 1)}${isEN() ? "K" : `${NBSP}mil`}`;
      return `R$${NBSP}${num(v, 0)}`;
    },
    brlCurto: (v) => {
      if (v == null || !isFinite(v)) return "–";
      const a = Math.abs(v);
      if (a >= 1e6) return `R$${NBSP}${num(v / 1e6, 1)}${isEN() ? "M" : `${NBSP}mi`}`;
      if (a >= 1e3) return `R$${NBSP}${num(v / 1e3, 0)}${isEN() ? "K" : `${NBSP}mil`}`;
      return `R$${NBSP}${num(v, 0)}`;
    },
    reais: (v) => (v == null || !isFinite(v) ? "–" : `R$${NBSP}${num(v, 2)}`),
    pct: (v, d = 1) => (v == null || !isFinite(v) ? "–" : `${num(v, d)}%`),
    dias: (v, d = 1) => (v == null || !isFinite(v) ? "–" : `${num(v, d)}${NBSP}${isEN() ? "days" : "dias"}`),
    diasCurto: (v, d = 1) => (v == null || !isFinite(v) ? "–" : `${num(v, d)}${NBSP}d`),
    sinal: (v, d = 1, suf = "%") => {
      if (v == null || !isFinite(v)) return t("semBase");
      const sig = v > 0 ? "+" : v < 0 ? MENOS : "";
      return `${sig}${num(Math.abs(v), d)}${suf}`;
    },
    mes: (am) => {
      if (!am) return "";
      const m = +am.slice(5, 7) - 1;
      return isEN() ? `${MESES.en[m]} ${am.slice(2, 4)}` : `${MESES.pt[m]}/${am.slice(2, 4)}`;
    },
    mesAno: (am) => {
      if (!am) return "";
      const m = +am.slice(5, 7) - 1;
      return isEN() ? `${MESES.en[m]} ${am.slice(0, 4)}` : `${MESES.pt[m]}/${am.slice(0, 4)}`;
    },
    mesLongo: (am) => {
      if (!am) return "";
      const m = +am.slice(5, 7) - 1;
      return isEN() ? `${MESES_LONGOS.en[m]} ${am.slice(0, 4)}` : `${MESES_LONGOS.pt[m]} de ${am.slice(0, 4)}`;
    },
    stamp: (s) => {
      if (!s) return "–";
      const d = new Date(s);
      if (isNaN(d)) return limparTexto(s);
      return d.toLocaleDateString(isEN() ? "en-US" : "pt-BR");
    },
  };

  const nomeRegiao = (r) => (isEN() ? (REGIAO_EN[r] || r) : r);
  const nomePag = (k, row) => {
    if (isEN() && row?.tipo_en) return limparTexto(row.tipo_en);
    if (!isEN() && row?.tipo_pt) return limparTexto(row.tipo_pt);
    return PAG_NOME[k] ? PAG_NOME[k][isEN() ? 1 : 0] : String(k).replace(/_/g, " ");
  };
  const bonitoCat = (s) => {
    const str = limparTexto(String(s || "").replace(/_/g, " "));
    return str ? str.charAt(0).toUpperCase() + str.slice(1) : "–";
  };
  const nomeCat = (r) => bonitoCat(isEN() ? (r.categoria_en || r.categoria_pt) : (r.categoria_pt || r.categoria_en));

  /* ---------- Tema ---------- */
  function aplicarTema(tema) {
    raiz.dataset.theme = tema;
    $$("[data-tema]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tema === tema)));
  }

  /* ---------- Agregação de dados ---------- */
  const D = () => state.D;
  const anoDe = (r) => String(r.ano ?? String(r.ano_mes || "").slice(0, 4));
  const okAno = (r) => state.ano === "all" || anoDe(r) === state.ano;
  const okReg = (r) => !state.regiao || r.regiao === state.regiao;
  const filtrar = (arr, { ano = true, reg = true } = {}) =>
    (arr || []).filter((r) => (!ano || okAno(r)) && (!reg || okReg(r)));
  const somar = (arr, f) => arr.reduce((acc, r) => acc + (+(typeof f === "function" ? f(r) : r[f]) || 0), 0);
  const agrupar = (arr, f) => arr.reduce((m, r) => { const k = f(r); (m.get(k) || m.set(k, []).get(k)).push(r); return m; }, new Map());

  const CAMPOS = [
    "pedidos", "gmv_nominal", "gmv_real", "frete", "entregues_com_data",
    "no_prazo", "soma_dias_entrega", "n_atrasados", "soma_dias_atraso", "soma_nota", "n_nota",
  ];
  function agregarMensal(rows) {
    const s = Object.fromEntries(CAMPOS.map((k) => [k, 0]));
    for (const r of rows) {
      for (const k of CAMPOS) {
        if (k === "entregues_com_data") s[k] += +(r.entregues_com_data ?? r.entregues ?? 0);
        else s[k] += +(r[k] || 0);
      }
    }
    return {
      pedidos: s.pedidos,
      gmvNom: s.gmv_nominal,
      gmv: s.gmv_real,
      frete: s.frete,
      ticket: s.pedidos ? s.gmv_real / s.pedidos : NaN,
      prazo: s.entregues_com_data ? (100 * s.no_prazo) / s.entregues_com_data : NaN,
      dias: s.entregues_com_data ? s.soma_dias_entrega / s.entregues_com_data : NaN,
      atrasoMedio: s.n_atrasados ? s.soma_dias_atraso / s.n_atrasados : NaN,
      nota: s.n_nota ? s.soma_nota / s.n_nota : NaN,
      fretePct: s.gmv_nominal ? (100 * s.frete) / s.gmv_nominal : NaN,
    };
  }

  function contextoPeriodo() {
    const fim = D().meta?.periodo?.entregues_fim || "2018-08";
    const anoMax = +fim.slice(0, 4);
    const mm = fim.slice(5, 7);
    const janAtual = [`${anoMax}-01`, fim];
    const janBase = [`${anoMax - 1}-01`, `${anoMax - 1}-${mm}`];
    const mArr = MESES[state.lang];
    const rotAtual = isEN() ? `${mArr[0]}–${mArr[+mm - 1]} ${anoMax}` : `${mArr[0]}–${mArr[+mm - 1]}/${anoMax}`;
    const rotBase = isEN() ? `${mArr[0]}–${mArr[+mm - 1]} ${anoMax - 1}` : `${mArr[0]}–${mArr[+mm - 1]}/${anoMax - 1}`;
    return { fim, anoMax, mm, janAtual, janBase, rotAtual, rotBase };
  }

  function faixaJanela([i, f], reg = state.regiao) {
    return agregarMensal(D().mensal_regiao.filter((r) => r.ano_mes >= i && r.ano_mes <= f && (!reg || r.regiao === reg)));
  }

  function comparacaoYoY(reg = state.regiao) {
    const ctx = contextoPeriodo();
    if (state.ano === "2016" || state.ano === "2017") {
      return { disponivel: false, ...ctx };
    }
    const cur = faixaJanela(ctx.janAtual, reg);
    const prev = faixaJanela(ctx.janBase, reg);
    return { disponivel: prev.pedidos >= 50 && cur.pedidos > 0, cur, prev, ...ctx };
  }

  function serieMensalAtiva(reg = state.regiao) {
    const ctx = contextoPeriodo();
    const meses = [];
    if (state.ano === "all") {
      for (let a = ctx.anoMax - 1, m = 1; a < ctx.anoMax || m <= +ctx.mm; ) {
        meses.push(`${a}-${String(m).padStart(2, "0")}`);
        if (++m > 12) { m = 1; a++; }
      }
    } else {
      const rows = D().mensal_regiao.filter((r) => anoDe(r) === state.ano && r.pedidos > 0);
      const unicos = [...new Set(rows.map((r) => r.ano_mes))].sort();
      meses.push(...unicos);
    }
    const porMes = agrupar(D().mensal_regiao.filter((r) => !reg || r.regiao === reg), (r) => r.ano_mes);
    return meses.map((am) => ({ am, ...agregarMensal(porMes.get(am) || []) }));
  }

  function porRegiaoAtivo() {
    const baseRows = filtrar(D().mensal_regiao, { reg: false });
    const g = agrupar(baseRows, (r) => r.regiao);
    return REGIOES.map((reg) => ({ reg, ...agregarMensal(g.get(reg) || []) }));
  }

  function faixasAtraso() {
    const raw = filtrar(D().faixa_atraso).filter((r) => +r.ordem >= 0 && +r.ordem <= 4);
    const g = agrupar(raw, (r) => +r.ordem);
    return [0, 1, 2, 3, 4].map((o) => {
      const rs = g.get(o) || [];
      const nNota = somar(rs, "n_nota");
      const somaNota = somar(rs, "soma_nota");
      const n5 = somar(rs, "notas_5");
      const n1 = somar(rs, "notas_1");
      return {
        ordem: o,
        label: t(`faixa.${o}`),
        pedidos: somar(rs, "pedidos"),
        nNota,
        nota: nNota ? somaNota / nNota : NaN,
        pct5: nNota ? (100 * n5) / nNota : NaN,
        pct1: nNota ? (100 * n1) / nNota : NaN,
      };
    });
  }

  function ufStats() {
    const g = agrupar(filtrar(D().uf_ano, { reg: false }), (r) => r.uf);
    return [...g.entries()].map(([uf, rs]) => {
      const pop = rs[0].populacao;
      const gmv = somar(rs, "gmv_real");
      const ent = somar(rs, (r) => r.entregues_com_data ?? r.entregues);
      const nNota = somar(rs, "n_nota");
      return {
        uf,
        nome: rs[0].nome,
        regiao: rs[0].regiao,
        pop,
        pedidos: somar(rs, "pedidos"),
        gmv,
        gmv100k: pop ? (gmv / pop) * 1e5 : NaN,
        onTime: ent ? (100 * somar(rs, "no_prazo")) / ent : NaN,
        lead: ent ? somar(rs, "soma_dias_entrega") / ent : NaN,
        rating: nNota ? somar(rs, "soma_nota") / nNota : NaN,
      };
    });
  }

  /* ---------- Primitivas SVG e Dica (tooltip) ---------- */
  const dicaEl = $("#dica");
  function mostrarDica(html, x, y) {
    dicaEl.innerHTML = html;
    const w = dicaEl.offsetWidth || 180;
    const h = dicaEl.offsetHeight || 60;
    dicaEl.style.left = `${Math.min(Math.max(8, x + 14), innerWidth - w - 8)}px`;
    dicaEl.style.top = `${y - h - 12 < 8 ? y + 16 : y - h - 12}px`;
    dicaEl.classList.add("visivel");
  }
  const esconderDica = () => dicaEl.classList.remove("visivel");
  const par = (k, v) => `<span class="par">${esc(k)} <b>${esc(v)}</b></span>`;
  const setaSvg = (v) => (!isFinite(v) || Math.abs(v) < 1e-9 ? ""
    : `<svg class="seta" width="8" height="8" viewBox="0 0 8 8" aria-hidden="true"><path d="${v > 0 ? "M4 1 7.5 7H.5Z" : "M4 7 .5 1h7Z"}"/></svg>`);
  const checkSvg = (ok) => (ok
    ? `<svg class="icone-check" width="18" height="18" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 6.5 12 13 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    : `<svg class="icone-check ruim" width="18" height="18" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`);
  const tom = (v, bomSeSobe = true) => (!isFinite(v) || Math.abs(v) < 1e-9 ? "neutro" : (v > 0) === bomSeSobe ? "bom" : "ruim");
  const vazio = (alvo, msg = t("vazio")) => { alvo.innerHTML = `<div class="estado">${esc(msg)}</div>`; };

  function escala(max, n = 4) {
    const safeMax = max > 0 && isFinite(max) ? max : 1;
    const bruto = safeMax / n;
    const p = 10 ** Math.floor(Math.log10(bruto));
    const passo = [1, 2, 2.5, 5, 10].map((k) => k * p).find((s) => s >= bruto) || p;
    const ticks = [];
    for (let v = 0; v <= Math.ceil(safeMax / passo) * passo + 1e-9; v += passo) ticks.push(+v.toFixed(6));
    return { t: ticks, passo, topo: ticks[ticks.length - 1] };
  }
  const casas = (passo) => (Number.isInteger(passo) ? 0 : Number.isInteger(passo * 10) ? 1 : 2);
  function barraH(x0, y, w, h, r = 4) {
    const rw = Math.max(0, w);
    if (rw <= 0) return "";
    r = Math.max(0, Math.min(r, rw, h / 2));
    return `M${x0},${y}H${x0 + rw - r}a${r},${r} 0 0 1 ${r},${r}V${y + h - r}a${r},${r} 0 0 1 ${-r},${r}H${x0}Z`;
  }
  function barraV(x, yTop, w, yBase, r = 4) {
    const bh = Math.max(0, yBase - yTop);
    if (bh <= 0) return "";
    r = Math.max(0, Math.min(r, bh, w / 2));
    return `M${x},${yBase}V${yTop + r}a${r},${r} 0 0 1 ${r},${-r}H${x + w - r}a${r},${r} 0 0 1 ${r},${r}V${yBase}Z`;
  }
  function truncar(str, maxC) {
    const s = String(str || "");
    return s.length > maxC ? `${s.slice(0, maxC - 1)}…` : s;
  }

  function sparkSvg(vals, corteIdx) {
    const ok = vals.filter(isFinite);
    if (ok.length < 2) return "";
    const lo = Math.min(...ok), hi = Math.max(...ok), W = 96, H = 24;
    const x = (i) => (vals.length <= 1 ? W / 2 : (i * W) / (vals.length - 1));
    const y = (v) => H - 2 - ((v - lo) / (hi - lo || 1)) * (H - 4);
    const caminho = (i0, i1) => {
      let d = "", pen = false;
      for (let i = Math.max(0, i0); i <= Math.min(vals.length - 1, i1); i++) {
        if (!isFinite(vals[i])) { pen = false; continue; }
        d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(vals[i]).toFixed(1)}`;
        pen = true;
      }
      return d;
    };
    const ult = vals.length - 1;
    let body = "";
    if (corteIdx > 0 && corteIdx < vals.length) {
      body += `<path class="serie serie-fora" d="${caminho(0, corteIdx)}"/>`;
      body += `<path class="serie" d="${caminho(corteIdx, ult)}"/>`;
    } else {
      body += `<path class="serie" d="${caminho(0, ult)}"/>`;
    }
    if (isFinite(vals[ult])) body += `<circle class="ponto" cx="${x(ult).toFixed(1)}" cy="${y(vals[ult]).toFixed(1)}" r="4"/>`;
    return `<svg class="kpi-spark" viewBox="0 0 ${W} ${H}" aria-hidden="true">${body}</svg>`;
  }

  function renderKpis(el, items) {
    el.innerHTML = items.map((k) => {
      const rightBottom = k.delta !== undefined
        ? `<p class="kpi-delta ${k.tom || "neutro"}"${k.title ? ` title="${esc(k.title)}"` : ""}>${k.seta ? setaSvg(k.deltaVal) : ""}${esc(k.delta)}</p>`
        : `<p class="kpi-nota">${esc(k.nota || "")}</p>`;
      return `<article class="kpi${k.spark ? "" : " sem-spark"}" aria-label="${esc(`${k.rot}: ${k.ariaVal ?? k.val}`)}">
        <p class="kpi-rotulo" title="${esc(k.rot)}">${esc(k.rot)}</p>
        <p class="kpi-valor">${k.valHtml ?? esc(k.val)}</p>
        ${k.spark || ""}
        ${rightBottom}
      </article>`;
    }).join("");
  }

  /* ---------- Gráficos reutilizáveis (SVG + CSS tokens) ---------- */
  function desenharBarrasH(box, opts) {
    const W = box.clientWidth, H = box.clientHeight;
    const dados = opts.dados;
    if (!dados.length || !dados.some((d) => isFinite(opts.valor(d)) && opts.valor(d) > 0) || W < 60 || H < 40) {
      return vazio(box);
    }
    const estreito = W < 380;
    const lPad = estreito ? Math.min(opts.l || 92, 114) : (opts.l || 92);
    const rotFn = estreito && opts.rotuloEstreito ? opts.rotuloEstreito : opts.rotulo;
    const rPad = estreito ? (opts.rEstreito ?? Math.min(opts.r || 68, 72)) : (opts.r || 68);
    const maxChars = Math.max(10, Math.floor((lPad - 8) / 6.5));
    const m = { t: opts.extra ? 18 : 2, r: rPad, l: lPad, b: 2 };
    const iw = Math.max(30, W - m.l - m.r);
    const banda = (H - m.t - m.b) / dados.length;
    const h = Math.min(20, Math.max(8, banda * 0.56));
    const maxVal = Math.max(...dados.map((d) => opts.valor(d) || 0), opts.ref || 0) || 1;
    const x = (v) => (Math.max(0, v) / maxVal) * iw;
    const rx = opts.ref != null && isFinite(opts.ref) ? m.l + x(opts.ref) : -1;

    let svg = dados.map((d, i) => {
      const y0 = m.t + i * banda;
      const yb = y0 + (banda - h) / 2;
      const w = x(opts.valor(d) || 0);
      const apagada = opts.apagada ? opts.apagada(d, i) : false;
      const clsBar = opts.classeBarra ? opts.classeBarra(d, i) : "barra";
      const txt = rotFn(d);
      let lx = m.l + w + 6;
      if (rx > 0 && lx < rx && lx + txt.length * 6.8 > rx - 4) lx = rx + 6;
      const inter = Boolean(opts.onClick);
      const labelTxt = truncar(opts.nome(d), maxChars);
      return `<g class="barra-g${inter ? " interativa" : ""}${apagada ? " apagada" : ""}" data-idx="${i}" tabindex="0" ${inter ? `role="button" aria-pressed="${Boolean(opts.ativo && opts.ativo(d))}"` : 'role="listitem"'} aria-label="${esc(`${opts.nome(d)}: ${opts.rotulo(d)}`)}">
        <rect class="alvo" x="0" y="${(y0 + 1).toFixed(1)}" width="${W}" height="${Math.max(4, banda - 2).toFixed(1)}" rx="4"/>
        <text class="rot-forte" x="0" y="${(yb + h / 2 + 4).toFixed(1)}">${esc(labelTxt)}</text>
        <path class="${clsBar}" d="${barraH(m.l, yb, w, h)}"/>
        <text class="rot" x="${lx.toFixed(1)}" y="${(yb + h / 2 + 4).toFixed(1)}">${esc(txt)}</text>
      </g>`;
    }).join("");

    const extra = opts.extra ? opts.extra.replace(/\{x:([\d.]+)\}/g, (_, v) => (m.l + x(+v)).toFixed(1)) : "";
    svg = extra + svg + `<line class="base" x1="${m.l}" x2="${m.l}" y1="${m.t}" y2="${H - m.b}"/>`;
    const sr = opts.srCaption ? `<div class="sr-only"><table><caption>${esc(opts.srCaption)}</caption><thead><tr><th scope="col">${esc(opts.srCol1 || "Item")}</th><th scope="col">${esc(opts.srCol2 || "Valor")}</th></tr></thead><tbody>${dados.map((d) => `<tr><th scope="row">${esc(opts.nome(d))}</th><td>${esc(opts.rotulo(d))}</td></tr>`).join("")}</tbody></table></div>` : "";
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${svg}</svg>${sr}`;

    box.querySelectorAll(".barra-g").forEach((g) => {
      const d = dados[+g.dataset.idx];
      if (opts.onClick) {
        g.addEventListener("click", () => opts.onClick(d));
        g.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); opts.onClick(d); }
        });
      }
      g.addEventListener("pointermove", (ev) => mostrarDica(opts.dica(d), ev.clientX, ev.clientY));
      g.addEventListener("pointerleave", esconderDica);
      g.addEventListener("focus", () => {
        const r = g.getBoundingClientRect();
        mostrarDica(opts.dica(d), r.left + r.width / 2, r.top);
      });
      g.addEventListener("blur", esconderDica);
    });
  }

  function desenharColunas(box, opts) {
    const W = box.clientWidth, H = box.clientHeight;
    const dados = opts.dados;
    if (!dados.length || W < 60 || H < 50) return vazio(box);
    const hasSub = Boolean(opts.sub);
    const m = { t: 20, r: 8, b: hasSub ? 36 : 22, l: opts.semEixoY ? 4 : 34 };
    const iw = Math.max(40, W - m.l - m.r);
    const ih = Math.max(30, H - m.t - m.b);
    const yBase = m.t + ih;
    const sc = opts.yMax != null
      ? { t: opts.yTicks || escala(opts.yMax).t, topo: opts.yMax }
      : escala(Math.max(...dados.map((d) => opts.valor(d) || 0)), 4);
    const y = (v) => yBase - (Math.max(0, v) / (sc.topo || 1)) * ih;
    const banda = iw / dados.length;
    const bw = Math.min(24, Math.max(10, banda * 0.56));

    let svg = "";
    if (!opts.semEixoY) {
      svg += sc.t.map((v, i) => `<line class="${i ? "grade" : "base"}" x1="${m.l}" x2="${W - m.r}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"/>`
        + (i === 0 ? "" : `<text class="eixo" x="${m.l - 6}" y="${(y(v) + 4).toFixed(1)}" text-anchor="end">${esc(opts.yFmt ? opts.yFmt(v) : num(v, 0))}</text>`)).join("");
    } else {
      svg += `<line class="base" x1="${m.l}" x2="${W - m.r}" y1="${yBase.toFixed(1)}" y2="${yBase.toFixed(1)}"/>`;
    }

    svg += dados.map((d, i) => {
      const val = opts.valor(d);
      const cx = m.l + banda * i + banda / 2;
      const top = isFinite(val) ? y(val) : yBase;
      const clsBar = opts.classeBarra ? opts.classeBarra(d, i) : "barra";
      const clsLbl = opts.destaque && opts.destaque(d, i) ? "rot-forte" : "rot";
      const rotVal = isFinite(val) ? opts.rotulo(d) : "–";
      const subTxt = hasSub && opts.sub(d) ? `<text class="eixo-nota" x="${cx.toFixed(1)}" y="${(yBase + 30).toFixed(1)}" text-anchor="middle">${esc(opts.sub(d))}</text>` : "";
      return `<g class="barra-g" data-idx="${i}" tabindex="0" role="listitem" aria-label="${esc(`${opts.nome(d)}: ${rotVal}`)}">
        <rect class="alvo" x="${(m.l + banda * i + 1).toFixed(1)}" y="${m.t}" width="${Math.max(4, banda - 2).toFixed(1)}" height="${(ih + 4).toFixed(1)}" rx="4"/>
        <path class="${clsBar}" d="${barraV(cx - bw / 2, top, bw, yBase)}"/>
        <text class="${clsLbl}" x="${cx.toFixed(1)}" y="${(top - 6).toFixed(1)}" text-anchor="middle">${esc(rotVal)}</text>
        <text class="eixo" x="${cx.toFixed(1)}" y="${(yBase + 16).toFixed(1)}" text-anchor="middle">${esc(opts.nome(d))}</text>
        ${subTxt}
      </g>`;
    }).join("");

    const sr = opts.srCaption ? `<div class="sr-only"><table><caption>${esc(opts.srCaption)}</caption><thead><tr><th scope="col">${esc(opts.srCol1 || "Item")}</th><th scope="col">${esc(opts.srCol2 || "Valor")}</th></tr></thead><tbody>${dados.map((d) => `<tr><th scope="row">${esc(opts.nome(d))}</th><td>${esc(isFinite(opts.valor(d)) ? opts.rotulo(d) : "–")}</td></tr>`).join("")}</tbody></table></div>` : "";
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${svg}</svg>${sr}`;

    box.querySelectorAll(".barra-g").forEach((g) => {
      const d = dados[+g.dataset.idx];
      g.addEventListener("pointermove", (ev) => mostrarDica(opts.dica(d), ev.clientX, ev.clientY));
      g.addEventListener("pointerleave", esconderDica);
      g.addEventListener("focus", () => {
        const r = g.getBoundingClientRect();
        mostrarDica(opts.dica(d), r.left + r.width / 2, r.top);
      });
      g.addEventListener("blur", esconderDica);
    });
  }

  /* ---------- PÁGINA 01: Visão executiva ---------- */
  function renderP1(root) {
    const scoped = filtrar(D().mensal_regiao);
    const a = agregarMensal(scoped);
    const cmp = comparacaoYoY(state.regiao);
    const serie = serieMensalAtiva(state.regiao);
    const corteIdx = state.ano === "all" ? serie.findIndex((p) => p.am === `${cmp.anoMax}-01`) : -1;

    const kpiDef = [
      {
        rot: t("k.gmvReal"), val: fmt.brl(a.gmv),
        dVal: cmp.disponivel ? 100 * (cmp.cur.gmv / cmp.prev.gmv - 1) : NaN,
        dFmt: (v) => fmt.sinal(v, 1, "%"), s: (p) => p.gmv,
      },
      {
        rot: t("k.pedidos"), val: fmt.int(a.pedidos),
        dVal: cmp.disponivel ? 100 * (cmp.cur.pedidos / cmp.prev.pedidos - 1) : NaN,
        dFmt: (v) => fmt.sinal(v, 1, "%"), s: (p) => p.pedidos,
      },
      {
        rot: t("k.noPrazo"), val: fmt.pct(a.prazo),
        dVal: cmp.disponivel ? cmp.cur.prazo - cmp.prev.prazo : NaN,
        dFmt: (v) => fmt.sinal(v, 1, `${NBSP}p.p.`), s: (p) => p.prazo,
      },
      {
        rot: t("k.nota"), val: fmt.dec(a.nota, 2),
        dVal: cmp.disponivel ? cmp.cur.nota - cmp.prev.nota : NaN,
        dFmt: (v) => fmt.sinal(v, 2, ""), s: (p) => p.nota,
      },
    ];

    root.innerHTML = `
      <section class="kpis" aria-label="${esc(isEN() ? "Key indicators" : "Indicadores principais")}" id="p1-kpis"></section>
      <section class="cartao col-8-a" aria-labelledby="t-p1-linha">
        <h2 id="t-p1-linha"></h2>
        <p class="sub" id="s-p1-linha"></p>
        <div class="plot" id="plot-p1-linha"></div>
      </section>
      <section class="cartao col-4-a" aria-labelledby="t-p1-regiao">
        <h2 id="t-p1-regiao"></h2>
        <p class="sub" id="s-p1-regiao"></p>
        <div class="plot" id="plot-p1-regiao"></div>
      </section>
      <section class="cartao col-6-b2" aria-labelledby="t-p1-macro">
        <h2 id="t-p1-macro"></h2>
        <p class="sub" id="s-p1-macro"></p>
        <div class="legenda" id="leg-p1-macro"></div>
        <div class="plot" id="plot-p1-macro"></div>
      </section>
      <section class="cartao col-6-b1 resp-cheia" aria-labelledby="t-p1-tabela">
        <h2 id="t-p1-tabela"></h2>
        <p class="sub" id="s-p1-tabela"></p>
        <div class="rolagem" id="p1-tabela" role="region" aria-labelledby="t-p1-tabela" tabindex="0"></div>
        <p class="dica-rolagem">${esc(t("dica.rolagem"))}</p>
      </section>`;

    renderKpis($("#p1-kpis", root), kpiDef.map((k) => ({
      rot: k.rot,
      val: k.val,
      spark: sparkSvg(serie.map(k.s), corteIdx),
      delta: isFinite(k.dVal) ? k.dFmt(k.dVal) : t("semBase"),
      deltaVal: k.dVal,
      seta: isFinite(k.dVal),
      tom: tom(k.dVal, true),
      title: cmp.disponivel ? `${cmp.rotAtual} vs ${cmp.rotBase}` : "",
    })));

    desenharP1Graficos(root, serie, cmp, corteIdx);
    desenharP1Tabela(root, cmp);
  }

  function desenharP1Graficos(root, serie, cmp, corteIdx) {
    // 1. Linha mensal de GMV real (atualiza títulos ANTES de medir clientWidth/clientHeight)
    const boxL = $("#plot-p1-linha", root);
    const baseMes = fmt.mesAno(D().meta?.mes_base_ipca || "2018-10");
    const dGmv = cmp.disponivel ? 100 * (cmp.cur.gmv / cmp.prev.gmv - 1) : NaN;
    if (isFinite(dGmv)) {
      if (isEN()) {
        const who = state.regiao ? `In ${nomeRegiao(state.regiao)}, real GMV` : "Real GMV";
        $("#t-p1-linha", root).textContent = `${who} ${dGmv >= 0 ? "grew" : "fell"} ${fmt.dec(Math.abs(dGmv))}% in ${cmp.rotAtual} vs ${cmp.rotBase}`;
      } else {
        const quem = state.regiao ? `No ${state.regiao}, o` : "O";
        $("#t-p1-linha", root).textContent = `${quem} GMV real ${dGmv >= 0 ? "cresceu" : "caiu"} ${fmt.dec(Math.abs(dGmv))}% em ${cmp.rotAtual} sobre ${cmp.rotBase}`;
      }
    } else {
      const tot = somar(serie, "gmv");
      $("#t-p1-linha", root).textContent = isEN()
        ? `Real GMV totaled ${fmt.brl(tot)} in ${state.ano}`
        : `GMV real somou ${fmt.brl(tot)} em ${state.ano}`;
    }
    const cinzaNota = state.ano === "all"
      ? (isEN() ? `; ${cmp.anoMax - 1} in gray` : `; ${cmp.anoMax - 1} em cinza`)
      : "";
    $("#s-p1-linha", root).textContent = serie.length
      ? (isEN()
        ? `R$ millions per month, at ${baseMes} prices (IPCA) · ${fmt.mes(serie[0].am)} to ${fmt.mes(serie[serie.length - 1].am)}${cinzaNota}`
        : `R$ milhões por mês, a preços de ${baseMes} (IPCA) · ${fmt.mes(serie[0].am)} a ${fmt.mes(serie[serie.length - 1].am)}${cinzaNota}`)
      : "";

    const W = boxL.clientWidth, H = boxL.clientHeight;
    if (!serie.some((p) => p.gmv > 0) || W < 60 || H < 50) {
      vazio(boxL);
    } else {
      const m = { t: 22, r: 82, b: 22, l: 2 };
      const iw = Math.max(40, W - m.l - m.r), ih = Math.max(30, H - m.t - m.b), n = serie.length;
      const maxMi = Math.max(...serie.map((p) => p.gmv)) / 1e6;
      const { t: ticks, passo, topo } = escala(maxMi);
      const x = (i) => m.l + (n <= 1 ? iw / 2 : (i * iw) / (n - 1));
      const y = (v) => m.t + ih - ((v / 1e6) / (topo || 1)) * ih;
      const dc = casas(passo);

      let svg = ticks.map((v, i) => `<line class="${i ? "grade" : "base"}" x1="${m.l}" x2="${W - m.r}" y1="${y(v * 1e6).toFixed(1)}" y2="${y(v * 1e6).toFixed(1)}"/>`
        + (i === 0 ? "" : `<text class="eixo" x="${m.l}" y="${(y(v * 1e6) - 5).toFixed(1)}">${i === ticks.length - 1 ? `R$${NBSP}${num(v, dc)}${isEN() ? "M" : `${NBSP}mi`}` : num(v, dc)}</text>`)).join("");

      const cada = n <= 6 ? 1 : (3 * iw) / (n - 1) < 48 ? 6 : 3;
      const mArr = MESES[state.lang];
      svg += serie.map((p, i) => {
        const mesN = +p.am.slice(5);
        if (n > 6 && (mesN - 1) % cada !== 0) return "";
        const txt = mesN === 1 || i === 0 ? fmt.mes(p.am) : mArr[mesN - 1];
        return `<text class="eixo" x="${x(i).toFixed(1)}" y="${H - 4}" text-anchor="${i === 0 ? "start" : "middle"}">${txt}</text>`;
      }).join("");

      const trecho = (i0, i1) => serie.slice(i0, i1 + 1).map((p, j) => `${j ? "L" : "M"}${x(i0 + j).toFixed(1)},${y(p.gmv).toFixed(1)}`).join("");
      if (corteIdx > 0 && corteIdx < n) {
        svg += `<path class="serie serie-fora" d="${trecho(0, corteIdx)}"/><path class="serie" d="${trecho(corteIdx, n - 1)}"/>`;
      } else {
        svg += `<path class="serie" d="${trecho(0, n - 1)}"/>`;
      }

      const iPico = serie.reduce((b, p, i) => (p.gmv > serie[b].gmv ? i : b), 0);
      const ult = n - 1;
      if (iPico !== ult) {
        const p = serie[iPico];
        const bf = +p.am.slice(5) === 11 ? " · Black Friday" : "";
        const anc = x(iPico) > W - m.r - 96 ? "end" : x(iPico) < 96 ? "start" : "middle";
        const picoTxt = isEN() ? `Peak ${fmt.mes(p.am)}: ${fmt.brl(p.gmv)}${bf}` : `Pico em ${fmt.mes(p.am)}: ${fmt.brl(p.gmv)}${bf}`;
        svg += `<circle class="ponto${corteIdx > 0 && iPico < corteIdx ? " ponto-fora" : ""}" cx="${x(iPico).toFixed(1)}" cy="${y(p.gmv).toFixed(1)}" r="4"/>`
          + `<text class="rot" x="${x(iPico).toFixed(1)}" y="${Math.max(12, y(p.gmv) - 10).toFixed(1)}" text-anchor="${anc}">${esc(picoTxt)}</text>`;
      }
      const pu = serie[ult];
      svg += `<circle class="ponto" cx="${x(ult).toFixed(1)}" cy="${y(pu.gmv).toFixed(1)}" r="4"/>`
        + `<text class="rot-fraco" x="${(x(ult) + 10).toFixed(1)}" y="${(y(pu.gmv) - 4).toFixed(1)}">${esc(fmt.mes(pu.am))}</text>`
        + `<text class="rot-forte" x="${(x(ult) + 10).toFixed(1)}" y="${(y(pu.gmv) + 12).toFixed(1)}">${esc(fmt.brl(pu.gmv))}</text>`;
      svg += `<line class="mira" id="mira-gmv" x1="0" x2="0" y1="${m.t}" y2="${(m.t + ih).toFixed(1)}" visibility="hidden"/>`
        + `<circle class="ponto" id="pt-gmv" r="4" visibility="hidden"/>`
        + `<rect x="${m.l}" y="0" width="${iw}" height="${H}" fill="transparent"/>`;

      const tituloL = $("#t-p1-linha", root).textContent;
      boxL.innerHTML = `<svg viewBox="0 0 ${W} ${H}" tabindex="0" role="img" aria-label="${esc(tituloL)}">${svg}</svg>`
        + `<div class="sr-only"><table><caption>${esc(tituloL)}</caption><thead><tr><th scope="col">${isEN() ? "Month" : "Mês"}</th><th scope="col">${esc(t("k.gmvReal"))}</th><th scope="col">${esc(t("k.gmvNom"))}</th><th scope="col">${esc(t("k.pedidos"))}</th></tr></thead><tbody>`
        + serie.map((p) => `<tr><th scope="row">${esc(fmt.mesLongo(p.am))}</th><td>${esc(fmt.brl(p.gmv))}</td><td>${esc(fmt.brl(p.gmvNom))}</td><td>${esc(fmt.int(p.pedidos))}</td></tr>`).join("")
        + `</tbody></table></div>`;

      const elSvg = boxL.querySelector("svg"), mira = elSvg.querySelector("#mira-gmv"), pt = elSvg.querySelector("#pt-gmv");
      let atualI = ult;
      const marcar = (i, cx, cy) => {
        atualI = i = Math.max(0, Math.min(n - 1, i));
        const p = serie[i], X = x(i), Y = y(p.gmv);
        mira.setAttribute("x1", X); mira.setAttribute("x2", X); mira.setAttribute("visibility", "visible");
        pt.setAttribute("cx", X); pt.setAttribute("cy", Y); pt.setAttribute("visibility", "visible");
        pt.classList.toggle("ponto-fora", corteIdx > 0 && i < corteIdx);
        const r = elSvg.getBoundingClientRect();
        mostrarDica(
          `<strong>${esc(fmt.mesLongo(p.am))}</strong>${par(t("k.gmvReal"), fmt.brl(p.gmv))}${par(t("k.gmvNom"), fmt.brl(p.gmvNom))}${par(t("k.pedidos"), fmt.int(p.pedidos))}${par(t("k.noPrazo"), fmt.pct(p.prazo))}`,
          cx ?? r.left + (X / W) * r.width,
          cy ?? r.top + (Y / H) * r.height
        );
      };
      const limpar = () => { mira.setAttribute("visibility", "hidden"); pt.setAttribute("visibility", "hidden"); esconderDica(); };
      elSvg.addEventListener("pointermove", (ev) => {
        const r = elSvg.getBoundingClientRect(), px = ((ev.clientX - r.left) / r.width) * W;
        const idx = n <= 1 ? 0 : Math.round(((px - m.l) / iw) * (n - 1));
        marcar(idx, ev.clientX, ev.clientY);
      });
      elSvg.addEventListener("pointerleave", limpar);
      elSvg.addEventListener("blur", limpar);
      elSvg.addEventListener("focus", () => marcar(atualI));
      elSvg.addEventListener("keydown", (ev) => {
        if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") { ev.preventDefault(); marcar(atualI + (ev.key === "ArrowRight" ? 1 : -1)); }
        else if (ev.key === "Escape") limpar();
      });
    }

    // 2. GMV real por região (barras horizontais com destaque cruzado)
    const regs = porRegiaoAtivo().filter((d) => d.gmv > 0).sort((x1, x2) => x2.gmv - x1.gmv);
    const totReg = somar(regs, "gmv") || 1;
    const alvo = (state.regiao ? regs.find((d) => d.reg === state.regiao) : regs[0]) || regs[0];
    if (alvo) {
      $("#t-p1-regiao", root).textContent = isEN()
        ? `${nomeRegiao(alvo.reg)} accounts for ${fmt.pct((100 * alvo.gmv) / totReg)} of real GMV`
        : `${alvo.reg} responde por ${fmt.pct((100 * alvo.gmv) / totReg)} do GMV real`;
    }
    $("#s-p1-regiao", root).textContent = isEN()
      ? `R$ millions · click a bar to highlight`
      : `R$ milhões · clique numa barra para destacar`;

    desenharBarrasH($("#plot-p1-regiao", root), {
      dados: regs,
      l: 90,
      r: 56,
      nome: (d) => nomeRegiao(d.reg),
      valor: (d) => d.gmv,
      rotulo: (d) => (d.gmv >= 1e5 ? num(d.gmv / 1e6, 2) : `${num(d.gmv / 1e3, 1)}${isEN() ? "K" : `${NBSP}mil`}`),
      apagada: (d) => Boolean(state.regiao && d.reg !== state.regiao),
      ativo: (d) => d.reg === state.regiao,
      onClick: (d) => escolherRegiao(d.reg === state.regiao ? null : d.reg),
      dica: (d) => `<strong>${esc(nomeRegiao(d.reg))}</strong>${par(t("k.gmvReal"), fmt.brl(d.gmv))}${par(isEN() ? "Share" : "Participação", fmt.pct((100 * d.gmv) / totReg))}${par(t("k.pedidos"), fmt.int(d.pedidos))}${par(t("k.ticket"), fmt.reais(d.ticket))}`,
      srCaption: $("#t-p1-regiao", root).textContent,
      srCol1: isEN() ? "Region" : "Região",
      srCol2: t("k.gmvReal"),
    });

    // 3. Macro: Selic e IPCA 12m (eixo Y único em %, sem eixo duplo!)
    desenharP1Macro(root, serie);
  }

  function desenharP1Macro(root, serie) {
    const box = $("#plot-p1-macro", root);
    let macro = (D().macro_mensal || []).filter((r) => okAno(r));
    if (serie.length) {
      const i0 = serie[0].am, i1 = serie[serie.length - 1].am;
      const recortado = macro.filter((r) => r.ano_mes >= i0 && r.ano_mes <= i1);
      if (recortado.length >= 2) macro = recortado;
    }
    const comSelic = macro.filter((r) => r.selic_media != null && isFinite(r.selic_media));
    const comIpca = macro.filter((r) => r.ipca_12m_pct != null && isFinite(r.ipca_12m_pct));

    if (comSelic.length >= 2) {
      const s0 = comSelic[0].selic_media, s1 = comSelic[comSelic.length - 1].selic_media;
      const ipcaFim = comIpca.length ? comIpca[comIpca.length - 1].ipca_12m_pct : NaN;
      if (isEN()) {
        const verbo = Math.abs(s1 - s0) < 0.05 ? `stayed at ${fmt.pct(s1, 2)}` : `${s1 < s0 ? "fell" : "rose"} from ${fmt.pct(s0, 2)} to ${fmt.pct(s1, 2)}`;
        $("#t-p1-macro", root).textContent = `Selic ${verbo} while 12m IPCA reached ${fmt.pct(ipcaFim, 2)}`;
      } else {
        const verbo = Math.abs(s1 - s0) < 0.05 ? `ficou em ${fmt.pct(s1, 2)}` : `${s1 < s0 ? "caiu" : "subiu"} de ${fmt.pct(s0, 2)} para ${fmt.pct(s1, 2)}`;
        $("#t-p1-macro", root).textContent = `Selic ${verbo} com IPCA 12m em ${fmt.pct(ipcaFim, 2)}`;
      }
    } else {
      $("#t-p1-macro", root).textContent = isEN() ? "Selic policy rate and 12-month IPCA" : "Selic meta e IPCA acumulado em 12 meses";
    }

    const bm = D().meta?.benchmark_macro_atual;
    let refTxt = "";
    if (Array.isArray(bm)) {
      const sel = bm.find((b) => b.indicador === "selic_meta_aa")?.valor_recente;
      const ipc = bm.find((b) => b.indicador === "ipca_12m_pct")?.valor_recente;
      if (sel != null && ipc != null) {
        refTxt = isEN()
          ? ` · BCB ref.: Selic ${fmt.pct(sel, 2)}, IPCA ${fmt.pct(ipc, 2)}`
          : ` · ref. BCB: Selic ${fmt.pct(sel, 2)}, IPCA ${fmt.pct(ipc, 2)}`;
      }
    }
    $("#s-p1-macro", root).textContent = (isEN() ? "Rate in % (Selic p.a. and 12m IPCA) · BCB/SGS 432 and 433" : "Taxa em % (Selic a.a. e IPCA 12m) · BCB/SGS 432 e 433") + refTxt;
    $("#leg-p1-macro", root).innerHTML = `<span class="legenda-item"><i class="legenda-traco"></i>${isEN() ? "Selic (% p.a.)" : "Selic (% a.a.)"}</span>`
      + `<span class="legenda-item"><i class="legenda-traco s2"></i>${isEN() ? "IPCA 12m (%)" : "IPCA 12m (%)"}</span>`;

    // Medir SOMENTE depois de inserir título, subtítulo e legenda!
    const W = box.clientWidth, H = box.clientHeight;
    if (macro.length < 2 || W < 60 || H < 50) return vazio(box);
    const m = { t: 14, r: 54, b: 22, l: 2 };
    const iw = Math.max(40, W - m.l - m.r), ih = Math.max(30, H - m.t - m.b), n = macro.length;
    const maxV = Math.max(...macro.flatMap((r) => [r.selic_media || 0, r.ipca_12m_pct || 0]));
    const { t: ticks, topo } = escala(maxV, 3);
    const x = (i) => m.l + (n <= 1 ? iw / 2 : (i * iw) / (n - 1));
    const y = (v) => m.t + ih - (v / (topo || 1)) * ih;

    let svg = ticks.map((v, i) => `<line class="${i ? "grade" : "base"}" x1="${m.l}" x2="${W - m.r}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"/>`
      + (i === 0 ? "" : `<text class="eixo" x="${m.l}" y="${(y(v) - 4).toFixed(1)}">${num(v, 0)}%</text>`)).join("");

    const cada = n <= 6 ? 1 : (3 * iw) / (n - 1) < 52 ? 6 : 3;
    const mArr = MESES[state.lang];
    svg += macro.map((r, i) => {
      const mesN = +r.ano_mes.slice(5);
      if (n > 6 && (mesN - 1) % cada !== 0) return "";
      const txt = mesN === 1 || i === 0 ? fmt.mes(r.ano_mes) : mArr[mesN - 1];
      return `<text class="eixo" x="${x(i).toFixed(1)}" y="${H - 4}" text-anchor="${i === 0 ? "start" : "middle"}">${txt}</text>`;
    }).join("");

    const pathOf = (k) => {
      let d = "", pen = false;
      macro.forEach((r, i) => {
        const v = r[k];
        if (v == null || !isFinite(v)) { pen = false; return; }
        d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
        pen = true;
      });
      return d;
    };
    svg += `<path class="serie" d="${pathOf("selic_media")}"/>`;
    svg += `<path class="serie-2" d="${pathOf("ipca_12m_pct")}"/>`;

    const ult = n - 1, u = macro[ult];
    let ySel = y(u.selic_media), yIpc = y(u.ipca_12m_pct);
    if (Math.abs(ySel - yIpc) < 14) {
      if (ySel <= yIpc) { ySel -= 7; yIpc += 7; } else { yIpc -= 7; ySel += 7; }
    }
    svg += `<circle class="ponto" cx="${x(ult).toFixed(1)}" cy="${y(u.selic_media).toFixed(1)}" r="4"/>`
      + `<circle class="ponto-2" cx="${x(ult).toFixed(1)}" cy="${y(u.ipca_12m_pct).toFixed(1)}" r="4"/>`
      + `<text class="rot-forte" x="${(x(ult) + 8).toFixed(1)}" y="${(ySel + 4).toFixed(1)}">${esc(fmt.pct(u.selic_media, 2))}</text>`
      + `<text class="rot" x="${(x(ult) + 8).toFixed(1)}" y="${(yIpc + 4).toFixed(1)}">${esc(fmt.pct(u.ipca_12m_pct, 2))}</text>`;

    svg += `<line class="mira" id="mira-mac" x1="0" x2="0" y1="${m.t}" y2="${(m.t + ih).toFixed(1)}" visibility="hidden"/>`
      + `<circle class="ponto" id="pt-sel" r="4" visibility="hidden"/>`
      + `<circle class="ponto-2" id="pt-ipc" r="4" visibility="hidden"/>`
      + `<rect x="${m.l}" y="0" width="${iw}" height="${H}" fill="transparent"/>`;

    const tituloM = $("#t-p1-macro", root).textContent;
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" tabindex="0" role="img" aria-label="${esc(tituloM)}">${svg}</svg>`
      + `<div class="sr-only"><table><caption>${esc(tituloM)}</caption><thead><tr><th scope="col">${isEN() ? "Month" : "Mês"}</th><th scope="col">Selic</th><th scope="col">IPCA 12m</th><th scope="col">PTAX</th></tr></thead><tbody>`
      + macro.map((r) => `<tr><th scope="row">${esc(fmt.mesLongo(r.ano_mes))}</th><td>${esc(fmt.pct(r.selic_media, 2))}</td><td>${esc(fmt.pct(r.ipca_12m_pct, 2))}</td><td>${esc(fmt.reais(r.ptax_media))}</td></tr>`).join("")
      + `</tbody></table></div>`;

    const elSvg = box.querySelector("svg"), mira = elSvg.querySelector("#mira-mac"), ptS = elSvg.querySelector("#pt-sel"), ptI = elSvg.querySelector("#pt-ipc");
    let atualI = ult;
    const marcar = (i, cx, cy) => {
      atualI = i = Math.max(0, Math.min(n - 1, i));
      const r = macro[i], X = x(i);
      mira.setAttribute("x1", X); mira.setAttribute("x2", X); mira.setAttribute("visibility", "visible");
      ptS.setAttribute("cx", X); ptS.setAttribute("cy", y(r.selic_media)); ptS.setAttribute("visibility", "visible");
      ptI.setAttribute("cx", X); ptI.setAttribute("cy", y(r.ipca_12m_pct)); ptI.setAttribute("visibility", "visible");
      const rect = elSvg.getBoundingClientRect();
      mostrarDica(
        `<strong>${esc(fmt.mesLongo(r.ano_mes))}</strong>${par("Selic (% a.a.)", fmt.pct(r.selic_media, 2))}${par("IPCA 12m", fmt.pct(r.ipca_12m_pct, 2))}${par(isEN() ? "Monthly IPCA" : "IPCA mensal", fmt.pct(r.ipca_mensal_pct, 2))}${par("PTAX (R$/US$)", fmt.reais(r.ptax_media))}`,
        cx ?? rect.left + (X / W) * rect.width,
        cy ?? rect.top + (y(r.selic_media) / H) * rect.height
      );
    };
    const limpar = () => {
      mira.setAttribute("visibility", "hidden");
      ptS.setAttribute("visibility", "hidden");
      ptI.setAttribute("visibility", "hidden");
      esconderDica();
    };
    elSvg.addEventListener("pointermove", (ev) => {
      const rect = elSvg.getBoundingClientRect(), px = ((ev.clientX - rect.left) / rect.width) * W;
      marcar(Math.round(((px - m.l) / iw) * (n - 1)), ev.clientX, ev.clientY);
    });
    elSvg.addEventListener("pointerleave", limpar);
    elSvg.addEventListener("blur", limpar);
    elSvg.addEventListener("focus", () => marcar(atualI));
    elSvg.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") { ev.preventDefault(); marcar(atualI + (ev.key === "ArrowRight" ? 1 : -1)); }
      else if (ev.key === "Escape") limpar();
    });
  }

  function desenharP1Tabela(root, cmp) {
    const dados = porRegiaoAtivo().sort((a, b) => b.gmv - a.gmv);
    const br = agregarMensal(filtrar(D().mensal_regiao, { reg: false }));
    const baseMes = fmt.mesAno(D().meta?.mes_base_ipca || "2018-10");
    $("#t-p1-tabela", root).textContent = isEN() ? "Summary by region" : "Resumo por região";
    $("#s-p1-tabela", root).textContent = cmp.disponivel
      ? (isEN() ? `Values in ${baseMes} BRL · Δ GMV ${cmp.rotAtual} vs ${cmp.rotBase}` : `Valores em R$ de ${baseMes} · Δ GMV de ${cmp.rotAtual} sobre ${cmp.rotBase}`)
      : (isEN() ? `Values in ${baseMes} BRL · ${state.ano}` : `Valores em R$ de ${baseMes} · recorte de ${state.ano}`);

    const celulas = (d, regKey) => {
      const c = comparacaoYoY(regKey);
      const dv = c.disponivel ? 100 * (c.cur.gmv / c.prev.gmv - 1) : NaN;
      return `<td>${fmt.int(d.pedidos)}</td><td>${fmt.brl(d.gmv)}</td>`
        + `<td><span class="delta ${tom(dv)}">${isFinite(dv) ? setaSvg(dv) : ""}${isFinite(dv) ? fmt.sinal(dv) : "–"}</span></td>`
        + `<td>${fmt.reais(d.ticket)}</td><td>${fmt.pct(d.prazo)}</td><td>${fmt.dec(d.nota, 2)}</td>`;
    };
    $("#p1-tabela", root).innerHTML = `<table>
      <thead><tr>
        <th scope="col">${isEN() ? "Region" : "Região"}</th>
        <th scope="col">${isEN() ? "Orders" : "Pedidos"}</th>
        <th scope="col">${isEN() ? "Real GMV" : "GMV real"}</th>
        <th scope="col">Δ GMV</th>
        <th scope="col">${isEN() ? "Real ticket" : "Ticket real"}</th>
        <th scope="col">${isEN() ? "On time" : "No prazo"}</th>
        <th scope="col">${isEN() ? "Score" : "Nota"}</th>
      </tr></thead>
      <tbody>${dados.map((d) => `<tr class="${d.reg === state.regiao ? "ativa" : state.regiao ? "apagada" : ""}">
        <td><button type="button" class="linha-reg" data-regiao="${esc(d.reg)}" aria-pressed="${d.reg === state.regiao}">${esc(nomeRegiao(d.reg))}</button></td>
        ${celulas(d, d.reg)}
      </tr>`).join("")}</tbody>
      <tfoot><tr><td>${t("f.brasil")}</td>${celulas(br, null)}</tr></tfoot>
    </table>`;
  }

  /* ---------- PÁGINA 02: Logística e SLA ---------- */
  const MAPA_METRICAS = {
    gmv100k: { key: "gmv100k", lab: "m.gmv100k", fmt: (v) => fmt.brlCurto(v), melhor: "high" },
    onTime: { key: "onTime", lab: "m.onTime", fmt: (v) => fmt.pct(v), melhor: "high" },
    lead: { key: "lead", lab: "m.lead", fmt: (v) => fmt.dias(v), melhor: "low" },
    rating: { key: "rating", lab: "m.rating", fmt: (v) => fmt.dec(v, 2), melhor: "high" },
  };

  function renderP2(root) {
    const scoped = filtrar(D().mensal_regiao);
    const a = agregarMensal(scoped);
    const cmp = comparacaoYoY(state.regiao);
    const serie = serieMensalAtiva(state.regiao);
    const corteIdx = state.ano === "all" ? serie.findIndex((p) => p.am === `${cmp.anoMax}-01`) : -1;
    const dr = faixasAtraso();
    const nLate = somar(dr.slice(1), "nNota");
    const notaLate = nLate ? somar(dr.slice(1), (x) => (isFinite(x.nota) ? x.nota * x.nNota : 0)) / nLate : NaN;
    const notaOn = dr[0]?.nota;
    const quedaNota = isFinite(notaLate) && isFinite(notaOn) ? notaLate - notaOn : NaN;

    const kpis = [
      {
        rot: t("k.prazo"), val: fmt.dias(a.dias),
        spark: sparkSvg(serie.map((p) => p.dias), corteIdx),
        deltaVal: cmp.disponivel ? cmp.cur.dias - cmp.prev.dias : NaN,
        delta: cmp.disponivel ? fmt.sinal(cmp.cur.dias - cmp.prev.dias, 1, `${NBSP}d`) : t("semBase"),
        seta: cmp.disponivel,
        tom: cmp.disponivel ? tom(cmp.cur.dias - cmp.prev.dias, false) : "neutro",
      },
      {
        rot: t("k.noPrazo"), val: fmt.pct(a.prazo),
        spark: sparkSvg(serie.map((p) => p.prazo), corteIdx),
        deltaVal: cmp.disponivel ? cmp.cur.prazo - cmp.prev.prazo : NaN,
        delta: cmp.disponivel ? fmt.sinal(cmp.cur.prazo - cmp.prev.prazo, 1, `${NBSP}p.p.`) : t("semBase"),
        seta: cmp.disponivel,
        tom: cmp.disponivel ? tom(cmp.cur.prazo - cmp.prev.prazo, true) : "neutro",
      },
      {
        rot: t("k.notaAtraso"), val: fmt.dec(notaLate, 2),
        deltaVal: quedaNota,
        delta: isFinite(quedaNota) ? `${fmt.sinal(quedaNota, 2, "")} ${isEN() ? "vs on time" : "vs prazo"}` : t("semBase"),
        seta: isFinite(quedaNota),
        tom: tom(quedaNota, true),
        title: isFinite(notaOn) ? `${isEN() ? "On time" : "No prazo"}: ${fmt.dec(notaOn, 2)}` : "",
      },
      {
        rot: t("k.frete"), val: fmt.pct(a.fretePct),
        spark: sparkSvg(serie.map((p) => p.fretePct), corteIdx),
        deltaVal: cmp.disponivel ? cmp.cur.fretePct - cmp.prev.fretePct : NaN,
        delta: cmp.disponivel ? fmt.sinal(cmp.cur.fretePct - cmp.prev.fretePct, 1, `${NBSP}p.p.`) : t("semBase"),
        seta: cmp.disponivel,
        tom: cmp.disponivel ? tom(cmp.cur.fretePct - cmp.prev.fretePct, false) : "neutro",
      },
    ];

    const mm = MAPA_METRICAS[state.mapMetric];
    const segMetric = `<div class="seg" role="group" aria-label="${esc(isEN() ? "Map metric" : "Indicador do mapa")}">${Object.values(MAPA_METRICAS).map((m) =>
      `<button type="button" data-metric="${m.key}" aria-pressed="${m.key === state.mapMetric}">${esc(t(m.lab))}</button>`).join("")}</div>`;
    const segView = `<div class="seg" role="group" aria-label="${esc(isEN() ? "View" : "Visualização")}">
      <button type="button" data-mapview="map" aria-pressed="${state.mapView === "map"}">${esc(t("map.mapa"))}</button>
      <button type="button" data-mapview="table" aria-pressed="${state.mapView === "table"}">${esc(t("map.tabela"))}</button>
    </div>`;

    root.innerHTML = `
      <section class="kpis" aria-label="${esc(isEN() ? "Logistics indicators" : "Indicadores de logística")}" id="p2-kpis"></section>
      <section class="cartao col-6-a" aria-labelledby="t-p2-atraso">
        <h2 id="t-p2-atraso"></h2>
        <p class="sub" id="s-p2-atraso"></p>
        <div class="plot" id="plot-p2-atraso"></div>
      </section>
      <section class="cartao col-6-b1" aria-labelledby="t-p2-prazo">
        <h2 id="t-p2-prazo"></h2>
        <p class="sub" id="s-p2-prazo"></p>
        <div class="plot" id="plot-p2-prazo"></div>
      </section>
      <section class="cartao col-6-ab" aria-labelledby="t-p2-mapa">
        <div class="cartao-topo">
          <div class="cartao-titulos">
            <h2 id="t-p2-mapa"></h2>
            <p class="sub" id="s-p2-mapa"></p>
          </div>
        </div>
        <div class="cartao-ctl" style="margin-top:8px">${segMetric}${segView}</div>
        <div class="mapa-area ${mm.melhor === "low" ? "mapa-cor-neg" : "mapa-cor-pos"}" id="plot-p2-mapa"></div>
      </section>`;

    renderKpis($("#p2-kpis", root), kpis);
    $$("button[data-metric]", root).forEach((b) => b.addEventListener("click", () => { state.mapMetric = b.dataset.metric; render(); }));
    $$("button[data-mapview]", root).forEach((b) => b.addEventListener("click", () => { state.mapView = b.dataset.mapview; render(); }));

    desenharP2Graficos(root, dr);
  }

  function desenharP2Graficos(root, dr) {
    // 1. Nota por faixa de atraso (barras verticais, 0 a 5, largura <= 24px)
    const totAval = somar(dr, "nNota") || 1;
    const n0 = dr[0]?.nota, n4 = dr[4]?.nota;
    if (isFinite(n0) && isFinite(n4)) {
      $("#t-p2-atraso", root).textContent = isEN()
        ? `At 15+ days late, the score drops from ${fmt.dec(n0, 2)} to ${fmt.dec(n4, 2)}`
        : `Com 15+ dias de atraso, a nota cai de ${fmt.dec(n0, 2)} para ${fmt.dec(n4, 2)}`;
    } else {
      $("#t-p2-atraso", root).textContent = isEN() ? "Average score by delay bucket" : "Nota média por faixa de atraso";
    }
    $("#s-p2-atraso", root).textContent = isEN()
      ? "Average review score (1 to 5) · below each bar: reviewed orders"
      : "Nota média da avaliação (1 a 5) · abaixo da barra: pedidos avaliados";

    desenharColunas($("#plot-p2-atraso", root), {
      dados: dr,
      yMax: 5,
      yTicks: [0, 1, 2, 3, 4, 5],
      yFmt: (v) => num(v, 0),
      nome: (d) => d.label,
      valor: (d) => d.nota,
      rotulo: (d) => fmt.dec(d.nota, 2),
      sub: (d) => fmt.int(d.nNota),
      classeBarra: (_d, i) => (i === 0 ? "barra" : i === 4 ? "barra-destaque-neg" : "barra-neutra"),
      destaque: (_d, i) => i === 0 || i === 4,
      dica: (d) => `<strong>${esc(d.label)}</strong>${par(t("k.nota"), fmt.dec(d.nota, 2))}${par(isEN() ? "Reviewed" : "Avaliados", fmt.int(d.nNota))}${par(isEN() ? "Share" : "Participação", fmt.pct((100 * d.nNota) / totAval))}${par(isEN() ? "Score 5" : "Nota 5", fmt.pct(d.pct5))}${par(isEN() ? "Score 1" : "Nota 1", fmt.pct(d.pct1))}`,
      srCaption: $("#t-p2-atraso", root).textContent,
      srCol1: isEN() ? "Delay bucket" : "Faixa de atraso",
      srCol2: t("k.nota"),
    });

    // 2. Prazo médio por região com linha de referência Brasil
    const regs = porRegiaoAtivo().filter((d) => isFinite(d.dias)).sort((a, b) => b.dias - a.dias);
    const br = agregarMensal(filtrar(D().mensal_regiao, { reg: false })).dias;
    if (regs.length >= 2) {
      if (state.regiao) {
        const d = regs.find((q) => q.reg === state.regiao);
        if (d) {
          const dif = d.dias - br;
          $("#t-p2-prazo", root).textContent = isEN()
            ? `In ${nomeRegiao(d.reg)}, delivery takes ${fmt.dias(d.dias)}, ${fmt.dec(Math.abs(dif))} ${dif >= 0 ? "above" : "below"} Brazil average`
            : `No ${d.reg}, a entrega leva ${fmt.dias(d.dias)}, ${fmt.dec(Math.abs(dif))} ${dif >= 0 ? "acima" : "abaixo"} da média do Brasil`;
        }
      } else {
        const maior = regs[0], menor = regs[regs.length - 1];
        $("#t-p2-prazo", root).textContent = isEN()
          ? `${nomeRegiao(maior.reg)} waits ${fmt.dec(maior.dias / menor.dias)}× as long as ${nomeRegiao(menor.reg)}`
          : `No ${maior.reg}, a entrega leva ${fmt.dec(maior.dias / menor.dias)} vezes o tempo do ${menor.reg}`;
      }
    }
    $("#s-p2-prazo", root).textContent = isEN()
      ? "Average days from purchase to delivery · vertical line: Brazil · click to highlight"
      : "Dias entre compra e entrega, média · linha vertical: Brasil · clique para destacar";

    const boxP = $("#plot-p2-prazo", root);
    const refSvg = isFinite(br)
      ? `<line class="ref" x1="{x:${br}}" x2="{x:${br}}" y1="14" y2="${boxP.clientHeight}"/>`
        + `<text class="rot" x="{x:${br}}" y="10" text-anchor="middle">${esc(`${t("f.brasil")}: ${fmt.dec(br)}`)}</text>`
      : "";

    desenharBarrasH(boxP, {
      dados: regs,
      l: 90,
      r: 68,
      nome: (d) => nomeRegiao(d.reg),
      valor: (d) => d.dias,
      rotulo: (d) => fmt.dias(d.dias),
      apagada: (d) => Boolean(state.regiao && d.reg !== state.regiao),
      ativo: (d) => d.reg === state.regiao,
      onClick: (d) => escolherRegiao(d.reg === state.regiao ? null : d.reg),
      extra: refSvg,
      ref: br,
      dica: (d) => `<strong>${esc(nomeRegiao(d.reg))}</strong>${par(t("k.prazo"), fmt.dias(d.dias))}${par(isEN() ? "Diff. vs Brazil" : "Diferença do Brasil", fmt.sinal(d.dias - br, 1, `${NBSP}d`))}${par(t("k.noPrazo"), fmt.pct(d.prazo))}${par(t("k.pedidos"), fmt.int(d.pedidos))}`,
      srCaption: $("#t-p2-prazo", root).textContent,
      srCol1: isEN() ? "Region" : "Região",
      srCol2: t("k.prazo"),
    });

    // 3. Mapa / Tabela 27 UFs
    const mm = MAPA_METRICAS[state.mapMetric];
    const ufs = ufStats().filter((u) => isFinite(u[mm.key]));
    const ranked = [...ufs].sort((p, q) => (mm.melhor === "high" ? q[mm.key] - p[mm.key] : p[mm.key] - q[mm.key]));
    if (ranked.length >= 2) {
      const best = ranked[0], worst = ranked[ranked.length - 1];
      $("#t-p2-mapa", root).textContent = isEN()
        ? `${best.uf} leads and ${worst.uf} ranks last · ${t(mm.lab)}`
        : `${best.uf} lidera e ${worst.uf} fica por último · ${t(mm.lab)}`;
    }
    $("#s-p2-mapa", root).textContent = isEN()
      ? "By customer state · IBGE population · click a state to highlight its region"
      : "Por UF do cliente · população IBGE · clique numa UF para destacar a região";

    const boxMap = $("#plot-p2-mapa", root);
    if (!ufs.length) return vazio(boxMap);
    if (state.mapView === "table") {
      boxMap.innerHTML = `<div class="rolagem" role="region" aria-labelledby="t-p2-mapa" tabindex="0"><table>
        <thead><tr>
          <th scope="col">UF</th>
          <th scope="col">${isEN() ? "Region" : "Região"}</th>
          <th scope="col">${isEN() ? "Orders" : "Pedidos"}</th>
          <th scope="col">${esc(t("m.gmv100k"))}</th>
          <th scope="col">${esc(t("m.lead"))}</th>
          <th scope="col">${esc(t("m.onTime"))}</th>
          <th scope="col">${esc(t("m.rating"))}</th>
        </tr></thead>
        <tbody>${ranked.map((u) => `<tr class="${u.regiao === state.regiao ? "ativa" : state.regiao ? "apagada" : ""}">
          <td><button type="button" class="linha-reg" data-regiao="${esc(u.regiao)}" aria-pressed="${u.regiao === state.regiao}">${esc(u.uf)}</button></td>
          <td>${esc(nomeRegiao(u.regiao))}</td>
          <td>${fmt.int(u.pedidos)}</td>
          <td>${fmt.brlCurto(u.gmv100k)}</td>
          <td>${fmt.diasCurto(u.lead)}</td>
          <td>${fmt.pct(u.onTime)}</td>
          <td>${fmt.dec(u.rating, 2)}</td>
        </tr>`).join("")}</tbody>
      </table></div><p class="dica-rolagem">${esc(t("dica.rolagem"))}</p>`;
    } else {
      desenharCartogramaUF(boxMap, ufs, ranked, mm);
    }
  }

  function desenharCartogramaUF(box, ufs, ranked, mm) {
    const vals = ufs.map((u) => u[mm.key]);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const faixaDe = (v) => {
      if (!isFinite(v)) return 0;
      const k = hi === lo ? 0.5 : (v - lo) / (hi - lo);
      return Math.min(5, Math.max(1, Math.floor(k * 4.999) + 1));
    };
    const curto = (v) => {
      if (mm.key === "gmv100k") return v >= 1e6 ? `${num(v / 1e6, 1)}${isEN() ? "M" : "mi"}` : `${num(v / 1e3, 0)}${isEN() ? "K" : "mil"}`;
      if (mm.key === "onTime") return `${num(v, 0)}%`;
      if (mm.key === "lead") return `${num(v, 0)}d`;
      return num(v, 1);
    };

    const byUf = new Map(ufs.map((u) => [u.uf, u]));
    const cell = 43, gap = 3, W = cell * 7 + 4, H = cell * 8 + 4;
    const tilesSvg = Object.entries(TILES).map(([uf, [c, r]]) => {
      const u = byUf.get(uf);
      const q = u ? faixaDe(u[mm.key]) : 0;
      const fora = Boolean(u && state.regiao && u.regiao !== state.regiao);
      const x = 2 + c * cell, y = 2 + r * cell, s = cell - gap;
      return `<g class="tile tile-q${q}${fora ? " apagada" : ""}" data-uf="${uf}" tabindex="${u ? 0 : -1}" role="button" aria-label="${esc(u ? `${u.nome} (${uf}): ${mm.fmt(u[mm.key])}` : uf)}">
        <rect x="${x}" y="${y}" width="${s}" height="${s}" rx="4"/>
        <text x="${(x + s / 2).toFixed(1)}" y="${(y + s / 2 - 2).toFixed(1)}" text-anchor="middle">${uf}</text>
        ${u ? `<text class="tile-sub" x="${(x + s / 2).toFixed(1)}" y="${(y + s / 2 + 11).toFixed(1)}" text-anchor="middle">${esc(curto(u[mm.key]))}</text>` : ""}
      </g>`;
    }).join("");

    const li = (u, pos) => `<li><b>${pos}. ${esc(u.uf)}</b><span>${esc(u.nome)}</span><strong>${esc(mm.fmt(u[mm.key]))}</strong></li>`;
    box.innerHTML = `<div class="mapa-grade">
      <div class="mapa-svg-box">
        <svg viewBox="0 0 ${W} ${H}" style="max-width:${W}px" role="img" aria-label="${esc(isEN() ? "Brazil tile map by state" : "Cartograma do Brasil por UF")}">${tilesSvg}</svg>
        <div class="faixas-legenda">
          <span>${esc(mm.fmt(lo))}</span>
          <div class="faixas-blocos" aria-hidden="true"><span class="q1"></span><span class="q2"></span><span class="q3"></span><span class="q4"></span><span class="q5"></span></div>
          <span>${esc(mm.fmt(hi))}</span>
        </div>
      </div>
      <div class="ranking-uf">
        <h3>${esc(t("map.top"))}</h3>
        <ol>${ranked.slice(0, 5).map((u, i) => li(u, i + 1)).join("")}</ol>
        <h3>${esc(t("map.bot"))}</h3>
        <ol>${ranked.slice(-5).reverse().map((u, i) => li(u, ranked.length - i)).join("")}</ol>
      </div>
    </div>`;

    box.querySelectorAll(".tile[data-uf]").forEach((g) => {
      const u = byUf.get(g.dataset.uf);
      if (!u) return;
      const tipHtml = `<strong>${esc(u.nome)} · ${u.uf}</strong>${par(isEN() ? "Region" : "Região", nomeRegiao(u.regiao))}${par(t("m.gmv100k"), fmt.brlCurto(u.gmv100k))}${par(t("m.onTime"), fmt.pct(u.onTime))}${par(t("m.lead"), fmt.dias(u.lead))}${par(t("m.rating"), fmt.dec(u.rating, 2))}${par(t("k.pedidos"), fmt.int(u.pedidos))}${par(isEN() ? "Population" : "População", fmt.int(u.pop))}`;
      g.addEventListener("pointermove", (ev) => mostrarDica(tipHtml, ev.clientX, ev.clientY));
      g.addEventListener("pointerleave", esconderDica);
      g.addEventListener("focus", () => { const r = g.getBoundingClientRect(); mostrarDica(tipHtml, r.left + r.width / 2, r.top); });
      g.addEventListener("blur", esconderDica);
      g.addEventListener("click", () => escolherRegiao(u.regiao === state.regiao ? null : u.regiao));
      g.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); escolherRegiao(u.regiao === state.regiao ? null : u.regiao); }
      });
    });
  }

  /* ---------- PÁGINA 03: Comercial e coorte ---------- */
  function renderP3(root) {
    const scoped = filtrar(D().mensal_regiao);
    const a = agregarMensal(scoped);
    const cmp = comparacaoYoY(state.regiao);
    const serie = serieMensalAtiva(state.regiao);
    const corteIdx = state.ano === "all" ? serie.findIndex((p) => p.am === `${cmp.anoMax}-01`) : -1;

    const cats = filtrar(D().categoria_ano_regiao);
    const pays = filtrar(D().pagamento_ano_regiao);
    const payTot = somar(pays, "valor") || 1;
    const payOrd = somar(pays, "pedidos") || 1;
    const payG = agrupar(pays, (r) => r.tipo);
    const cardRows = payG.get("credit_card") || [];
    const inst = filtrar(D().parcelas_ano_regiao);
    const instOrd = somar(inst, "pedidos") || 1;
    const mediaParcelas = somar(inst, (r) => r.parcelas * r.pedidos) / instOrd;

    const decNum = (x) => +String(x.ordem ?? x.decil ?? "").replace(/\D/g, "") || 0;
    const dec = (D().vendedores_decil || []).filter((x) => decNum(x) >= 1 && decNum(x) <= 10).slice().sort((p, q) => decNum(p) - decNum(q));
    const decTot = somar(dec, "gmv_real") || 1;

    const kg = D().kpis_gabarito || {};
    const repPct = kg.pct_clientes_recompra ?? 3.0;
    const repCli = kg.clientes_recompra ?? 0;
    const totCli = kg.clientes_unicos_entregues ?? 0;

    const kpis = [
      {
        rot: t("k.ticket"), val: fmt.reais(a.ticket),
        spark: sparkSvg(serie.map((p) => p.ticket), corteIdx),
        deltaVal: cmp.disponivel ? 100 * (cmp.cur.ticket / cmp.prev.ticket - 1) : NaN,
        delta: cmp.disponivel ? fmt.sinal(100 * (cmp.cur.ticket / cmp.prev.ticket - 1), 1, "%") : t("semBase"),
        seta: cmp.disponivel,
        tom: cmp.disponivel ? tom(cmp.cur.ticket - cmp.prev.ticket, true) : "neutro",
      },
      {
        rot: t("k.cartao"), val: fmt.pct((100 * somar(cardRows, "pedidos")) / payOrd),
        nota: isEN() ? `${fmt.dec(mediaParcelas)} avg. installm.` : `${fmt.dec(mediaParcelas)} parcelas médias`,
      },
      {
        rot: t("k.recompra"), val: fmt.pct(repPct),
        nota: `${fmt.int(repCli)} ${isEN() ? "of" : "de"} ${fmt.int(totCli)}`,
      },
      {
        rot: t("k.top10"), val: dec.length ? fmt.pct((100 * dec[0].gmv_real) / decTot) : "–",
        nota: dec.length ? `${fmt.int(dec[0].vendedores)} ${isEN() ? "sellers" : "vendedores"}` : "",
      },
    ];

    const pagToggle = `<div class="seg" role="group" aria-label="${esc(isEN() ? "Payment view" : "Visão de pagamentos")}">
      <button type="button" data-pagview="meios" aria-pressed="${state.pagView === "meios"}">${esc(t("pag.meios"))}</button>
      <button type="button" data-pagview="parcelas" aria-pressed="${state.pagView === "parcelas"}">${esc(t("pag.parcelas"))}</button>
    </div>`;

    root.innerHTML = `
      <section class="kpis" aria-label="${esc(isEN() ? "Commercial indicators" : "Indicadores comerciais")}" id="p3-kpis"></section>
      <section class="cartao col-7-a" aria-labelledby="t-p3-pareto">
        <h2 id="t-p3-pareto"></h2>
        <p class="sub" id="s-p3-pareto"></p>
        <div class="plot" id="plot-p3-pareto"></div>
      </section>
      <section class="cartao col-5-a" aria-labelledby="t-p3-pag">
        <div class="cartao-topo">
          <div class="cartao-titulos">
            <h2 id="t-p3-pag"></h2>
            <p class="sub" id="s-p3-pag"></p>
          </div>
          <div class="cartao-ctl">${pagToggle}</div>
        </div>
        <div class="plot" id="plot-p3-pag"></div>
      </section>
      <section class="cartao col-7-b1" aria-labelledby="t-p3-coorte">
        <h2 id="t-p3-coorte"></h2>
        <p class="sub" id="s-p3-coorte"></p>
        <div class="rolagem" id="p3-coorte" role="region" aria-labelledby="t-p3-coorte" tabindex="0"></div>
        <p class="dica-rolagem">${esc(t("dica.rolagem"))}</p>
      </section>
      <section class="cartao col-5-b2" aria-labelledby="t-p3-vendedores">
        <h2 id="t-p3-vendedores"></h2>
        <p class="sub" id="s-p3-vendedores"></p>
        <div class="plot" id="plot-p3-vendedores"></div>
      </section>`;

    renderKpis($("#p3-kpis", root), kpis);
    $$("button[data-pagview]", root).forEach((b) => b.addEventListener("click", () => { state.pagView = b.dataset.pagview; render(); }));

    desenharP3Graficos(root, cats, payG, payTot, inst, instOrd, dec, decTot, decNum);
    desenharP3Coorte(root);
  }

  function desenharP3Graficos(root, cats, payG, payTot, inst, instOrd, dec, decTot, decNum) {
    // 1. Pareto de categorias (barras horizontais com rótulo direto + % acumulado, ZERO segundo eixo Y!)
    const cg = agrupar(cats, (r) => r.categoria_pt);
    const catTot = somar(cats, "gmv_real") || 1;
    const catList = [...cg.entries()].map(([k, rs]) => ({
      key: k,
      label: nomeCat(rs[0]),
      gmv: somar(rs, "gmv_real"),
      pedidos: somar(rs, "pedidos"),
      itens: somar(rs, "itens"),
    })).sort((p, q) => q.gmv - p.gmv);
    let acum = 0;
    catList.forEach((c, i) => { acum += c.gmv; c.pct = (100 * c.gmv) / catTot; c.cum = (100 * acum) / catTot; c.rank = i + 1; });
    const n80 = catList.findIndex((c) => c.cum >= 80) + 1;
    const sel = state.categoria !== "all" ? catList.find((c) => c.key === state.categoria) : null;
    const top = catList.slice(0, 8);
    if (sel && !top.some((c) => c.key === sel.key)) top[top.length - 1] = sel;

    if (sel) {
      $("#t-p3-pareto", root).textContent = isEN()
        ? `${sel.label}: ${fmt.brl(sel.gmv)} · #${sel.rank} · ${fmt.pct(sel.pct)} of GMV`
        : `${sel.label}: ${fmt.brl(sel.gmv)} · #${sel.rank} · ${fmt.pct(sel.pct)} do GMV`;
    } else if (n80) {
      $("#t-p3-pareto", root).textContent = isEN()
        ? `${n80} of ${catList.length} categories make up 80% of real GMV`
        : `${n80} de ${catList.length} categorias somam 80% do GMV real`;
    }
    $("#s-p3-pareto", root).textContent = isEN()
      ? "Top 8 categories in real GMV (right label: GMV and cumulative %) · click to filter"
      : "Top 8 categorias em GMV real (rótulo: valor e % acumulado) · clique para filtrar";

    desenharBarrasH($("#plot-p3-pareto", root), {
      dados: top,
      l: 164,
      r: 112,
      rEstreito: 64,
      nome: (d) => d.label,
      valor: (d) => d.gmv,
      rotulo: (d) => `${fmt.brlCurto(d.gmv)} (${fmt.pct(d.cum, 0)})`,
      rotuloEstreito: (d) => fmt.brlCurto(d.gmv),
      apagada: (d) => Boolean(sel && d.key !== sel.key),
      ativo: (d) => Boolean(sel && d.key === sel.key),
      onClick: (d) => { state.categoria = state.categoria === d.key ? "all" : d.key; sincronizarFiltros(); render(); },
      dica: (d) => `<strong>#${d.rank} ${esc(d.label)}</strong>${par(t("k.gmvReal"), fmt.brl(d.gmv))}${par(isEN() ? "Share" : "Participação", fmt.pct(d.pct))}${par(isEN() ? "Cumulative %" : "% acumulado", fmt.pct(d.cum))}${par(t("k.pedidos"), fmt.int(d.pedidos))}${par(isEN() ? "Items" : "Itens", fmt.int(d.itens))}`,
      srCaption: $("#t-p3-pareto", root).textContent,
      srCol1: t("f.categoria"),
      srCol2: t("k.gmvReal"),
    });

    // 2. Pagamentos OU Parcelamento (toggle limpo sem espremer gráficos)
    if (state.pagView === "meios") {
      const payItems = [...payG.entries()].map(([k, rs]) => ({
        key: k,
        label: nomePag(k, rs[0]),
        valor: somar(rs, "valor"),
        pedidos: somar(rs, "pedidos"),
        pct: (100 * somar(rs, "valor")) / payTot,
      })).filter((p) => p.valor > 0 && p.pct >= 0.05).sort((p, q) => q.valor - p.valor);

      if (payItems.length) {
        $("#t-p3-pag", root).textContent = isEN()
          ? `${payItems[0].label}: ${fmt.pct(payItems[0].pct, 1)} of paid value`
          : `${payItems[0].label}: ${fmt.pct(payItems[0].pct, 1)} do valor pago`;
      }
      $("#s-p3-pag", root).textContent = isEN()
        ? "Share of total value paid, by main payment method"
        : "Participação no valor total pago, por meio principal";

      desenharBarrasH($("#plot-p3-pag", root), {
        dados: payItems,
        l: 122,
        r: 56,
        nome: (d) => d.label,
        valor: (d) => d.pct,
        rotulo: (d) => fmt.pct(d.pct),
        classeBarra: (_d, i) => (i === 0 ? "barra" : "barra-neutra"),
        dica: (d) => `<strong>${esc(d.label)}</strong>${par(isEN() ? "Share" : "Participação", fmt.pct(d.pct))}${par(isEN() ? "Value paid" : "Valor pago", fmt.brl(d.valor))}${par(t("k.pedidos"), fmt.int(d.pedidos))}`,
        srCaption: $("#t-p3-pag", root).textContent,
        srCol1: isEN() ? "Method" : "Meio",
        srCol2: isEN() ? "Share" : "Participação",
      });
    } else {
      const ig = agrupar(inst, (r) => Math.min(10, Math.max(1, +r.parcelas || 1)));
      const instItems = [...Array(10)].map((_, i) => {
        const k = i + 1;
        const v = somar(ig.get(k) || [], "pedidos");
        return { k, label: k === 10 ? "10+" : `${k}x`, pedidos: v, pct: (100 * v) / instOrd };
      });
      const pctParc = (100 * (instOrd - somar(ig.get(1) || [], "pedidos"))) / instOrd;
      $("#t-p3-pag", root).textContent = isEN()
        ? `${fmt.pct(pctParc, 0)} of card orders are paid in installments`
        : `${fmt.pct(pctParc, 0)} dos pedidos no cartão são parcelados`;
      $("#s-p3-pag", root).textContent = isEN()
        ? "Credit-card orders by installment count (10+ groups 10 to 24x)"
        : "Pedidos no cartão por parcelas (10+ agrupa 10 a 24x)";

      desenharColunas($("#plot-p3-pag", root), {
        dados: instItems,
        semEixoY: true,
        nome: (d) => d.label,
        valor: (d) => d.pedidos,
        rotulo: (d) => (d.pedidos >= 1000 ? `${num(d.pedidos / 1000, 1)}${isEN() ? "k" : "k"}` : num(d.pedidos, 0)),
        classeBarra: (d) => (d.k === 1 ? "barra" : "barra-neutra"),
        destaque: (d) => d.k === 1,
        dica: (d) => `<strong>${esc(d.label)}</strong>${par(t("k.pedidos"), fmt.int(d.pedidos))}${par(isEN() ? "Share" : "Participação", fmt.pct(d.pct))}`,
        srCaption: $("#t-p3-pag", root).textContent,
        srCol1: isEN() ? "Installments" : "Parcelas",
        srCol2: t("k.pedidos"),
      });
    }

    // 3. Concentração de vendedores por decil (D1 em acento, D2..D10 em mark-muted)
    if (dec.length) {
      $("#t-p3-vendedores", root).textContent = isEN()
        ? `Top 10% of sellers hold ${fmt.pct((100 * dec[0].gmv_real) / decTot, 0)} of real GMV`
        : `Os 10% maiores vendedores somam ${fmt.pct((100 * dec[0].gmv_real) / decTot, 0)} do GMV`;
    }
    $("#s-p3-vendedores", root).textContent = isEN()
      ? "Share of real GMV by seller decile (D1 = top 10%)"
      : "Participação no GMV real por decil (D1 = 10% maiores)";

    desenharColunas($("#plot-p3-vendedores", root), {
      dados: dec.map((x) => ({
        lbl: `D${decNum(x)}`,
        pct: (100 * x.gmv_real) / decTot,
        acum: x.pct_gmv_acumulado,
        vendedores: x.vendedores,
        pedidos: x.pedidos,
        gmv: x.gmv_real,
      })),
      semEixoY: true,
      nome: (d) => d.lbl,
      valor: (d) => d.pct,
      rotulo: (d) => fmt.pct(d.pct, d.pct < 10 ? 1 : 0),
      classeBarra: (_d, i) => (i === 0 ? "barra" : "barra-neutra"),
      destaque: (_d, i) => i === 0,
      dica: (d) => `<strong>${esc(d.lbl)}</strong>${par(isEN() ? "Share" : "Participação", fmt.pct(d.pct))}${par(isEN() ? "Cumulative" : "Acumulado", fmt.pct(d.acum))}${par(isEN() ? "Sellers" : "Vendedores", fmt.int(d.vendedores))}${par(t("k.gmvReal"), fmt.brl(d.gmv))}`,
      srCaption: $("#t-p3-vendedores", root).textContent,
      srCol1: isEN() ? "Decile" : "Decil",
      srCol2: isEN() ? "Share" : "Participação",
    });
  }

  function desenharP3Coorte(root) {
    const co = (D().coorte || []).filter((c) => c.clientes > 0);
    const box = $("#p3-coorte", root);
    if (!co.length) return vazio(box);
    const nM = Math.max(...co.map((c) => (c.retidos || []).length));
    const taxas = co.map((c) => (c.retidos || []).map((v) => (v != null && c.clientes ? (100 * v) / c.clientes : null)));
    const maxR = Math.max(...taxas.flat().filter((v) => v != null && isFinite(v))) || 1;
    const m1 = (100 * somar(co, (c) => (c.retidos || [])[0] || 0)) / (somar(co, "clientes") || 1);

    $("#t-p3-coorte", root).textContent = isEN()
      ? `Repurchase is rare: ${fmt.pct(m1, m1 < 1 ? 2 : 1)} return the next month`
      : `A recompra é rara: ${fmt.pct(m1, m1 < 1 ? 2 : 1)} voltam no mês seguinte`;
    $("#s-p3-coorte", root).textContent = isEN()
      ? "% of cohort customers (first-purchase month) buying again in M+n"
      : "% de clientes da coorte (mês da 1ª compra) que voltam no mês M+n";

    const nivel = (v) => {
      if (v == null || v <= 0) return "coh-0";
      const k = Math.sqrt(v / maxR);
      if (k >= 0.78) return "coh-4";
      if (k >= 0.52) return "coh-3";
      if (k >= 0.30) return "coh-2";
      return "coh-1";
    };

    box.innerHTML = `<table class="coorte">
      <thead><tr>
        <th class="col-mes" scope="col">${isEN() ? "Cohort" : "Coorte"}</th>
        <th scope="col">${isEN() ? "Customers" : "Clientes"}</th>
        ${[...Array(nM)].map((_, i) => `<th scope="col">M+${i + 1}</th>`).join("")}
      </tr></thead>
      <tbody>${co.map((c, ri) => `<tr>
        <td class="col-mes">${esc(fmt.mes(c.coorte))}</td>
        <td class="col-n">${fmt.int(c.clientes)}</td>
        ${[...Array(nM)].map((_, i) => {
          const v = taxas[ri][i];
          if (v == null) return "<td></td>";
          return `<td class="${nivel(v)}" title="${esc(`${fmt.int(c.retidos[i])} / ${fmt.int(c.clientes)}`)}">${fmt.pct(v, v > 0 && v < 1 ? 2 : 1)}</td>`;
        }).join("")}
      </tr>`).join("")}</tbody>
    </table>`;
  }

  /* ---------- PÁGINA 04: Qualidade e linhagem ---------- */
  function renderP4(root) {
    const q = D().qualidade || {};
    const ct = q.contagens || {};
    const regras = (q.regras || []).slice();
    const gab = q.gabarito || {};
    const raw = ct.pedidos_brutos || 0;
    const valid = ct.pedidos_analisados || 0;
    const excl = raw - valid;
    const anom = ct.total_anomalias ?? somar(regras, "linhas_afetadas");
    const dup = ct.reviews_duplicadas ?? 0;
    const ok = gab.conferem === true || (gab.conferem != null && gab.consultas != null && gab.conferem === gab.consultas);
    const okNum = gab.conferem === true ? gab.consultas : gab.conferem;

    const kpis = [
      {
        rot: t("k.brutos"), val: fmt.int(raw),
        nota: isEN() ? "Olist orders file" : "base Olist de pedidos",
      },
      {
        rot: t("k.analisados"), val: fmt.int(valid),
        nota: isEN() ? `${fmt.pct((100 * valid) / (raw || 1))} · ${fmt.int(excl)} excl.` : `${fmt.pct((100 * valid) / (raw || 1))} · ${fmt.int(excl)} excl.`,
      },
      {
        rot: t("k.anomalias"), val: fmt.int(anom),
        nota: isEN() ? `${regras.length} rules · ${fmt.int(dup)} dup. rev.` : `${regras.length} regras · ${fmt.int(dup)} rev. dup.`,
      },
      {
        rot: t("k.gabarito"),
        val: `${okNum}/${gab.consultas}`,
        valHtml: `${checkSvg(ok)}<span>${esc(`${okNum}/${gab.consultas}`)}</span>`,
        nota: isEN() ? "SQL queries matched" : "consultas conferidas",
      },
    ];

    const fontes = D().meta?.fontes || [];
    const fontesRes = D().meta?.fontes_resumo || [];
    const nSources = fontesRes.length || fontes.length;
    const linToggle = fontesRes.length && fontes.length
      ? `<div class="seg" role="group" aria-label="${esc(isEN() ? "Lineage view" : "Visão de linhagem")}">
          <button type="button" data-linview="summary" aria-pressed="${state.linView === "summary"}">${esc(t("lin.resumo", { n: fontesRes.length }))}</button>
          <button type="button" data-linview="all" aria-pressed="${state.linView === "all"}">${esc(t("lin.arquivos", { n: fontes.length }))}</button>
        </div>`
      : "";

    root.innerHTML = `
      <section class="kpis" aria-label="${esc(isEN() ? "Data quality indicators" : "Indicadores de qualidade")}" id="p4-kpis"></section>
      <section class="cartao col-7-a" aria-labelledby="t-p4-auditoria">
        <h2 id="t-p4-auditoria"></h2>
        <p class="sub" id="s-p4-auditoria"></p>
        <div class="rolagem" id="p4-auditoria" role="region" aria-labelledby="t-p4-auditoria" tabindex="0"></div>
        <p class="dica-rolagem">${esc(t("dica.rolagem"))}</p>
      </section>
      <section class="cartao col-5-a" aria-labelledby="t-p4-regras">
        <h2 id="t-p4-regras"></h2>
        <p class="sub" id="s-p4-regras"></p>
        <div class="plot" id="plot-p4-regras"></div>
      </section>
      <section class="cartao col-12-b" aria-labelledby="t-p4-linhagem">
        <div class="cartao-topo">
          <div class="cartao-titulos">
            <h2 id="t-p4-linhagem"></h2>
            <p class="sub" id="s-p4-linhagem"></p>
          </div>
          <div class="cartao-ctl">${linToggle}</div>
        </div>
        <div class="rolagem" id="p4-linhagem" role="region" aria-labelledby="t-p4-linhagem" tabindex="0"></div>
        <p class="dica-rolagem">${esc(t("dica.rolagem"))}</p>
      </section>`;

    renderKpis($("#p4-kpis", root), kpis);
    $$("button[data-linview]", root).forEach((b) => b.addEventListener("click", () => { state.linView = b.dataset.linview; render(); }));

    const tx = (r, k) => limparTexto((isEN() && r[`${k}_en`]) ? r[`${k}_en`] : r[k]);
    const shortTbl = (s) => String(s || "").replace(/^olist_/, "").replace(/_dataset\.csv$/, ".csv");
    const shortLic = (s) => {
      const m = limparTexto(s);
      if (/CC BY/i.test(m)) return "CC BY-NC-SA 4.0";
      if (/Banco Central/i.test(m)) return isEN() ? "BCB Public Data" : "BCB · Dados públicos";
      if (/IBGE/i.test(m)) return isEN() ? "IBGE Public Data" : "IBGE · Dados públicos";
      return truncar(m.split("(")[0].trim(), 32);
    };

    $("#t-p4-auditoria", root).textContent = isEN()
      ? `${regras.length} quality rules logged ${fmt.int(anom)} anomalies without silent drops`
      : `${regras.length} regras de qualidade registraram ${fmt.int(anom)} anomalias sem descarte silencioso`;
    $("#s-p4-auditoria", root).textContent = isEN()
      ? `Scrollable table with all ${regras.length} rules logged in qualidade_auditoria`
      : `Tabela rolável com as ${regras.length} regras registradas em qualidade_auditoria`;

    $("#p4-auditoria", root).innerHTML = regras.length
      ? `<table class="tbl-texto">
          <thead><tr>
            <th class="esq" scope="col">${isEN() ? "Rule" : "Regra"}</th>
            <th scope="col">${isEN() ? "Records" : "Registros"}</th>
            <th scope="col">% ${isEN() ? "base" : "base"}</th>
            <th class="esq" scope="col">${isEN() ? "Treatment" : "Tratamento"}</th>
          </tr></thead>
          <tbody>${regras.map((r) => `<tr>
            <td class="esq"><strong>${esc(tx(r, "regra"))}</strong><div><code title="${esc(r.tabela)}">${esc(shortTbl(r.tabela))}</code></div></td>
            <td>${fmt.int(r.linhas_afetadas)}</td>
            <td>${r.pct != null ? fmt.pct(r.pct, 2) : "–"}</td>
            <td class="esq sec">${esc(tx(r, "tratamento"))}</td>
          </tr>`).join("")}</tbody>
        </table>`
      : `<div class="estado">${esc(t("vazio"))}</div>`;

    const sorted = regras.slice().sort((p, q2) => (q2.linhas_afetadas || 0) - (p.linhas_afetadas || 0));
    desenharP4Grafico(root, sorted, tx);

    $("#t-p4-linhagem", root).textContent = isEN()
      ? `${nSources} public sources (${fontes.length} files), zero API keys`
      : `${nSources} fontes públicas (${fontes.length} arquivos), sem chave de API`;
    $("#s-p4-linhagem", root).textContent = isEN()
      ? "Reproducible ingestion with UTC timestamps and SHA-256 in scripts/coletar_dados.py"
      : "Coleta reprodutível com carimbo UTC e SHA-256 em scripts/coletar_dados.py";

    const showSum = fontesRes.length && state.linView === "summary";
    $("#p4-linhagem", root).innerHTML = showSum
      ? `<table class="tbl-texto">
          <thead><tr>
            <th class="esq" scope="col">${isEN() ? "Source" : "Fonte"}</th>
            <th scope="col">${isEN() ? "Files" : "Arquivos"}</th>
            <th scope="col">${isEN() ? "Records" : "Registros"}</th>
            <th scope="col">${isEN() ? "Collected" : "Coletado em"}</th>
            <th class="esq" scope="col">${isEN() ? "License" : "Licença"}</th>
          </tr></thead>
          <tbody>${fontesRes.map((f) => `<tr>
            <td class="esq"><strong>${esc(limparTexto(f.fonte))}</strong></td>
            <td>${fmt.int(f.arquivos)}</td>
            <td>${fmt.int(f.registros)}</td>
            <td>${esc(fmt.stamp(f.coletado_em))}</td>
            <td class="esq sec" title="${esc(limparTexto(f.licenca))}">${esc(shortLic(f.licenca))}</td>
          </tr>`).join("")}</tbody>
        </table>`
      : `<table class="tbl-texto">
          <thead><tr>
            <th class="esq" scope="col">${isEN() ? "Source" : "Fonte"}</th>
            <th class="esq" scope="col">${isEN() ? "File" : "Arquivo"}</th>
            <th class="esq" scope="col">Endpoint</th>
            <th scope="col">${isEN() ? "Records" : "Registros"}</th>
            <th scope="col">${isEN() ? "Collected" : "Coletado em"}</th>
          </tr></thead>
          <tbody>${fontes.map((f) => `<tr>
            <td class="esq"><strong>${esc(limparTexto(f.fonte || f.nome))}</strong></td>
            <td class="esq"><code>${esc(f.nome)}</code></td>
            <td class="esq"><code class="url-curta" title="${esc(f.endpoint)}">${esc(f.endpoint)}</code></td>
            <td>${fmt.int(f.registros)}</td>
            <td>${esc(fmt.stamp(f.coletado_em))}</td>
          </tr>`).join("")}</tbody>
        </table>`;
  }

  function desenharP4Grafico(root, sorted, tx) {
    if (sorted.length) {
      $("#t-p4-regras", root).textContent = isEN()
        ? `${tx(sorted[0], "regra")} leads with ${fmt.int(sorted[0].linhas_afetadas)} records`
        : `${tx(sorted[0], "regra")} lidera com ${fmt.int(sorted[0].linhas_afetadas)} registros`;
    }
    $("#s-p4-regras", root).textContent = isEN()
      ? "Top 6 audit rules by affected records"
      : "Top 6 regras por volume de registros afetados";

    const regraCurta = (r) => (REGRA_CURTA[r.regra_id] ? REGRA_CURTA[r.regra_id][isEN() ? 1 : 0] : tx(r, "regra"));
    desenharBarrasH($("#plot-p4-regras", root), {
      dados: sorted.slice(0, 6),
      l: 132,
      r: 52,
      nome: regraCurta,
      valor: (r) => r.linhas_afetadas,
      rotulo: (r) => fmt.int(r.linhas_afetadas),
      classeBarra: (_r, i) => (i === 0 ? "barra" : "barra-neutra"),
      dica: (r) => `<strong>${esc(tx(r, "regra"))}</strong>${par(isEN() ? "Records" : "Registros", fmt.int(r.linhas_afetadas))}${par("% base", r.pct != null ? fmt.pct(r.pct, 2) : "–")}${par(isEN() ? "Table" : "Tabela", r.tabela || "–")}`,
      srCaption: $("#t-p4-regras", root).textContent,
      srCol1: isEN() ? "Rule" : "Regra",
      srCol2: isEN() ? "Records" : "Registros",
    });
  }

  /* ---------- Cabeçalho, filtros, i18n e navegação ---------- */
  const PAGES = { p1: renderP1, p2: renderP2, p3: renderP3, p4: renderP4 };

  function atualizarCabecalho() {
    const p = state.page;
    const cmp = contextoPeriodo();
    $("#titulo-pagina").textContent = t(`${p}.title`);
    if (p === "p1" || p === "p2") {
      $("#sub-pagina").textContent = (state.ano === "all" || state.ano === String(cmp.anoMax))
        ? t(`${p}.subBase`, { atual: cmp.rotAtual, base: cmp.rotBase })
        : t(`${p}.subAno`, { ano: state.ano });
    } else {
      $("#sub-pagina").textContent = t(`${p}.sub`);
    }
    document.title = `${t(`${p}.title`)} · ${t("brand.title")}`;

    const desab = p === "p4";
    $$("#filtro-ano button, #filtro-regiao button").forEach((b) => { b.disabled = desab; });
    $("#wrap-categoria").hidden = p !== "p3";
    $("#f-categoria").disabled = p !== "p3";
  }

  function construirFiltros() {
    if (!state.D) return;
    const anos = [...new Set((D().mensal_regiao || []).filter((r) => r.pedidos > 0).map(anoDe))].sort();
    $("#filtro-ano").innerHTML = ["all", ...anos].map((a) =>
      `<button type="button" data-ano="${a}" aria-pressed="${state.ano === a}">${esc(a === "all" ? t("f.todos") : a)}</button>`).join("");

    const regs = REGIOES.filter((r) => (D().mensal_regiao || []).some((x) => x.regiao === r));
    $("#filtro-regiao").innerHTML = [null, ...regs].map((r) =>
      `<button type="button" data-regiao="${r ?? ""}" aria-pressed="${state.regiao === r}">${esc(r ? nomeRegiao(r) : t("f.brasil"))}</button>`).join("");

    const cg = agrupar(D().categoria_ano_regiao || [], (r) => r.categoria_pt);
    const cats = [...cg.entries()].map(([k, rs]) => ({ k, label: nomeCat(rs[0]), v: somar(rs, "gmv_real") })).sort((a, b) => b.v - a.v);
    $("#f-categoria").innerHTML = `<option value="all">${esc(t("f.todasCat"))}</option>`
      + cats.map((c) => `<option value="${esc(c.k)}">${esc(c.label)}</option>`).join("");

    sincronizarFiltros();
  }

  function sincronizarFiltros() {
    $$("#filtro-ano button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.ano === state.ano)));
    $$("#filtro-regiao button").forEach((b) => b.setAttribute("aria-pressed", String((b.dataset.regiao || null) === state.regiao)));
    const sel = $("#f-categoria");
    if (sel) {
      if (![...sel.options].some((o) => o.value === state.categoria)) state.categoria = "all";
      sel.value = state.categoria;
      sel.classList.toggle("ativo", state.categoria !== "all");
    }
    const temFiltro = state.ano !== "all" || state.regiao !== null || state.categoria !== "all";
    $("#f-reset").hidden = !temFiltro || state.page === "p4";
  }

  function aplicarI18n() {
    raiz.lang = isEN() ? "en" : "pt-BR";
    $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
    if (state.D) {
      const m = D().meta || {};
      const baseMes = fmt.mesAno(m.mes_base_ipca || "2018-10");
      $("#fonte").textContent = t("foot.source", { base: baseMes });
      const gerado = new Date(m.gerado_em);
      $("#assinatura").textContent = !isNaN(gerado)
        ? t("foot.updated", { data: gerado.toLocaleDateString(isEN() ? "en-US" : "pt-BR") })
        : "Rafael Balchuna";
      construirFiltros();
    }
  }

  function escolherRegiao(r) {
    state.regiao = r || null;
    sincronizarFiltros();
    render();
  }

  function render() {
    if (!state.D) return;
    const p = state.page;
    $$(".painel-pagina").forEach((s) => { s.hidden = s.id !== p; });
    $$(".aba").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.page === p)));
    atualizarCabecalho();
    sincronizarFiltros();
    esconderDica();
    PAGES[p]($(`#${p}`));
    gravarHash();
  }

  function lerHash() {
    const [p, qs] = location.hash.replace(/^#/, "").split("?");
    if (PAGES[p]) state.page = p;
    const q = new URLSearchParams(qs || "");
    const sp = new URLSearchParams(location.search);
    if (q.get("ano")) state.ano = q.get("ano");
    if (q.get("regiao")) state.regiao = q.get("regiao") === "all" ? null : q.get("regiao");
    if (q.get("categoria")) state.categoria = q.get("categoria");
    const lang = sp.get("lang") || q.get("lang") || ler("painel.lang");
    if (lang === "en" || lang === "pt") state.lang = lang;
    const temaUrl = sp.get("tema") || q.get("tema");
    const tema = (temaUrl === "dark" || temaUrl === "light")
      ? temaUrl
      : (ler("padrao-bi:tema") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
    aplicarTema(tema);
  }

  function gravarHash() {
    const q = new URLSearchParams();
    if (state.ano !== "all") q.set("ano", state.ano);
    if (state.regiao) q.set("regiao", state.regiao);
    if (state.categoria !== "all") q.set("categoria", state.categoria);
    const h = `#${state.page}${q.toString() ? `?${q}` : ""}`;
    if (location.hash !== h) history.replaceState(null, "", h);
  }

  function normalizar(raw) {
    const d = { ...raw };
    d.meta = d.meta || {};
    ["mensal_regiao", "macro_mensal", "uf_ano", "faixa_atraso", "categoria_ano_regiao", "pagamento_ano_regiao", "parcelas_ano_regiao", "coorte", "vendedores_decil"]
      .forEach((k) => { if (!Array.isArray(d[k])) d[k] = []; });
    d.macro_mensal = d.macro_mensal.map((r) => ({ ...r, ipca_12m_pct: r.ipca_12m_pct ?? r.ipca_acum_12m_pct }));
    const ords = d.faixa_atraso.map((r) => +r.ordem).filter(isFinite);
    const shift = ords.length && Math.min(...ords) === 1 ? -1 : 0;
    d.faixa_atraso = d.faixa_atraso.map((r) => ({ ...r, ordem: +r.ordem + shift })).filter((r) => r.ordem >= 0 && r.ordem <= 4);
    if (d.qualidade && Array.isArray(d.qualidade.regras)) {
      d.qualidade = {
        ...d.qualidade,
        regras: d.qualidade.regras.map((r) => ({ ...r, tabela: r.tabela ?? r.tabela_origem, pct: r.pct ?? r.pct_base })),
      };
    }
    return d;
  }

  function ligarEventos() {
    $$("[data-tema]").forEach((b) => b.addEventListener("click", () => {
      aplicarTema(b.dataset.tema);
      gravar("padrao-bi:tema", b.dataset.tema);
    }));
    $$("[data-lang]").forEach((b) => b.addEventListener("click", () => {
      state.lang = b.dataset.lang;
      gravar("painel.lang", state.lang);
      aplicarI18n();
      render();
    }));
    $$(".aba").forEach((b) => b.addEventListener("click", () => {
      state.page = b.dataset.page;
      render();
    }));
    $("#nav-abas").addEventListener("keydown", (ev) => {
      if (!["ArrowLeft", "ArrowRight"].includes(ev.key)) return;
      ev.preventDefault();
      const ids = Object.keys(PAGES);
      const next = ids[(ids.indexOf(state.page) + (ev.key === "ArrowRight" ? 1 : -1) + ids.length) % ids.length];
      state.page = next;
      render();
      $(`#tab-${next}`).focus();
    });

    document.addEventListener("click", (ev) => {
      const bAno = ev.target.closest("#filtro-ano button[data-ano]");
      if (bAno && !bAno.disabled) {
        state.ano = bAno.dataset.ano;
        sincronizarFiltros();
        render();
        return;
      }
      const bReg = ev.target.closest("button[data-regiao]");
      if (bReg && !bReg.disabled) {
        const r = bReg.dataset.regiao || null;
        escolherRegiao(bReg.classList.contains("linha-reg") && r === state.regiao ? null : r);
        if (!bReg.classList.contains("linha-reg")) {
          $(`#filtro-regiao button[data-regiao="${r ?? ""}"]`)?.focus();
        }
      }
    });

    $("#f-categoria").addEventListener("change", (ev) => {
      state.categoria = ev.target.value;
      sincronizarFiltros();
      render();
    });
    $("#f-reset").addEventListener("click", () => {
      state.ano = "all";
      state.regiao = null;
      state.categoria = "all";
      sincronizarFiltros();
      render();
    });
    addEventListener("hashchange", () => { lerHash(); sincronizarFiltros(); render(); });

    let pendente = 0;
    let larguraAnt = $(".pagina").clientWidth;
    new ResizeObserver(() => {
      const w = $(".pagina").clientWidth;
      if (w === larguraAnt) return;
      larguraAnt = w;
      cancelAnimationFrame(pendente);
      pendente = requestAnimationFrame(() => render());
    }).observe($(".pagina"));
  }

  async function iniciar() {
    lerHash();
    ligarEventos();
    aplicarI18n();
    try {
      let bruto = window.RESUMO;
      if (!bruto) {
        const res = await fetch("dados/resumo.json", { cache: "no-cache" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        bruto = await res.json();
      }
      if (!bruto || !Array.isArray(bruto.mensal_regiao)) throw new Error("Estrutura inválida");
      state.D = normalizar(bruto);
      $("#status").hidden = true;
      aplicarI18n();
      render();
    } catch (err) {
      const st = $("#status");
      st.hidden = false;
      st.setAttribute("role", "alert");
      st.innerHTML = `<h2>${esc(t("status.errTitle"))}</h2><p class="sub">${t("status.errBody")}</p>`;
      console.warn("[painel] erro ao carregar dados:", err.message);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
