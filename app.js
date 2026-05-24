/* Tableau de bord multi-modeles (cote supercars - marche US).
   Lit le catalogue (data/catalog.js -> window.COTE_CATALOG) pour proposer un
   selecteur marque/modele. Une fois un modele choisi, le bundle dedie
   (data/<slug>/dashboard.js -> window.COTE) est charge a la demande. */
"use strict";

(function () {
  /* ---------- constantes ---------- */

  const STORAGE_KEY = "cote.model.slug";
  const MONTHS_FR = ["janv.", "fevr.", "mars", "avr.", "mai", "juin",
    "juil.", "aout", "sept.", "oct.", "nov.", "dec."];
  const PALETTE = ["#e63329", "#f0a202", "#3a9bdc", "#34c759",
    "#a280ff", "#ff8857", "#ec4899", "#10b981"];
  const KNOWN_VARIANT_COLORS = {
    "Italia": "#e63329", "Spider": "#f0a202",
    "Speciale": "#3a9bdc", "Speciale A": "#34c759",
    "Tributo": "#e63329",
    "LP610-4": "#f0a202", "Spyder": "#f0a202",
    "Performante": "#3a9bdc", "EVO": "#a280ff",
    "STO": "#e63329", "Tecnica": "#34c759",
    "GT3": "#e63329", "GT3 Touring": "#34c759", "GT3 RS": "#a280ff",
  };
  const BRAND_ACCENTS = {
    "Ferrari": { accent: "#ff2800", soft: "#ff5a3c" },
    "Lamborghini": { accent: "#f47b00", soft: "#ffa64d" },
    "Porsche": { accent: "#d5001c", soft: "#ff5a3c" },
    "default": { accent: "#ff2800", soft: "#ff5a3c" },
  };
  const NEW_THRESHOLD_DAYS = 7;
  const KINDS = [
    { kind: "dealer", label: "Annonces concessionnaires" },
    { kind: "auction", label: "Ventes aux enchères" },
  ];

  /* ---------- etat global du dashboard (rempli apres chargement) ---------- */

  let data = null;          // window.COTE pour le modele charge
  let activeModelSlug = null;
  let activeKind = "dealer";
  let activeVariant = "Toutes";
  let sortKey = "deal_pct";
  let sortDir = -1;
  let VARIANTS = [];
  let VARIANT_COLORS = {};
  let RESIDUAL = 20;
  let DEAL_STRONG = 26;
  let DEAL_MILD = 12;

  const fmtUSD = new Intl.NumberFormat("fr-FR",
    { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const fmtInt = new Intl.NumberFormat("fr-FR");

  /* ---------- utilitaires ---------- */

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
        "'": "&#39;" }[c];
    });
  }

  function compact(v) {
    if (v == null) return "—";
    if (v >= 1e6) return (v / 1e6).toFixed(2).replace(".", ",") + " M$";
    if (v >= 1e3) return Math.round(v / 1e3) + " k$";
    return Math.round(v) + " $";
  }

  function pctText(v) {
    return (v >= 0 ? "+" : "") + v.toFixed(1).replace(".", ",") + " %";
  }

  function relativeDays(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const days = Math.floor((Date.now() - d.getTime()) / 86400000);
    if (days < 0) return "";
    if (days === 0) return "aujourd'hui";
    if (days === 1) return "hier";
    return "il y a " + days + " j";
  }

  function isNew(iso) {
    if (!iso) return false;
    const d = new Date(iso);
    if (isNaN(d)) return false;
    const days = (Date.now() - d.getTime()) / 86400000;
    return days >= 0 && days <= NEW_THRESHOLD_DAYS;
  }
  function newBadge() {
    return '<span class="new-badge">Nouveau</span>';
  }

  function monthLabel(iso) {
    const parts = String(iso).split("-");
    return MONTHS_FR[(+parts[1] || 1) - 1] + " " + parts[0].slice(2);
  }

  function dateLabel(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.getDate() + " " + MONTHS_FR[d.getMonth()].replace(".", "") +
      " " + d.getFullYear();
  }

  function dateTimeLabel(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    const h = String(d.getHours()).padStart(2, "0");
    const m = String(d.getMinutes()).padStart(2, "0");
    return dateLabel(iso) + " à " + h + ":" + m;
  }

  function relativeShort(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const sec = Math.floor((Date.now() - d.getTime()) / 1000);
    if (sec < 60) return "à l'instant";
    const min = Math.floor(sec / 60);
    if (min < 60) return "il y a " + min + " min";
    const h = Math.floor(min / 60);
    if (h < 24) return "il y a " + h + " h";
    const days = Math.floor(h / 24);
    return "il y a " + days + " j";
  }

  function isHttpUrl(u) {
    return /^https?:\/\//i.test(String(u || ""));
  }

  function linkedYear(l) {
    if (isHttpUrl(l.url)) {
      return '<a href="' + esc(l.url) + '" target="_blank" ' +
        'rel="noopener noreferrer">' + l.year + " ↗</a>";
    }
    return String(l.year);
  }

  function bandTitle(est) {
    if (!est) return "";
    const f = 1 + RESIDUAL / 100;
    return "Fourchette du modèle : " + compact(est / f) + " – " + compact(est * f);
  }

  function filteredListings() {
    return data.listings.filter(function (l) {
      const kindOk = (l.kind || "dealer") === activeKind;
      const variantOk = activeVariant === "Toutes" || l.variant === activeVariant;
      return kindOk && variantOk;
    });
  }

  function computeStats(list) {
    const prices = list.map((l) => l.price).filter((p) => p > 0)
      .sort((a, b) => a - b);
    const miles = list.map((l) => l.mileage).filter((m) => m > 0);
    if (!prices.length) return { count: 0 };
    const sum = prices.reduce((a, b) => a + b, 0);
    const mid = Math.floor(prices.length / 2);
    const median = prices.length % 2
      ? prices[mid]
      : Math.round((prices[mid - 1] + prices[mid]) / 2);
    return {
      count: prices.length,
      avg: Math.round(sum / prices.length),
      median: median,
      min: prices[0],
      max: prices[prices.length - 1],
      avgMileage: miles.length
        ? Math.round(miles.reduce((a, b) => a + b, 0) / miles.length)
        : null,
    };
  }

  function historyValue(point) {
    if (activeVariant === "Toutes") return point.overall.avg_price;
    return point.by_variant ? point.by_variant[activeVariant] : null;
  }

  function computeTrend() {
    const h = data.history || [];
    if (h.length < 2) return null;
    const last = h[h.length - 1];
    const targetDate = (+last.date.slice(0, 4) - 1) + last.date.slice(4);
    let prev = h[0];
    for (const p of h) {
      if (p.date <= targetDate) prev = p;
    }
    const from = historyValue(prev);
    const to = historyValue(last);
    if (!from || !to) return null;
    return {
      pct: ((to - from) / from) * 100,
      months: monthsBetween(prev.date, last.date),
    };
  }

  function monthsBetween(a, b) {
    const da = a.split("-"), db = b.split("-");
    return (db[0] - da[0]) * 12 + (db[1] - da[1]);
  }

  function dealClass(pct) {
    if (pct == null) return "neutral";
    if (pct >= DEAL_STRONG) return "good";
    if (pct >= DEAL_MILD) return "mid";
    if (pct > -DEAL_MILD) return "neutral";
    return "over";
  }
  function dealLabel(pct) {
    if (pct == null) return "—";
    if (pct >= DEAL_STRONG) return "Bonne affaire";
    if (pct >= DEAL_MILD) return "Sous la cote";
    if (pct > -DEAL_MILD) return "Dans le marché";
    return "Au-dessus";
  }
  function dealBadge(pct) {
    if (pct == null) return '<span class="deal neutral">—</span>';
    return '<span class="deal ' + dealClass(pct) + '" title="' +
      dealLabel(pct) + '">' + pctText(pct) + "</span>";
  }

  function thumbCell(l) {
    const bg = l.image_url
      ? 'background-image:url(\'' + esc(l.image_url) + '\')'
      : "";
    const box = '<div class="thumb-img" style="' + bg + '"></div>';
    const inner = isHttpUrl(l.url)
      ? '<a href="' + esc(l.url) + '" target="_blank" rel="noopener noreferrer">'
        + box + "</a>"
      : box;
    return '<td class="thumb">' + inner + "</td>";
  }

  const VIN_RE = /[A-HJ-NPR-Z0-9]{17}/i;
  function vinOf(l) {
    if (l.vin) return String(l.vin).toUpperCase();
    const m = VIN_RE.exec(l.url || "");
    return m ? m[0].toUpperCase() : "";
  }
  function vinLink(vin) {
    if (!vin) return "—";
    return '<a href="https://epicvin.com/fr/' +
      'check-vin-number-and-get-the-vehicle-history-report/checkout/' +
      encodeURIComponent(vin.toLowerCase()) +
      '" target="_blank" rel="noopener noreferrer" ' +
      'title="Rapport d\'historique du véhicule par VIN (epicvin)">' +
      esc(vin) + "</a>";
  }
  function titleCell(l) {
    if (l.clean_title === true) return '<span class="avis good">Propre</span>';
    if (l.clean_title === false) return '<span class="avis over">⚠ Non propre</span>';
    return "—";
  }
  function avisFor(l) {
    const text = ((l.url || "") + " " + (l.title || "")).toLowerCase();
    if (l.clean_title === false || /\b(salvage|rebuilt|flood)\b/.test(text)) {
      return { txt: "Titre à risque", cls: "over" };
    }
    if (/liberty.?walk|widebody|wide.?body|novitec|misha|prior.?design|replica/.test(text)) {
      return { txt: "Modifiée — décote", cls: "over" };
    }
    const p = l.deal_pct;
    if (p == null) return { txt: "—", cls: "neutral" };
    if (p >= DEAL_STRONG) return { txt: "Écart fort — à vérifier", cls: "good" };
    if (p >= DEAL_MILD) return { txt: "Sous la cote — à étudier", cls: "mid" };
    if (p > -DEAL_MILD) return { txt: "Au prix du marché", cls: "neutral" };
    return { txt: "Au-dessus du marché", cls: "over" };
  }

  /* ---------- indicateurs (KPI) ---------- */

  function renderKpis() {
    const list = filteredListings();
    const s = computeStats(list);
    const trend = computeTrend();
    const cards = [];

    if (!s.count) {
      document.getElementById("kpis").innerHTML =
        '<div class="banner">Aucune annonce pour cette version.</div>';
      return;
    }

    cards.push(kpi("Prix moyen", fmtUSD.format(s.avg)));
    cards.push(kpi("Prix médian", fmtUSD.format(s.median)));
    cards.push(kpi("Fourchette", compact(s.min) + " – " + compact(s.max)));
    cards.push(kpi("Kilométrage moyen",
      s.avgMileage != null ? fmtInt.format(s.avgMileage) + " mi" : "—"));
    cards.push(kpi("Annonces suivies", String(s.count)));

    const newCount = list.filter((l) => isNew(l.posted_at)).length;
    cards.push(kpi("Nouvelles (≤ 7 j)", String(newCount),
      "récentes sur le marché", newCount ? "up" : ""));

    if (trend) {
      const arrow = trend.pct >= 0 ? "▲" : "▼";
      const cls = trend.pct >= 0 ? "up" : "down";
      cards.push(kpi("Tendance " + (trend.months || 12) + " mois",
        arrow + " " + pctText(trend.pct), "cote moyenne", cls));
    } else {
      cards.push(kpi("Tendance", "—"));
    }

    const dealCount = list.filter((l) => l.status === "for_sale"
      && l.deal_pct != null && l.deal_pct >= DEAL_STRONG).length;
    cards.push(kpi("Bonnes affaires", String(dealCount),
      "≥ " + Math.round(DEAL_STRONG) + " % sous la cote", dealCount ? "up" : ""));

    document.getElementById("kpis").innerHTML = cards.join("");
  }

  function kpi(label, value, sub, cls) {
    return '<div class="kpi"><div class="kpi-label">' + label +
      '</div><div class="kpi-value ' + (cls || "") + '">' + value +
      "</div>" + (sub ? '<div class="kpi-sub">' + sub + "</div>" : "") +
      "</div>";
  }

  /* ---------- bonnes affaires ---------- */

  function renderDeals() {
    const deals = filteredListings()
      .filter((l) => l.status === "for_sale" && l.deal_pct != null
        && l.deal_pct >= DEAL_MILD && l.price > 0)
      .sort((a, b) => b.deal_pct - a.deal_pct)
      .slice(0, 12);

    const note = document.getElementById("valuation-note");
    const method = (data.valuation && data.valuation.method)
      || "régression sur millésime, kilométrage et version";
    const scored = filteredListings().filter((l) => l.deal_pct != null).length;
    note.innerHTML = "Valeur estimée par " + esc(method) +
      ". Imprécision du modèle ≈ <strong>±" + Math.round(RESIDUAL) +
      "&nbsp;%</strong> — " +
      "le millésime, le kilométrage et la version ne capturent ni les options, " +
      "ni l'état, ni la certification. Un écart fort est une <em>piste à " +
      "investiguer</em> : bonne affaire possible, ou voiture à vérifier " +
      "(accident, entretien…). " + deals.length + " annonce(s) sous la cote " +
      "sur " + scored + " évaluées.";

    if (!deals.length) {
      document.getElementById("deals-list").innerHTML =
        '<p class="empty">Aucune annonce sous la cote pour cette sélection.</p>';
      return;
    }

    const rows = deals.map((l) => {
      return "<tr>" +
        thumbCell(l) +
        '<td class="num">' + linkedYear(l) + "</td>" +
        "<td>" + variantTag(l.variant) +
        (isNew(l.posted_at) ? " " + newBadge() : "") + "</td>" +
        '<td class="num">' + fmtUSD.format(l.price) + "</td>" +
        '<td class="num" title="' + esc(bandTitle(l.estimated_value)) + '">' +
        fmtUSD.format(l.estimated_value) + "</td>" +
        '<td class="num">' + dealBadge(l.deal_pct) + "</td>" +
        '<td class="num">' +
        (l.mileage ? fmtInt.format(l.mileage) + " mi" : "—") + "</td>" +
        "<td>" + esc(l.location || l.source || "—") + "</td>" +
        "</tr>";
    }).join("");

    document.getElementById("deals-list").innerHTML =
      "<table><thead><tr>" +
      "<th></th>" +
      '<th class="num">Millésime</th><th>Version</th>' +
      '<th class="num">Prix demandé</th><th class="num">Valeur estimée</th>' +
      '<th class="num">Écart</th><th class="num">Kilométrage</th>' +
      "<th>Localisation</th></tr></thead><tbody>" + rows + "</tbody></table>";
  }

  /* ---------- evolution de la cote ---------- */

  function renderHistory() {
    const series = (data.history || [])
      .map((p) => ({ label: monthLabel(p.date), y: historyValue(p) }))
      .filter((p) => p.y != null);
    document.getElementById("history-hint").textContent =
      activeVariant === "Toutes"
        ? "toutes versions confondues"
        : "version " + activeVariant;
    document.getElementById("chart-history").innerHTML = lineChart(series);
  }

  function lineChart(series) {
    if (series.length < 2) return '<p class="empty">Historique insuffisant.</p>';
    const W = 880, H = 320, m = { t: 18, r: 26, b: 46, l: 88 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const ys = series.map((p) => p.y);
    let lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys);
    const pad = (hi - lo) * 0.2 || hi * 0.1;
    lo = Math.max(0, lo - pad);
    hi = hi + pad;
    const n = series.length;
    const X = (i) => m.l + (n <= 1 ? iw / 2 : (iw * i) / (n - 1));
    const Y = (v) => m.t + ih - (ih * (v - lo)) / (hi - lo);

    let grid = "", yLabels = "";
    for (let g = 0; g <= 4; g++) {
      const v = lo + ((hi - lo) * g) / 4;
      const y = Y(v).toFixed(1);
      grid += '<line class="grid" x1="' + m.l + '" y1="' + y +
        '" x2="' + (m.l + iw) + '" y2="' + y + '"/>';
      yLabels += '<text class="axis-y" x="' + (m.l - 10) + '" y="' +
        (Y(v) + 4).toFixed(1) + '">' + compact(v) + "</text>";
    }

    let xLabels = "";
    const step = Math.max(1, Math.round(n / 7));
    series.forEach((p, i) => {
      if (i % step === 0 || i === n - 1) {
        xLabels += '<text class="axis-x" x="' + X(i).toFixed(1) +
          '" y="' + (H - 16) + '">' + p.label + "</text>";
      }
    });

    const linePath = series.map((p, i) =>
      (i ? "L" : "M") + X(i).toFixed(1) + "," + Y(p.y).toFixed(1)).join(" ");
    const areaPath = "M" + X(0).toFixed(1) + "," + Y(lo).toFixed(1) + " " +
      series.map((p, i) => "L" + X(i).toFixed(1) + "," + Y(p.y).toFixed(1)).join(" ") +
      " L" + X(n - 1).toFixed(1) + "," + Y(lo).toFixed(1) + " Z";

    let dots = "";
    series.forEach((p, i) => {
      dots += '<circle class="dot" r="3.6" cx="' + X(i).toFixed(1) +
        '" cy="' + Y(p.y).toFixed(1) + '"><title>' + p.label + " : " +
        fmtUSD.format(p.y) + "</title></circle>";
    });

    return '<svg class="chart" viewBox="0 0 ' + W + " " + H +
      '" role="img" aria-label="Evolution de la cote">' + grid +
      '<path class="area" d="' + areaPath + '"/>' +
      '<path class="line" d="' + linePath + '"/>' +
      dots + yLabels + xLabels + "</svg>";
  }

  /* ---------- prix moyen par millesime ---------- */

  function renderYearChart() {
    const list = filteredListings();
    const years = {};
    list.forEach((l) => {
      (years[l.year] = years[l.year] || []).push(l.price);
    });
    const items = Object.keys(years).sort().map((y) => {
      const ps = years[y].filter((p) => p > 0);
      return {
        label: y,
        value: ps.length ? Math.round(ps.reduce((a, b) => a + b, 0) / ps.length) : 0,
      };
    }).filter((it) => it.value > 0);
    document.getElementById("chart-year").innerHTML = barChart(items);
  }

  function barChart(items) {
    if (!items.length) return '<p class="empty">Pas de données.</p>';
    const W = 430, H = 300, m = { t: 26, r: 14, b: 40, l: 76 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const hi = Math.max.apply(null, items.map((i) => i.value)) * 1.12;
    const n = items.length;
    const slot = iw / n;
    const bw = Math.min(46, slot * 0.62);
    const Y = (v) => m.t + ih - (ih * v) / hi;

    let grid = "", yLabels = "";
    for (let g = 0; g <= 4; g++) {
      const v = (hi * g) / 4;
      const y = Y(v).toFixed(1);
      grid += '<line class="grid" x1="' + m.l + '" y1="' + y + '" x2="' +
        (m.l + iw) + '" y2="' + y + '"/>';
      yLabels += '<text class="axis-y" x="' + (m.l - 9) + '" y="' +
        (Y(v) + 4).toFixed(1) + '">' + compact(v) + "</text>";
    }

    let bars = "";
    items.forEach((it, i) => {
      const cx = m.l + slot * (i + 0.5);
      const y = Y(it.value);
      bars += '<rect class="bar" x="' + (cx - bw / 2).toFixed(1) + '" y="' +
        y.toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' +
        (m.t + ih - y).toFixed(1) + '" rx="3"><title>' + it.label + " : " +
        fmtUSD.format(it.value) + "</title></rect>";
      bars += '<text class="bar-label" x="' + cx.toFixed(1) + '" y="' +
        (y - 7).toFixed(1) + '">' + compact(it.value) + "</text>";
      bars += '<text class="axis-x" x="' + cx.toFixed(1) + '" y="' +
        (H - 14) + '">' + it.label + "</text>";
    });

    return '<svg class="chart" viewBox="0 0 ' + W + " " + H +
      '" role="img" aria-label="Prix moyen par millesime">' +
      grid + bars + yLabels + "</svg>";
  }

  /* ---------- scatter prix vs km ---------- */

  function renderScatter() {
    const list = filteredListings().filter((l) => l.price > 0 && l.mileage > 0);
    const variants = activeVariant === "Toutes" ? VARIANTS : [activeVariant];
    document.getElementById("scatter-legend").innerHTML = variants
      .filter((v) => list.some((l) => l.variant === v))
      .map((v) => '<span><i style="background:' + VARIANT_COLORS[v] +
        '"></i>' + esc(v) + "</span>").join("");
    document.getElementById("chart-scatter").innerHTML = scatterChart(list);
  }

  function scatterChart(list) {
    if (!list.length) return '<p class="empty">Pas de données.</p>';
    const W = 430, H = 300, m = { t: 16, r: 16, b: 44, l: 78 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const maxX = Math.max.apply(null, list.map((l) => l.mileage)) * 1.08;
    const maxY = Math.max.apply(null, list.map((l) => l.price)) * 1.1;
    const X = (v) => m.l + (iw * v) / maxX;
    const Y = (v) => m.t + ih - (ih * v) / maxY;

    let grid = "", yLabels = "", xLabels = "";
    for (let g = 0; g <= 4; g++) {
      const vy = (maxY * g) / 4, y = Y(vy).toFixed(1);
      grid += '<line class="grid" x1="' + m.l + '" y1="' + y + '" x2="' +
        (m.l + iw) + '" y2="' + y + '"/>';
      yLabels += '<text class="axis-y" x="' + (m.l - 9) + '" y="' +
        (Y(vy) + 4).toFixed(1) + '">' + compact(vy) + "</text>";
      const vx = (maxX * g) / 4;
      xLabels += '<text class="axis-x" x="' + X(vx).toFixed(1) + '" y="' +
        (H - 14) + '">' + Math.round(vx / 1000) + " k mi</text>";
    }

    let dots = "";
    list.forEach((l) => {
      dots += '<circle class="point" r="5" cx="' + X(l.mileage).toFixed(1) +
        '" cy="' + Y(l.price).toFixed(1) + '" fill="' +
        (VARIANT_COLORS[l.variant] || PALETTE[0]) +
        '" fill-opacity="0.85"><title>' +
        esc(l.title) + "\n" + fmtUSD.format(l.price) + " — " +
        fmtInt.format(l.mileage) + " mi</title></circle>";
    });

    return '<svg class="chart" viewBox="0 0 ' + W + " " + H +
      '" role="img" aria-label="Prix en fonction du kilometrage">' +
      grid + dots + yLabels + xLabels + "</svg>";
  }

  /* ---------- tableau des annonces ---------- */

  function renderTable() {
    const list = filteredListings().slice();
    const cols = [
      { key: "image_url", label: "", num: false, sortable: false },
      { key: "year", label: "Millésime", num: true },
      { key: "variant", label: "Version", num: false },
      { key: "price", label: "Prix", num: true },
      { key: "estimated_value", label: "Valeur est.", num: true },
      { key: "deal_pct", label: "Écart cote", num: true },
      { key: "mileage", label: "Kilométrage", num: true },
      { key: "location", label: "Localisation", num: false },
      { key: "posted_at", label: "Postée", num: false },
      { key: "vin", label: "VIN", num: false, sortable: false },
      { key: "clean_title", label: "Titre", num: false, sortable: false },
      { key: "avis", label: "Avis", num: false, sortable: false },
    ];

    list.sort((a, b) => {
      // Tri sur "variant" : on suit l'ordre du catalogue (base -> top de gamme)
      // plutot que l'alphabetique, sinon "Spider" arrive apres "Speciale A"
      // et "GT3 RS" avant "GT3 Touring" — pas l'ordre naturel.
      if (sortKey === "variant") {
        const ia = VARIANTS.indexOf(a.variant);
        const ib = VARIANTS.indexOf(b.variant);
        const ra = ia < 0 ? VARIANTS.length : ia;
        const rb = ib < 0 ? VARIANTS.length : ib;
        if (ra !== rb) return sortDir * (ra - rb);
        // Au sein d'une meme version : meilleure affaire d'abord.
        return (b.deal_pct || -Infinity) - (a.deal_pct || -Infinity);
      }
      const va = a[sortKey], vb = b[sortKey];
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "string") return sortDir * va.localeCompare(vb);
      return sortDir * (va - vb);
    });

    document.getElementById("table-count").textContent =
      list.length + (list.length > 1 ? " véhicules" : " véhicule");

    if (!list.length) {
      document.getElementById("listings-table").innerHTML =
        '<p class="empty">Aucune annonce.</p>';
      return;
    }

    const head = cols.map((c) => {
      const sortable = c.sortable !== false;
      const mark = sortable && c.key === sortKey
        ? (sortDir < 0 ? " ↓" : " ↑") : "";
      const cls = ((c.num ? "num " : "") + (sortable ? "" : "nosort")).trim();
      return "<th" + (cls ? ' class="' + cls + '"' : "") +
        (sortable ? ' data-key="' + c.key + '"' : "") + ">" + c.label +
        mark + "</th>";
    }).join("");

    // Groupage par variante quand on trie sur `variant` (clic sur l'en-tete
    // Version, ou toggle "Grouper" actif). Affiche un en-tete de section avec
    // le nom + la couleur de la variante avant chaque groupe.
    const grouped = sortKey === "variant" && activeVariant === "Toutes";
    let body;
    if (grouped) {
      const groups = {};
      const order = [];
      list.forEach(function (l) {
        if (!(l.variant in groups)) {
          groups[l.variant] = [];
          order.push(l.variant);
        }
        groups[l.variant].push(l);
      });
      body = order.map(function (v) {
        const header = '<tr class="group-header"><td colspan="' + cols.length +
          '">' + variantTag(v) + ' <span class="group-count">' +
          groups[v].length + (groups[v].length > 1 ? " annonces" : " annonce") +
          "</span></td></tr>";
        return header + groups[v].map(renderRow).join("");
      }).join("");
    } else {
      body = list.map(renderRow).join("");
    }

    document.getElementById("listings-table").innerHTML =
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body +
      "</tbody></table>";

    document.querySelectorAll("#listings-table thead th").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-key");
        if (!key) return;
        if (key === sortKey) {
          sortDir = -sortDir;
        } else {
          sortKey = key;
          sortDir = key === "variant" || key === "location" ? 1 : -1;
        }
        renderSortControl();
        renderTable();
      });
    });
  }

  function renderRow(l) {
    const vin = vinOf(l);
    const avis = avisFor(l);
    return "<tr>" +
      thumbCell(l) +
      '<td class="num">' + linkedYear(l) + "</td>" +
      "<td>" + variantTag(l.variant) + "</td>" +
      '<td class="num">' + fmtUSD.format(l.price) + "</td>" +
      '<td class="num" title="' + esc(bandTitle(l.estimated_value)) + '">' +
      (l.estimated_value ? fmtUSD.format(l.estimated_value) : "—") + "</td>" +
      '<td class="num">' + dealBadge(l.deal_pct) + "</td>" +
      '<td class="num">' +
      (l.mileage ? fmtInt.format(l.mileage) + " mi" : "—") + "</td>" +
      "<td>" + esc(l.location || "—") + "</td>" +
      '<td title="' + esc(l.posted_at || "") + '">' +
      (relativeDays(l.posted_at) || "—") +
      (isNew(l.posted_at) ? " " + newBadge() : "") + "</td>" +
      '<td class="vin">' + vinLink(vin) + "</td>" +
      "<td>" + titleCell(l) + "</td>" +
      '<td><span class="avis ' + avis.cls + '">' + avis.txt + "</span></td>" +
      "</tr>";
  }

  function variantTag(v) {
    return '<span class="tag" style="background:' +
      (VARIANT_COLORS[v] || PALETTE[0]) + '">' + esc(v) + "</span>";
  }

  /* Menu deroulant "Trier par" : pilote sortKey/sortDir. L'option "Version
     (groupé)" est desactivee quand le filtre version est deja sur une seule
     variante (le groupage n'aurait alors qu'un groupe). Si l'utilisateur trie
     en cliquant sur une autre colonne du tableau, le select affiche
     "(personnalisé)" pour ne pas mentir sur l'etat reel. */
  const SORT_OPTIONS = [
    { value: "deal_pct:desc", label: "Bonne affaire ↓",
      key: "deal_pct", dir: -1 },
    { value: "price:desc", label: "Prix ↓ (cher → bas)",
      key: "price", dir: -1 },
    { value: "price:asc", label: "Prix ↑ (bas → cher)",
      key: "price", dir: 1 },
    { value: "year:desc", label: "Millésime ↓ (récent)",
      key: "year", dir: -1 },
    { value: "year:asc", label: "Millésime ↑ (ancien)",
      key: "year", dir: 1 },
    { value: "variant:asc", label: "Version (groupé)",
      key: "variant", dir: 1 },
  ];

  function renderSortControl() {
    const select = document.getElementById("sort-select");
    if (!select) return;
    const groupingDisabled = activeVariant !== "Toutes";
    // Si on etait en tri groupe et que le filtre vient de cibler une seule
    // version, on retombe sur le tri par defaut (le groupage n'a plus de sens).
    if (groupingDisabled && sortKey === "variant") {
      sortKey = "deal_pct";
      sortDir = -1;
    }
    const current = sortKey + ":" + (sortDir < 0 ? "desc" : "asc");
    const match = SORT_OPTIONS.find(function (o) { return o.value === current; });
    let html = "";
    if (!match) {
      html += '<option value="__custom" selected disabled>(personnalisé)</option>';
    }
    html += SORT_OPTIONS.map(function (opt) {
      const sel = match && opt.value === current ? " selected" : "";
      const dis = (opt.value === "variant:asc" && groupingDisabled)
        ? " disabled" : "";
      return '<option value="' + opt.value + '"' + sel + dis + '>' +
        esc(opt.label) + '</option>';
    }).join("");
    select.innerHTML = html;
    if (!select.dataset.bound) {
      select.addEventListener("change", function () {
        const opt = SORT_OPTIONS.find(function (o) {
          return o.value === select.value;
        });
        if (!opt) return;
        sortKey = opt.key;
        sortDir = opt.dir;
        renderSortControl();
        renderTable();
      });
      select.dataset.bound = "1";
    }
  }

  /* ---------- onglets et filtre par version ---------- */

  function renderTabs() {
    const container = document.getElementById("kind-tabs");
    container.innerHTML = KINDS.map(function (t) {
      const n = data.listings.filter(function (l) {
        return (l.kind || "dealer") === t.kind;
      }).length;
      return '<button class="kind-tab' +
        (t.kind === activeKind ? " active" : "") +
        '" data-kind="' + t.kind + '">' + t.label +
        ' <span class="tab-count">(' + n + ")</span></button>";
    }).join("");
    container.querySelectorAll(".kind-tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activeKind = btn.getAttribute("data-kind");
        activeVariant = "Toutes";
        renderTabs();
        renderPills();
        renderAll();
      });
    });
  }

  function renderPills() {
    const inKind = data.listings.filter(function (l) {
      return (l.kind || "dealer") === activeKind;
    });
    const options = ["Toutes"].concat(VARIANTS);
    document.getElementById("variant-filter").innerHTML = options.map((v) => {
      const count = v === "Toutes"
        ? inKind.length
        : inKind.filter((l) => l.variant === v).length;
      return '<button class="pill' + (v === activeVariant ? " active" : "") +
        '" data-variant="' + esc(v) + '"' + (count ? "" : " disabled") + ">" +
        esc(v) + " (" + count + ")</button>";
    }).join("");

    document.querySelectorAll(".pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.disabled) return;
        activeVariant = btn.getAttribute("data-variant");
        renderPills();
        renderAll();
      });
    });
  }

  /* ---------- en-tete / pied de page ---------- */

  function renderMeta() {
    const iso = data.generated_at;
    const sources = esc((data.sources || []).join(", ") || "—");
    const meta = document.getElementById("meta");

    function paint() {
      meta.innerHTML =
        'Mise à jour&nbsp;: <span title="' + esc(iso) + '">' +
        esc(dateTimeLabel(iso)) + ' <span class="meta-relative">' +
        esc(relativeShort(iso)) + "</span></span>" +
        "<br>Sources&nbsp;: " + sources +
        "<br>" + data.listings.length + " annonces suivies";
    }
    paint();
    setInterval(paint, 60 * 1000);

    document.getElementById("footer-meta").textContent =
      "Données générées le " + dateTimeLabel(iso) + " — " +
      data.listings.length + " annonces (" +
      ((data.sources || []).join(", ") || "—") + ").";
  }

  /* ---------- bouton "Mettre a jour" en un clic ---------- */

  function pad2(n) { return String(n).padStart(2, "0"); }
  function hhmm() {
    const d = new Date();
    return pad2(d.getHours()) + ":" + pad2(d.getMinutes());
  }

  function showUpdateBanner(state, message, actionsHref) {
    let banner = document.getElementById("update-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "update-banner";
      const main = document.querySelector("main");
      main.insertBefore(banner, main.firstChild);
    }
    banner.className = "update-banner " + state;
    const seeRun = actionsHref
      ? '<a href="' + esc(actionsHref) + '" target="_blank" ' +
        'rel="noopener noreferrer">Voir le run ↗</a>'
      : "";
    const reload = state === "refreshed"
      ? '<button class="update-banner-reload">↻ Recharger</button>' : "";
    banner.innerHTML =
      '<span>' + esc(message) + '</span>' +
      '<div class="update-banner-actions">' + seeRun + reload +
      '<button class="update-banner-close" aria-label="Fermer">×</button>' +
      '</div>';
    const r = banner.querySelector(".update-banner-reload");
    if (r) r.addEventListener("click", function () { location.reload(); });
    banner.querySelector(".update-banner-close")
      .addEventListener("click", function () { banner.remove(); });
  }

  function pollForRefresh(initialGeneratedAt, actionsHref) {
    const start = Date.now();
    const slug = activeModelSlug;
    const timer = setInterval(function () {
      if (Date.now() - start > 6 * 60 * 1000) {
        clearInterval(timer);
        return;
      }
      fetch("data/" + encodeURIComponent(slug) + "/listings.json?ts=" + Date.now(),
        { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          if (j && j.generated_at && j.generated_at !== initialGeneratedAt) {
            clearInterval(timer);
            showUpdateBanner("refreshed",
              "✓ Données rafraîchies (générées à " +
              j.generated_at.slice(11, 16) + " UTC) — recharge la page " +
              "pour les voir.", actionsHref);
          }
        })
        .catch(function () { /* ignore */ });
    }, 15000);
  }

  function setupUpdateButton() {
    const cfg = window.COTE_CONFIG || {};
    const btn = document.querySelector(".update-btn");
    if (!btn || !cfg.updateEndpoint) return;
    const original = btn.textContent.trim();
    const actionsHref = btn.getAttribute("href");
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (btn.dataset.busy) return;
      btn.dataset.busy = "1";
      btn.textContent = "⏳ Lancement…";
      showUpdateBanner("running",
        "Demande de mise à jour en cours…", actionsHref);
      fetch(cfg.updateEndpoint, { method: "POST" })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (d) {
          if (d && d.ok) {
            showUpdateBanner("launched",
              "✓ Mise à jour lancée à " + hhmm() +
              ". Les nouvelles données apparaîtront ici dans environ 1 à 2 minutes.",
              actionsHref);
            pollForRefresh(
              (window.COTE && window.COTE.generated_at) || "", actionsHref);
          } else {
            const msg = (d && (d.message || d.error)) || "Échec";
            showUpdateBanner("warn", "⚠ " + msg, actionsHref);
          }
        })
        .catch(function () {
          showUpdateBanner("warn",
            "⚠ Échec réseau — réessaie.", actionsHref);
        })
        .finally(function () {
          setTimeout(function () {
            btn.textContent = original;
            delete btn.dataset.busy;
          }, 3000);
        });
    });
  }

  function renderAll() {
    renderKpis();
    renderInvestment();
    renderDeals();
    renderHistory();
    renderYearChart();
    renderScatter();
    renderSortControl();
    renderTable();
  }

  /* ---------- carte these d'investissement ---------- */

  function renderInvestment() {
    const card = document.getElementById("investment-card");
    if (!card) return;
    const inv = data.model && data.model.investment;
    if (!inv || !inv.summary) {
      card.hidden = true;
      return;
    }
    const verdict = inv.verdict
      ? '<span class="verdict-pill ' + esc(inv.class || "neutral") + '">' +
        esc(inv.verdict) + '</span>'
      : "";
    const focus = inv.focus
      ? '<p class="invest-line"><span class="invest-tag focus">➜ À privilégier</span> ' +
        esc(inv.focus) + '</p>'
      : "";
    const risk = inv.risk
      ? '<p class="invest-line"><span class="invest-tag risk">⚠ Risque</span> ' +
        esc(inv.risk) + '</p>'
      : "";
    card.hidden = false;
    card.innerHTML =
      '<div class="card-head">' +
      '<h2>Verdict investissement ' + verdict + '</h2>' +
      '<span class="card-hint">lecture marché US, à pondérer selon ton profil</span>' +
      '</div>' +
      '<p class="invest-summary">' + esc(inv.summary) + '</p>' +
      focus + risk;
  }

  /* ---------- selecteur marque / modele ---------- */

  function renderPicker(opts) {
    opts = opts || {};
    document.getElementById("dashboard-main").hidden = true;
    document.getElementById("change-car-btn").hidden = true;
    document.getElementById("model-title").textContent = "Cote supercars";
    document.getElementById("model-subtitle").textContent =
      "Choisis une voiture à suivre";
    applyBrandAccent("default");

    const catalog = window.COTE_CATALOG;
    const picker = document.getElementById("car-picker");
    picker.hidden = false;

    if (!catalog || !Array.isArray(catalog.models) || !catalog.models.length) {
      picker.innerHTML = '<div class="picker-inner">' +
        '<h2>Catalogue indisponible</h2>' +
        '<p class="picker-sub">Lance le scraper pour générer ' +
        '<code>data/catalog.js</code>&nbsp;: ' +
        '<code>python3 -m scraper --seed</code>.</p></div>';
      return;
    }

    const brands = {};
    catalog.models.forEach(function (m) {
      (brands[m.brand] = brands[m.brand] || []).push(m);
    });

    let html = '<div class="picker-inner">' +
      '<h2>Quelle voiture veux-tu suivre&nbsp;?</h2>' +
      '<p class="picker-sub">Sélectionne la marque puis le modèle. ' +
      'Tu pourras changer à tout moment depuis le bouton en haut.</p>';

    if (opts.warning) {
      html += '<div class="picker-warning">⚠ ' + esc(opts.warning) + '</div>';
    }

    Object.keys(brands).sort().forEach(function (brand) {
      html += '<div class="brand-block"><h3>' + esc(brand) + '</h3>' +
        '<div class="models">';
      brands[brand].forEach(function (m) {
        const cls = m.has_data ? "" : " no-data";
        const sub = m.has_data
          ? (m.count != null ? m.count + " annonces suivies" : "Données disponibles")
          : "Données à venir";
        const inv = m.investment || {};
        const verdictPill = inv.verdict
          ? '<span class="verdict-pill ' + esc(inv.class || "neutral") +
            '" title="Verdict d\'investissement">' + esc(inv.verdict) + '</span>'
          : "";
        html += '<button class="model-card' + cls +
          '" data-slug="' + esc(m.slug) + '">' +
          '<span class="card-row">' +
          '<span class="model-name">' + esc(m.name) + '</span>' +
          verdictPill +
          '</span>' +
          '<span class="model-years">' + m.year_range[0] + " – " +
          m.year_range[1] + '</span>' +
          '<span class="model-sub">' + esc(sub) + '</span>' +
          '</button>';
      });
      html += '</div></div>';
    });
    html += '</div>';
    picker.innerHTML = html;

    picker.querySelectorAll(".model-card").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const slug = btn.dataset.slug;
        const m = catalog.models.find(function (x) { return x.slug === slug; });
        if (!m) return;
        localStorage.setItem(STORAGE_KEY, slug);
        loadModel(m);
      });
    });
  }

  function applyBrandAccent(brand) {
    const a = BRAND_ACCENTS[brand] || BRAND_ACCENTS.default;
    document.documentElement.style.setProperty("--accent", a.accent);
    document.documentElement.style.setProperty("--accent-soft", a.soft);
  }

  function changeCar() {
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  }

  function bindChangeCar() {
    const btn = document.getElementById("change-car-btn");
    if (btn && !btn.dataset.bound) {
      btn.addEventListener("click", changeCar);
      btn.dataset.bound = "1";
    }
  }

  /* ---------- chargement d'un modele ---------- */

  function loadModel(model) {
    if (!model.has_data) {
      localStorage.removeItem(STORAGE_KEY);
      renderPicker({
        warning: "Pas encore de données pour " + model.brand + " " +
          model.name + ". Le scraper les ajoutera au prochain run. " +
          "Choisis un autre modèle en attendant.",
      });
      return;
    }

    activeModelSlug = model.slug;
    applyBrandAccent(model.brand);

    if (window.COTE && window.COTE.model
        && window.COTE.model.slug === model.slug) {
      onBundleLoaded(model);
      return;
    }

    const url = "data/" + encodeURIComponent(model.slug) +
      "/dashboard.js?ts=" + Date.now();
    const script = document.createElement("script");
    script.src = url;
    script.onload = function () { onBundleLoaded(model); };
    script.onerror = function () {
      localStorage.removeItem(STORAGE_KEY);
      renderPicker({
        warning: "Bundle de données introuvable pour " + model.brand + " " +
          model.name + " (data/" + model.slug + "/dashboard.js).",
      });
    };
    document.body.appendChild(script);
  }

  function onBundleLoaded(model) {
    data = window.COTE;
    if (!data || !Array.isArray(data.listings)) {
      localStorage.removeItem(STORAGE_KEY);
      renderPicker({
        warning: "Bundle invalide pour " + model.brand + " " + model.name + ".",
      });
      return;
    }

    // Choisit l'onglet par defaut sur celui qui contient au moins une annonce
    // (sinon le modele type "tout-encheres" comme F8 affiche 0 par defaut).
    const dealerCount = data.listings.filter(function (l) {
      return (l.kind || "dealer") === "dealer";
    }).length;
    const auctionCount = data.listings.filter(function (l) {
      return l.kind === "auction";
    }).length;
    activeKind = dealerCount > 0 ? "dealer"
      : (auctionCount > 0 ? "auction" : "dealer");
    activeVariant = "Toutes";
    sortKey = "deal_pct";
    sortDir = -1;

    VARIANTS = (data.model && data.model.variants) || model.variants || [];
    VARIANT_COLORS = {};
    VARIANTS.forEach(function (v, i) {
      VARIANT_COLORS[v] = KNOWN_VARIANT_COLORS[v] || PALETTE[i % PALETTE.length];
    });

    RESIDUAL = (data.valuation && data.valuation.residual_pct > 0)
      ? data.valuation.residual_pct : 20;
    DEAL_STRONG = 1.3 * RESIDUAL;
    DEAL_MILD = 0.6 * RESIDUAL;

    document.getElementById("car-picker").hidden = true;
    document.getElementById("dashboard-main").hidden = false;
    document.getElementById("change-car-btn").hidden = false;
    document.getElementById("model-title").textContent =
      "Cote " + data.model.brand + " " + data.model.name;
    document.getElementById("model-subtitle").textContent =
      "Suivi de valeur — marché des États-Unis";

    bindChangeCar();
    renderMeta();
    renderTabs();
    renderPills();
    renderAll();
    setupUpdateButton();
  }

  /* ---------- bootstrap ---------- */

  function bootstrap() {
    const catalog = window.COTE_CATALOG;
    if (!catalog || !Array.isArray(catalog.models)) {
      renderPicker();
      return;
    }
    const slug = localStorage.getItem(STORAGE_KEY);
    const model = slug
      ? catalog.models.find(function (m) { return m.slug === slug; })
      : null;
    if (!model) {
      renderPicker();
      return;
    }
    loadModel(model);
  }

  bootstrap();
})();
