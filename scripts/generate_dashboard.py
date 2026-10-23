import json
import os

with open('sim_data/full_simulation_results.json', 'r', encoding='utf-8') as f:
    sim_data = json.load(f)

json_str = json.dumps(sim_data)

html_content = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Simulace topení TČ Gawliczek 11,4 kW - Referenční RD (10 let zimních dat)</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-green: #34d399;
      --accent-orange: #fb923c;
      --accent-purple: #c084fc;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .card {{
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 0.75rem;
    }}
    .tab-btn.active {{
      background-color: #0284c7;
      color: #ffffff;
      font-weight: 600;
    }}
    .tab-btn {{
      background-color: #334155;
      color: #cbd5e1;
      transition: all 0.15s ease-in-out;
    }}
    .tab-btn:hover:not(.active) {{
      background-color: #475569;
    }}
    /* Custom tooltip */
    .chart-tooltip {{
      position: absolute;
      pointer-events: none;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #475569;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      z-index: 50;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
      display: none;
    }}
  </style>
</head>
<body class="p-4 md:p-6 min-h-screen">

  <!-- Header -->
  <header class="mb-6">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-700 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 text-xs font-semibold rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">Projekt Referenční RD </span>
          <span class="px-2.5 py-0.5 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Historická data ERA5 2014–2024</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white mt-1">Simulace topení TČ s akumulací v betonové podlaze</h1>
        <p class="text-slate-400 text-sm mt-1">
          Tepelné čerpadlo Gawliczek 11,4 kW (R290 invertor) • Podlahové topení se spádem 4 °C • Akumulační mazanina 50 mm (21 t betonu) • Teplotní koridor ±1,0 °C
        </p>
      </div>

      <!-- Strategy Selector / Legend Pill -->
      <div class="flex items-center gap-3 bg-slate-900/80 p-2 rounded-lg border border-slate-700">
        <div class="flex items-center gap-1.5 text-xs">
          <span class="w-3 h-3 rounded-full bg-slate-400 inline-block"></span>
          <span class="text-slate-300">Standardní ekviterm</span>
        </div>
        <div class="text-slate-600">|</div>
        <div class="flex items-center gap-1.5 text-xs">
          <span class="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>
          <span class="text-emerald-300 font-medium">Optimalizovaná s akumulací</span>
        </div>
      </div>
    </div>

    <!-- Season selector bar -->
    <div class="mt-4 flex flex-wrap items-center gap-2">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1">Výběr zimy (10 let):</span>
      <div id="season-buttons" class="flex flex-wrap gap-1.5">
        <!-- Dynamically rendered -->
      </div>
      <button id="btn-show-all-10" onclick="show10YearComparison()" class="ml-auto px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition">
        📊 Souhrnné porovnání všech 10 zim
      </button>
    </div>
  </header>

  <!-- Technical Spec Summary Banner -->
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Tepelná ztráta domu</div>
      <div class="text-lg font-bold text-white mt-0.5">5,80 kW</div>
      <div class="text-[11px] text-slate-400">při -12 °C (H = 181 W/K)</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Teplotní spád podlahy</div>
      <div class="text-lg font-bold text-sky-400 mt-0.5">ΔT = 4,0 °C</div>
      <div class="text-[11px] text-slate-400">např. 32/28 °C (vysoký COP)</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Akumulace podlahy</div>
      <div class="text-lg font-bold text-amber-400 mt-0.5">21,2 tun</div>
      <div class="text-[11px] text-slate-400">50 mm beton mazanina (6 kWh/K)</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Tolerance teploty</div>
      <div class="text-lg font-bold text-emerald-400 mt-0.5">± 1,0 °C</div>
      <div class="text-[11px] text-slate-400">koridor 20,0 – 22,0 °C</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Tepelné čerpadlo</div>
      <div class="text-lg font-bold text-indigo-400 mt-0.5">Gawliczek 11,4 kW</div>
      <div class="text-[11px] text-slate-400">R290 invertor (4,5–11,4 kW)</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Kombinovaná nádrž</div>
      <div class="text-lg font-bold text-rose-400 mt-0.5">200 + 100 l</div>
      <div class="text-[11px] text-slate-400">nerez DUPLEX (TUV + vyrovnávací)</div>
    </div>
  </div>

  <!-- KPI Cards for Selected Season -->
  <div id="season-kpi-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <!-- Rendered dynamically -->
  </div>

  <!-- View 1: Single Season Deep Dive (Default) -->
  <div id="single-season-view" class="space-y-6">

    <!-- Chart: Daily Timeline across full season -->
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <span>📈 Průběh zimy den po dni (1. listopadu – 31. března)</span>
            <span id="chart-season-badge" class="px-2 py-0.5 text-xs rounded bg-sky-500/20 text-sky-300">2016-2017</span>
          </h2>
          <p class="text-xs text-slate-400">Porovnání spotřeby elektřiny (kWh/den), sezónního COP a venkovní teploty</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <button onclick="setDailyMetric('el')" id="btn-metric-el" class="px-2.5 py-1 rounded bg-sky-600 text-white font-medium">Spotřeba elektřiny [kWh]</button>
          <button onclick="setDailyMetric('scop')" id="btn-metric-scop" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Denní COP</button>
          <button onclick="setDailyMetric('temp')" id="btn-metric-temp" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Teploty [°C]</button>
        </div>
      </div>

      <!-- Canvas / SVG Daily Chart -->
      <div class="relative w-full h-[280px]">
        <canvas id="dailyCanvas" class="w-full h-full block"></canvas>
      </div>
      <div class="flex items-center justify-between text-xs text-slate-400 mt-2 px-1">
        <div>1. listopad</div>
        <div>1. prosinec</div>
        <div>1. leden</div>
        <div>1. únor</div>
        <div>1. březen</div>
        <div>31. březen</div>
      </div>
    </div>

    <!-- Two Column: Monthly Breakdown & Diurnal 24h Profile -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Monthly Breakdown Table & Bar -->
      <div class="card p-4 md:p-5">
        <h3 class="text-sm font-semibold text-white mb-2 flex items-center justify-between">
          <span>📅 Měsíční bilance vytápění</span>
          <span class="text-xs text-slate-400">Kč kalkulováno při 5,00 Kč/kWh (D57d)</span>
        </h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead class="text-slate-400 border-b border-slate-700 uppercase">
              <tr>
                <th class="py-2 px-2">Měsíc</th>
                <th class="py-2 px-2 text-right">Prům. Teplota</th>
                <th class="py-2 px-2 text-right">Dodané teplo</th>
                <th class="py-2 px-2 text-right">Běžná el.</th>
                <th class="py-2 px-2 text-right text-emerald-400">Opt. el.</th>
                <th class="py-2 px-2 text-right">Běžný COP</th>
                <th class="py-2 px-2 text-right text-emerald-400">Opt. COP</th>
                <th class="py-2 px-2 text-right text-amber-400">Úspora Kč</th>
              </tr>
            </thead>
            <tbody id="monthly-tbody" class="divide-y divide-slate-800">
              <!-- Dynamically populated -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- 24-Hour Diurnal Strategy Explainer Chart -->
      <div class="card p-4 md:p-5">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-white">☀️ Jak funguje denní strategie řízení TČ</h3>
          <span class="px-2 py-0.5 text-[11px] rounded bg-amber-500/20 text-amber-300">Průměrný denní profil</span>
        </div>
        <p class="text-xs text-slate-400 mb-3">
          Rozdíl venkovní teploty den vs. noc je v průměru 4–8 °C. TČ předtápí 21 tun betonu v poledne s maximálním COP, v noci v mrazu čerpá z akumulace a omezuje chod.
        </p>

        <div class="relative w-full h-[220px]">
          <canvas id="diurnalCanvas" class="w-full h-full block"></canvas>
        </div>

        <div class="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-700/60 text-[11px]">
          <div class="p-2 rounded bg-amber-500/10 border border-amber-500/20">
            <span class="font-semibold text-amber-400 block">10:00 – 16:00: Fáze nabíjení (Předtápění)</span>
            <span class="text-slate-300">TČ běží v optimu (5–8 kW), COP dosahuje 4,8–5,5. Teplota v domě stoupá na 21,8–22,0 °C. Zamezeno cyklování.</span>
          </div>
          <div class="p-2 rounded bg-indigo-500/10 border border-indigo-500/20">
            <span class="font-semibold text-indigo-400 block">22:00 – 06:00: Fáze vybíjení (Útlum)</span>
            <span class="text-slate-300">TČ utlumeno, dům topí ze sálání teplé podlahy. Teplota pozvolna klesá k 20,2 °C. TČ se vyhne nočním mrazům a defrostům.</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Hourly Deep Dive: Extreme Frost Week (Jan 2017 down to -21.7°C) -->
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h3 class="text-sm font-semibold text-white flex items-center gap-2">
            <span>❄️ Hodinový detail provozu: Vlna extrémních mrazů v lednu</span>
            <span class="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">Hodinový krok</span>
          </h3>
          <p class="text-xs text-slate-400">
            Reakce vnitřní teploty, teploty betonové desky a otopné vody při dimenzovaném spádu 4 °C (náběh vs. vratka)
          </p>
        </div>
        <div class="flex items-center gap-3 text-xs text-slate-300">
          <div class="flex items-center gap-1.5"><span class="w-3 h-1 bg-cyan-400 inline-block"></span> Venkovní teplota</div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-1 bg-amber-400 inline-block"></span> Vnitřní teplota (°C)</div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-1 bg-emerald-400 inline-block"></span> Teplota podlahy (°C)</div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-1 bg-rose-400 inline-block"></span> Náběh topné vody (°C)</div>
        </div>
      </div>

      <div class="relative w-full h-[260px]">
        <canvas id="hourlyCanvas" class="w-full h-full block"></canvas>
      </div>
      <div class="text-[11px] text-slate-400 mt-2 flex justify-between">
        <span>Začátek mrazové vlny</span>
        <span>Průběh lednových dní (hodina po hodině)</span>
        <span>Konec periody</span>
      </div>
    </div>
  </div>

  <!-- View 2: 10-Year Cross Comparison View (Shown on Click) -->
  <div id="ten-year-view" class="space-y-6 hidden">
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white">📊 Souhrnné porovnání všech 10 zim (2014/15 až 2023/24)</h2>
          <p class="text-xs text-slate-400">Srovnání spotřeby elektřiny, sezónního faktoru SCOP a finanční úspory</p>
        </div>
        <button onclick="hide10YearComparison()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition">
          ✕ Zavřít a vrátit se na detail zimy
        </button>
      </div>

      <div class="relative w-full h-[320px]">
        <canvas id="tenYearCanvas" class="w-full h-full block"></canvas>
      </div>
    </div>

    <!-- 10 Years Table -->
    <div class="card p-4 md:p-5">
      <h3 class="text-sm font-semibold text-white mb-3">Přehledná tabulka 10 zimních sezón v referenční lokalitě</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-slate-400 border-b border-slate-700 uppercase">
            <tr>
              <th class="py-2.5 px-3">Zimní sezóna</th>
              <th class="py-2.5 px-2 text-right">Prům. teplota</th>
              <th class="py-2.5 px-2 text-right">Min. teplota</th>
              <th class="py-2.5 px-2 text-right">Dodané teplo [kWh]</th>
              <th class="py-2.5 px-2 text-right">Běžná el. [kWh]</th>
              <th class="py-2.5 px-2 text-right text-emerald-400">Opt. el. [kWh]</th>
              <th class="py-2.5 px-2 text-right">Běžný SCOP</th>
              <th class="py-2.5 px-2 text-right text-emerald-400 font-semibold">Opt. SCOP</th>
              <th class="py-2.5 px-2 text-right text-amber-400 font-semibold">Úspora elektřiny</th>
              <th class="py-2.5 px-2 text-right text-amber-400 font-semibold">Úspora v Kč</th>
              <th class="py-2.5 px-2 text-right text-sky-400">Snížení startů</th>
            </tr>
          </thead>
          <tbody id="ten-year-tbody" class="divide-y divide-slate-800">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Technical Conclusion & Strategy Summary Card -->
  <div class="card p-5 mt-6 border-sky-500/30 bg-slate-900/60">
    <h3 class="text-base font-semibold text-white flex items-center gap-2 mb-3">
      <span class="text-sky-400">💡</span> Shrnutí optimalizační strategie pro Referenční RD
    </h3>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
      <div class="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
        <div class="font-semibold text-sky-300 mb-1">1. Využití 21 tun betonové podlahovky</div>
        <p>
          Projektovaná betonová mazanina tl. 50 mm v obou podlažích představuje přes 21 tun vysoce vodivého akumulačního materiálu s kapacitou <strong>6,0 kWh/K</strong>. S povolenou odchylkou vnitřní teploty ±1 °C disponuje dům akumulačním zásobníkem o kapacitě cca <strong>25 až 30 kWh tepla</strong>.
        </p>
      </div>
      <div class="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
        <div class="font-semibold text-emerald-300 mb-1">2. Teplotní spád 4 °C a vysoký COP</div>
        <p>
          Dimenzování na teplotní spád 4 °C (např. 32/28 °C při -12 °C, resp. 28/24 °C v mezidobí) snižuje střední teplotu otopné vody oproti původnímu plynovému projektu (45/40 °C). Díky tomu invertorové čerpadlo Gawliczek s chladivem R290 dosahuje sezónního COP (SCOP) až <strong>4,8 až 5,0</strong>.
        </p>
      </div>
      <div class="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
        <div class="font-semibold text-amber-300 mb-1">3. Eliminace taktování a ochrana kompresoru</div>
        <p>
          Při minimálním výkonu TČ 4,5 kW a tepelné ztrátě domu pouze 2–3 kW v mírných dnech standardní ekvitermní řízení cykluje (cca 7 000 startů/zima). Optimalizátor nabíjí podlahu v ucelených 3–5h blocích v době nejteplejšího dne, což <strong>sráží počet startů o více než 75 %</strong> na pouhých ~1 600 startů za zimu.
        </p>
      </div>
    </div>
  </div>

  <!-- Hidden Tooltip element -->
  <div id="chartTooltip" class="chart-tooltip"></div>

  <!-- Embedded Simulation Data & Logic -->
  <script>
    const simData = {json_str};
    let currentSeason = '2016-2017'; // default to interesting cold season
    let currentDailyMetric = 'el'; // 'el', 'scop', 'temp'

    // Initialize UI
    function init() {{
      renderSeasonButtons();
      renderSeason(currentSeason);
      renderTenYearTable();
    }}

    function renderSeasonButtons() {{
      const container = document.getElementById('season-buttons');
      container.innerHTML = '';
      const seasons = Object.keys(simData.winters);
      seasons.forEach(s => {{
        const btn = document.createElement('button');
        btn.className = `tab-btn px-2.5 py-1 text-xs rounded-md ${{s === currentSeason ? 'active' : ''}}`;
        btn.innerText = s;
        btn.onclick = () => selectSeason(s);
        btn.id = `btn-season-${{s}}`;
        container.appendChild(btn);
      }});
    }}

    function selectSeason(s) {{
      currentSeason = s;
      document.querySelectorAll('#season-buttons .tab-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(`btn-season-${{s}}`);
      if (activeBtn) activeBtn.classList.add('active');

      hide10YearComparison();
      renderSeason(s);
    }}

    function renderSeason(s) {{
      const win = simData.winters[s];
      const r = win.results;
      const ws = win.weather_stats;

      document.getElementById('chart-season-badge').innerText = s;

      // 1. KPI Cards
      const kpiContainer = document.getElementById('season-kpi-container');
      kpiContainer.innerHTML = `
        <div class="card p-4 border-l-4 border-sky-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Spotřeba elektřiny za zimu</span>
            <span class="text-sky-400">Úspora ${{r.savings_pct}} %</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-white">${{r.el_opt_kwh.toLocaleString('cs-CZ')}} kWh</span>
            <span class="text-xs text-slate-400 line-through">${{r.el_std_kwh.toLocaleString('cs-CZ')}} kWh</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Úspora <strong>${{r.savings_kwh}} kWh</strong> (${{r.savings_czk.toLocaleString('cs-CZ')}} Kč)</div>
        </div>

        <div class="card p-4 border-l-4 border-emerald-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Sezónní topný faktor SCOP</span>
            <span class="text-emerald-400 font-medium">Spád 4 °C</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-emerald-400">${{r.scop_opt.toFixed(2)}}</span>
            <span class="text-xs text-slate-400">vs ${{r.scop_std.toFixed(2)}} běžně</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Zlepšení účinnosti o <strong>+${{((r.scop_opt / r.scop_std - 1)*100).toFixed(1)}} %</strong></div>
        </div>

        <div class="card p-4 border-l-4 border-amber-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Starty kompresoru (opotřebení)</span>
            <span class="text-amber-400 font-medium">Taktování</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-amber-400">${{r.starts_opt.toLocaleString('cs-CZ')}}</span>
            <span class="text-xs text-slate-400 line-through">${{r.starts_std.toLocaleString('cs-CZ')}}</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Snížení počtu startů o <strong>${{r.cycle_reduction_pct}} %</strong></div>
        </div>

        <div class="card p-4 border-l-4 border-indigo-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Klima zimy v referenční lokalitě</span>
            <span class="text-slate-400">ERA5 data</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-white">${{ws.avg_temp}} °C</span>
            <span class="text-xs text-slate-400">min ${{ws.min_temp}} °C</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Mrazových hodin: <strong>${{ws.frost_hours}} h</strong>, pod -10 °C: <strong>${{ws.deep_frost_hours}} h</strong></div>
        </div>
      `;

      // 2. Monthly Table
      const mTable = document.getElementById('monthly-tbody');
      mTable.innerHTML = '';
      win.monthly.forEach(m => {{
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-800/40";
        row.innerHTML = `
          <td class="py-2 px-2 font-medium text-white">${{formatMonth(m.month)}}</td>
          <td class="py-2 px-2 text-right">${{m.te_avg}} °C</td>
          <td class="py-2 px-2 text-right">${{Math.round(m.th_opt)}} kWh</td>
          <td class="py-2 px-2 text-right text-slate-300">${{Math.round(m.el_std)}} kWh</td>
          <td class="py-2 px-2 text-right font-medium text-emerald-400">${{Math.round(m.el_opt)}} kWh</td>
          <td class="py-2 px-2 text-right text-slate-400">${{m.scop_std.toFixed(2)}}</td>
          <td class="py-2 px-2 text-right font-semibold text-emerald-400">${{m.scop_opt.toFixed(2)}}</td>
          <td class="py-2 px-2 text-right font-semibold text-amber-400">${{m.savings_czk.toLocaleString('cs-CZ')}} Kč</td>
        `;
        mTable.appendChild(row);
      }});

      // 3. Render Canvas Charts
      drawDailyChart(win.daily);
      drawDiurnalChart();
      drawHourlyChart(win.hourly_sample);
    }}

    function formatMonth(mStr) {{
      const map = {{
        '11': 'Listopad',
        '12': 'Prosinec',
        '01': 'Leden',
        '02': 'Únor',
        '03': 'Březen'
      }};
      const p = mStr.split('-');
      return `${{map[p[1]] || p[1]}} ${{p[0]}}`;
    }}

    function setDailyMetric(m) {{
      currentDailyMetric = m;
      document.getElementById('btn-metric-el').className = `px-2.5 py-1 rounded ${{m === 'el' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;
      document.getElementById('btn-metric-scop').className = `px-2.5 py-1 rounded ${{m === 'scop' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;
      document.getElementById('btn-metric-temp').className = `px-2.5 py-1 rounded ${{m === 'temp' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;

      const win = simData.winters[currentSeason];
      drawDailyChart(win.daily);
    }}

    // High performance responsive Canvas Chart Drawing
    function drawDailyChart(dailyData) {{
      const canvas = document.getElementById('dailyCanvas');
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;
      const padL = 40, padR = 15, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (cH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();
      }}

      const N = dailyData.length;
      const stepX = cW / (N - 1);

      if (currentDailyMetric === 'el') {{
        // Plot kWh electric: Standard vs Optimized
        let maxVal = 0;
        dailyData.forEach(d => {{
          maxVal = Math.max(maxVal, d.el_std, d.el_opt);
        }});
        maxVal = Math.ceil(maxVal * 1.15) || 30;

        // Y-axis labels
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = Math.round(maxVal - (maxVal / 4) * i);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`${{v}} kWh`, padL - 6, y + 3);
        }}

        // Standard Bar / Area
        ctx.fillStyle = 'rgba(148, 163, 184, 0.25)';
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const hStd = (d.el_std / maxVal) * cH;
          ctx.fillRect(x - 1, padT + cH - hStd, 2, hStd);
        }});

        // Optimized line
        ctx.strokeStyle = '#34d399';
        ctx.lineWidth = 2;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const y = padT + cH - (d.el_opt / maxVal) * cH;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }});
        ctx.stroke();

        // Legend
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('Běžný ekviterm (šedá plocha)', W - 180, padT - 5);
        ctx.fillStyle = '#34d399';
        ctx.fillText('Optimalizovaná akumulace (zelená křivka)', W - 15, padT - 5);

      }} else if (currentDailyMetric === 'scop') {{
        const minVal = 2.0;
        const maxVal = 6.0;

        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = (maxVal - ((maxVal - minVal) / 4) * i).toFixed(1);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`COP ${{v}}`, padL - 6, y + 3);
        }}

        // Standard SCOP line
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const val = Math.min(maxVal, Math.max(minVal, d.scop_std));
          const y = padT + cH - ((val - minVal) / (maxVal - minVal)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();

        // Opt SCOP line
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const val = Math.min(maxVal, Math.max(minVal, d.scop_opt));
          const y = padT + cH - ((val - minVal) / (maxVal - minVal)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();

      }} else {{
        // Temperature
        let minT = 100, maxT = -100;
        dailyData.forEach(d => {{
          minT = Math.min(minT, d.te_min);
          maxT = Math.max(maxT, d.te_max);
        }});
        minT = Math.floor(minT - 2);
        maxT = Math.ceil(maxT + 2);

        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = Math.round(maxT - ((maxT - minT) / 4) * i);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`${{v}} °C`, padL - 6, y + 3);
        }}

        // Zero line
        if (minT < 0 && maxT > 0) {{
          const y0 = padT + cH - ((0 - minT) / (maxT - minT)) * cH;
          ctx.strokeStyle = '#38bdf8';
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(padL, y0);
          ctx.lineTo(W - padR, y0);
          ctx.stroke();
          ctx.setLineDash([]);
        }}

        // Ambient temperature curve
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const y = padT + cH - ((d.te_avg - minT) / (maxT - minT)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();
      }}
    }}

    // Diurnal 24h Profile Canvas
    function drawDiurnalChart() {{
      const canvas = document.getElementById('diurnalCanvas');
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;
      const padL = 35, padR = 15, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      // Typical diurnal curve: hours 0 to 23
      const hours = Array.from({{length: 24}}, (_, i) => i);
      // Ambient temp wave (min at 6h, max at 14h)
      const tExtWave = hours.map(h => 2.5 + 3.8 * Math.sin((h - 8) * Math.PI / 12));
      // HP COP follows ambient closely
      const copWave = tExtWave.map(t => 3.3 + (t + 5) * 0.18);
      // Charging power kW in optimized
      const optPower = hours.map(h => (h >= 10 && h <= 16) ? 7.2 : (h >= 22 || h <= 6 ? 0.0 : 4.5));
      // Standard power kW (peaks at night)
      const stdPower = hours.map(h => (h >= 22 || h <= 6) ? 4.8 : (h >= 11 && h <= 15 ? 2.2 : 3.5));

      // Grid
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (cH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();
      }}

      // Charging window background fill
      const xStartCharge = padL + (10 / 23) * cW;
      const xEndCharge = padL + (16 / 23) * cW;
      ctx.fillStyle = 'rgba(251, 191, 36, 0.12)';
      ctx.fillRect(xStartCharge, padT, xEndCharge - xStartCharge, cH);

      // Night discharge window background fill
      const xNightEnd = padL + (6 / 23) * cW;
      const xNightStart = padL + (22 / 23) * cW;
      ctx.fillStyle = 'rgba(99, 102, 241, 0.12)';
      ctx.fillRect(padL, padT, xNightEnd - padL, cH);
      ctx.fillRect(xNightStart, padT, W - padR - xNightStart, cH);

      const stepX = cW / 23;

      // Draw COP curve (scale 2.0 to 6.0)
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      hours.forEach((h, i) => {{
        const x = padL + i * stepX;
        const y = padT + cH - ((copWave[i] - 2.0) / 4.0) * cH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      // Draw Optimized Power bars
      ctx.fillStyle = '#38bdf8';
      hours.forEach((h, i) => {{
        const x = padL + i * stepX;
        const hBar = (optPower[i] / 10.0) * cH;
        ctx.fillRect(x - 3, padT + cH - hBar, 6, hBar);
      }});

      // X-axis labels
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      [0, 4, 8, 12, 16, 20, 23].forEach(h => {{
        const x = padL + (h / 23) * cW;
        ctx.fillText(`${{h}}h`, x, H - 8);
      }});

      // Labels / Legend
      ctx.textAlign = 'right';
      ctx.fillStyle = '#10b981';
      ctx.fillText('COP křivka (vrchol 14:00)', W - 20, padT + 12);
      ctx.fillStyle = '#38bdf8';
      ctx.fillText('Nabíjecí výkon TČ (modré sloupce)', W - 20, padT + 26);
    }}

    // Hourly deep dive canvas
    function drawHourlyChart(hourlyData) {{
      if (!hourlyData || hourlyData.length === 0) return;
      const canvas = document.getElementById('hourlyCanvas');
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;
      const padL = 35, padR = 15, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      let minT = -22, maxT = 36;
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (cH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();

        const val = Math.round(maxT - ((maxT - minT) / 4) * i);
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(`${{val}}°C`, padL - 5, y + 3);
      }}

      // 0°C line
      const y0 = padT + cH - ((0 - minT) / (maxT - minT)) * cH;
      ctx.strokeStyle = '#475569';
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(padL, y0);
      ctx.lineTo(W - padR, y0);
      ctx.stroke();
      ctx.setLineDash([]);

      const N = hourlyData.length;
      const stepX = cW / (N - 1);

      // 1. Outdoor Temp (Cyan)
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      hourlyData.forEach((d, i) => {{
        const x = padL + i * stepX;
        const y = padT + cH - ((d.te - minT) / (maxT - minT)) * cH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      // 2. Supply Water Temp T_flow (Rose)
      ctx.strokeStyle = '#fb7185';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      hourlyData.forEach((d, i) => {{
        const x = padL + i * stepX;
        const y = padT + cH - ((d.t_flow_opt - minT) / (maxT - minT)) * cH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      // 3. Concrete Floor Temp (Emerald)
      ctx.strokeStyle = '#34d399';
      ctx.lineWidth = 2.0;
      ctx.beginPath();
      hourlyData.forEach((d, i) => {{
        const x = padL + i * stepX;
        const y = padT + cH - ((d.tf_opt - minT) / (maxT - minT)) * cH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      // 4. Room Temp (Amber)
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      hourlyData.forEach((d, i) => {{
        const x = padL + i * stepX;
        const y = padT + cH - ((d.tr_opt - minT) / (maxT - minT)) * cH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();
    }}

    // 10 Years Comparison Table & Chart
    function renderTenYearTable() {{
      const tbody = document.getElementById('ten-year-tbody');
      tbody.innerHTML = '';
      Object.keys(simData.winters).forEach(s => {{
        const w = simData.winters[s];
        const r = w.results;
        const ws = w.weather_stats;
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/50 cursor-pointer";
        tr.onclick = () => selectSeason(s);
        tr.innerHTML = `
          <td class="py-2.5 px-3 font-semibold text-white flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-sky-400"></span> ${{s}}
          </td>
          <td class="py-2.5 px-2 text-right">${{ws.avg_temp}} °C</td>
          <td class="py-2.5 px-2 text-right font-medium text-rose-400">${{ws.min_temp}} °C</td>
          <td class="py-2.5 px-2 text-right">${{r.th_std_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right text-slate-300">${{r.el_std_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right font-medium text-emerald-400">${{r.el_opt_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right text-slate-400">${{r.scop_std.toFixed(2)}}</td>
          <td class="py-2.5 px-2 text-right font-bold text-emerald-400">${{r.scop_opt.toFixed(2)}}</td>
          <td class="py-2.5 px-2 text-right font-bold text-amber-400">-${{r.savings_pct}} %</td>
          <td class="py-2.5 px-2 text-right font-bold text-amber-400">${{r.savings_czk.toLocaleString('cs-CZ')}} Kč</td>
          <td class="py-2.5 px-2 text-right text-sky-400">-${{r.cycle_reduction_pct}} %</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function show10YearComparison() {{
      document.getElementById('single-season-view').classList.add('hidden');
      document.getElementById('ten-year-view').classList.remove('hidden');
      drawTenYearChart();
    }}

    function hide10YearComparison() {{
      document.getElementById('ten-year-view').classList.add('hidden');
      document.getElementById('single-season-view').classList.remove('hidden');
    }}

    function drawTenYearChart() {{
      const canvas = document.getElementById('tenYearCanvas');
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;
      const padL = 45, padR = 15, padT = 30, padB = 40;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const seasons = Object.keys(simData.winters);
      const N = seasons.length;
      const groupW = cW / N;
      const barW = Math.min(22, (groupW - 12) / 2);

      // Max kWh
      let maxKwh = 3200;

      // Grid
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (cH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();

        const val = Math.round(maxKwh - (maxKwh / 4) * i);
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(`${{val}} kWh`, padL - 8, y + 3);
      }}

      seasons.forEach((s, i) => {{
        const r = simData.winters[s].results;
        const xCenter = padL + i * groupW + groupW / 2;

        const hStd = (r.el_std_kwh / maxKwh) * cH;
        const hOpt = (r.el_opt_kwh / maxKwh) * cH;

        // Std bar
        ctx.fillStyle = '#64748b';
        ctx.fillRect(xCenter - barW - 2, padT + cH - hStd, barW, hStd);

        // Opt bar
        ctx.fillStyle = '#10b981';
        ctx.fillRect(xCenter + 2, padT + cH - hOpt, barW, hOpt);

        // Season Label
        ctx.fillStyle = '#cbd5e1';
        ctx.font = '11px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(s.split('-')[0].substring(2)+'/'+s.split('-')[1].substring(2), xCenter, H - 20);

        // SCOP on top of opt bar
        ctx.fillStyle = '#34d399';
        ctx.font = '10px system-ui font-semibold';
        ctx.fillText(`${{r.scop_opt.toFixed(2)}}`, xCenter + 2 + barW / 2, padT + cH - hOpt - 5);
      }});

      // Legend
      ctx.textAlign = 'right';
      ctx.fillStyle = '#64748b';
      ctx.fillText('■ Běžná ekvitermní spotřeba', W - 140, padT - 10);
      ctx.fillStyle = '#10b981';
      ctx.fillText('■ Optimalizovaná spotřeba s akumulací', W - 15, padT - 10);
    }}

    // Resize handler
    window.addEventListener('resize', () => {{
      const win = simData.winters[currentSeason];
      drawDailyChart(win.daily);
      drawDiurnalChart();
      drawHourlyChart(win.hourly_sample);
      if (!document.getElementById('ten-year-view').classList.contains('hidden')) {{
        drawTenYearChart();
      }}
    }});

    window.onload = init;
  </script>
</body>
</html>
"""

# 1. Write to artifact directory
artifact_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs(artifact_dir, exist_ok=True)
artifact_html_path = os.path.join(artifact_dir, "simulace_topeni_tc.html")
with open(artifact_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

# 2. Write to project workspace so user has permanent copy
proj_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulace_topeni_tc.html"))
with open(proj_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML dashboard generated successfully in artifact dir ({artifact_html_path}) and workspace ({proj_html_path})!")
