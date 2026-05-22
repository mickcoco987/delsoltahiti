/* Tableau de bord de la cote Ferrari 458 Italia (marche US).
   Lit les donnees produites par le scraper dans window.COTE (data/dashboard.js).
   Graphiques en SVG, sans dependance externe. */
"use strict";

(function () {
  const data = window.COTE;
  const main = document.querySelector("main");

  if (!data || !Array.isArray(data.listings)) {
    main.innerHTML =
      '<div class="banner">Donnees indisponibles. Lancez le scraper pour ' +
      "les generer&nbsp;: <code>python -m scraper --seed</code>, puis " +
      "servez le dossier&nbsp;: <code>python -m http.server</code>.</div>";
    return;
  }

  const VARIANTS = ["Italia", "Spider", "Speciale", "Speciale A"];
  const VARIANT_COLORS = {
    Italia: "var(--c-italia)",
    Spider: "var(--c-spider)",
    Speciale: "var(--c-speciale)",
    "Speciale A": "var(--c-speciale-a)",
  };
  const MONTHS_FR = ["janv.", "fevr.", "mars", "avr.", "mai", "juin",
    "juil.", "aout", "sept.", "oct.", "nov.", "dec."];

  const fmtUSD = new Intl.NumberFormat("fr-FR",
    { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const fmtInt = new Intl.NumberFormat("fr-FR");

  // Imprecision du modele de valeur (en %). Les seuils de bonne affaire en
  // sont des multiples : on ne signale que les ecarts sortant du bruit.
  const RESIDUAL = (data.valuation && data.valuation.residual_pct > 0)
    ? data.valuation.residual_pct : 20;
  const DEAL_STRONG = 1.3 * RESIDUAL;   // "bonne affaire"
  const DEAL_MILD = 0.6 * RESIDUAL;     // "sous la cote"

  let activeVariant = "Toutes";
  let sortKey = "deal_pct";
  let sortDir = -1;

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

  function isHttpUrl(u) {
    return /^https?:\/\//i.test(String(u || ""));
  }

  // Cellule millesime cliquable vers l'annonce d'origine si l'URL est valide.
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
    return activeVariant === "Toutes"
      ? data.listings
      : data.listings.filter((l) => l.variant === activeVariant);
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

  /* ---------- score de bonne affaire (calibre sur le bruit du modele) ------ */

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

  /* ---------- VIN et avis ---------- */

  const VIN_RE = /ZFF[0-9A-HJ-NPR-Z]{14}/i;

  // VIN fourni par la source, sinon extrait de l'URL de l'annonce.
  function vinOf(l) {
    if (l.vin) return String(l.vin).toUpperCase();
    const m = VIN_RE.exec(l.url || "");
    return m ? m[0].toUpperCase() : "";
  }

  // VIN cliquable vers epicvin : rapport d'historique du vehicule par VIN.
  function vinLink(vin) {
    if (!vin) return "—";
    return '<a href="https://epicvin.com/fr/' +
      'check-vin-number-and-get-the-vehicle-history-report/checkout/' +
      encodeURIComponent(vin.toLowerCase()) +
      '" target="_blank" rel="noopener noreferrer" ' +
      'title="Rapport d\'historique du véhicule par VIN (epicvin)">' +
      esc(vin) + "</a>";
  }

  // Cellule "Titre" : statut de titre propre fourni par la source.
  function titleCell(l) {
    if (l.clean_title === true) return '<span class="avis good">Propre</span>';
    if (l.clean_title === false) return '<span class="avis over">⚠ Non propre</span>';
    return "—";
  }

  // Avis automatique : drapeaux modification/titre puis position vs cote.
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

  /* ---------- section bonnes affaires ---------- */

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
        '<td class="num">' + linkedYear(l) + "</td>" +
        "<td>" + variantTag(l.variant) + "</td>" +
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
      '<th class="num">Millésime</th><th>Version</th>' +
      '<th class="num">Prix demandé</th><th class="num">Valeur estimée</th>' +
      '<th class="num">Écart</th><th class="num">Kilométrage</th>' +
      "<th>Localisation</th></tr></thead><tbody>" + rows + "</tbody></table>";
  }

  /* ---------- graphique : evolution de la cote ---------- */

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

  /* ---------- graphique : prix moyen par millesime ---------- */

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

  /* ---------- graphique : prix vs kilometrage ---------- */

  function renderScatter() {
    const list = filteredListings().filter((l) => l.price > 0 && l.mileage > 0);
    const variants = activeVariant === "Toutes" ? VARIANTS : [activeVariant];
    document.getElementById("scatter-legend").innerHTML = variants
      .filter((v) => list.some((l) => l.variant === v))
      .map((v) => '<span><i style="background:' + VARIANT_COLORS[v] +
        '"></i>' + v + "</span>").join("");
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
        VARIANT_COLORS[l.variant] + '" fill-opacity="0.85"><title>' +
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
      { key: "year", label: "Millésime", num: true },
      { key: "variant", label: "Version", num: false },
      { key: "price", label: "Prix", num: true },
      { key: "estimated_value", label: "Valeur est.", num: true },
      { key: "deal_pct", label: "Écart cote", num: true },
      { key: "mileage", label: "Kilométrage", num: true },
      { key: "location", label: "Localisation", num: false },
      { key: "vin", label: "VIN", num: false, sortable: false },
      { key: "clean_title", label: "Titre", num: false, sortable: false },
      { key: "avis", label: "Avis", num: false, sortable: false },
    ];

    list.sort((a, b) => {
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

    const rows = list.map((l) => {
      const vin = vinOf(l);
      const avis = avisFor(l);
      return "<tr>" +
        '<td class="num">' + linkedYear(l) + "</td>" +
        "<td>" + variantTag(l.variant) + "</td>" +
        '<td class="num">' + fmtUSD.format(l.price) + "</td>" +
        '<td class="num" title="' + esc(bandTitle(l.estimated_value)) + '">' +
        (l.estimated_value ? fmtUSD.format(l.estimated_value) : "—") + "</td>" +
        '<td class="num">' + dealBadge(l.deal_pct) + "</td>" +
        '<td class="num">' +
        (l.mileage ? fmtInt.format(l.mileage) + " mi" : "—") + "</td>" +
        "<td>" + esc(l.location || "—") + "</td>" +
        '<td class="vin">' + vinLink(vin) + "</td>" +
        "<td>" + titleCell(l) + "</td>" +
        '<td><span class="avis ' + avis.cls + '">' + avis.txt + "</span></td>" +
        "</tr>";
    }).join("");

    document.getElementById("listings-table").innerHTML =
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + rows +
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
        renderTable();
      });
    });
  }

  function variantTag(v) {
    return '<span class="tag" style="background:' + VARIANT_COLORS[v] +
      '">' + esc(v) + "</span>";
  }

  /* ---------- filtre par version ---------- */

  function renderPills() {
    const options = ["Toutes"].concat(VARIANTS);
    document.getElementById("variant-filter").innerHTML = options.map((v) => {
      const count = v === "Toutes"
        ? data.listings.length
        : data.listings.filter((l) => l.variant === v).length;
      return '<button class="pill' + (v === activeVariant ? " active" : "") +
        '" data-variant="' + v + '"' + (count ? "" : " disabled") + ">" +
        v + " (" + count + ")</button>";
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
    const gen = dateLabel(data.generated_at);
    const sources = esc((data.sources || []).join(", ") || "—");
    document.getElementById("meta").innerHTML =
      "Mise à jour&nbsp;: " + esc(gen) + "<br>Sources&nbsp;: " + sources +
      "<br>" + data.listings.length + " annonces suivies";
    document.getElementById("footer-meta").textContent =
      "Données générées le " + gen + " — " + data.listings.length +
      " annonces (" + ((data.sources || []).join(", ") || "—") + ").";
  }

  /* ---------- bouton "Mettre a jour" en un clic ---------- */

  // Si COTE_CONFIG.updateEndpoint est defini, le bouton declenche le workflow
  // via le Worker Cloudflare au lieu d'ouvrir la page GitHub Actions.
  function setupUpdateButton() {
    const cfg = window.COTE_CONFIG || {};
    const btn = document.querySelector(".update-btn");
    if (!btn || !cfg.updateEndpoint) return;
    const original = btn.textContent.trim();
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (btn.dataset.busy) return;
      btn.dataset.busy = "1";
      btn.textContent = "⏳ Lancement…";
      fetch(cfg.updateEndpoint, { method: "POST" })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (d) {
          if (d && d.ok) {
            btn.textContent = "✓ Mise à jour lancée";
          } else {
            const msg = (d && (d.message || d.error)) || "Échec";
            btn.textContent = "⚠ " + msg;
          }
        })
        .catch(function () { btn.textContent = "⚠ Échec — réessaie"; })
        .finally(function () {
          setTimeout(function () {
            btn.textContent = original;
            delete btn.dataset.busy;
          }, 6000);
        });
    });
  }

  /* ---------- rendu global ---------- */

  function renderAll() {
    renderKpis();
    renderDeals();
    renderHistory();
    renderYearChart();
    renderScatter();
    renderTable();
  }

  renderMeta();
  renderPills();
  renderAll();
  setupUpdateButton();
})();
