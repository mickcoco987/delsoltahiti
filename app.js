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

  let activeVariant = "Toutes";
  let sortKey = "price";
  let sortDir = -1;

  /* ---------- utilitaires ---------- */

  function compact(v) {
    if (v == null) return "—";
    if (v >= 1e6) return (v / 1e6).toFixed(2).replace(".", ",") + " M$";
    if (v >= 1e3) return Math.round(v / 1e3) + " k$";
    return Math.round(v) + " $";
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
    return { pct: ((to - from) / from) * 100, months: monthsBetween(prev.date, last.date) };
  }

  function monthsBetween(a, b) {
    const da = a.split("-"), db = b.split("-");
    return (db[0] - da[0]) * 12 + (db[1] - da[1]);
  }

  /* ---------- indicateurs (KPI) ---------- */

  function renderKpis() {
    const s = computeStats(filteredListings());
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
      const sign = trend.pct >= 0 ? "+" : "";
      const arrow = trend.pct >= 0 ? "▲" : "▼";
      const cls = trend.pct >= 0 ? "up" : "down";
      cards.push(kpi(
        "Tendance " + (trend.months || 12) + " mois",
        arrow + " " + sign + trend.pct.toFixed(1).replace(".", ",") + " %",
        "cote moyenne",
        cls));
    } else {
      cards.push(kpi("Tendance", "—"));
    }

    document.getElementById("kpis").innerHTML = cards.join("");
  }

  function kpi(label, value, sub, cls) {
    return '<div class="kpi"><div class="kpi-label">' + label +
      '</div><div class="kpi-value ' + (cls || "") + '">' + value +
      "</div>" + (sub ? '<div class="kpi-sub">' + sub + "</div>" : "") +
      "</div>";
  }

  /* ---------- graphique : evolution de la cote ---------- */

  function renderHistory() {
    const series = (data.history || [])
      .map((p) => ({ label: monthLabel(p.date), y: historyValue(p) }))
      .filter((p) => p.y != null);
    const hint = document.getElementById("history-hint");
    hint.textContent = activeVariant === "Toutes"
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
        l.title + "\n" + fmtUSD.format(l.price) + " — " +
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
      { key: "mileage", label: "Kilométrage", num: true },
      { key: "location", label: "Localisation", num: false },
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
      const mark = c.key === sortKey ? (sortDir < 0 ? " ↓" : " ↑") : "";
      return '<th class="' + (c.num ? "num" : "") + '" data-key="' + c.key +
        '">' + c.label + mark + "</th>";
    }).join("");

    const rows = list.map((l) => {
      return "<tr>" +
        '<td class="num">' + l.year + "</td>" +
        "<td>" + variantTag(l.variant) + "</td>" +
        '<td class="num">' + fmtUSD.format(l.price) + "</td>" +
        '<td class="num">' +
        (l.mileage ? fmtInt.format(l.mileage) + " mi" : "—") + "</td>" +
        "<td>" + (l.location || "—") + "</td>" +
        "</tr>";
    }).join("");

    document.getElementById("listings-table").innerHTML =
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + rows +
      "</tbody></table>";

    document.querySelectorAll("thead th").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-key");
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
      '">' + v + "</span>";
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
    const sources = (data.sources || []).join(", ") || "—";
    document.getElementById("meta").innerHTML =
      "Mise à jour&nbsp;: " + gen + "<br>Source&nbsp;: " + sources +
      "<br>" + data.listings.length + " annonces suivies";
    document.getElementById("footer-meta").textContent =
      "Données générées le " + gen + " — " + data.listings.length +
      " annonces (" + sources + ").";
  }

  /* ---------- rendu global ---------- */

  function renderAll() {
    renderKpis();
    renderHistory();
    renderYearChart();
    renderScatter();
    renderTable();
  }

  renderMeta();
  renderPills();
  renderAll();
})();
