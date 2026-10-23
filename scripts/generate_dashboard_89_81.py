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
  <title>Simulace topení TČ Gawliczek (8,9 kW vs 8,1 kW Ultra tiché) - Referenční RD</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
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
    .model-btn.active {{
      background-color: #0284c7;
      color: #ffffff;
      font-weight: 600;
      border-color: #38bdf8;
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
          <span class="px-2.5 py-0.5 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">10 zimních sezón ERA5 (2014–2024)</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white mt-1">Srovnávací simulace topení TČ: 8,9 kW Invertor vs. 8,1 kW Ultra tiché</h1>
        <p class="text-slate-400 text-sm mt-1">
          Podlahové vytápění dimenzované na spád 4 °C • Akumulační mazanina 50 mm (21 t betonu) • Koridor vnitřní teploty ±1,0 °C
        </p>
      </div>

      <!-- Model Switcher Pill -->
      <div class="bg-slate-900/90 p-1.5 rounded-xl border border-slate-700 flex items-center gap-1.5 shadow-lg">
        <button id="btn-model-89kw" onclick="selectModel('89kw')" class="model-btn active px-3 py-1.5 text-xs rounded-lg border border-transparent transition flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-sky-400"></span>
          <span>8,9 kW R290</span>
          <span class="bg-sky-950 text-sky-300 text-[10px] px-1.5 py-0.2 rounded font-bold">58 630 Kč</span>
        </button>
        <button id="btn-model-81kw" onclick="selectModel('81kw')" class="model-btn px-3 py-1.5 text-xs rounded-lg border border-transparent text-slate-300 hover:text-white transition flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>8,1 kW Ultra tiché</span>
          <span class="bg-emerald-950 text-emerald-300 text-[10px] px-1.5 py-0.2 rounded font-bold">TOP SCOP</span>
        </button>
      </div>
    </div>

    <!-- Season selector bar -->
    <div class="mt-4 flex flex-wrap items-center gap-2">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1">Výběr zimy (10 sezón):</span>
      <div id="season-buttons" class="flex flex-wrap gap-1.5">
        <!-- Dynamically rendered -->
      </div>
      <button id="btn-show-all-10" onclick="show10YearComparison()" class="ml-auto px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5">
        <span>📊 Souhrnné porovnání 10 zim</span>
      </button>
    </div>
  </header>

  <!-- Technical Specs Banner -->
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
      <div class="text-[11px] text-slate-400">50 mm beton (6,0 kWh/K)</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Tolerance teploty</div>
      <div class="text-lg font-bold text-emerald-400 mt-0.5">± 1,0 °C</div>
      <div class="text-[11px] text-slate-400">koridor 20,0 – 22,0 °C</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Vybraný model TČ</div>
      <div id="spec-hp-name" class="text-sm font-bold text-sky-400 mt-1 truncate">8,9 kW Invertor</div>
      <div id="spec-hp-mod" class="text-[11px] text-slate-400">Modulace: 2,5 – 8,9 kW</div>
    </div>
    <div class="card p-3">
      <div class="text-[11px] font-medium text-slate-400 uppercase">Cena & Hlučnost</div>
      <div id="spec-hp-price" class="text-sm font-bold text-rose-400 mt-1">58 630 Kč bez DPH</div>
      <div id="spec-hp-noise" class="text-[11px] text-slate-400">Hluk: ~48-52 dB(A)</div>
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
          <p class="text-xs text-slate-400">Srovnání spotřeby elektřiny (kWh/den), sezónního COP a venkovní teploty</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <button onclick="setDailyMetric('el')" id="btn-metric-el" class="px-2.5 py-1 rounded bg-sky-600 text-white font-medium">Spotřeba elektřiny [kWh]</button>
          <button onclick="setDailyMetric('scop')" id="btn-metric-scop" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Denní COP</button>
          <button onclick="setDailyMetric('temp')" id="btn-metric-temp" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Teploty [°C]</button>
        </div>
      </div>

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

    <!-- Two Column: Monthly Breakdown & Model Comparison -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Monthly Breakdown Table -->
      <div class="card p-4 md:p-5">
        <h3 class="text-sm font-semibold text-white mb-2 flex items-center justify-between">
          <span>📅 Měsíční bilance vytápění</span>
          <span class="text-xs text-slate-400">5,00 Kč/kWh (D57d)</span>
        </h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead class="text-slate-400 border-b border-slate-700 uppercase">
              <tr>
                <th class="py-2 px-2">Měsíc</th>
                <th class="py-2 px-2 text-right">Prům. Teplota</th>
                <th class="py-2 px-2 text-right">8,9kW Běžná</th>
                <th class="py-2 px-2 text-right text-sky-400">8,9kW Opt.</th>
                <th class="py-2 px-2 text-right text-emerald-400 font-semibold">8,1kW Opt.</th>
                <th class="py-2 px-2 text-right text-sky-400 font-semibold">8,9kW SCOP</th>
                <th class="py-2 px-2 text-right text-emerald-400 font-semibold">8,1kW SCOP</th>
              </tr>
            </thead>
            <tbody id="monthly-tbody" class="divide-y divide-slate-800">
              <!-- Dynamically populated -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Direct Head-to-Head Comparison Card -->
      <div class="card p-4 md:p-5">
        <h3 class="text-sm font-semibold text-white mb-2 flex items-center justify-between">
          <span>⚖️ Přímé srovnání obou optimálních čerpadel</span>
          <span class="px-2 py-0.5 text-[11px] rounded bg-sky-500/20 text-sky-300">Zima <span id="h2h-season-label">2016-2017</span></span>
        </h3>
        <div class="space-y-3 mt-3 text-xs">
          <div class="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
            <div class="flex justify-between items-center mb-1">
              <span class="text-slate-300 font-medium">Sezónní topný faktor SCOP</span>
              <span class="text-emerald-400 font-bold text-sm" id="h2h-scop-diff">+0.30 vyšší pro 8,1 kW</span>
            </div>
            <div class="w-full bg-slate-700 h-2 rounded-full overflow-hidden flex">
              <div id="bar-scop-89" class="bg-sky-500 h-full" style="width: 48%"></div>
              <div id="bar-scop-81" class="bg-emerald-400 h-full" style="width: 52%"></div>
            </div>
            <div class="flex justify-between text-[11px] text-slate-400 mt-1">
              <span id="h2h-scop-89">8,9 kW Invertor: 4.47</span>
              <span id="h2h-scop-81" class="text-emerald-400 font-semibold">8,1 kW Ultra tiché: 4.77</span>
            </div>
          </div>

          <div class="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
            <div class="flex justify-between items-center mb-1">
              <span class="text-slate-300 font-medium">Spotřeba elektřiny za zimu [kWh]</span>
              <span class="text-emerald-400 font-bold text-sm" id="h2h-el-diff">-153 kWh pro 8,1 kW</span>
            </div>
            <div class="flex justify-between text-[11px] text-slate-400 mt-1">
              <span id="h2h-el-89">8,9 kW Opt: 2 388 kWh (11 940 Kč)</span>
              <span id="h2h-el-81" class="text-emerald-400 font-semibold">8,1 kW Opt: 2 235 kWh (11 175 Kč)</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 text-[11px]">
            <div class="p-2.5 rounded bg-sky-950/40 border border-sky-800/40">
              <span class="font-bold text-sky-400 block mb-0.5">8,9 kW Invertor (Cenový favorit)</span>
              <span class="text-slate-300">Cena <strong>58 630 Kč bez DPH</strong>. Kompresor Highly/Hitachi. Vynikající poměr cena/výkon.</span>
            </div>
            <div class="p-2.5 rounded bg-emerald-950/40 border border-emerald-800/40">
              <span class="font-bold text-emerald-400 block mb-0.5">8,1 kW Ultra tiché (Komfort favorit)</span>
              <span class="text-slate-300">Cena <strong>69 950 Kč bez DPH</strong>. Kompresor Panasonic, hluk jen 35–38 dB, nejvyšší SCOP.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- View 2: 10-Year Cross Comparison View -->
  <div id="ten-year-view" class="space-y-6 hidden">
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white">📊 Souhrnné porovnání všech 10 zim (2014/15 až 2023/24)</h2>
          <p class="text-xs text-slate-400">Srovnání spotřeby elektřiny obou čerpadel a sezónního SCOP</p>
        </div>
        <button onclick="hide10YearComparison()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition">
          ✕ Zpět na detail zimy
        </button>
      </div>

      <div class="relative w-full h-[320px]">
        <canvas id="tenYearCanvas" class="w-full h-full block"></canvas>
      </div>
    </div>

    <!-- 10 Years Table -->
    <div class="card p-4 md:p-5">
      <h3 class="text-sm font-semibold text-white mb-3">Kompletní srovnání 10 zimních sezón v referenční lokalitě</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-slate-400 border-b border-slate-700 uppercase">
            <tr>
              <th class="py-2.5 px-3">Zima</th>
              <th class="py-2.5 px-2 text-right">Prům. T</th>
              <th class="py-2.5 px-2 text-right">Min. T</th>
              <th class="py-2.5 px-2 text-right">8,9kW Běžná [kWh]</th>
              <th class="py-2.5 px-2 text-right text-sky-400 font-semibold">8,9kW Opt [kWh]</th>
              <th class="py-2.5 px-2 text-right text-emerald-400 font-bold">8,1kW Opt [kWh]</th>
              <th class="py-2.5 px-2 text-right text-sky-400">SCOP 8,9</th>
              <th class="py-2.5 px-2 text-right text-emerald-400 font-bold">SCOP 8,1</th>
              <th class="py-2.5 px-2 text-right text-amber-400 font-bold">Úspora 8,1 vs 8,9 Běžná</th>
              <th class="py-2.5 px-2 text-right text-amber-400 font-bold">Úspora v Kč</th>
            </tr>
          </thead>
          <tbody id="ten-year-tbody" class="divide-y divide-slate-800">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    const simData = {json_str};
    let currentSeason = '2016-2017';
    let currentModel = '89kw'; // '89kw' or '81kw'
    let currentDailyMetric = 'el';

    function init() {{
      renderSeasonButtons();
      renderSeason(currentSeason);
      renderTenYearTable();
    }}

    function selectModel(m) {{
      currentModel = m;
      document.getElementById('btn-model-89kw').className = `model-btn px-3 py-1.5 text-xs rounded-lg border border-transparent transition flex items-center gap-1.5 ${{m === '89kw' ? 'active' : 'text-slate-300 hover:text-white'}}`;
      document.getElementById('btn-model-81kw').className = `model-btn px-3 py-1.5 text-xs rounded-lg border border-transparent transition flex items-center gap-1.5 ${{m === '81kw' ? 'active' : 'text-slate-300 hover:text-white'}}`;

      const mInfo = simData.parameters.models[m];
      document.getElementById('spec-hp-name').innerText = mInfo.name;
      document.getElementById('spec-hp-mod').innerText = `Modulace: ${{mInfo.min_kw}} – ${{mInfo.max_kw}} kW`;
      document.getElementById('spec-hp-price').innerText = `${{mInfo.price_czk.toLocaleString('cs-CZ')}} Kč bez DPH`;
      document.getElementById('spec-hp-noise').innerText = `Hluk: ${{mInfo.noise}}`;

      renderSeason(currentSeason);
    }}

    function renderSeasonButtons() {{
      const container = document.getElementById('season-buttons');
      container.innerHTML = '';
      Object.keys(simData.winters).forEach(s => {{
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
      document.getElementById('h2h-season-label').innerText = s;

      document.getElementById('h2h-scop-89').innerText = `8,9 kW: ${{r.scop_89_opt.toFixed(2)}}`;
      document.getElementById('h2h-scop-81').innerText = `8,1 kW: ${{r.scop_81_opt.toFixed(2)}}`;
      document.getElementById('h2h-scop-diff').innerText = `+${{(r.scop_81_opt - r.scop_89_opt).toFixed(2)}} vyšší pro 8,1 kW`;
      document.getElementById('h2h-el-89').innerText = `8,9 kW Opt: ${{r.el_89_opt_kwh.toLocaleString('cs-CZ')}} kWh`;
      document.getElementById('h2h-el-81').innerText = `8,1 kW Opt: ${{r.el_81_opt_kwh.toLocaleString('cs-CZ')}} kWh`;
      document.getElementById('h2h-el-diff').innerText = `-${{(r.el_89_opt_kwh - r.el_81_opt_kwh).toFixed(0)}} kWh pro 8,1 kW`;

      const activeElOpt = currentModel === '89kw' ? r.el_89_opt_kwh : r.el_81_opt_kwh;
      const activeElStd = currentModel === '89kw' ? r.el_89_std_kwh : r.el_81_std_kwh;
      const activeScopOpt = currentModel === '89kw' ? r.scop_89_opt : r.scop_81_opt;
      const activeScopStd = currentModel === '89kw' ? r.scop_89_std : r.scop_81_std;
      const activeStartsOpt = currentModel === '89kw' ? r.starts_89_opt : r.starts_81_opt;
      const activeStartsStd = currentModel === '89kw' ? r.starts_89_std : r.starts_81_std;

      const kpiContainer = document.getElementById('season-kpi-container');
      kpiContainer.innerHTML = `
        <div class="card p-4 border-l-4 border-sky-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Spotřeba elektřiny [${{currentModel === '89kw' ? '8,9 kW' : '8,1 kW'}}]</span>
            <span class="text-sky-400 font-medium">Úspora ${{((1 - activeElOpt/activeElStd)*100).toFixed(1)}} %</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-white">${{activeElOpt.toLocaleString('cs-CZ')}} kWh</span>
            <span class="text-xs text-slate-400 line-through">${{activeElStd.toLocaleString('cs-CZ')}} kWh</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Náklady: <strong>${{(activeElOpt * 5).toLocaleString('cs-CZ')}} Kč</strong> (5 Kč/kWh)</div>
        </div>

        <div class="card p-4 border-l-4 border-emerald-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Sezónní topný faktor SCOP</span>
            <span class="text-emerald-400 font-medium">Spád 4 °C</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-emerald-400">${{activeScopOpt.toFixed(2)}}</span>
            <span class="text-xs text-slate-400">vs ${{activeScopStd.toFixed(2)}} běžně</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">${{currentModel === '89kw' ? 'Kompresor HIGHLY/Hitachi' : 'Kompresor Panasonic Inverter'}}</div>
        </div>

        <div class="card p-4 border-l-4 border-amber-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Počet startů kompresoru</span>
            <span class="text-amber-400 font-medium">Modulace od 2,5 kW</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-amber-400">${{activeStartsOpt.toLocaleString('cs-CZ')}}</span>
            <span class="text-xs text-slate-400 line-through">${{activeStartsStd.toLocaleString('cs-CZ')}}</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">Snížení cyklů o <strong>${{((1 - activeStartsOpt/activeStartsStd)*100).toFixed(0)}} %</strong></div>
        </div>

        <div class="card p-4 border-l-4 border-indigo-500">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Rozdíl spotřeby mezi modely</span>
            <span class="text-emerald-400 font-semibold">8,1kW vs 8,9kW</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-2xl font-bold text-emerald-400">-${{r.savings_81opt_vs_89opt_kwh}} kWh</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">8,1 kW ušetří <strong>${{r.savings_81opt_vs_89opt_czk.toLocaleString('cs-CZ')}} Kč</strong> navíc</div>
        </div>
      `;

      const mTable = document.getElementById('monthly-tbody');
      mTable.innerHTML = '';
      win.monthly.forEach(m => {{
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-800/40";
        row.innerHTML = `
          <td class="py-2 px-2 font-medium text-white">${{formatMonth(m.month)}}</td>
          <td class="py-2 px-2 text-right">${{m.te_avg}} °C</td>
          <td class="py-2 px-2 text-right text-slate-400">${{Math.round(m.el_89_std)}} kWh</td>
          <td class="py-2 px-2 text-right text-sky-400 font-semibold">${{Math.round(m.el_89_opt)}} kWh</td>
          <td class="py-2 px-2 text-right font-bold text-emerald-400">${{Math.round(m.el_81_opt)}} kWh</td>
          <td class="py-2 px-2 text-right text-sky-400 font-semibold">${{m.scop_89_opt.toFixed(2)}}</td>
          <td class="py-2 px-2 text-right font-bold text-emerald-400">${{m.scop_81_opt.toFixed(2)}}</td>
        `;
        mTable.appendChild(row);
      }});

      drawDailyChart(win.daily);
    }}

    function formatMonth(mStr) {{
      const map = {{ '11': 'Listopad', '12': 'Prosinec', '01': 'Leden', '02': 'Únor', '03': 'Březen' }};
      const p = mStr.split('-');
      return `${{map[p[1]] || p[1]}} ${{p[0]}}`;
    }}

    function setDailyMetric(m) {{
      currentDailyMetric = m;
      document.getElementById('btn-metric-el').className = `px-2.5 py-1 rounded ${{m === 'el' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;
      document.getElementById('btn-metric-scop').className = `px-2.5 py-1 rounded ${{m === 'scop' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;
      document.getElementById('btn-metric-temp').className = `px-2.5 py-1 rounded ${{m === 'temp' ? 'bg-sky-600 text-white font-medium' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}}`;
      drawDailyChart(simData.winters[currentSeason].daily);
    }}

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
        let maxVal = 32;

        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = Math.round(maxVal - (maxVal / 4) * i);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`${{v}} kWh`, padL - 6, y + 3);
        }}

        // 8.9 kW Std area
        ctx.fillStyle = 'rgba(148, 163, 184, 0.2)';
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const hStd = (d.el_89_std / maxVal) * cH;
          ctx.fillRect(x - 1, padT + cH - hStd, 2, hStd);
        }});

        // 8.9 kW Opt curve (sky)
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const y = padT + cH - (d.el_89_opt / maxVal) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();

        // 8.1 kW Opt curve (emerald)
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const y = padT + cH - (d.el_81_opt / maxVal) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();

        ctx.textAlign = 'right';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('8,9 kW Běžná ekviterm', W - 230, padT - 5);
        ctx.fillStyle = '#38bdf8';
        ctx.fillText('8,9 kW Opt (58 630 Kč)', W - 130, padT - 5);
        ctx.fillStyle = '#10b981';
        ctx.fillText('8,1 kW Ultra tiché Opt', W - 15, padT - 5);

      }} else if (currentDailyMetric === 'scop') {{
        const minVal = 2.0, maxVal = 6.0;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = (maxVal - ((maxVal - minVal) / 4) * i).toFixed(1);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`COP ${{v}}`, padL - 6, y + 3);
        }}

        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        dailyData.forEach((d, i) => {{
          const x = padL + i * stepX;
          const val = Math.min(maxVal, Math.max(minVal, d.scop_81_opt));
          const y = padT + cH - ((val - minVal) / (maxVal - minVal)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();

      }} else {{
        let minT = -22, maxT = 24;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {{
          const v = Math.round(maxT - ((maxT - minT) / 4) * i);
          const y = padT + (cH / 4) * i;
          ctx.fillText(`${{v}} °C`, padL - 6, y + 3);
        }}

        const y0 = padT + cH - ((0 - minT) / (maxT - minT)) * cH;
        ctx.strokeStyle = '#38bdf8';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padL, y0);
        ctx.lineTo(W - padR, y0);
        ctx.stroke();
        ctx.setLineDash([]);

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
          <td class="py-2.5 px-2 text-right text-slate-400">${{r.el_89_std_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right text-sky-400 font-semibold">${{r.el_89_opt_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right font-bold text-emerald-400">${{r.el_81_opt_kwh.toLocaleString('cs-CZ')}}</td>
          <td class="py-2.5 px-2 text-right text-sky-400 font-medium">${{r.scop_89_opt.toFixed(2)}}</td>
          <td class="py-2.5 px-2 text-right font-bold text-emerald-400">${{r.scop_81_opt.toFixed(2)}}</td>
          <td class="py-2.5 px-2 text-right font-bold text-amber-400">-${{r.savings_81opt_vs_89std_pct}} %</td>
          <td class="py-2.5 px-2 text-right font-bold text-amber-400">${{r.savings_81opt_vs_89std_czk.toLocaleString('cs-CZ')}} Kč</td>
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
      const barW = Math.min(18, (groupW - 14) / 3);
      let maxKwh = 3000;

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

        const h89Std = (r.el_89_std_kwh / maxKwh) * cH;
        const h89Opt = (r.el_89_opt_kwh / maxKwh) * cH;
        const h81Opt = (r.el_81_opt_kwh / maxKwh) * cH;

        // 8.9kW Std
        ctx.fillStyle = '#64748b';
        ctx.fillRect(xCenter - barW * 1.5 - 2, padT + cH - h89Std, barW, h89Std);

        // 8.9kW Opt
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(xCenter - barW / 2, padT + cH - h89Opt, barW, h89Opt);

        // 8.1kW Opt
        ctx.fillStyle = '#10b981';
        ctx.fillRect(xCenter + barW / 2 + 2, padT + cH - h81Opt, barW, h81Opt);

        ctx.fillStyle = '#cbd5e1';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(s.split('-')[0].substring(2)+'/'+s.split('-')[1].substring(2), xCenter, H - 20);

        ctx.fillStyle = '#34d399';
        ctx.font = '9px system-ui font-bold';
        ctx.fillText(`${{r.scop_81_opt.toFixed(2)}}`, xCenter + barW / 2 + 2 + barW / 2, padT + cH - h81Opt - 4);
      }});

      ctx.textAlign = 'right';
      ctx.fillStyle = '#64748b';
      ctx.fillText('■ 8,9 kW Běžná', W - 230, padT - 10);
      ctx.fillStyle = '#38bdf8';
      ctx.fillText('■ 8,9 kW Opt', W - 145, padT - 10);
      ctx.fillStyle = '#10b981';
      ctx.fillText('■ 8,1 kW Ultra tiché Opt', W - 15, padT - 10);
    }}

    window.addEventListener('resize', () => {{
      renderSeason(currentSeason);
      if (!document.getElementById('ten-year-view').classList.contains('hidden')) {{
        drawTenYearChart();
      }}
    }});

    window.onload = init;
  </script>
</body>
</html>
"""

artifact_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs(artifact_dir, exist_ok=True)
with open(os.path.join(artifact_dir, "simulace_topeni_tc.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulace_topeni_tc.html")), "w", encoding="utf-8") as f:
    f.write(html_content)

print("Dashboard with 8.9 kW and 8.1 kW Ultra tiché successfully generated!")
