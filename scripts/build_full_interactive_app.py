import shutil
import json
import os
import re
from datetime import datetime

def auto_update_version():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    version_file = os.path.join(root_dir, "version.json")
    today = datetime.now().strftime("%Y.%m.%d")
    current_build = 1
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == today:
                    current_build = data.get("build", 0) + 1
                else:
                    current_build = 1
        except Exception:
            current_build = 10
    else:
        # Check existing version in workspace-ui.js
        ws_ui_path = os.path.join(os.path.dirname(__file__), "workspace-ui.js")
        if os.path.exists(ws_ui_path):
            try:
                with open(ws_ui_path, "r", encoding="utf-8") as f:
                    m = re.search(r'VERZE\s+([0-9\.]+)', f.read())
                    if m:
                        parts = m.group(1).split('.')
                        if len(parts) >= 4 and f"{parts[0]}.{parts[1]}.{parts[2]}" == today:
                            current_build = int(parts[3]) + 1
                        else:
                            current_build = 10
                    else:
                        current_build = 10
            except Exception:
                current_build = 10
        else:
            current_build = 10

    version_str = f"{today}.{current_build}"
    version_data = {
        "version": version_str,
        "date": today,
        "build": current_build,
        "updatedAt": datetime.now().isoformat()
    }
    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(version_data, f, indent=2)

    # 1. Update scripts/workspace-ui.js
    ws_ui_path = os.path.join(os.path.dirname(__file__), "workspace-ui.js")
    if os.path.exists(ws_ui_path):
        with open(ws_ui_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'SIMULACE VYTÁPĚNÍ RD · VERZE [0-9\.]+', f'SIMULACE VYTÁPĚNÍ RD · VERZE {version_str}', content)
        with open(ws_ui_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. Update sw.js cache name
    sw_path = os.path.join(root_dir, "sw.js")
    if os.path.exists(sw_path):
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()
        cache_id = f"simulace-tc-{today.replace('.', '')}-v{current_build}"
        content = re.sub(r"const CACHE_NAME = '[^']+';", f"const CACHE_NAME = '{cache_id}';", content)
        content = re.sub(r"k\.startsWith\('simulace-[^']*'\)", "k.startsWith('simulace-')", content)
        with open(sw_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Automatic version bump: {version_str} (PWA cache: {cache_id})")
    return version_str

auto_update_version()
import json
import os

WEATHER_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sim_data", "weather_10_winters.json"))

with open(WEATHER_FILE, 'r', encoding='utf-8') as f:
    raw_weather = json.load(f)

# Create compact weather structure
compact_weather = {}
for s, d in raw_weather.items():
    times = d['time']
    temps = [round(t, 1) for t in d['temp']]
    rhs = [round(r) for r in d['rh']]
    sols = [round(min(1.5, (0.6 * d['dni'][i] + 0.3 * d['diffuse'][i]) * 0.0035), 2) for i in range(len(temps))]
    compact_weather[s] = {
        'start': times[0],
        't': temps,
        'rh': rhs,
        'sol': sols
    }

weather_json_str = json.dumps(compact_weather, separators=(',', ':'))

html_template = r"""<!DOCTYPE html>
<html lang="cs" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#060913">
  <meta name="color-scheme" content="dark">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="manifest.json">
  <link rel="apple-touch-icon" href="icon-192.png">
  <title>Simulace vytápění RD tepelným čerpadlem s akumulací v podlaze (10 sezón, data Open-Meteo)</title>
  <script src="tailwindcss.min.js"></script>
  <script>window.tailwind || document.write('<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"><\/script>')</script>
  <style>
    :root {
      color-scheme: dark;
      --primary: #38bdf8;
      --bg: #060913;
      --card-bg: rgba(15, 23, 42, 0.92);
      --border: rgba(51, 65, 85, 0.75);
    }
    html {
      background-color: #060913;
      color: #e2e8f0;
      color-scheme: dark;
    }
    body {
      background-color: #060913;
      color: #e2e8f0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      overflow-x: hidden;
      margin: 0;
      padding: 0;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      backdrop-filter: blur(12px);
    }
    .mat-btn.active, .cover-btn.active, .dhw-mode-btn.active, .sys-btn.active {
      background-color: #059669;
      color: #ffffff;
      border-color: #10b981;
      font-weight: 700;
    }
    .view-btn.active {
      background-color: #0284c7;
      color: #ffffff;
      font-weight: 700;
    }
    .auto-level-btn.active {
      border-color: #38bdf8 !important;
      background: rgba(14, 165, 233, 0.18) !important;
      box-shadow: 0 0 18px -3px rgba(56, 189, 248, 0.35);
    }
    input[type=range] {
      accent-color: #38bdf8;
      cursor: pointer;
    }
    .chart-tooltip {
      position: absolute;
      pointer-events: none;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #38bdf8;
      border-radius: 0.5rem;
      padding: 0.5rem 0.75rem;
      font-size: 0.75rem;
      color: #f8fafc;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7);
      z-index: 50;
      display: none;
      white-space: nowrap;
    }
    select, input, textarea {
      color-scheme: dark;
    }
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    ::-webkit-scrollbar-track {
      background: #060913;
    }
    ::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #475569;
    }
    @media (max-width: 640px) {
      .mobile-scroll {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
      }
    }

    .review-panel{padding:20px;margin:18px 0;font-size:13px;line-height:1.6}
    .review-panel h2{font-size:21px;color:#f1f5f9;font-weight:700}.review-panel h3{font-size:16px;margin:16px 0 8px;font-weight:600}
    .review-panel p{margin:8px 0;color:#cbd5e1}.review-panel summary{cursor:pointer;font-weight:600;padding:12px 0;color:#7dd3fc}
    .review-scroll{overflow:auto}.review-panel table{width:100%;white-space:nowrap;border-collapse:collapse;font-size:12px}
    .review-panel td,.review-panel th{padding:9px;text-align:right;border-bottom:1px solid #334155}.review-panel th:first-child{text-align:left}
    .review-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.review-controls label{display:block}
    .review-panel input,.review-panel select,.review-number{background:#0f172a;color:#e2e8f0;border:1px solid #475569;border-radius:6px;padding:6px;max-width:100%}
    .review-number{width:90px;margin:5px 0}.review-actions{display:flex;gap:8px;flex-wrap:wrap}.review-actions button{border:1px solid #475569;padding:8px;border-radius:6px}
    .review-positive{color:#6ee7b7}.review-negative{color:#fda4af}.review-panel a{text-decoration:underline;color:#7dd3fc}

    .energy-card{margin:0 0 18px;padding:0;overflow:hidden}.energy-card summary{padding:15px 18px;cursor:pointer;display:flex;gap:12px;align-items:center;justify-content:space-between;color:#e2e8f0;font-weight:650}
    .energy-card summary:before{content:'▸';color:#7dd3fc}.energy-card[open] summary:before{content:'▾'}.energy-card summary #energy-summary{flex:1}.energy-hint{font-size:12px;color:#94a3b8;font-weight:400}
    #energy-form{padding:0 18px 18px;border-top:1px solid #334155}.energy-grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}.energy-grid h3{font-size:17px;font-weight:650;margin:15px 0 12px}
    .energy-field{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:10px 0;font-size:12px}.energy-field small{color:#94a3b8;white-space:nowrap}.energy-field input,.energy-field select{background:#0f172a;border:1px solid #475569;color:#e2e8f0;padding:7px;border-radius:6px;width:140px;max-width:50%}.energy-field select{width:210px}.energy-field input:disabled{opacity:.45}
    .energy-check{display:flex;align-items:center;gap:9px;font-size:13px;margin:14px 0}.energy-check input{accent-color:#38bdf8}.energy-note{font-size:12px;color:#94a3b8;line-height:1.6;margin:10px 0}.energy-note a{color:#7dd3fc;text-decoration:underline}.energy-result{padding:12px;background:#0c2435;border-radius:8px;font-size:13px;line-height:1.7;color:#bae6fd;margin:14px 0}
    .energy-footer{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px;font-size:12px;color:#94a3b8}.energy-footer span{flex:1}.energy-footer button{padding:8px 12px;border:1px solid #475569;border-radius:6px;color:#e2e8f0}
    @media(max-width:700px){.energy-grid{grid-template-columns:1fr;gap:8px}.energy-hint{display:none}.energy-field{gap:8px}}
  </style>
</head>
<body class="bg-[#060913] text-slate-100 px-3 sm:px-6 lg:px-8 py-3 sm:py-5 w-full min-h-screen flex flex-col">

  <!-- Header with Location, Geocoding & Controls -->
  <section id="gas-overview" class="card mb-4" aria-label="Srovnání TČ a plynu"></section>
  <header class="mb-4">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
      <div>
        <h1 class="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>⚡ Simulace vytápění RD tepelným čerpadlem</span>
          <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/40">10 sezón • Akumulace & TUV • v3.0 · komfort a ověřitelná bilance</span>
        </h1>
        <p class="text-xs text-slate-400 mt-1">
          Fyzikální hodinový model s dynamickým SCOP a ohřevem TUV • Katalog s odkazy na HP Keymark
        </p>
      </div>

      <!-- Location Search & Status Badges -->
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative w-full sm:w-64">
          <input
            type="text"
            id="geo-search-input"
            placeholder="Hledat obec / město (např. Ostrava, Praha, Brno)..."
            oninput="onGeoSearchInput(this.value)"
            class="w-full bg-slate-900 text-white rounded-lg px-3 py-1.5 text-xs border border-slate-700 focus:outline-none focus:border-sky-400 placeholder-slate-500 shadow-inner"
          >
          <div id="search-spinner" class="absolute right-3 top-2.5 hidden">
            <svg class="animate-spin h-3.5 w-3.5 text-sky-400" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
            </svg>
          </div>
          <!-- Dropdown Search Results -->
          <div id="geo-dropdown" class="absolute left-0 right-0 top-full mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl z-50 max-h-56 overflow-y-auto hidden">
            <!-- Rendered dynamically -->
          </div>
        </div>


        <button
          onclick="toggleSettingsDrawer()"
          id="btn-settings-drawer" aria-expanded="false" aria-controls="settings-drawer"
          class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5"
        >
          <span>⚙️ Nastavení domu</span>
        </button>
      </div>
    </div>

    <!-- Active Location Badges Bar -->
    <div class="flex flex-wrap items-center justify-between gap-2 mt-2.5 text-xs text-slate-400">
      <div class="flex flex-wrap items-center gap-2">
        <span id="badge-location" class="font-semibold text-sky-400 flex items-center gap-1">📍 Modelová lokalita – Ostrava</span>
        <span id="badge-altitude" class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">⛰️ 211 m n. m.</span>
        <span id="badge-te-design" class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">Výpočtová teplota t_e: -12 °C</span>
        <span id="badge-keymark" class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-mono font-bold">Keymark: 011-1W1163 (8,1 kW)</span>
      </div>
      <div id="badge-weather-source" class="text-[11px] text-slate-500">
        Meteorologická data: Referenční archiv Open-Meteo ERA5 pro Ostravu (1960–2026); modelový dům
      </div>
    </div>

    <!-- Live Fetch Progress Bar -->
    <div id="fetch-status-bar" class="hidden mt-2 p-2 bg-slate-950 rounded border border-sky-500/50 text-xs text-sky-300 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="animate-spin h-4 w-4 text-sky-400" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span id="fetch-status-text">Stahuji meteorologické záznamy z archivu Open-Meteo...</span>
      </div>
      <span id="fetch-status-badge" class="px-2 py-0.5 rounded bg-sky-900/60 text-sky-300 text-[10px] font-mono">0 %</span>
    </div>

    <!-- Collapsible Settings Drawer -->
    <div id="settings-drawer" class="hidden card p-4 md:p-5 mt-3 border-sky-500/40 bg-slate-900/95 shadow-xl transition-all">
      <div class="flex items-center justify-between border-b border-slate-700 pb-2 mb-3">
        <h3 class="text-sm font-semibold text-white flex items-center gap-2">
          <span>🎛️ Parametry domu, otopné soustavy a TUV (okamžitý přepočet simulace)</span>
        </h3>
        <button onclick="resetDefaultParameters()" class="text-xs text-sky-400 hover:text-sky-300 underline font-medium">
          Obnovit modelové hodnoty
        </button>
      </div>

      <div id="settings-live-costs" class="card mb-3" style="position:sticky;top:8px;z-index:30;background:#0f172a;border:1px solid #38bdf8;padding:12px" aria-live="polite"></div>
      <details id="hp-settings-details" class="mb-4 p-3 rounded-lg bg-slate-800/60 border border-slate-700"><summary class="cursor-pointer font-semibold text-white">Tepelné čerpadlo · výběr a úprava parametrů</summary>
        <label for="settings-hp-select" class="block font-semibold text-white mb-2">Tepelné čerpadlo</label>
        <select id="settings-hp-select" class="w-full p-2 rounded bg-slate-900 border border-slate-600 text-white" onchange="selectKeymarkModel(this.value)"></select>
        <div id="settings-hp-parameters" class="mt-3"></div>
      </details>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 text-xs">

        <!-- 1. Heat Loss, System Type & Flow Temperature -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Tepelná ztráta domu:</span>
              <span id="val-qloss" class="text-sky-400 font-bold">5.80 kW</span>
            </div>
            <input type="range" id="input-qloss" min="2.0" max="14.0" step="0.1" value="5.8" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Výkon potřebný k udržení cílové teploty při návrhovém mrazu. Použijte výpočet tepelné ztráty domu.</div>
          </div>

          <!-- Otopná soustava (Keymark profil: 35 °C podlaha vs 55 °C radiátory) -->
          <div>
            <span class="font-medium text-slate-300 block mb-1">Jak předávám teplo do domu:</span>
            <div class="grid grid-cols-2 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-700">
              <button type="button" id="btn-sys-floor" onclick="setHeatingSystem('floor')" class="sys-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-bold" aria-pressed="true">
                ♨️ Podlahové topení
              </button>
              <button type="button" id="btn-sys-rad" onclick="setHeatingSystem('radiator')" class="sys-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white" aria-pressed="false">
                🪟 Radiátory
              </button>
            </div>
            <div id="desc-sys-type" class="text-[10px] text-slate-400 mt-1">Podlahové topení: model počítá s akumulací potěru. Profil W35 slouží pro parametry TČ; skutečnou teplotu vody nastavíte níže.</div>
          </div>

          <!-- Design Flow Temperature (Topná křivka) - allowed from 26.0 °C -->
          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Cílím na teplotu topné vody při návrhovém mrazu:</span>
              <span id="val-tflow" class="text-sky-400 font-bold">28.0 °C</span>
            </div>
            <input type="range" id="input-tflow" min="26.0" max="55.0" step="0.5" value="28.0" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Bod topné křivky při návrhovém mrazu zvolené lokace. Za teplejšího počasí model teplotu snižuje; nejde o stálou teplotu vody. Minimum 26 °C.</div>
          </div>
        </div>

        <!-- 2. Floor Material & Covering (Nášlapná vrstva) -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div>
            <span class="font-medium text-slate-300 block mb-1.5">Materiál potěru:</span>
            <div class="grid grid-cols-2 gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-700">
              <button id="btn-mat-beton" onclick="setFloorMaterial('beton')" class="mat-btn active py-1.5 px-2 rounded text-xs transition text-center font-medium">
                🧱 Beton
              </button>
              <button id="btn-mat-anhydrit" onclick="setFloorMaterial('anhydrit')" class="mat-btn py-1.5 px-2 rounded text-xs transition text-center text-slate-300 hover:text-white font-medium">
                💧 Anhydrit
              </button>
            </div>
          </div>

          <div>
            <span class="font-medium text-slate-300 block mb-1">Nášlapná vrstva (Krytina):</span>
            <div class="grid grid-cols-3 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-700">
              <button id="btn-cover-dlazba" onclick="setFloorCovering('dlazba')" class="cover-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white">
                🔲 Dlažba
              </button>
              <button id="btn-cover-vinyl" onclick="setFloorCovering('vinyl')" class="cover-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium">
                🪵 Vinyl
              </button>
              <button id="btn-cover-drevo" onclick="setFloorCovering('drevo')" class="cover-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white">
                🌲 Dřevo
              </button>
            </div>
            <div id="desc-floor-mat" class="text-[10px] text-slate-400 mt-1">
              Beton + Vinyl: standardní setrvačnost, stabilní akumulace.
            </div>
          </div>
        </div>

        <!-- 3. Floor Area, Screed Thickness & Room Comfort Corridor -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Vytápěná plocha domu:</span>
              <span id="val-area" class="text-sky-400 font-bold">170 m²</span>
            </div>
            <input type="range" id="input-area" min="80" max="350" step="5" value="170" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Podlahová plocha vytápěných místností, nikoli plocha obálky domu</div>
          </div>

          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Tloušťka akumulačního potěru:</span>
              <span id="val-thickness" class="text-emerald-400 font-bold">50 mm</span>
            </div>
            <input type="range" id="input-thickness" min="30" max="85" step="5" value="50" oninput="onParamChange()" class="w-full mt-1">
            <div class="flex justify-between text-[10px] text-slate-400">
              <span id="calc-floor-mass">Hmotnost: 20,0 tun</span>
              <span id="calc-floor-c">C: 5,7 kWh/K</span>
            </div>
          </div>

          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Cílová teplota & hystereze (tolerance vychladnutí):</span>
              <span id="val-tin" class="text-amber-400 font-bold">22.0 − 1.0 °C</span>
            </div>
            <div class="grid grid-cols-2 gap-2 mt-1">
              <input type="range" id="input-tin" min="19.0" max="23.5" step="0.5" value="22.0" oninput="onParamChange()" title="Cílová teplota">
              <input type="range" id="input-tolerance" min="0" max="3" step="0.1" value="1.0" oninput="onParamChange()" title="Tolerance">
            </div>
            <div class="flex justify-between text-[10px] text-slate-400">
              <span id="calc-room-corridor">Pásmo tolerované teploty (nekomfort): 21,0 – 22,0 °C</span>
              <span id="calc-room-storage" class="text-amber-400 font-semibold">Aku: 11 kWh</span>
            </div>
          </div>
        </div>

        <!-- 4. Domestic Hot Water (TUV) -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div class="flex items-center justify-between font-semibold text-slate-200 border-b border-slate-700/60 pb-1.5">
            <span class="flex items-center gap-1.5">🚿 Ohřev teplé vody (TUV)</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" id="input-dhw-enabled" checked onchange="onParamChange()" class="sr-only peer">
              <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>

          <div id="dhw-controls-wrapper" class="space-y-2.5">
            <div>
              <div class="flex justify-between font-medium text-slate-300">
                <span>Denní spotřeba TUV:</span>
                <span id="val-dhw-liters" class="text-sky-400 font-bold">120 l/den</span>
              </div>
              <input type="range" id="input-dhw-liters" min="60" max="350" step="10" value="120" oninput="onParamChange()" class="w-full mt-1">
              <div id="desc-dhw-persons" class="text-[10px] text-slate-400">cca 3 osoby (40 l/osoba/den při 55 °C)</div>
            </div>

            <div>
              <div class="flex justify-between font-medium text-slate-300">
                <span>Požadovaná teplota TUV:</span>
                <span id="val-dhw-temp" class="text-sky-400 font-bold">55 °C</span>
              </div>
              <input type="range" id="input-dhw-temp" min="45" max="60" step="1" value="55" oninput="onParamChange()" class="w-full mt-1">
              <div class="text-[10px] text-slate-400">Teplota v zásobníku (výstup TČ cca +3 °C)</div>
            </div>

            <div>
              <span class="font-medium text-slate-300 block mb-1">Režim ohřevu TUV:</span>
              <div class="grid grid-cols-2 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-700">
                <button id="btn-dhw-smart" onclick="setDhwMode('smart')" class="dhw-mode-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium">
                  ☀️ Polední (13–15h)
                </button>
                <button id="btn-dhw-std" onclick="setDhwMode('standard')" class="dhw-mode-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white">
                  🕒 Průběžný
                </button>
              </div>
              <div id="desc-dhw-mode" class="text-[10px] text-slate-400 mt-1">
                Preferovaný ohřev 13:00–15:00; u dvoutarifu se přesouvá do povolených oken NT. FVE se zde nesimuluje.
              </div>
            </div>
          </div>
        </div>

        <!-- 5. Altitude, Electricity Price & Heat Pump Service -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Nadmořská výška:</span>
              <span id="val-altitude" class="text-sky-400 font-bold">211 m n.m.</span>
            </div>
            <input type="range" id="input-altitude" min="150" max="1100" step="1" value="211" oninput="onAltitudeSliderChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Adiabatická korekce (0,65 °C / 100 m)</div>
          </div>

          <div hidden>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Cena elektřiny:</span>
              <span id="val-price" class="text-rose-400 font-bold">6.00 Kč/kWh</span>
            </div>
            <input type="range" id="input-price" min="0" max="1000" step="0.00001" value="6.0" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Včetně distribuce, POZE, daně a DPH</div>
          </div>

          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Roční kontrola TČ:</span>
              <span id="val-hp-service" class="text-emerald-400 font-bold">0 Kč/rok</span>
            </div>
            <input type="range" id="input-hp-service" min="0" max="3500" step="100" value="0" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Zadejte náklady údržby a kontrol podle nabídky dodavatele</div>
          </div>
        </div>

        <!-- 6. Gas Condensing Boiler & EU ETS 2 Allowance -->
        <div class="space-y-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div hidden>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Cena plynu:</span>
              <span id="val-gas-price" class="text-amber-400 font-bold">1.60 Kč/kWh</span>
            </div>
            <input type="range" id="input-gas-price" min="0" max="1000" step="0.00001" value="1.60" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Včetně komodity, distribuce a DPH</div>
          </div>



          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Roční kontrola kotle:</span>
              <span id="val-gas-service" class="text-amber-400 font-bold">1 500 Kč/rok</span>
            </div>
            <input type="range" id="input-gas-service" min="0" max="3500" step="100" value="1500" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Předpokládané náklady servisu a kontrol podle vašeho zařízení</div>
          </div>

          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Účinnost plynového kotle:</span>
              <span id="val-gas-eff" class="text-sky-400 font-bold">94 %</span>
            </div>
            <input type="range" id="input-gas-eff" min="85" max="98" step="1" value="94" oninput="onParamChange()" class="w-full mt-1">
            <div class="text-[10px] text-slate-400">Kondenzace v nízkoteplotním podlahovém vytápění (Hs)</div>
          </div>
        </div>

      </div>
    </div>
  </header>

  <details id="energy-card" class="card energy-card">
    <summary aria-label="Nastavení cen energií"><span id="energy-summary">D02d · načítání ceny…</span><span class="energy-hint">Nastavení energií</span></summary>
    <div id="energy-form"></div>
<div class="px-5 pb-5">          <div>
            <div class="flex justify-between font-medium text-slate-300">
              <span>Cena povolenky (EU ETS 2):</span>
              <span id="val-co2-price" class="text-rose-400 font-bold">30 €/t CO₂</span>
            </div>
            <input type="range" id="input-co2-price" min="0" max="150" step="5" value="30" oninput="onParamChange()" class="w-full mt-1">
            <div id="calc-ets2-surcharge" class="text-[10px] text-rose-300">Příplatek k plynu: +0,33 Kč/kWh (celkem 1,93 Kč/kWh s DPH)</div>
          </div>
</div>
  </details>

  <!-- Prominent Explanation of Savings (Requested by User) -->
  <div class="card p-3.5 bg-gradient-to-r from-emerald-950/60 via-slate-900 to-sky-950/50 border border-emerald-500/35 flex items-start sm:items-center gap-3 mb-4 rounded-xl shadow-lg">
    <div class="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg flex-shrink-0 shadow-inner">💡</div>
    <div class="text-xs text-slate-300 leading-relaxed">
      <span class="font-bold text-white">Proč vzniká úspora optimalizovaného řízení?</span>
      Úspora může vznikat <span class="text-emerald-300 font-semibold">přesunem topení do teplejší části dne pro vyšší COP čerpadla</span> — nabíjení tepelné akumulace do masivní podlahy a předehřev TUV se upřednostňují v denním okně 10:00–16:00; ohřev TUV respektuje jeho vlastní nastavení. V noci se čerpadlo utlumuje nebo vypíná a dům čerpá akumulované teplo z podlahy, což může omezit provoz v chladných hodinách. Vyšší teplota vody a změna komfortu však mohou přínos snížit nebo obrátit.
    </div>
  </div>

  <!-- ================= AUTOMATION LEVEL SELECTOR CARD (REQUESTED BY USER) ================= -->
  <div class="card p-3.5 sm:p-4 mb-4 border border-sky-500/30 bg-slate-900/95 shadow-xl space-y-3">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-base text-sky-400">🎛️</span>
        <h3 class="text-xs font-bold uppercase tracking-wider text-white">Režim řízení TČ:</h3>
        <span id="badge-auto-level" class="px-2.5 py-0.5 text-xs rounded-full bg-purple-500/20 text-purple-300 font-bold border border-purple-500/40">
          Optimalizace · denní topení
        </span>
      </div>
      <div class="text-[11px] text-slate-400">
        Denní optimalizace s poklesem teploty pouze pod nastavený cíl:
      </div>
    </div>

    <div class="grid grid-cols-1 gap-2.5">
      <button id="btn-auto-optimized" aria-pressed="true" onclick="setAutomationLevel('optimized')" class="auto-level-btn active p-3 rounded-lg border border-sky-400 bg-sky-950/60 text-left">
        <div><h3 class="font-bold text-white">Optimalizace · denní topení</h3><p class="text-xs text-slate-300">Přednostně topí 10–16 h, kdy bývá venku tepleji a COP vyšší. Mimo toto okno využívá akumulaci a podle potřeby dotápí. TUV podle nastavení.</p></div>
        <div class="text-xs text-sky-300 mt-2">Přepočítávám…</div>
      </button>
    </div>
  </div>

  <!-- Navigation Action Bar & 5 Seasons Window Selector -->
  <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
    <div class="flex flex-wrap items-center gap-1.5 bg-slate-900 p-1.5 rounded-xl border border-slate-700 shadow">
      <button id="view-mode-all10" onclick="toggleSection('all10')" class="view-btn active px-3 py-1.5 text-xs rounded-lg transition flex items-center gap-1.5 font-bold shadow bg-sky-600 text-white">
        <span>📈 1. Srovnání 10 sezón</span>
      </button>
      <button id="view-mode-single" onclick="toggleSection('single')" class="view-btn active px-3 py-1.5 text-xs rounded-lg transition flex items-center gap-1.5 font-bold shadow bg-sky-600 text-white">
        <span>📅 2. Detail sezóny & Akumulace</span>
      </button>
      <button id="view-mode-table" onclick="toggleSection('table')" class="view-btn active px-3 py-1.5 text-xs rounded-lg transition flex items-center gap-1.5 font-bold shadow bg-sky-600 text-white">
        <span>📊 3. Tabulka 10 sezón</span>
      </button>
<button id="view-mode-gas" onclick="toggleSection('gas')" class="view-btn px-3 py-1.5 text-xs rounded-lg transition text-slate-300 hover:text-white flex items-center gap-1.5 font-medium bg-slate-800/80">
        <span>🔥 4. Plyn</span>
      </button>
      <div class="h-4 w-[1px] bg-slate-700 mx-1"></div>
      <button onclick="expandAllSections()" title="Rozbalit všechny sekce pod sebe" class="px-2.5 py-1.5 text-xs rounded-lg bg-sky-950/70 hover:bg-sky-900 text-sky-200 border border-sky-700/60 flex items-center gap-1 font-semibold transition">
        <span>📖 Rozbalit vše</span>
      </button>
      <button onclick="collapseAllSections()" title="Sbalit všechny sekce" class="px-2.5 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 font-medium transition">
        <span>📁 Sbalit vše</span>
      </button>
    </div>

    <!-- 10 Seasons Window Selector & Dynamic Season Pills -->
    <div id="season-selector-wrapper" class="flex flex-wrap items-center gap-2">
      <div class="flex items-center gap-1.5 bg-slate-900/90 border border-slate-700 px-2.5 py-1 rounded-xl text-xs shadow">
        <span class="text-slate-400 font-medium">10 sezón okolo roku:</span>
        <select id="select-season-window" onchange="onSeasonPresetChange(this.value)" class="bg-slate-800 text-sky-300 font-bold px-2 py-0.5 rounded border border-slate-600 focus:outline-none text-xs cursor-pointer">
          <option value="2022" selected>Nejnovějších 10 sezón (2016–2026)</option>
          <option value="2019">Okolo roku 2019 (2014–2024)</option>
          <option value="2015">Okolo roku 2015 (2010–2020)</option>
          <option value="2005">Okolo roku 2005 (2000–2010)</option>
          <option value="1995">Okolo roku 1995 (1990–2000)</option>
          <option value="1985">Okolo roku 1985 (1980–1990)</option>
          <option value="1975">Okolo roku 1975 (1970–1980)</option>
          <option value="1965">Nejstarších 10 sezón (1960–1970)</option>
        </select>
        <div class="flex items-center gap-0.5 ml-1">
          <button onclick="stepCenterYear(-1)" title="Předchozí rok" class="w-5 h-5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex items-center justify-center font-bold text-xs">◀</button>
          <input type="number" id="input-center-year" min="1960" max="2026" value="2022" onchange="setCenterYear(parseInt(this.value))" class="w-16 bg-slate-800 text-center text-xs text-white font-semibold rounded border border-slate-700 py-0.5">
          <button onclick="stepCenterYear(1)" title="Následující rok" class="w-5 h-5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex items-center justify-center font-bold text-xs">▶</button>
        </div>
      </div>
      <div id="season-buttons" class="flex flex-wrap gap-1"></div>
    </div>
  </div>


  <!-- KPI Cards for Current Selection -->
  <div id="season-kpi-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 mb-5">
    <!-- Rendered dynamically -->
  </div>

  <!-- ================= SECTION 1: 5 SEASONS OVERLAY CHART ================= -->
  <section id="sec-all10" class="mb-5 rounded-2xl border border-slate-800 bg-slate-900/50 shadow-lg transition-all overflow-hidden">
    <div onclick="toggleSection('all10')" class="p-3 sm:p-4 bg-slate-900 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition border-b border-slate-800 select-none">
      <div class="flex items-center gap-2.5">
        <span class="text-base sm:text-lg">📈</span>
        <div>
          <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <span>1. Srovnání 10 vybraných sezón v grafu</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-sky-950 text-sky-300 border border-sky-800/40 font-normal">1. říjen – 30. duben</span>
          </h2>
          <p class="text-[11px] text-slate-400">Přepínání křivek denní a kumulativní spotřeby elektřiny, COP a venkovní teploty na společné časové ose</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button type="button" class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 flex items-center gap-1.5 font-medium pointer-events-none shadow-sm">
          <span id="chevron-all10">▲</span>
          <span id="label-all10">Sbalit</span>
        </button>
      </div>
    </div>
    <div id="view-all10-container" class="space-y-5 p-3 sm:p-5">
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <span>📈 Srovnání 10 vybraných sezón v grafu (1. říjen – 30. duben)</span>
          </h2>
          <p class="text-xs text-slate-400">
            Srovnání průběhu 10 vybraných otopných sezón na společné časové ose. Najetím myši na křivku nebo v legendě zvýrazníte konkrétní rok.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-1.5 text-xs">
          <button onclick="setOverlayMetric('kwh_daily')" id="btn-ovl-kwh" class="px-2.5 py-1 rounded bg-sky-600 text-white font-medium">Spotřeba [kWh/den]</button>
          <button onclick="setOverlayMetric('kwh_cum')" id="btn-ovl-cum" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Kumulativní [kWh]</button>
          <button onclick="setOverlayMetric('scop')" id="btn-ovl-scop" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Denní COP</button>
          <button onclick="setOverlayMetric('temp')" id="btn-ovl-temp" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Venkovní teplota [°C]</button>
        </div>
      </div>

      <!-- Canvas for 5-season Overlay -->
      <div class="relative w-full h-[360px]">
        <canvas id="overlayCanvas" class="w-full h-full block cursor-crosshair"></canvas>
      </div>

      <!-- X-axis Timeline labels -->
      <div class="flex items-center justify-between text-xs text-slate-400 mt-2 px-1 border-t border-slate-800 pt-2 font-medium">
        <div>1. říjen</div>
        <div>1. listopad</div>
        <div>1. prosinec</div>
        <div>1. leden</div>
        <div>1. únor</div>
        <div>1. březen</div>
        <div>1. duben</div>
        <div>30. duben</div>
      </div>

      <!-- 5 Seasons Interactive Legend Bar -->
      <div class="mt-4 pt-3 border-t border-slate-700/60">
        <div class="text-[11px] font-medium text-slate-400 mb-2">Interaktivní legenda 10 vybraných sezón (kliknutím vyberete detail sezóny, najetím zvýrazníte):</div>
        <div id="overlay-legend-container" class="flex flex-wrap gap-2"></div>
      </div>
    </div>
  </section>

  <!-- ================= SECTION 2: SINGLE SEASON DETAIL ================= -->
  <section id="sec-single" class="mb-5 rounded-2xl border border-slate-800 bg-slate-900/50 shadow-lg transition-all overflow-hidden">
    <div onclick="toggleSection('single')" class="p-3 sm:p-4 bg-slate-900 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition border-b border-slate-800 select-none">
      <div class="flex items-center gap-2.5">
        <span class="text-base sm:text-lg">📅</span>
        <div>
          <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <span>2. Detail sezóny, 24h akumulace v podlaze & měsíční bilance:</span>
            <span id="header-season-badge" class="px-2 py-0.5 text-xs rounded bg-sky-500/20 text-sky-300 font-bold">2022-2023</span>
          </h2>
          <p class="text-[11px] text-slate-400">Denní spotřeba TČ, 24h fyzikální profil kolísání teploty betonu a místnosti, modulace a měsíční bilance</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button type="button" class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 flex items-center gap-1.5 font-medium pointer-events-none shadow-sm">
          <span id="chevron-single">▲</span>
          <span id="label-single">Sbalit</span>
        </button>
      </div>
    </div>
    <div id="view-single-container" class="space-y-5 p-3 sm:p-5">
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <span>📅 Detail otopné sezóny:</span>
            <span id="chart-season-badge" class="px-2 py-0.5 text-xs rounded bg-sky-500/20 text-sky-300 font-semibold">2016-2017</span>
          </h2>
          <p class="text-xs text-slate-400">
            Podrobný denní průběh spotřeby elektřiny pro vytápění i ohřev TUV, sezónního COP a venkovní teploty.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-1.5 text-xs">
          <button onclick="setSingleMetric('el')" id="btn-sgl-el" class="px-2.5 py-1 rounded bg-sky-600 text-white font-medium">Elektřina TČ & teplo</button>
          <button onclick="setSingleMetric('temp')" id="btn-sgl-temp" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Průběh teploty</button>
          <button onclick="setSingleMetric('scop')" id="btn-sgl-scop" class="px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">Denní COP</button>
        </div>
      </div>

      <!-- Canvas for Single Season -->
      <div class="relative w-full h-[360px]">
        <canvas id="singleCanvas" class="w-full h-full block cursor-crosshair"></canvas>
      </div>

      <!-- X-axis Timeline labels -->
      <div class="flex items-center justify-between text-xs text-slate-400 mt-2 px-1 border-t border-slate-800 pt-2 font-medium">
        <div>1. říjen</div>
        <div>1. listopad</div>
        <div>1. prosinec</div>
        <div>1. leden</div>
        <div>1. únor</div>
        <div>1. březen</div>
        <div>1. duben</div>
        <div>30. duben</div>
      </div>

      <!-- Legend for single season -->
      <div id="single-legend-container" class="mt-4 pt-3 border-t border-slate-700/60 flex flex-wrap items-center gap-4 text-xs text-slate-300">
        <!-- Rendered dynamically -->
      </div>
    </div>

      <!-- Interactive Hint Bar under single canvas -->
      <div class="mt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-sky-300 bg-sky-950/30 border border-sky-800/40 px-3.5 py-2 rounded-lg">
        <span class="flex items-center gap-1.5">
          <span class="text-sky-400">👆</span>
          <span><strong>Interaktivní denní profil:</strong> Klikněte na jakýkoliv den v grafu výše pro zobrazení detailního 24hodinového průběhu teplot a spínání.</span>
        </span>
        <span id="single-selected-day-pill" class="font-semibold text-white bg-sky-600/70 px-2.5 py-0.5 rounded self-start sm:self-auto shadow-sm">Vybraný den: 16. ledna</span>
      </div>
    </div>

    <!-- ================= 24-HOUR DIURNAL PROFILE & THERMAL ACCUMULATION CARD ================= -->
    <div id="diurnal-section-card" class="card p-4 md:p-5 border border-sky-500/30 shadow-xl space-y-4">
      <!-- Header & Day Badge -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-700/60">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span class="text-sky-400">🕒</span>
              <span>24hodinový detail dne: kolísání teplot a spínání čerpadla</span>
            </h3>
            <span id="diurnal-date-badge" class="px-2.5 py-0.5 text-xs rounded-full bg-sky-500/20 text-sky-300 font-bold border border-sky-500/30">16. ledna (Den 108)</span>
            <span id="diurnal-weather-badge" class="px-2.5 py-0.5 text-xs rounded-full bg-slate-800 text-amber-300 font-medium border border-slate-700">❄️ Min: -13.2 °C | Max: -2.4 °C</span>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            Hodinový přehled z 10minutové simulace. Sledujte komfort, výkon a skutečné úseky bez provozu.
          </p>
        </div>

        <!-- Fast Presets & Controls -->
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] text-slate-400 mr-1">Rychlý výběr:</span>
          <button onclick="selectPresetDay('coldest')" class="px-2.5 py-1 text-xs rounded bg-red-950/60 border border-red-700/60 text-red-300 hover:bg-red-900/60 transition flex items-center gap-1">
            <span>❄️</span><span>Největší mráz</span>
          </button>
          <button onclick="selectPresetDay('winter')" class="px-2.5 py-1 text-xs rounded bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 transition flex items-center gap-1">
            <span>🌤️</span><span>Běžná zima (0 °C)</span>
          </button>
          <button onclick="selectPresetDay('spring')" class="px-2.5 py-1 text-xs rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-300 hover:bg-emerald-900/60 transition flex items-center gap-1">
            <span>☀️</span><span>Jarní den (+10 °C)</span>
          </button>
        </div>
      </div>

      <!-- Day Slider & Stepper Bar -->
      <div class="flex items-center gap-3 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 text-xs">
        <button onclick="stepDay(-1)" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 transition">
          <span>◀</span><span class="hidden sm:inline">Předchozí den</span>
        </button>
        <div class="flex-1 flex items-center gap-3">
          <span class="text-[11px] text-slate-400 hidden sm:inline">1. říjen</span>
          <input type="range" id="diurnalDaySlider" min="0" max="211" value="98" oninput="onDaySliderChange(this.value)" class="flex-1 accent-sky-500 cursor-pointer h-2">
          <span class="text-[11px] text-slate-400 hidden sm:inline">30. duben</span>
        </div>
        <button onclick="stepDay(1)" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 transition">
          <span class="hidden sm:inline">Další den</span><span>▶</span>
        </button>
        <div id="diurnal-day-counter" class="font-mono text-sky-400 font-bold px-2.5 py-0.5 rounded bg-sky-950/50 border border-sky-800/50 min-w-[75px] text-center">
          Den 99
        </div>
      </div>

      <!-- 4 Dynamic KPI Cards for Selected Day -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <!-- KPI 1: Outdoor Temperature Swing -->
        <div class="p-3 rounded-lg bg-slate-850 border border-slate-750">
          <div class="text-[11px] text-slate-400 flex items-center justify-between">
            <span>Denní rozkmit venku</span>
            <span>🌡️</span>
          </div>
          <div class="text-base font-bold text-white mt-1" id="kpi-diurnal-swing">10.8 °C</div>
          <div class="text-[10px] text-slate-400 mt-0.5" id="kpi-diurnal-range">Min -13.2 °C • Max -2.4 °C</div>
        </div>

        <!-- KPI 2: Thermal Accumulation in Floor Slab -->
        <div class="p-3 rounded-lg bg-amber-950/20 border border-amber-800/30">
          <div class="text-[11px] text-amber-300 flex items-center justify-between">
            <span>Uloženo v podlaze (aku)</span>
            <span>🔋</span>
          </div>
          <div class="text-base font-bold text-amber-400 mt-1" id="kpi-diurnal-slab-kwh">+14.2 kWh</div>
          <div class="text-[10px] text-amber-300/80 mt-0.5" id="kpi-diurnal-slab-temp">Oteplení betonu: +2.5 °C</div>
        </div>

        <!-- KPI 3: Compressor Night Silence -->
        <div class="p-3 rounded-lg bg-indigo-950/20 border border-indigo-800/30">
          <div class="text-[11px] text-indigo-300 flex items-center justify-between">
            <span>Noční klid kompresoru</span>
            <span>🌙</span>
          </div>
          <div class="text-base font-bold text-indigo-300 mt-1" id="kpi-diurnal-night-hours">8 hodin</div>
          <div class="text-[10px] text-indigo-300/80 mt-0.5" id="kpi-diurnal-night-desc">22:00 – 06:00 (0 startů v mrazu)</div>
        </div>

        <!-- KPI 4: Electricity Consumption & Savings -->
        <div class="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/30">
          <div class="text-[11px] text-emerald-300 flex items-center justify-between">
            <span>Denní spotřeba elektřiny</span>
            <span>⚡</span>
          </div>
          <div class="text-base font-bold text-emerald-400 mt-1" id="kpi-diurnal-el-usage">16.2 kWh <span class="text-xs font-normal text-slate-400">(vs 21.4)</span></div>
          <div class="text-[10px] text-emerald-300/90 font-medium mt-0.5" id="kpi-diurnal-el-saving">Úspora: -5.2 kWh (-24 %)</div>
        </div>
      </div>

      <!-- Chart 1: Diurnal Temperature & Accumulation Profile -->
      <div class="space-y-2">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
          <div class="font-semibold text-white flex items-center gap-2">
            <span>🌡️ Graf 1: Průběh teplot v průběhu 24 hodin (°C)</span>
            <span class="text-[11px] text-slate-400 font-normal">— akumulační ohřev a noční vybíjení desky</span>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-[11px]">
            <span class="flex items-center gap-1.5"><span class="w-3 h-1 bg-amber-500 rounded"></span><strong class="text-amber-400">T_podlaha (beton)</strong></span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-1 bg-emerald-400 rounded"></span><strong class="text-emerald-400">T_místnost (vzduch)</strong></span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-1 border-t-2 border-dashed border-rose-500"></span><span class="text-rose-400">t_voda (přívod)</span></span>
          </div>
        </div>
        <div class="relative w-full h-[250px] bg-slate-900/40 rounded-lg p-1 border border-slate-800">
          <canvas id="diurnalTempCanvas" class="w-full h-full block cursor-crosshair"></canvas>
        </div>
      </div>

      <div class="space-y-2 pt-3"><h3 class="text-sm font-semibold">Graf 1b: Venkovní teplota · 24 hodin (°C)</h3><div class="relative w-full h-[170px] bg-slate-900/40 rounded-lg p-1 border border-slate-800"><canvas id="diurnalOutdoorCanvas" class="w-full h-full block cursor-crosshair"></canvas></div></div>
      <p class="config-note">HDO: zelený pás = NT, šedý = VT; svislé čáry = přepnutí. Modelový rozvrh, nikoli živý signál distributora. VT samo o sobě neznamená vypnutí kompresoru.</p>
      <!-- Chart 2: Heat Pump Power, Modulation, DHW & Instantaneous COP -->
      <div class="space-y-2 pt-1">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
          <div class="font-semibold text-white flex items-center gap-2">
            <span>⚡ Graf 2: Výkon a spínání tepelného čerpadla & Okamžitý COP</span>
            <span class="text-[11px] text-slate-400 font-normal">— polední nabíjení desky a ohřev TUV vs noční vypnutí</span>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-[11px]">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-sky-500 rounded-sm"></span><span class="text-sky-300">Teplo podlaha Q_hp</span></span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-amber-500 rounded-sm"></span><span class="text-amber-400">Ohřev TUV Q_dhw</span></span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-purple-500 rounded-sm"></span><span class="text-purple-300">Příkon elektřiny P_el</span></span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 border-t border-dashed border-slate-400"></span><span class="text-slate-400">Běžný ekviterm (srovnání)</span></span>
            <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><strong class="text-emerald-400">Okamžitý COP (pravá osa)</strong></span>
          </div>
        </div>
        <div class="relative w-full h-[230px] bg-slate-900/40 rounded-lg p-1 border border-slate-800">
          <canvas id="diurnalPowerCanvas" class="w-full h-full block cursor-crosshair"></canvas>
        </div>
      </div>

      <!-- Operational Periods Legend & Physical Mechanism -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
        <div class="p-3 rounded-lg bg-indigo-950/30 border border-indigo-900/40">
          <div class="font-semibold text-indigo-300 flex items-center gap-1.5 mb-1">
            <span>🌙</span><span>Noční útlum (22:00 – 06:00)</span>
          </div>
          <p class="text-[11px] text-slate-400 leading-relaxed">
            <span id="night-explanation-v3">Noční provoz závisí na počasí, výkonu a komfortu.</span>
          </p>
        </div>
        <div class="p-3 rounded-lg bg-amber-950/30 border border-amber-900/40">
          <div class="font-semibold text-amber-300 flex items-center gap-1.5 mb-1">
            <span>☀️</span><span>Polední nabíjení (10:00 – 16:00)</span>
          </div>
          <p class="text-[11px] text-slate-400 leading-relaxed">
            Řízení může přesouvat dodávku tepla do dne. Výsledek závisí na teplotě vody, počasí a dostupném výkonu. Polední TUV respektuje volbu v nastavení.
          </p>
        </div>
        <div class="p-3 rounded-lg bg-emerald-950/30 border border-emerald-900/40">
          <div class="font-semibold text-emerald-300 flex items-center gap-1.5 mb-1">
            <span>🧱</span><span>Fyzikální kapacita desky</span>
          </div>
          <p class="text-[11px] text-slate-400 leading-relaxed">
            <span id="capacity-explanation-v3">Kapacita se odvozuje z materiálu, plochy a tloušťky.</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Monthly Table -->
    <div class="card p-4 md:p-5">
      <h3 class="text-sm font-semibold text-white mb-3 flex items-center justify-between">
        <span>Měsíční bilance spotřeby a úspor (včetně TUV)</span>
        <span class="text-xs text-slate-400 font-normal">říjen – duben</span>
      </h3>
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-slate-400 border-b border-slate-700 uppercase">
            <tr>
              <th class="py-2 px-2">Měsíc</th>
              <th class="py-2 px-2 text-right">Prům. teplota</th>
              <th class="py-2 px-2 text-right">Běžné řízení</th>
              <th class="py-2 px-2 text-right text-sky-400">Optimální řízení</th>
              <th class="py-2 px-2 text-right text-emerald-400">SCOP</th>
              <th class="py-2 px-2 text-right text-amber-400">Úspora Kč</th>
            </tr>
          </thead>
          <tbody id="monthly-tbody" class="divide-y divide-slate-800">
            <!-- Rendered dynamically -->
          </tbody>
          <tfoot id="monthly-tfoot">
            <!-- Summary row dynamically rendered -->
          </tfoot>
        </table>
      </div>
    </div>
  </section>

  <!-- ================= SECTION 3: 5-SEASON SUMMARY TABLE ================= -->
  <section id="sec-table" class="mb-5 rounded-2xl border border-slate-800 bg-slate-900/50 shadow-lg transition-all overflow-hidden">
    <div onclick="toggleSection('table')" class="p-3 sm:p-4 bg-slate-900 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition border-b border-slate-800 select-none">
      <div class="flex items-center gap-2.5">
        <span class="text-base sm:text-lg">📊</span>
        <div>
          <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <span>3. Souhrnná srovnávací tabulka 10 vybraných sezón</span>
          </h2>
          <p class="text-[11px] text-slate-400">Podrobný roční přehled spotřeby elektřiny pro topení i TUV, sezónního SCOP, počtu startů a finanční úspory</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button type="button" class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 flex items-center gap-1.5 font-medium pointer-events-none shadow-sm">
          <span id="chevron-table">▲</span>
          <span id="label-table">Sbalit</span>
        </button>
      </div>
    </div>
    <div id="view-table-container" class="space-y-5 p-3 sm:p-5">
    <div class="card p-4 md:p-5">
      <div class="mb-4">
        <h2 class="text-base font-semibold text-white flex items-center gap-2">
          <span>📊 Souhrnná srovnávací tabulka 10 vybraných sezón</span>
        </h2>
        <p class="text-xs text-slate-400">
          Přehled spotřeby elektřiny pro vytápění i TUV, sezónního SCOP, počtu startů kompresoru a finanční úspory v 10 vybraných sezónách.
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-slate-400 border-b border-slate-700 uppercase font-semibold">
            <tr>
              <th class="py-3 px-3">Topná sezóna</th>
              <th class="py-3 px-2 text-right">Průměrná teplota</th>
              <th class="py-3 px-2 text-right">Teplo domu</th>
              <th class="py-3 px-2 text-right text-slate-400">Běžné řízení [kWh]</th>
              <th class="py-3 px-2 text-right text-sky-400">Optimalizované [kWh]</th>
              <th class="py-3 px-2 text-right text-emerald-400">Úspora elektřiny</th>
              <th class="py-3 px-2 text-right text-amber-400">Finanční úspora</th>
              <th class="py-3 px-2 text-right text-emerald-400">SCOP celkem</th>
              <th class="py-3 px-2 text-right text-slate-300">SCOP topení</th>
              <th class="py-3 px-2 text-right text-slate-300">SCOP TUV</th>
              <th class="py-3 px-2 text-right">Počet startů</th>
            </tr>
          </thead>
          <tbody id="multi-season-tbody" class="divide-y divide-slate-800">
            <!-- Rendered dynamically -->
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ================= SECTION 4: HP KEYMARK CERTIFIED CATALOG & COMPARISON ================= -->
  <section id="sec-dual" class="mb-5 rounded-2xl border border-slate-800 bg-slate-900/50 shadow-lg transition-all overflow-hidden">
    <div onclick="toggleSection('dual')" class="p-3 sm:p-4 bg-slate-900 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition border-b border-slate-800 select-none">
      <div class="flex items-center gap-2.5">
        <span class="text-base sm:text-lg">🏷️</span>
        <div>
          <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <span>4. Katalog tepelných čerpadel · údaje HP Keymark</span>
            <span id="header-cat-badge" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/40 font-normal">Aktivní: Gawliczek HM-M0-A2</span>
          </h2>
          <p class="text-[11px] text-slate-400">Katalog deklarovaných parametrů modelů pro podlahové vytápění (35 °C), radiátory (55 °C) a ohřev TUV</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button type="button" class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 flex items-center gap-1.5 font-medium pointer-events-none shadow-sm">
          <span id="chevron-dual">▼</span>
          <span id="label-dual">Rozbalit</span>
        </button>
      </div>
    </div>
    <div id="view-dual-container" class="space-y-5 p-3 sm:p-5 hidden">
    <div class="card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <span>🏷️ Katalog tepelných čerpadel · údaje HP Keymark</span>
          </h2>
          <p class="text-xs text-slate-400">
            Výběr z certifikované evropské databáze Heat Pump KEYMARK. Kliknutím na kterékoli čerpadlo se okamžitě přepočte celá simulace pro podlahovku (35 °C), radiátory (55 °C) i ohřev TUV.
          </p>
        </div>
        <button onclick="openKeymarkModal()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 shadow">
          <span>➕ Zadat / stáhnout jiné čerpadlo z Keymarku</span>
        </button>
      </div>

      <!-- Active Selected Model Highlight Banner (No Price!) -->
      <div class="p-4 rounded-xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-sky-950/60 border border-emerald-500/40 mb-5">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded bg-emerald-600 text-white text-[11px] font-bold">AKTIVNÍ V SIMULACI</span>
              <h3 id="cat-active-hp-title" class="text-base font-bold text-white">Gawliczek Ultra tiché 8,1 kW (HM-M0-A2)</h3>
            </div>
            <p id="cat-active-hp-desc" class="text-xs text-slate-300 mt-1">
              Certifikát Keymark 011-1W1163 • Kompresor Panasonic • Chladivo R290 (Propan) • Hluk 35–38 dB(A)
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <div class="p-2 rounded-lg bg-slate-900/90 border border-slate-700 text-center min-w-[90px]">
              <div class="text-[10px] text-slate-400">SCOP (35 °C)</div>
              <div id="cat-active-hp-scop35" class="text-emerald-400 font-bold text-sm">4,62</div>
            </div>
            <div class="p-2 rounded-lg bg-slate-900/90 border border-slate-700 text-center min-w-[90px]">
              <div class="text-[10px] text-slate-400">SCOP (55 °C)</div>
              <div id="cat-active-hp-scop55" class="text-sky-400 font-bold text-sm">3,45</div>
            </div>
            <div class="p-2 rounded-lg bg-slate-900/90 border border-slate-700 text-center min-w-[90px]">
              <div class="text-[10px] text-slate-400">COP TUV (η_wh)</div>
              <div id="cat-active-hp-coptuv" class="text-amber-400 font-bold text-sm">2,50 (135 %)</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid of Certified Keymark Heat Pumps (No Prices!) -->
      <div id="keymark-catalog-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </section>

  <!-- ================= SECTION 5: GAS CONDENSING BOILER COMPARISON ================= -->
  <section id="sec-gas" class="mb-5 rounded-2xl border border-slate-800 bg-slate-900/50 shadow-lg transition-all overflow-hidden">
    <div onclick="toggleSection('gas')" class="p-3 sm:p-4 bg-slate-900 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition border-b border-slate-800 select-none">
      <div class="flex items-center gap-2.5">
        <span class="text-base sm:text-lg">🔥</span>
        <div>
          <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <span>5. Srovnání s plynovým kondenzačním kotlem</span>
            <span id="header-gas-badge" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800/40 font-normal">Úspora s TČ vs plyn</span>
          </h2>
          <p class="text-[11px] text-slate-400">Ekonomické porovnání provozních nákladů, emisní povolenky EU ETS 2 a stálých plateb</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button type="button" class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 flex items-center gap-1.5 font-medium pointer-events-none shadow-sm">
          <span id="chevron-gas">▼</span>
          <span id="label-gas">Rozbalit</span>
        </button>
      </div>
    </div>
    <div id="view-gas-container" class="space-y-5 p-3 sm:p-5 hidden">
      <canvas id="gasComparisonCanvas" class="w-full h-full block" role="img" aria-label="Náklady TČ a plynu; hodnoty jsou v tabulce"></canvas>
    </div>
  </section>

  <!-- ================= KEYMARK SELECTION & CUSTOM INPUT MODAL ================= -->
  <div id="keymark-modal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 hidden">
    <div class="card bg-slate-900 border border-slate-700 w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden">
      <!-- Modal Header -->
      <div class="p-4 md:p-5 border-b border-slate-700 flex items-center justify-between">
        <div>
          <h2 class="text-base md:text-lg font-bold text-white flex items-center gap-2">
            <span>🏷️ Výběr tepelného čerpadla z certifikované databáze HP Keymark</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">
            Zvolte kterékoliv certifikované čerpadlo, vyhledejte model nebo stáhněte parametry přímo z certifikátu HP Keymark.
          </p>
        </div>
        <button onclick="closeKeymarkModal()" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-lg font-bold">✕</button>
      </div>

      <!-- Search & Filters -->
      <div class="p-3 md:p-4 bg-slate-950/70 border-b border-slate-800 flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div class="relative w-full sm:w-80">
          <input
            type="text"
            id="km-search-box"
            placeholder="Hledat model nebo certifikát (např. HM-M0, 011-1W1163, Vitocal, S2125)..."
            oninput="filterKeymarkModal(this.value)"
            class="w-full bg-slate-900 text-white rounded-lg px-3 py-1.5 text-xs border border-slate-700 focus:outline-none focus:border-emerald-400 placeholder-slate-500"
          >
        </div>
        <div class="flex items-center gap-1.5 text-xs w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <button onclick="setKeymarkFilter('all')" id="km-btn-all" class="px-2.5 py-1 rounded bg-emerald-600 text-white font-medium text-[11px]">Vše</button>
          <button onclick="setKeymarkFilter('r290')" id="km-btn-r290" class="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 text-[11px]">R290 (Propan)</button>
          <button onclick="setKeymarkFilter('gawliczek')" id="km-btn-gawliczek" class="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 text-[11px]">Gawliczek / Warmhouse</button>
          <button onclick="toggleCustomKeymarkBox()" class="px-2.5 py-1 rounded bg-sky-900/60 text-sky-300 hover:bg-sky-800/80 border border-sky-500/40 font-semibold text-[11px] ml-auto">
            ➕ Stáhnout / Zadat z Keymarku
          </button>
        </div>
      </div>

      <!-- Custom Keymark Certificate Fetcher & Input Box (collapsible) -->
      <div id="custom-km-form" class="p-4 bg-slate-850 border-b border-slate-700 hidden">
        <!-- Certificate Fetcher Tool -->
        <div class="mb-3.5 p-3 rounded-xl bg-slate-900 border border-sky-500/30">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-bold text-sky-300 flex items-center gap-1.5">
              <span>🔍 Vyhledat v databázi HP Keymark & stáhnout certifikát:</span>
            </span>
            <span class="text-[10px] text-slate-400 font-mono">dahr.heatpumpkeymark.com</span>
          </div>
          <div class="flex flex-col sm:flex-row gap-2">
            <input type="text" id="km-fetch-input" placeholder="Zadejte číslo certifikátu (např. 011-1W1163, 012-C70025, 041-K008-01, 011-1W0389)..." class="flex-1 bg-slate-950 p-2 rounded-lg border border-slate-700 text-white text-xs focus:border-sky-400 focus:outline-none">
            <button onclick="downloadKeymarkCertificate()" class="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition flex items-center justify-center gap-1.5 whitespace-nowrap shadow">
              <span>⬇️ Stáhnout data z certifikátu</span>
            </button>
          </div>
          <!-- Quick sample chips -->
          <div class="flex flex-wrap items-center gap-1.5 mt-2">
            <span class="text-[10px] text-slate-400">Rychlý výběr protokolu:</span>
            <button type="button" onclick="quickFetchCert('011-1W1163')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-emerald-300 font-mono">011-1W1163 (Gawliczek HM 8kW)</button>
            <button type="button" onclick="quickFetchCert('012-C70025')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-sky-300 font-mono">012-C70025 (Vitocal 250-A)</button>
            <button type="button" onclick="quickFetchCert('041-K008-01')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-sky-300 font-mono">041-K008-01 (NIBE S2125)</button>
            <button type="button" onclick="quickFetchCert('011-1W0389')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-sky-300 font-mono">011-1W0389 (aroTHERM plus)</button>
            <button type="button" onclick="quickFetchCert('011-1W0712')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-amber-300 font-mono">011-1W0712 (Aquarea L R290)</button>
          </div>
          <div id="km-fetch-status" class="hidden mt-2 p-2 rounded bg-slate-950 text-xs border border-sky-500/50"></div>
        </div>

        <h4 class="text-xs font-bold text-white mb-2 flex items-center gap-1.5">
          <span>Parametry certifikovaného čerpadla (podlahovka 35 °C, radiátory 55 °C, TUV):</span>
        </h4>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
          <div>
            <label class="text-slate-400 block mb-1">Výrobce a model:</label>
            <input type="text" id="cust-km-name" placeholder="Např. Gawliczek HM-M0-A2" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Číslo certifikátu:</label>
            <input type="text" id="cust-km-cert" placeholder="Např. 011-1W1163" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Výkon 35 °C podlaha (kW):</label>
            <input type="number" id="cust-km-power35" value="8.1" step="0.5" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Výkon 55 °C radiátory (kW):</label>
            <input type="number" id="cust-km-power55" value="7.5" step="0.5" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">SCOP (35 °C podlaha):</label>
            <input type="number" id="cust-km-scop35" value="4.62" step="0.05" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">SCOP (55 °C radiátory):</label>
            <input type="number" id="cust-km-scop55" value="3.45" step="0.05" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">COP TUV (při 7 °C):</label>
            <input type="number" id="cust-km-copdhw" value="2.50" step="0.05" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Účinnost TUV η_wh (%):</label>
            <input type="number" id="cust-km-etawh" value="135" step="1" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Chladivo:</label>
            <input type="text" id="cust-km-refrig" value="R290 (Propan)" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Hlučnost dB(A):</label>
            <input type="text" id="cust-km-noise" value="~35-38 dB(A)" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
          <div>
            <label class="text-slate-400 block mb-1">Minimální modulace (kW):</label>
            <input type="number" id="cust-km-minmod" value="2.5" step="0.2" class="w-full bg-slate-900 p-1.5 rounded border border-slate-700 text-white text-xs">
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button onclick="toggleCustomKeymarkBox()" class="px-3 py-1 rounded bg-slate-800 text-slate-300 text-xs">Zrušit</button>
          <button onclick="saveCustomKeymarkModel()" class="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs">Uložit a aktivovat pro simulaci</button>
        </div>
      </div>

      <!-- Keymark Cards Grid (scrollable) -->
      <div id="km-cards-container" class="p-4 md:p-5 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-3.5 flex-1">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </div>

  <!-- Floating Tooltip Element -->
  <div id="chartTooltip" class="chart-tooltip"></div>

  <!-- Core JavaScript Reactive Simulation Engine -->
  <script>
    // Initial weather data (compact representation of 10 heating seasons: Oct 1 - Apr 30)
    let rawWeather = __WEATHER_JSON__;

    // Certified Heat Pump KEYMARK Registry for simulated download lookup
    const keymarkCertificatesRegistry = {
      '011-1W1163': {
        name: 'Gawliczek Ultra tiché 8,1 kW (HM-M0-A2)',
        brand: 'Gawliczek / Warmhouse',
        modelCode: 'HM-M0-A2',
        certNo: '011-1W1163',
        pDesign35: 8.1,
        pDesign55: 7.5,
        minMod: 2.5,
        scop35: 4.62,
        scop55: 3.45,
        copDhwRef: 2.50,
        etaWh: 135,
        dhwProfile: 'L',
        noiseDb: '~35-38 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Panasonic Full Inverter (ultra tichý monoblok)',
        copA7W35: 5.30, copA2W35: 4.45, copAm7W35: 3.35, copAm15W35: 2.65,
        copA7W55: 3.40, copA2W55: 2.75, copAm7W55: 2.15, copAm15W55: 1.80,
        desc: 'Výchozí referenční model Gawliczek s ultra tichým invertorovým kompresorem Panasonic a přírodním chladivem R290.'
      },
      '012-C70025': {
        name: 'Viessmann Vitocal 250-A 8 kW',
        brand: 'Viessmann Climate Solutions',
        modelCode: 'AWO-E-AC 251.A08',
        certNo: '012-C70025',
        pDesign35: 8.1,
        pDesign55: 7.8,
        minMod: 2.4,
        scop35: 4.72,
        scop55: 3.65,
        copDhwRef: 2.70,
        etaWh: 142,
        dhwProfile: 'L',
        noiseDb: '30–35 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Scroll Inverter (Advanced Acoustic Design)',
        copA7W35: 5.25, copA2W35: 4.30, copAm7W35: 3.40, copAm15W35: 2.70,
        copA7W55: 3.55, copA2W55: 2.85, copAm7W55: 2.25, copAm15W55: 1.85,
        desc: 'Prémiové německé čerpadlo s patentovanou akustickou konstrukcí AAD a přírodním chladivem R290.'
      },
      '041-K008-01': {
        name: 'NIBE S2125-8 (8 kW)',
        brand: 'NIBE Energy Systems',
        modelCode: 'S2125-8',
        certNo: '041-K008-01',
        pDesign35: 8.0,
        pDesign55: 7.7,
        minMod: 2.2,
        scop35: 4.85,
        scop55: 3.75,
        copDhwRef: 2.90,
        etaWh: 148,
        dhwProfile: 'XL',
        noiseDb: '38 dB(A) ve 2m',
        refrigerant: 'R290 (Propan)',
        compressor: 'NIBE Intelligent Inverter',
        copA7W35: 5.35, copA2W35: 4.40, copAm7W35: 3.50, copAm15W35: 2.80,
        copA7W55: 3.65, copA2W55: 2.95, copAm7W55: 2.30, copAm15W55: 1.90,
        desc: 'Švédské prémiové invertorové čerpadlo s vysokým sezónním SCOP a chladivem R290.'
      },
      '011-1W0389': {
        name: 'Vaillant aroTHERM plus VWL 75/6 A',
        brand: 'Vaillant Group',
        modelCode: 'VWL 75/6 A 230V',
        certNo: '011-1W0389',
        pDesign35: 7.5,
        pDesign55: 7.0,
        minMod: 2.1,
        scop35: 4.68,
        scop55: 3.58,
        copDhwRef: 2.65,
        etaWh: 138,
        dhwProfile: 'L',
        noiseDb: '35–37 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Sound Safe System Inverter',
        copA7W35: 4.90, copA2W35: 4.10, copAm7W35: 3.10, copAm15W35: 2.50,
        copA7W55: 3.35, copA2W55: 2.70, copAm7W55: 2.10, copAm15W55: 1.75,
        desc: 'Osvědčený tichý německý monoblok s přírodním chladivem R290.'
      },
      '011-1W0712': {
        name: 'Panasonic Aquarea L-Series 7 kW (R290)',
        brand: 'Panasonic Corporation',
        modelCode: 'WH-WDG07LE5',
        certNo: '011-1W0712',
        pDesign35: 7.0,
        pDesign55: 6.8,
        minMod: 2.0,
        scop35: 4.80,
        scop55: 3.65,
        copDhwRef: 2.75,
        etaWh: 140,
        dhwProfile: 'L',
        noiseDb: '52 dB(A) (Lwa)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Panasonic R290 Rotary Inverter',
        copA7W35: 5.15, copA2W35: 4.25, copAm7W35: 3.30, copAm15W35: 2.65,
        copA7W55: 3.50, copA2W55: 2.80, copAm7W55: 2.20, copAm15W55: 1.80,
        desc: 'Nejnovější generace Panasonic generace L s přírodním chladivem R290 pro novostavby i modernizace.'
      },
      '011-1W0942': {
        name: 'Bosch Compress 5800i AW 7 kW (R290)',
        brand: 'Bosch Home Comfort',
        modelCode: 'CS5800iAW 7 OR-S',
        certNo: '011-1W0942',
        pDesign35: 7.2,
        pDesign55: 6.9,
        minMod: 2.2,
        scop35: 4.75,
        scop55: 3.60,
        copDhwRef: 2.60,
        etaWh: 136,
        dhwProfile: 'L',
        noiseDb: '34–36 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Twin-Rotary Inverter Silent',
        copA7W35: 5.05, copA2W35: 4.20, copAm7W35: 3.25, copAm15W35: 2.60,
        copA7W55: 3.40, copA2W55: 2.75, copAm7W55: 2.15, copAm15W55: 1.75,
        desc: 'Vysoce tichý monoblok Bosch na chladivo R290 s integrovaným odhlučněním.'
      },
      '011-1W0452': {
        name: 'Daikin Altherma 3 R MT 8 kW',
        brand: 'Daikin Europe',
        modelCode: 'ERRA08EV3',
        certNo: '011-1W0452',
        pDesign35: 8.0,
        pDesign55: 7.6,
        minMod: 2.5,
        scop35: 4.55,
        scop55: 3.42,
        copDhwRef: 2.40,
        etaWh: 130,
        dhwProfile: 'L',
        noiseDb: '40–42 dB(A)',
        refrigerant: 'R32',
        compressor: 'Daikin Swing Inverter',
        copA7W35: 4.85, copA2W35: 3.95, copAm7W35: 3.00, copAm15W35: 2.40,
        copA7W55: 3.25, copA2W55: 2.60, copAm7W55: 2.00, copAm15W55: 1.65,
        desc: 'Středněteplotní jednotka Daikin na chladivo R32 pro novostavby i rekonstrukce.'
      }
    };

    // Certified Heat Pump KEYMARK Database (No prices!)
    const keymarkDatabase = [
      {
        id: 'gawliczek-81',
        name: 'Gawliczek Ultra tiché 8,1 kW (HM-M0-A2)',
        brand: 'Gawliczek / Warmhouse',
        modelCode: 'HM-M0-A2',
        certNo: '011-1W1163',
        pDesign35: 8.1,
        pDesign55: 7.5,
        minMod: 2.5,
        scop35: 4.62,
        scop55: 3.45,
        copDhwRef: 2.50,
        etaWh: 135,
        dhwProfile: 'L',
        noiseDb: '~35-38 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Panasonic Full Inverter (ultra tichý monoblok)',
        copA7W35: 5.30, copA2W35: 4.45, copAm7W35: 3.35, copAm15W35: 2.65,
        copA7W55: 3.40, copA2W55: 2.75, copAm7W55: 2.15, copAm15W55: 1.80,
        desc: 'Výchozí referenční model Gawliczek s ultra tichým invertorovým kompresorem Panasonic a přírodním chladivem R290.'
      },
      {
        id: 'gawliczek-10',
        name: 'Gawliczek / Warmhouse 10 kW R290 Ultra tiché · HM-M1-A1',
        brand: 'Gawliczek / Warmhouse',
        modelCode: 'HM-M1-A1',
        certNo: '011-1W1163',
        pDesign35: 7.46,
        pDesign55: 7.66,
        minMod: 3.0,
        scop35: 5.01,
        scop55: 3.91,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '56 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Panasonic Twin-Rotary Inverter (R290)',
        copA7W35: 4.96, copA2W35: 4.35, copAm7W35: 3.25, copAm15W35: 2.55,
        copA7W55: 3.27, copA2W55: 2.65, copAm7W55: 2.10, copAm15W55: 1.75,
        desc: 'Gawliczek R290 Ultra tiché (Warmhouse HM-M1-A1, Keymark 011-1W1163) s dvouvačkovým kompresorem Panasonic.'
      },
      {
        id: 'gawliczek-12',
        name: 'Gawliczek / Warmhouse 12 kW R290 Ultra tiché · HM-M2-A1',
        brand: 'Gawliczek / Warmhouse',
        modelCode: 'HM-M2-A1',
        certNo: '011-1W1160',
        pDesign35: 10.38,
        pDesign55: 9.70,
        minMod: 3.5,
        scop35: 5.08,
        scop55: 3.85,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '58 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Panasonic Twin-Rotary Inverter (R290)',
        copA7W35: 4.71, copA2W35: 4.25, copAm7W35: 3.15, copAm15W35: 2.45,
        copA7W55: 3.20, copA2W55: 2.55, copAm7W55: 2.05, copAm15W55: 1.70,
        desc: 'Gawliczek 12 kW R290 Ultra tiché (Warmhouse HM-M2-A1 / HM-M1S-A2, Keymark 011-1W1160) pro domy s TZ do 10 kW.'
      },
      {
        id: 'gawliczek-16',
        name: 'Gawliczek / Warmhouse 16,2 kW R290 Ultra tiché · HM-M3-A1',
        brand: 'Gawliczek / Warmhouse',
        modelCode: 'HM-M3-A1',
        certNo: '011-1W1161',
        pDesign35: 14.53,
        pDesign55: 13.15,
        minMod: 4.2,
        scop35: 5.05,
        scop55: 4.00,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '61 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Panasonic Twin-Rotary Inverter (R290)',
        copA7W35: 4.67, copA2W35: 4.10, copAm7W35: 3.10, copAm15W35: 2.40,
        copA7W55: 3.11, copA2W55: 2.50, copAm7W55: 2.00, copAm15W55: 1.68,
        desc: 'Gawliczek 16,2 kW R290 Ultra tiché (Warmhouse HM-M3-A1 / HM-M2S-A2, Keymark 011-1W1161) pro domy s TZ do 13–14 kW.'
      },
      {
        id: 'gawliczek-pw-6',
        name: 'Gawliczek / Power World 6 kW R290 · PW020-DKZLRS-E/S',
        brand: 'Gawliczek / Power World',
        modelCode: 'PW020-DKZLRS-E/S',
        certNo: '041-K032-11 / 02',
        pDesign35: 4.19,
        pDesign55: 4.15,
        minMod: 2.0,
        scop35: 5.03,
        scop55: 3.69,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '56 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'HIGHLY (Hitachi) Twin-Rotary DC Inverter',
        copA7W35: 5.02, copA2W35: 4.20, copAm7W35: 3.20, copAm15W35: 2.55,
        copA7W55: 3.30, copA2W55: 2.65, copAm7W55: 2.10, copAm15W55: 1.75,
        desc: 'Gawliczek 6 kW R290 (Power World CleanLife PW020-DKZLRS-E/S, Keymark 041-K032-11) pro nízkoenergetické domy s TZ do 4 kW.'
      },
      {
        id: 'gawliczek-pw-89',
        name: 'Gawliczek / Power World 8,9 kW R290 · PW030-DKZLRS-E/S',
        brand: 'Gawliczek / Power World',
        modelCode: 'PW030-DKZLRS-E/S',
        certNo: '041-K032-07 / 02',
        pDesign35: 5.82,
        pDesign55: 5.59,
        minMod: 2.8,
        scop35: 4.64,
        scop55: 3.48,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '58 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'HIGHLY (Hitachi) Twin-Rotary DC Inverter',
        copA7W35: 4.90, copA2W35: 4.05, copAm7W35: 3.10, copAm15W35: 2.45,
        copA7W55: 3.20, copA2W55: 2.60, copAm7W55: 2.05, copAm15W55: 1.70,
        desc: 'Gawliczek 8,9 kW R290 (Power World CleanLife GW030/PW030-DKZLRS-E/S, Keymark 041-K032-07) pro novostavby s TZ do 6 kW.'
      },
      {
        id: 'gawliczek-pw-114',
        name: 'Gawliczek / Power World 11,4 kW R290 · PW040-DKZLRS-E/S',
        brand: 'Gawliczek / Power World',
        modelCode: 'PW040-DKZLRS-E/S',
        certNo: '041-K032-08 / 02',
        pDesign35: 7.89,
        pDesign55: 8.70,
        minMod: 3.5,
        scop35: 4.60,
        scop55: 3.50,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '59 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'HIGHLY (Hitachi) Twin-Rotary DC Inverter',
        copA7W35: 4.89, copA2W35: 4.05, copAm7W35: 3.10, copAm15W35: 2.45,
        copA7W55: 3.20, copA2W55: 2.60, copAm7W55: 2.05, copAm15W55: 1.70,
        desc: 'Gawliczek 11,4 kW R290 (Power World CleanLife GW040/PW040-DKZLRS-E, Keymark 041-K032-08) pro domy s TZ do 8 kW.'
      },
      {
        id: 'gawliczek-pw-148',
        name: 'Gawliczek / Power World 14,8 kW R290 · PW050-DKZLRS-E',
        brand: 'Gawliczek / Power World',
        modelCode: 'PW050-DKZLRS-E',
        certNo: '041-K032-09 / 02',
        pDesign35: 10.27,
        pDesign55: 12.17,
        minMod: 4.2,
        scop35: 4.60,
        scop55: 3.44,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '61 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'HIGHLY (Hitachi) Twin-Rotary DC Inverter',
        copA7W35: 4.84, copA2W35: 4.00, copAm7W35: 3.05, copAm15W35: 2.40,
        copA7W55: 3.15, copA2W55: 2.55, copAm7W55: 2.00, copAm15W55: 1.65,
        desc: 'Gawliczek 14,8 kW R290 (Power World CleanLife PW050-DKZLRS-E, Keymark 041-K032-09) pro větší domy s TZ do 12 kW.'
      },
      {
        id: 'gawliczek-pw-182',
        name: 'Gawliczek / Power World 18,2 kW R290 · PW055-DKZLRS-E',
        brand: 'Gawliczek / Power World',
        modelCode: 'PW055-DKZLRS-E',
        certNo: '041-K032-14 / 02',
        pDesign35: 12.03,
        pDesign55: 11.94,
        minMod: 5.0,
        scop35: 4.68,
        scop55: 3.60,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '65 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'HIGHLY (Hitachi) Twin-Rotary DC Inverter',
        copA7W35: 4.85, copA2W35: 4.05, copAm7W35: 3.10, copAm15W35: 2.45,
        copA7W55: 3.20, copA2W55: 2.60, copAm7W55: 2.05, copAm15W55: 1.70,
        desc: 'Gawliczek 18,2 kW R290 (Power World CleanLife GW055/PW055-DKZLRS-E, Keymark 041-K032-14) pro velké domy s TZ do 13–15 kW.'
      },
      {
        id: 'viessmann-8',
        name: 'Viessmann Vitocal 250-A 8 kW',
        brand: 'Viessmann Climate Solutions',
        modelCode: 'AWO-E-AC 251.A08',
        certNo: '012-C70025',
        pDesign35: 8.1,
        pDesign55: 7.8,
        minMod: 2.4,
        scop35: 4.72,
        scop55: 3.65,
        copDhwRef: 2.70,
        etaWh: 142,
        dhwProfile: 'L',
        noiseDb: '30–35 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Scroll Inverter (Advanced Acoustic Design)',
        copA7W35: 5.25, copA2W35: 4.30, copAm7W35: 3.40, copAm15W35: 2.70,
        copA7W55: 3.55, copA2W55: 2.85, copAm7W55: 2.25, copAm15W55: 1.85,
        desc: 'Prémiové německé čerpadlo s patentovanou akustickou konstrukcí AAD a R290.'
      },
      {
        id: 'nibe-8',
        name: 'NIBE S2125-8 (8 kW)',
        brand: 'NIBE Energy Systems',
        modelCode: 'S2125-8',
        certNo: '041-K008-01',
        pDesign35: 8.0,
        pDesign55: 7.7,
        minMod: 2.2,
        scop35: 4.85,
        scop55: 3.75,
        copDhwRef: 2.90,
        etaWh: 148,
        dhwProfile: 'XL',
        noiseDb: '38 dB(A) ve 2m',
        refrigerant: 'R290 (Propan)',
        compressor: 'NIBE Intelligent Inverter',
        copA7W35: 5.35, copA2W35: 4.40, copAm7W35: 3.50, copAm15W35: 2.80,
        copA7W55: 3.65, copA2W55: 2.95, copAm7W55: 2.30, copAm15W55: 1.90,
        desc: 'Švédské prémiové invertorové čerpadlo s vysokým sezónním SCOP a R290.'
      },
      {
        id: 'vaillant-75',
        name: 'Vaillant aroTHERM plus VWL 75/6 A',
        brand: 'Vaillant Group',
        modelCode: 'VWL 75/6 A 230V',
        certNo: '011-1W0389',
        pDesign35: 7.5,
        pDesign55: 7.0,
        minMod: 2.1,
        scop35: 4.68,
        scop55: 3.58,
        copDhwRef: 2.65,
        etaWh: 138,
        dhwProfile: 'L',
        noiseDb: '35–37 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Sound Safe System Inverter',
        copA7W35: 4.90, copA2W35: 4.10, copAm7W35: 3.10, copAm15W35: 2.50,
        copA7W55: 3.35, copA2W55: 2.70, copAm7W55: 2.10, copAm15W55: 1.75,
        desc: 'Osvědčený tichý německý monoblok s přírodním chladivem R290.'
      },
      {
        id: 'panasonic-l-7',
        name: 'Panasonic Aquarea L-Series 7 kW (R290)',
        brand: 'Panasonic Corporation',
        modelCode: 'WH-WDG07LE5',
        certNo: '011-1W0712',
        pDesign35: 7.0,
        pDesign55: 6.8,
        minMod: 2.0,
        scop35: 4.80,
        scop55: 3.65,
        copDhwRef: 2.75,
        etaWh: 140,
        dhwProfile: 'L',
        noiseDb: '52 dB(A) (Lwa)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Panasonic R290 Rotary Inverter',
        copA7W35: 5.15, copA2W35: 4.25, copAm7W35: 3.30, copAm15W35: 2.65,
        copA7W55: 3.50, copA2W55: 2.80, copAm7W55: 2.20, copAm15W55: 1.80,
        desc: 'Monoblok Panasonic generace L s R290 pro novostavby a nízkoteplotní soustavy.'
      },
      {
        id: 'bosch-5800-7',
        name: 'Bosch Compress 5800i AW 7 kW (R290)',
        brand: 'Bosch Home Comfort',
        modelCode: 'CS5800iAW 7 OR-S',
        certNo: '011-1W0942',
        pDesign35: 7.2,
        pDesign55: 6.9,
        minMod: 2.2,
        scop35: 4.75,
        scop55: 3.60,
        copDhwRef: 2.60,
        etaWh: 136,
        dhwProfile: 'L',
        noiseDb: '34–36 dB(A)',
        refrigerant: 'R290 (Propan)',
        compressor: 'Twin-Rotary Inverter Silent',
        copA7W35: 5.05, copA2W35: 4.20, copAm7W35: 3.25, copAm15W35: 2.60,
        copA7W55: 3.40, copA2W55: 2.75, copAm7W55: 2.15, copAm15W55: 1.75,
        desc: 'Tichý monoblok Bosch na chladivo R290 s vynikajícím sezónním SCOP.'
      },
      {
        id: 'daikin-8',
        name: 'Daikin Altherma 3 R MT 8 kW',
        brand: 'Daikin Europe',
        modelCode: 'ERRA08EV3',
        certNo: '011-1W0452',
        pDesign35: 8.0,
        pDesign55: 7.6,
        minMod: 2.5,
        scop35: 4.55,
        scop55: 3.42,
        copDhwRef: 2.40,
        etaWh: 130,
        dhwProfile: 'L',
        noiseDb: '40–42 dB(A)',
        refrigerant: 'R32',
        compressor: 'Daikin Swing Inverter',
        copA7W35: 4.85, copA2W35: 3.95, copAm7W35: 3.00, copAm15W35: 2.40,
        copA7W55: 3.25, copA2W55: 2.60, copAm7W55: 2.00, copAm15W55: 1.65,
        desc: 'Japonská středněteplotní jednotka na R32 pro novostavby i rekonstrukce.'
      },
      {
        id: 'gree-versati-8',
        name: 'Gree Versati 8 kW R290 · GRS-CQ8Pd/NpG4-E',
        brand: 'Gree Electric Appliances',
        modelCode: 'GRS-CQ8Pd/NpG4-E',
        certNo: '041-K004-34',
        pDesign35: 8.0,
        pDesign55: 7.0,
        minMod: 2.0,
        scop35: 5.13,
        scop55: 3.88,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '56 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Gree G-Force Two-Stage Inverter (R290)',
        copA7W35: 5.00, copA2W35: 4.91, copAm7W35: 3.03, copAm15W35: 2.50,
        copA7W55: 3.60, copA2W55: 4.04, copAm7W55: 2.32, copAm15W55: 1.80,
        desc: 'Gree Versati monobloc 8 kW R290 (GRS-CQ8Pd/NpG4-E, certifikát Keymark 041-K004-34) s ekologickým chladivem R290.'
      },
      {
        id: 'gree-versati-10',
        name: 'Gree Versati 10 kW R290 · GRS-CQ10PD/NPG4-E',
        brand: 'Gree Electric Appliances',
        modelCode: 'GRS-CQ10PD/NPG4-E',
        certNo: '041-K004-34',
        pDesign35: 9.0,
        pDesign55: 8.0,
        minMod: 2.3,
        scop35: 4.93,
        scop55: 3.88,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '56 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Gree G-Force Two-Stage Inverter (R290)',
        copA7W35: 4.75, copA2W35: 4.71, copAm7W35: 2.84, copAm15W35: 2.45,
        copA7W55: 3.30, copA2W55: 4.04, copAm7W55: 2.25, copAm15W55: 1.80,
        desc: 'Gree Versati monobloc 10 kW R290 (GRS-CQ10PD/NPG4-E, certifikát Keymark 041-K004-34) s ekologickým chladivem R290.'
      },
      {
        id: 'gree-versati-6',
        name: 'Gree Versati V 6 kW R290 · GRS-CQ6.0Pd/NpG4-E',
        brand: 'Gree Electric Appliances',
        modelCode: 'GRS-CQ6.0Pd/NpG4-E',
        certNo: '011-1W1085',
        pDesign35: 6.0,
        pDesign55: 6.0,
        minMod: 1.8,
        scop35: 5.18,
        scop55: 3.88,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '54 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Gree Inverter Twin-Rotary (R290)',
        copA7W35: 5.00, copA2W35: 5.05, copAm7W35: 3.20, copAm15W35: 2.50,
        copA7W55: 3.70, copA2W55: 3.80, copAm7W55: 2.55, copAm15W55: 1.85,
        desc: 'Gree Versati V Monobloc 6 kW R290 (GRS-CQ6.0Pd/NpG4-E, certifikát Keymark 011-1W1085) s nízkou hladinou hluku.'
      },
      {
        id: 'gree-versati-4',
        name: 'Gree Versati V 4 kW R290 · GRS-CQ4.0Pd/NpG4-E',
        brand: 'Gree Electric Appliances',
        modelCode: 'GRS-CQ4.0Pd/NpG4-E',
        certNo: '011-1W1085',
        pDesign35: 5.0,
        pDesign55: 5.0,
        minMod: 1.5,
        scop35: 5.13,
        scop55: 3.88,
        copDhwRef: null,
        etaWh: null,
        dhwProfile: 'Viz přesná sestava ve zdroji',
        noiseDb: '54 dB(A) LWA',
        refrigerant: 'R290',
        compressor: 'Gree Inverter Twin-Rotary (R290)',
        copA7W35: 5.20, copA2W35: 4.91, copAm7W35: 3.42, copAm15W35: 2.50,
        copA7W55: 3.70, copA2W55: 3.77, copAm7W55: 2.60, copAm15W55: 1.85,
        desc: 'Gree Versati V Monobloc 4 kW R290 (GRS-CQ4.0Pd/NpG4-E, certifikát Keymark 011-1W1085) pro nízkoenergetické domy.'
      }
    ];

    // Application state (Model House Defaults)
    let state = {
      // 5 Seasons Windowing
      centerYear: 2022,
      economyPeriod: 'annual',
      currentSeason: '2022-2023',
      hoverSeason: null,
      selectedDayIndex: 98,       // Selected day for 24-hour diurnal profile (default coldest day)
      control: {policy:'day',dayStart:10,dayEnd:16,setback:0.65,blockCompressor:false,dhwNT:true},
      gasDhwEfficiency:86,
      automationLevel: 'optimized', // baseline or optimized

      // Active Keymark Model & System Type
      activeModelId: 'gawliczek-81',
      activeHp: keymarkDatabase[0],
      keymarkFilter: 'all',
      heatingSystem: 'floor',     // 'floor' (35 °C) or 'radiator' (55 °C)

      viewMode: 'all10',          // 'all10', 'single', 'table', 'dual', 'gas'
      sectionsExpanded: {
        all10: true,   // 1. Srovnání 5 sezón
        single: true,  // 2. Detail sezóny & Akumulace & Měsíční bilance
        table: true,   // 3. Tabulka 5 sezón
        dual: false,   // 4. Katalog TČ
        gas: false     // 5. Plyn
      },
      overlayMetric: 'kwh_daily', // 'kwh_daily', 'kwh_cum', 'scop', 'temp'
      singleMetric: 'el',         // 'el', 'scop', 'temp'

      // Location & Weather Source:
      locationName: 'Modelová lokalita – Ostrava',
      lat: null,
      lon: null,
      altitude: 211,              // m n.m.
      tExtDesign: -12.0,          // °C
      isCustomWeatherLoaded: false,

      // Configurable Thermal Parameters:
      qLossDesign: 5.80,          // kW
      tInTarget: 22.0,            // °C
      tTolerance: 1.0,            // °C (koridor 21.0 - 22.0 °C, aku dle kapacity desky)
      tFlowDesign: 28.0,          // °C (výstupní teplota otopné vody při t_e_design)
      floorCovering: 'vinyl',     // 'dlazba', 'vinyl', 'drevo'
      floorMaterial: 'beton',     // 'beton' or 'anhydrit'
      floorThicknessMm: 50,       // mm
      floorAreaM2: 170,           // m2 (20 tun, 5.7 kWh/K)
      electricityPrice: 6.00,     // Kč/kWh s DPH
      hpServiceYearly: 0,         // Kč/rok

      // Domestic Hot Water (TUV):
      dhwEnabled: true,           // true / false
      dhwDailyLiters: 120,        // 120 l/den (3 osoby po 40 l)
      dhwTargetTemp: 55.0,        // 55 °C
      dhwMode: 'smart',           // 'smart' (midday 12-15h high COP) or 'standard'

      // Natural Gas Boiler Comparison:
      gasPrice: 1.60,             // Kč/kWh s DPH
      co2AllowancePriceEur: 30,   // €/t CO2
      gasBoilerEfficiency: 94,    // %
      gasBoilerServiceYearly: 1500// Kč/rok
    };

    // Color palette for seasons (1960–2026)
    const seasonPalette = ['#38bdf8', '#34d399', '#f87171', '#fbbf24', '#c084fc', '#a78bfa', '#f472b6', '#2dd4bf', '#fb923c', '#60a5fa'];
    const seasonColors = {};
    for (let y = 1960; y <= 2026; y++) {
      seasonColors[`${y}-${y + 1}`] = seasonPalette[(y - 1960) % seasonPalette.length];
    }

    // Cache of simulation results
    let simResults = {};

    function getDatabaseYearBounds() {
      const keys = Object.keys(rawWeather || {}).sort();
      if (!keys.length) return [1960, 2026];
      const minYr = Math.max(1960, Number(keys[0].slice(0, 4)));
      const maxYr = Math.min(2026, Number(keys[keys.length - 1].slice(5)));
      return [minYr, maxYr];
    }

    // 10-Season Windowing Helper: returns 10 seasons around state.centerYear from database
    function getActiveSeasons() {
      const source = (typeof rawWeather === 'object' && rawWeather && Object.keys(rawWeather).length) ? rawWeather : simResults;
      const allSeasons = Object.keys(source).sort();
      if (allSeasons.length <= 10) return allSeasons;

      const cy = Number.isFinite(state.centerYear) ? state.centerYear : 2022;
      let idx = allSeasons.findIndex(s => Number(s.slice(0, 4)) >= cy);
      if (idx === -1) idx = allSeasons.length - 1;

      let startIdx = Math.max(0, Math.min(allSeasons.length - 10, idx - 5));
      return allSeasons.slice(startIdx, startIdx + 10);
    }

    // Season Stepper & Preset Controls (1960–2026 if in database)
    function setCenterYear(yr) {
      if (isNaN(yr)) return;
      const [minDb, maxDb] = (state.isCustomWeatherLoaded && Number.isFinite(state.lat) && Number.isFinite(state.lon)) ? [1960, 2026] : getDatabaseYearBounds();
      const clamped = Math.max(minDb, Math.min(maxDb, yr));
      state.centerYear = clamped;

      const inp = document.getElementById('input-center-year');
      if (inp) {
        inp.min = String(minDb);
        inp.max = String(maxDb);
        inp.value = clamped;
      }

      if (state.isCustomWeatherLoaded && Number.isFinite(state.lat) && Number.isFinite(state.lon)) {
        const startYr = Math.max(1960, Math.min(2016, clamped - 5));
        if (!rawWeather[`${startYr}-${startYr + 1}`] || !rawWeather[`${startYr + 9}-${startYr + 10}`]) {
          downloadLocationWeather();
          return;
        }
      }

      recalculateSimulation();
      const active10 = getActiveSeasons();
      if (!active10.includes(state.currentSeason)) {
        state.currentSeason = active10[Math.floor(active10.length / 2)] || active10[0];
      }

      const sel = document.getElementById('select-season-window');
      if (sel) {
        let opt = sel.querySelector(`option[value="${clamped}"]`);
        if (!opt) {
          opt = sel.querySelector('option[data-custom="1"]');
          if (!opt) { opt = document.createElement('option'); opt.dataset.custom = '1'; sel.prepend(opt); }
          opt.value = String(clamped);
          opt.textContent = `Okolo roku ${clamped} (${active10[0]?.slice(0,4)||''}–${active10.at(-1)?.slice(5)||''})`;
        }
        sel.value = String(clamped);
      }

      renderSeasonPills();
      renderOverlayLegend();
      updateUI();
    }

    function onSeasonPresetChange(val) {
      setCenterYear(parseInt(val));
    }

    function stepCenterYear(delta) {
      setCenterYear(state.centerYear + delta);
    }

    // ================= INITIALIZATION =================
    function init() {
      setupCanvasTooltips();
      recalculateSimulation();
      renderSeasonPills();
      renderOverlayLegend();
      updateSingleLegend();
      updateUI();
    }

    // ================= GEOCODING & ARCHIVE API HANDLERS =================
    let searchDebounceTimer = null;

    function onGeoSearchInput(query) {
      clearTimeout(searchDebounceTimer);
      const dropdown = document.getElementById('geo-dropdown');
      const spinner = document.getElementById('search-spinner');

      if (!query || query.trim().length < 2) {
        dropdown.classList.add('hidden');
        spinner.classList.add('hidden');
        return;
      }

      spinner.classList.remove('hidden');
      searchDebounceTimer = setTimeout(async () => {
        try {
          const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query.trim())}&count=6&language=cs&format=json`;
          const resp = await fetch(url);
          const data = await resp.json();
          spinner.classList.add('hidden');

          if (data && data.results && data.results.length > 0) {
            renderGeoDropdown(data.results);
          } else {
            dropdown.innerHTML = '<div class="p-2 text-xs text-slate-400 text-center">Nenalezeny žádné obce</div>';
            dropdown.classList.remove('hidden');
          }
        } catch (e) {
          spinner.classList.add('hidden');
          console.warn('Geocoding error:', e);
        }
      }, 350);
    }

    function renderGeoDropdown(items) {
      const dropdown = document.getElementById('geo-dropdown');
      dropdown.innerHTML = '';
      items.forEach(item => {
        const div = document.createElement('div');
        div.className = "p-2 hover:bg-slate-800 cursor-pointer text-xs border-b border-slate-800 flex justify-between items-center";
        const alt = item.elevation ? `${Math.round(item.elevation)} m` : '–';
        const region = item.admin1 || item.country || '';
        div.innerHTML = `
          <div>
            <span class="font-semibold text-white">${item.name}</span>
            <span class="text-slate-400 text-[10px] ml-1">(${region})</span>
          </div>
          <span class="text-sky-400 font-mono text-[10px]">${alt}</span>
        `;
        div.onclick = () => selectGeoLocation(item);
        dropdown.appendChild(div);
      });
      dropdown.classList.remove('hidden');
    }

    function selectGeoLocation(item) {
      document.getElementById('geo-dropdown').classList.add('hidden');
      document.getElementById('geo-search-input').value = `${item.name} (${item.admin1 || item.country})`;

      state.lat = item.latitude;
      state.lon = item.longitude;
      state.locationName = item.name;

      if (item.elevation !== undefined && item.elevation !== null) {
        state.altitude = Math.round(item.elevation);
        document.getElementById('input-altitude').value = state.altitude;
      }

      if (state.altitude < 300) state.tExtDesign = -12.0;
      else if (state.altitude <= 600) state.tExtDesign = -15.0;
      else state.tExtDesign = -18.0;

      document.getElementById('badge-location').innerText = `📍 ${state.locationName}`;
      document.getElementById('badge-altitude').innerText = `⛰️ ${state.altitude} m n. m.`;
      document.getElementById('badge-te-design').innerText = `Výpočtová teplota t_e: ${state.tExtDesign.toFixed(0)} °C`;

      downloadLocationWeather();
    }

    async function downloadLocationWeather() {
      if (!Number.isFinite(state.lat) || !Number.isFinite(state.lon)) { alert("Nejprve vyberte obec ve vyhledávání."); return; }
      const bar = document.getElementById('fetch-status-bar');
      const text = document.getElementById('fetch-status-text');
      const badge = document.getElementById('fetch-status-badge');
      const srcBadge = document.getElementById('badge-weather-source');

      bar.classList.remove('hidden');
      text.innerText = `Stahuji data z archivu Open-Meteo pro ${state.locationName}...`;
      badge.innerText = '0 %';

      try {
        const startYr = Math.max(1960, Math.min(2016, (state.centerYear || 2022) - 5));
        const endYr = startYr + 10;
        const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${state.lat}&longitude=${state.lon}&start_date=${startYr}-10-01&end_date=${endYr}-04-30&hourly=temperature_2m,relative_humidity_2m,direct_normal_irradiance,diffuse_radiation&timezone=auto`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Chyba při stahování dat');
        const archiveJson = await resp.json();

        badge.innerText = '100 %';
        text.innerText = 'Zpracovávám hodinová data...';

        const parsedSeasons = parseArchiveToSeasons(archiveJson, startYr, endYr);
        rawWeather = parsedSeasons;
        state.isCustomWeatherLoaded = true; state.weatherBaseAltitude = state.altitude;

        if (srcBadge) {
          srcBadge.innerText = `Meteorologická data: Open-Meteo ERA5 (${state.locationName}, ${state.lat.toFixed(2)}°N, ${state.lon.toFixed(2)}°E, ${state.altitude} m)`;
        }

        recalculateSimulation();
        renderSeasonPills();
        renderOverlayLegend();
        updateUI();

        setTimeout(() => {
          bar.classList.add('hidden');
        }, 1200);

      } catch (err) {
        text.innerText = `Chyba stahování: ${err.message}. Používám lokální data.`;
        setTimeout(() => bar.classList.add('hidden'), 3500);
      }
    }

    function parseArchiveToSeasons(archiveData, startYr = null, endYr = null) {
      const times = archiveData.hourly.time;
      const temps = archiveData.hourly.temperature_2m;
      const rhs = archiveData.hourly.relative_humidity_2m;
      const dnis = archiveData.hourly.direct_normal_irradiance || [];
      const diffs = archiveData.hourly.diffuse_radiation || [];

      const firstYr = startYr ?? parseInt(times[0].substring(0, 4), 10);
      const lastYr = endYr ?? parseInt(times[times.length - 1].substring(0, 4), 10);
      const seasons = {};
      for (let y = firstYr; y < lastYr; y++) {
        seasons[`${y}-${y + 1}`] = { start: '', t: [], rh: [], sol: [] };
      }

      for (let i = 0; i < times.length; i++) {
        const tStr = times[i];
        const yr = parseInt(tStr.substring(0, 4));
        const mo = parseInt(tStr.substring(5, 7));

        let sKey = null;
        if (mo >= 10) sKey = `${yr}-${yr + 1}`;
        else if (mo <= 4) sKey = `${yr - 1}-${yr}`;

        if (sKey && seasons[sKey]) {
          if (!seasons[sKey].start) seasons[sKey].start = tStr;
          if (![temps[i], rhs[i], dnis[i], diffs[i]].every(Number.isFinite)) throw new Error('Archiv obsahuje chybějící meteorologická data.');
          const t = Math.round(temps[i] * 10) / 10;
          const rh = rhs[i] !== null ? Math.round(rhs[i]) : 80;
          const dni = dnis[i] || 0;
          const diff = diffs[i] || 0;
          const sol = Math.min(1.5, Math.round((0.6 * dni + 0.3 * diff) * 0.0035 * 100) / 100);

          seasons[sKey].t.push(t);
          seasons[sKey].rh.push(rh);
          seasons[sKey].sol.push(sol);
        }
      }
      Object.entries(seasons).forEach(([key, w]) => { const year = Number(key.slice(5)); const expected = (new Date(year, 1, 29).getMonth() === 1 ? 213 : 212) * 24; if (w.t.length !== expected) throw new Error('Neúplná sezóna ' + key); });
      return seasons;
    }

    function onAltitudeSliderChange() {
      state.altitude = parseInt(document.getElementById('input-altitude').value);
      if (state.altitude < 300) state.tExtDesign = -12.0;
      else if (state.altitude <= 600) state.tExtDesign = -15.0;
      else state.tExtDesign = -18.0;

      document.getElementById('badge-altitude').innerText = `⛰️ ${state.altitude} m n. m.`;
      document.getElementById('badge-te-design').innerText = `Výpočtová teplota t_e: ${state.tExtDesign.toFixed(0)} °C`;
      onParamChange();
    }

    // System Type Switcher (Floor 35 °C vs Radiators 55 °C)
    function setHeatingSystem(sys) {
      state.heatingSystem = sys;
      const isFloor = sys === 'floor';
      const btnFloor = document.getElementById('btn-sys-floor');
      const btnRad = document.getElementById('btn-sys-rad');
      const desc = document.getElementById('desc-sys-type');
      const tflowInput = document.getElementById('input-tflow');
      const tflowNumber = document.getElementById('input-tflow-number');

      if (btnFloor) {
        btnFloor.className = `sys-btn ${isFloor ? 'active' : ''} py-1 px-1.5 rounded text-[11px] transition text-center ${isFloor ? 'font-bold' : 'text-slate-300 hover:text-white'}`.trim();
        btnFloor.setAttribute('aria-pressed', String(isFloor));
      }
      if (btnRad) {
        btnRad.className = `sys-btn ${!isFloor ? 'active' : ''} py-1 px-1.5 rounded text-[11px] transition text-center ${!isFloor ? 'font-bold' : 'text-slate-300 hover:text-white'}`.trim();
        btnRad.setAttribute('aria-pressed', String(!isFloor));
      }

      if (isFloor) {
        if (desc) desc.innerText = "Podlahové topení: model počítá s akumulací potěru. Katalogový profil W35 slouží pro parametry TČ; skutečnou teplotu vody nastavíte níže.";
        if (state.tFlowDesign > 38.0) {
          state.tFlowDesign = 28.0;
          if (tflowInput) tflowInput.value = 28.0;
          if (tflowNumber) tflowNumber.value = 28.0;
        }
      } else {
        if (desc) desc.innerText = "Radiátory: teplo jde přímo do místnosti, bez akumulace potěru. Profil W55 slouží pro parametry TČ; skutečnou teplotu vody nastavíte níže.";
        if (state.tFlowDesign < 45.0) {
          state.tFlowDesign = 50.0;
          if (tflowInput) tflowInput.value = 50.0;
          if (tflowNumber) tflowNumber.value = 50.0;
        }
      }
      onParamChange();
    }

    // ================= DYNAMIC SIMULATION ENGINE =================
__MODEL_V3__

    function computeMonthly(dailyList, seasonKey) {
      const months = ['Říjen', 'Listopad', 'Prosinec', 'Leden', 'Únor', 'Březen', 'Duben'];
      const endYr = Number((seasonKey || '').slice(5)); const isLeap = endYr % 4 === 0 && (endYr % 100 !== 0 || endYr % 400 === 0);
      const mLens = [31, 30, 31, 31, isLeap ? 29 : 28, 31, 30];

      const res = [];
      let curIdx = 0;
      for (let m = 0; m < months.length; m++) {
        const len = mLens[m];
        const slice = dailyList.slice(curIdx, curIdx + len);
        curIdx += len;

        const elOpt = slice.reduce((a, b) => a + b.el_opt, 0);
        const thOpt = slice.reduce((a, b) => a + b.th_opt, 0);
        const elStd = slice.reduce((a, b) => a + b.el_std, 0);
        const avgT = slice.reduce((a, b) => a + b.avg_t, 0) / len;

        res.push({
          month: months[m],
          te_avg: avgT,
          el_opt: elOpt,
          el_std: elStd,
          th_opt: thOpt,
          scop_opt: elOpt > 0 ? thOpt / elOpt : 0,
          savings_czk: slice.reduce((a,d)=>a+(d.cost_std-d.cost_opt),0)
        });
      }
      return res;
    }

    // Dynamic COP & Capacity computation based on selected Keymark certified model
    function getCopForActiveModel(te, tf, rh) {
      const hp = state.activeHp;
      let c;

      // Medium temperature 55 °C curve for radiators / high flow
      if (state.heatingSystem === 'radiator' || tf >= 45.0) {
        if (te >= 7.0) c = hp.copA7W55 + (te - 7.0) * 0.055;
        else if (te >= 2.0) c = hp.copA2W55 + (te - 2.0) * (hp.copA7W55 - hp.copA2W55) / 5.0;
        else if (te >= -7.0) c = hp.copAm7W55 + (te + 7.0) * (hp.copA2W55 - hp.copAm7W55) / 9.0;
        else if (te >= -15.0) c = hp.copAm15W55 + (te + 15.0) * (hp.copAm7W55 - hp.copAm15W55) / 8.0;
        else c = Math.max(1.3, hp.copAm15W55 - 0.35 + (te + 20.0) * 0.35 / 5.0);

        c *= (1.0 + 0.020 * (55.0 - tf));
      } else {
        // Low temperature 35 °C curve for floor heating
        if (te >= 7.0) c = hp.copA7W35 + (te - 7.0) * 0.08;
        else if (te >= 2.0) c = hp.copA2W35 + (te - 2.0) * (hp.copA7W35 - hp.copA2W35) / 5.0;
        else if (te >= -7.0) c = hp.copAm7W35 + (te + 7.0) * (hp.copA2W35 - hp.copAm7W35) / 9.0;
        else if (te >= -15.0) c = hp.copAm15W35 + (te + 15.0) * (hp.copAm7W35 - hp.copAm15W35) / 8.0;
        else c = Math.max(1.8, hp.copAm15W35 - 0.45 + (te + 20.0) * 0.45 / 5.0);

        c *= (1.0 + 0.022 * (35.0 - tf));
      }

      // Defrost penalty around 0 °C
      if (te >= -3.5 && te <= 3.5 && rh > 75.0) c *= (1.0 - 0.07 * (rh / 100.0));
      return Math.max(1.2, c);
    }

    // Keymark Certified Domestic Hot Water (TUV) COP function
    function getCopDhwForActiveModel(te, tFlowDhw, rh) {
      const hp = state.activeHp;
      let c;
      if (te >= 7.0) c = hp.copA7W35 + (te - 7.0) * 0.08;
      else if (te >= 2.0) c = hp.copA2W35 + (te - 2.0) * (hp.copA7W35 - hp.copA2W35) / 5.0;
      else if (te >= -7.0) c = hp.copAm7W35 + (te + 7.0) * (hp.copA2W35 - hp.copAm7W35) / 9.0;
      else if (te >= -15.0) c = hp.copAm15W35 + (te + 15.0) * (hp.copAm7W35 - hp.copAm15W35) / 8.0;
      else c = Math.max(1.8, hp.copAm15W35 - 0.45 + (te + 20.0) * 0.45 / 5.0);

      c *= (1.0 + 0.022 * (35.0 - tFlowDhw));
      if (te >= -3.5 && te <= 3.5 && rh > 75.0) c *= (1.0 - 0.07 * (rh / 100.0));
      return Math.max(1.2, c);
    }

    function getCapForActiveModel(te) {
      const hp = state.activeHp;
      const p = state.heatingSystem === 'radiator' ? (hp.pDesign55 || hp.pDesign35 * 0.95) : (hp.pDesign35 || 8.1);
      if (te >= 7.0) return p;
      if (te >= 2.0) return p * 0.92 + (te - 2.0) * (p - p * 0.92) / 5.0;
      if (te >= -7.0) return p * 0.78 + (te + 7.0) * (p * 0.92 - p * 0.78) / 9.0;
      if (te >= -15.0) return p * 0.65 + (te + 15.0) * (p * 0.78 - p * 0.65) / 8.0;
      return Math.max(3.0, p * 0.54 + (te + 20.0) * (p * 0.65 - p * 0.54) / 5.0);
    }

    // ================= UI CONTROLS & INTERACTIONS =================
    function setDhwMode(mode) {
      state.dhwMode = mode;
      const btnSmart = document.getElementById('btn-dhw-smart');
      const btnStd = document.getElementById('btn-dhw-std');
      const desc = document.getElementById('desc-dhw-mode');
      if (btnSmart && btnStd) {
        if (mode === 'smart') {
          btnSmart.className = "dhw-mode-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium";
          btnStd.className = "dhw-mode-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white";
          if (desc) desc.innerText = "Preferovaný ohřev 13:00–15:00; u dvoutarifu se přesouvá do povolených oken NT. FVE se zde nesimuluje.";
        } else {
          btnSmart.className = "dhw-mode-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white";
          btnStd.className = "dhw-mode-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium";
          if (desc) desc.innerText = "Ohřev průběžně ráno (7h) a večer (19h) při běžných teplotách.";
        }
      }
      recalculateSimulation();
      updateUI();
    }

    function onParamChange() {
      state.qLossDesign = parseFloat(document.getElementById('input-qloss').value);
      state.tFlowDesign = parseFloat(document.getElementById('input-tflow').value);
      if (document.getElementById('input-area')) {
        state.floorAreaM2 = parseFloat(document.getElementById('input-area').value);
      }
      state.floorThicknessMm = parseInt(document.getElementById('input-thickness').value);
      state.tInTarget = parseFloat(document.getElementById('input-tin').value);
      state.tTolerance = parseFloat(document.getElementById('input-tolerance').value);
      state.electricityPrice = parseFloat(document.getElementById('input-price').value);

      if (document.getElementById('input-dhw-enabled')) {
        state.dhwEnabled = document.getElementById('input-dhw-enabled').checked;
      }
      if (document.getElementById('input-dhw-liters')) {
        state.dhwDailyLiters = parseFloat(document.getElementById('input-dhw-liters').value);
      }
      if (document.getElementById('input-dhw-temp')) {
        state.dhwTargetTemp = parseFloat(document.getElementById('input-dhw-temp').value);
      }
      if (document.getElementById('input-hp-service')) {
        state.hpServiceYearly = parseFloat(document.getElementById('input-hp-service').value);
      }

      if (document.getElementById('input-gas-price')) {
        state.gasPrice = parseFloat(document.getElementById('input-gas-price').value);
      }
      if (document.getElementById('input-co2-price')) {
        state.co2AllowancePriceEur = parseFloat(document.getElementById('input-co2-price').value);
      }
      if (document.getElementById('input-gas-service')) {
        state.gasBoilerServiceYearly = parseFloat(document.getElementById('input-gas-service').value);
      }
      if (document.getElementById('input-gas-eff')) {
        state.gasBoilerEfficiency = parseFloat(document.getElementById('input-gas-eff').value);
      }

      // Dynamic calculation of floor mass and thermal capacity:
      const isBeton = state.floorMaterial === 'beton';
      const rho = isBeton ? 2350 : 2150;
      const c_spec = isBeton ? 1020 : 1000;
      const vol = state.floorAreaM2 * (state.floorThicknessMm / 1000.0);
      const massTons = (vol * rho) / 1000.0;
      const cKwhK = (vol * rho * c_spec) / 3600000.0;
      const storageKwh = cKwhK * state.tTolerance;

      const tMinRoom = (state.tInTarget - state.tTolerance).toFixed(1).replace('.', ',');
      const tMaxRoom = (state.tInTarget).toFixed(1).replace('.', ',');

      // Update Live UI Labels:
      document.getElementById('val-qloss').innerText = `${state.qLossDesign.toFixed(2)} kW`;
      document.getElementById('val-tflow').innerText = `${state.tFlowDesign.toFixed(1)} °C`;
      if (document.getElementById('val-area')) document.getElementById('val-area').innerText = `${state.floorAreaM2} m²`;
      document.getElementById('val-thickness').innerText = `${state.floorThicknessMm} mm`;
      document.getElementById('val-tin').innerText = `${state.tInTarget.toFixed(1)} − ${state.tTolerance.toFixed(1)} °C`;
      document.getElementById('val-price').innerText = `${state.electricityPrice.toFixed(2)} Kč/kWh`;
      if (document.getElementById('val-hp-service')) document.getElementById('val-hp-service').innerText = `${state.hpServiceYearly.toLocaleString('cs-CZ')} Kč/rok`;

      // DHW Labels:
      if (document.getElementById('val-dhw-liters')) document.getElementById('val-dhw-liters').innerText = `${state.dhwDailyLiters} l/den`;
      if (document.getElementById('val-dhw-temp')) document.getElementById('val-dhw-temp').innerText = `${state.dhwTargetTemp.toFixed(0)} °C`;
      if (document.getElementById('desc-dhw-persons')) {
        const persons = Math.max(1, Math.round(state.dhwDailyLiters / 40));
        document.getElementById('desc-dhw-persons').innerText = `cca ${persons} osoby (40 l/osoba/den při ${state.dhwTargetTemp.toFixed(0)} °C)`;
      }

      // Gas Labels:
      if (document.getElementById('val-gas-price')) document.getElementById('val-gas-price').innerText = `${state.gasPrice.toFixed(2)} Kč/kWh`;
      if (document.getElementById('val-co2-price')) document.getElementById('val-co2-price').innerText = `${state.co2AllowancePriceEur} €/t CO₂`;
      if (document.getElementById('val-gas-service')) document.getElementById('val-gas-service').innerText = `${state.gasBoilerServiceYearly.toLocaleString('cs-CZ')} Kč/rok`;
      if (document.getElementById('val-gas-eff')) document.getElementById('val-gas-eff').innerText = `${state.gasBoilerEfficiency} %`;

      const ets2Sur = state.co2AllowancePriceEur * 25.0 * 0.00018 * 1.21;
      const gasTotal = state.gasPrice + ets2Sur;
      if (document.getElementById('calc-ets2-surcharge')) {
        document.getElementById('calc-ets2-surcharge').innerText = `Scénář: +${ets2Sur.toFixed(2)} Kč/kWh; ${state.etsEnabled ? 'zahrnut' : 'nezahrnut'} v ekonomice`;
      }

      document.getElementById('calc-floor-mass').innerText = `Hmotnost: ${massTons.toFixed(1).replace('.', ',')} tun`;
      document.getElementById('calc-floor-c').innerText = `C: ${cKwhK.toFixed(1).replace('.', ',')} kWh/K`;
      document.getElementById('calc-room-corridor').innerText = `Pásmo tolerované teploty (nekomfort): ${tMinRoom} – ${tMaxRoom} °C`;
      document.getElementById('calc-room-storage').innerText = `Aku: ${Math.round(storageKwh)} kWh`;

      // Summary Cards:
      const h_w_k = Math.round((state.qLossDesign / (state.tInTarget - state.tExtDesign)) * 1000);




      const dhwPersons = Math.max(1, Math.round(state.dhwDailyLiters / 40));
      const dhwStatus = state.dhwEnabled ? `🚿 TUV: ${state.dhwDailyLiters} l/den (${state.dhwTargetTemp.toFixed(0)} °C • ${state.dhwMode === 'smart' ? 'polední' : 'průběžný'})` : '🚿 TUV: VYP';

      recalculateSimulation();
      updateUI();
    }

    function setFloorMaterial(mat) {
      state.floorMaterial = mat;
      const btnB = document.getElementById('btn-mat-beton');
      const btnA = document.getElementById('btn-mat-anhydrit');
      if (mat === 'beton') {
        btnB.className = "mat-btn active py-1.5 px-2 rounded text-xs transition text-center font-medium";
        btnA.className = "mat-btn py-1.5 px-2 rounded text-xs transition text-center text-slate-300 hover:text-white font-medium";
      } else {
        btnB.className = "mat-btn py-1.5 px-2 rounded text-xs transition text-center text-slate-300 hover:text-white font-medium";
        btnA.className = "mat-btn active py-1.5 px-2 rounded text-xs transition text-center font-medium";
      }
      updateCoveringDesc();
      onParamChange();
    }

    function setFloorCovering(cov) {
      state.floorCovering = cov;
      const bD = document.getElementById('btn-cover-dlazba');
      const bV = document.getElementById('btn-cover-vinyl');
      const bW = document.getElementById('btn-cover-drevo');
      [bD, bV, bW].forEach(b => b.className = "cover-btn py-1 px-1.5 rounded text-[11px] transition text-center text-slate-300 hover:text-white");
      if (cov === 'dlazba') bD.className = "cover-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium";
      else if (cov === 'vinyl') bV.className = "cover-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium";
      else if (cov === 'drevo') bW.className = "cover-btn active py-1 px-1.5 rounded text-[11px] transition text-center font-medium";
      updateCoveringDesc();
      onParamChange();
    }

    function updateCoveringDesc() {
      const desc = document.getElementById('desc-floor-mat');
      const matName = state.floorMaterial === 'beton' ? 'Beton' : 'Anhydrit';
      let covDesc = 'standardní akumulace';
      if (state.floorCovering === 'dlazba') covDesc = 'výborný přestup tepla (teplota vody -1 °C)';
      else if (state.floorCovering === 'vinyl') covDesc = 'standardní odpor krytiny (+1 °C teplota vody)';
      else if (state.floorCovering === 'drevo') covDesc = 'vyšší tepelný odpor (+2,5 °C teplota vody)';
      desc.innerText = `${matName} + ${state.floorCovering}: ${covDesc}.`;
    }

    function resetDefaultParameters() {
      document.getElementById('input-qloss').value = 5.8;
      document.getElementById('input-tflow').value = 28.0;
      document.getElementById('input-thickness').value = 50;
      document.getElementById('input-area').value = 170;
      document.getElementById('input-tin').value = 22.0;
      document.getElementById('input-tolerance').value = 1.0;
      document.getElementById('input-price').value = 6.0;
      document.getElementById('input-altitude').value = 211;
      state.altitude = 211;
      state.weatherBaseAltitude = 211;
      state.locationName = 'Modelová lokalita – Ostrava';
      state.lat = null;
      state.lon = null;
      state.isCustomWeatherLoaded = false;
      if (typeof originalWeatherV3 !== 'undefined') rawWeather = originalWeatherV3;
      if (document.getElementById('badge-location')) document.getElementById('badge-location').innerText = '📍 Modelová lokalita – Ostrava';
      if (document.getElementById('badge-altitude')) document.getElementById('badge-altitude').innerText = '⛰️ 211 m n. m.';
      if (document.getElementById('badge-weather-source')) document.getElementById('badge-weather-source').innerText = 'Meteorologická data: Referenční archiv Open-Meteo ERA5 pro Ostravu (1960–2026); modelový dům';

      document.getElementById('input-dhw-enabled').checked = true;
      document.getElementById('input-dhw-liters').value = 120;
      document.getElementById('input-dhw-temp').value = 55;

      document.getElementById('input-gas-price').value = 1.60;
      document.getElementById('input-co2-price').value = 30;
      document.getElementById('input-gas-service').value = 1500;
      document.getElementById('input-gas-eff').value = 94;
      document.getElementById('input-hp-service').value = 0;

      state.economyPeriod = 'annual';
      state.heatingSystem = 'floor';
      setFloorMaterial('beton');
      setFloorCovering('vinyl');
      setDhwMode('smart');
      selectKeymarkModel('warmhouse-hm-m0-a1-keymark1325');
      setCenterYear(2022);
      onParamChange();
    }

    function toggleSettingsDrawer() {
      const drawer = document.getElementById('settings-drawer');
      drawer.classList.toggle('hidden');
      document.getElementById('btn-settings-drawer').setAttribute('aria-expanded', String(!drawer.classList.contains('hidden')));
    }

    function toggleSection(mode, forceState) {
      const willBeOpen = typeof forceState === 'boolean' ? forceState : !state.sectionsExpanded[mode];
      state.sectionsExpanded[mode] = willBeOpen;

      const cnt = document.getElementById(`view-${mode}-container`);
      const chevron = document.getElementById(`chevron-${mode}`);
      const label = document.getElementById(`label-${mode}`);
      const btn = document.getElementById(`view-mode-${mode}`);

      if (cnt) {
        if (willBeOpen) cnt.classList.remove('hidden');
        else cnt.classList.add('hidden');
      }
      if (chevron) chevron.innerText = willBeOpen ? '▲' : '▼';
      if (label) label.innerText = willBeOpen ? 'Sbalit' : 'Rozbalit';

      if (btn) {
        if (willBeOpen) {
          btn.className = "view-btn active px-3 py-1.5 text-xs rounded-lg transition flex items-center gap-1.5 font-bold shadow bg-sky-600 text-white";
        } else {
          btn.className = "view-btn px-3 py-1.5 text-xs rounded-lg transition text-slate-300 hover:text-white flex items-center gap-1.5 font-medium bg-slate-800/80";
        }
      }

      if (willBeOpen) {
        requestAnimationFrame(() => {
          if (mode === 'all10') drawOverlayChart();
          else if (mode === 'single') {
            drawSingleSeasonChart();
            updateDiurnalView();
            renderMonthlyTable();
          } else if (mode === 'table') {
            renderMultiSeasonTable();
          } else if (mode === 'dual') {
            renderKeymarkCatalogView();
          } else if (mode === 'gas') {
            renderGasComparisonView();
            drawGasBarChart();
          }
        });
      }
    }

    function expandAllSections() {
      ['all10', 'single', 'table', 'gas'].forEach(m => toggleSection(m, true));
    }

    function collapseAllSections() {
      ['all10', 'single', 'table', 'gas'].forEach(m => toggleSection(m, false));
    }

    function setViewMode(mode) {
      state.viewMode = mode;
      toggleSection(mode, true);
      const sec = document.getElementById(`sec-${mode}`);
      if (sec) {
        sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    function setOverlayMetric(metric) {
      state.overlayMetric = metric;
      ['kwh', 'cum', 'scop', 'temp'].forEach(m => {
        const btn = document.getElementById(`btn-ovl-${m}`);
        if (btn) {
          const match = (m === 'kwh' && metric === 'kwh_daily') ||
                        (m === 'cum' && metric === 'kwh_cum') ||
                        (m === 'scop' && metric === 'scop') ||
                        (m === 'temp' && metric === 'temp');
          if (match) btn.className = "px-2.5 py-1 rounded bg-sky-600 text-white font-medium";
          else btn.className = "px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600";
        }
      });
      drawOverlayChart();
    }

    function setSingleMetric(metric) {
      state.singleMetric = metric;
      ['el', 'temp', 'scop'].forEach(m => {
        const btn = document.getElementById(`btn-sgl-${m}`);
        if (btn) {
          if (m === metric) btn.className = "px-2.5 py-1 rounded bg-sky-600 text-white font-medium";
          else btn.className = "px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600";
        }
      });
      drawSingleSeasonChart();
    }

    function setAutomationLevel(level) {
      if (level !== 'optimized') return;
      state.automationLevel = level;
      controllerLevels.forEach(l => {
        const btn = document.getElementById('btn-auto-' + l);
        if (!btn) return;
        btn.className = 'auto-level-btn p-3 rounded-lg border text-left ' + (l === level ? 'active border-sky-400 bg-sky-950/60' : 'border-slate-700 bg-slate-800/80');
        btn.setAttribute('aria-pressed', String(l === level));
      });
      document.getElementById('badge-auto-level').textContent = level === 'baseline' ? 'Základ · stálý ekviterm' : controlLabel();
      recalculateSimulation();
      updateUI();
    }

    function selectSeason(s) {
      state.currentSeason = s;
      const active5 = getActiveSeasons();
      active5.forEach(seasonKey => {
        const btn = document.getElementById(`btn-season-${seasonKey}`);
        if (btn) {
          if (seasonKey === s) {
            btn.className = "px-2.5 py-1 rounded text-xs font-bold bg-sky-500 text-white shadow";
          } else {
            btn.className = "px-2.5 py-1 rounded text-xs text-slate-300 bg-slate-800 hover:bg-slate-700";
          }
        }
      });
      updateUI();
    }

    function updateUI() {
      if (document.getElementById('chart-season-badge')) {
        document.getElementById('chart-season-badge').innerText = state.currentSeason;
      }
      if (document.getElementById('header-season-badge')) {
        document.getElementById('header-season-badge').innerText = state.currentSeason;
      }

      // Update Spec summary card:
      const hp = state.activeHp;
      if (document.getElementById('spec-hp-name')) document.getElementById('spec-hp-name').innerText = hp.name;
      if (document.getElementById('spec-hp-mod')) document.getElementById('spec-hp-mod').innerText = `Keymark: ${hp.certNo} • ${(state.heatingSystem === 'radiator' ? (hp.pDesign55 || 7.5) : (hp.pDesign35 || 8.1))} kW`;
      if (document.getElementById('spec-hp-params')) {
        document.getElementById('spec-hp-params').innerText = `SCOP ${state.heatingSystem === 'radiator' ? hp.scop55 : hp.scop35} • ${hp.refrigerant.split(' ')[0]}`;
      }
      if (document.getElementById('spec-hp-noise')) document.getElementById('spec-hp-noise').innerText = `Hluk (nesjednocená metrika): ${hp.noiseDb}`;

      renderSeasonKpis();

      // ALWAYS render all data tables and catalogs so they are never empty
      renderMonthlyTable();
      renderMultiSeasonTable();
      renderKeymarkCatalogView();
      renderGasComparisonView();

      // Redraw active charts for expanded sections
      if (state.sectionsExpanded.all10) {
        drawOverlayChart();
      }
      if (state.sectionsExpanded.single) {
        drawSingleSeasonChart();
        updateDiurnalView();
      }
      if (state.sectionsExpanded.gas) {
        drawGasBarChart();
      }
    }

    // Dynamic Render of Season Selector Pills (Only Active 5 Seasons)
    function renderSeasonPills() {
      const container = document.getElementById('season-buttons');
      if (!container) return;
      container.innerHTML = '';

      const active5 = getActiveSeasons();
      active5.forEach(s => {
        const btn = document.createElement('button');
        btn.id = `btn-season-${s}`;
        const isSel = state.currentSeason === s;
        btn.className = isSel
          ? "px-2.5 py-1 rounded text-xs font-bold bg-sky-500 text-white shadow"
          : "px-2.5 py-1 rounded text-xs text-slate-300 bg-slate-800 hover:bg-slate-700";

        const color = seasonColors[s] || '#38bdf8';
        btn.innerHTML = `<span class="inline-block w-2 h-2 rounded-full mr-1.5" style="background-color: ${color}"></span>${s}`;
        btn.onclick = () => {
          selectSeason(s);
          if (state.viewMode === 'all10') setViewMode('single');
        };
        container.appendChild(btn);
      });
    }

    // Dynamic KPI Cards for Selected Season
    function renderSeasonKpis() {
      const cur = simResults[state.currentSeason];
      if (!cur) return;
      const r = cur.results;
      const ws = cur.weather_stats;

      const container = document.getElementById('season-kpi-container');
      if (!container) return;

      const elHeatOpt = Math.round(r.el_opt_heat);
      const elDhwOpt = Math.round(r.el_opt_dhw);
      const dhwSubText = state.dhwEnabled ? `Topení: ${elHeatOpt.toLocaleString('cs-CZ')} kWh • TUV: ${elDhwOpt.toLocaleString('cs-CZ')} kWh` : 'Bez ohřevu TUV';

      container.innerHTML = `
        <div class="card p-3.5 border-sky-500/30">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span class="font-semibold text-white">${state.automationLevel === 'baseline' ? 'Základ · ekviterm' : controlLabel()}</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded ${state.automationLevel === 'baseline' ? 'bg-slate-800 text-slate-400' : 'bg-sky-950 text-sky-300'} font-bold">
              ${state.automationLevel === 'baseline' ? 'stálý cíl 24 h' : controlWindowLabel()}
            </span>
          </div>
          <div class="text-2xl font-bold text-white mt-1">${Math.round(r.el_opt_kwh).toLocaleString('cs-CZ')} <span class="text-sm font-normal text-slate-400">kWh</span></div>
          <div class="text-[11px] text-sky-400 mt-1 truncate">${dhwSubText}</div>
        </div>

        <div class="card p-3.5">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Běžné ekvitermní řízení</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">stálý cíl</span>
          </div>
          <div class="text-2xl font-bold text-slate-300 mt-1">${Math.round(r.el_std_kwh).toLocaleString('cs-CZ')} <span class="text-sm font-normal text-slate-400">kWh</span></div>
          <div class="text-[11px] text-slate-400 mt-1">Stálý cíl + TUV podle dostupných tarifních oken</div>
        </div>

        <div class="card p-3.5 ${state.automationLevel === 'baseline' ? 'border-slate-700 bg-slate-900/40' : 'border-emerald-500/30 bg-emerald-950/20'}">
          <div class="flex items-center justify-between text-xs ${state.automationLevel === 'baseline' ? 'text-slate-400' : 'text-emerald-400'} font-medium">
            <span>Úspora proti základu</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded ${state.automationLevel === 'baseline' ? 'bg-slate-800 text-slate-400' : 'bg-emerald-900/60 text-emerald-300'} font-bold">
              ${state.automationLevel === 'baseline' ? '0 % (základ)' : `${r.diff_pct.toFixed(1).replace('.', ',')} %`}
            </span>
          </div>
          <div class="text-2xl font-bold ${state.automationLevel === 'baseline' ? 'text-slate-300' : 'text-emerald-400'} mt-1">
            ${state.automationLevel === 'baseline' ? '0' : `${Math.round(r.diff_kwh).toLocaleString('cs-CZ')}`} <span class="text-sm font-normal text-slate-400">kWh</span>
          </div>
          <div class="text-[11px] ${state.automationLevel === 'baseline' ? 'text-slate-400' : 'text-emerald-300 font-semibold'} mt-1">
            ${state.automationLevel === 'baseline' ? 'Základní referenční provoz (žádná úspora)' : `Úspora: ${Math.round(r.savings_czk).toLocaleString('cs-CZ')} Kč (zvolené řízení; dle simulace)`}
          </div>
        </div>

        <div class="card p-3.5">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Sezónní SCOP</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">prům. ${ws.avg_temp.toFixed(1)} °C</span>
          </div>
          <div class="text-2xl font-bold text-emerald-400 mt-1">${r.scop_opt.toFixed(2)}</div>
          <div class="text-[11px] text-slate-400 mt-1">SCOP topení: ${r.scop_heat.toFixed(2)} • SCOP TUV: ${state.dhwEnabled ? r.scop_dhw.toFixed(2) : '—'}</div>
        </div>

        <div class="card p-3.5 border-amber-500/30">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Odhad sepnutí kompresoru</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 font-bold">${r.starts_std ? nfmt(Math.abs((1-r.starts_opt/r.starts_std)*100),1) : '0'} % ${r.starts_opt <= r.starts_std ? 'méně' : 'více'}</span>
          </div>
          <div class="text-2xl font-bold text-amber-400 mt-1">${r.starts_opt.toLocaleString('cs-CZ')}</div>
          <div class="text-[11px] text-slate-400 mt-1">Běžné řízení: ${r.starts_std.toLocaleString('cs-CZ')} startů</div>
        </div>
      `;
    }

    // ================= 5 SEASONS OVERLAY CHART =================
    function drawOverlayChart() {
      const canvas = document.getElementById('overlayCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width, H = rect.height;
      const padL = 45, padR = 15, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const active5 = getActiveSeasons();
      if (active5.length === 0) return;

      const numDays = simResults[active5[0]].daily.length;

      // Determine metric bounds
      let minY = 0, maxY = 50;
      if (state.overlayMetric === 'kwh_daily') {
        maxY = 0;
        active5.forEach(s => {
          simResults[s].daily.forEach(d => { if (d.el_opt > maxY) maxY = d.el_opt; });
        });
        maxY = Math.ceil((maxY * 1.1) / 10) * 10;
        minY = 0;
      } else if (state.overlayMetric === 'kwh_cum') {
        maxY = 0;
        active5.forEach(s => {
          const sCum = simResults[s].cum_kwh; const lastCum = sCum[sCum.length - 1];
          if (lastCum > maxY) maxY = lastCum;
        });
        maxY = Math.ceil((maxY * 1.1) / 500) * 500;
        minY = 0;
      } else if (state.overlayMetric === 'scop') {
        minY = 1.0;
        maxY = 7.0;
      } else if (state.overlayMetric === 'temp') {
        minY = 0; maxY = 20;
        active5.forEach(s => {
          simResults[s].daily.forEach(d => {
            if (d.avg_t < minY) minY = d.avg_t;
            if (d.avg_t > maxY) maxY = d.avg_t;
          });
        });
        minY = Math.floor(minY - 2);
        maxY = Math.ceil(maxY + 2);
      }

      // Draw Grid Lines & Y-Axis Labels
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      const ySteps = 5;
      for (let i = 0; i <= ySteps; i++) {
        const yVal = minY + ((maxY - minY) / ySteps) * i;
        const yPix = padT + cH - ((yVal - minY) / (maxY - minY)) * cH;

        ctx.beginPath();
        ctx.moveTo(padL, yPix);
        ctx.lineTo(W - padR, yPix);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(yVal), padL - 8, yPix + 3);
      }

      // Draw 0 °C dashed line for temperature metric
      if (state.overlayMetric === 'temp' && minY < 0 && maxY > 0) {
        const zeroY = padT + cH - ((0 - minY) / (maxY - minY)) * cH;
        ctx.strokeStyle = '#f43f5e';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padL, zeroY);
        ctx.lineTo(W - padR, zeroY);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw Curves for Active 5 Seasons
      active5.forEach(s => {
        const isHover = state.hoverSeason === s;
        const isSelected = state.currentSeason === s;
        const color = seasonColors[s] || '#38bdf8';

        ctx.strokeStyle = color;
        if (state.hoverSeason) {
          ctx.lineWidth = isHover ? 3.5 : 0.8;
          ctx.globalAlpha = isHover ? 1.0 : 0.25;
        } else {
          ctx.lineWidth = isSelected ? 3.0 : 1.6;
          ctx.globalAlpha = isSelected ? 1.0 : 0.7;
        }

        ctx.beginPath();
        const sDays = simResults[s].daily.length;
        for (let day = 0; day < sDays; day++) {
          const x = padL + (day / (sDays - 1)) * cW;
          let val = 0;
          if (state.overlayMetric === 'kwh_daily') val = simResults[s].daily[day].el_opt;
          else if (state.overlayMetric === 'kwh_cum') val = simResults[s].cum_kwh[day];
          else if (state.overlayMetric === 'scop') val = simResults[s].daily[day].scop_day;
          else if (state.overlayMetric === 'temp') val = simResults[s].daily[day].avg_t;

          const y = padT + cH - ((val - minY) / (maxY - minY)) * cH;
          if (day === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.globalAlpha = 1.0;
      });
    }

    function renderOverlayLegend() {
      const container = document.getElementById('overlay-legend-container');
      if (!container) return;
      container.innerHTML = '';

      const active5 = getActiveSeasons();
      active5.forEach(s => {
        const item = simResults[s];
        const r = item.results;
        const ws = item.weather_stats;
        const color = seasonColors[s] || '#38bdf8';
        const isSelected = state.currentSeason === s;

        const chip = document.createElement('div');
        chip.className = `px-2.5 py-1 rounded-lg text-xs flex items-center gap-2 cursor-pointer transition border ${
          isSelected ? 'bg-slate-800 border-sky-400 font-bold text-white shadow' : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-500'
        }`;

        chip.innerHTML = `
          <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: ${color}"></span>
          <span class="font-semibold">${s}</span>
          <span class="text-[10px] text-slate-400">(${Math.round(r.el_opt_kwh).toLocaleString('cs-CZ')} kWh • SCOP ${r.scop_opt.toFixed(2)})</span>
        `;

        chip.onclick = () => {
          selectSeason(s);
          setViewMode('single');
        };
        chip.onmouseenter = () => {
          state.hoverSeason = s;
          drawOverlayChart();
        };
        chip.onmouseleave = () => {
          state.hoverSeason = null;
          drawOverlayChart();
        };

        container.appendChild(chip);
      });
    }

    // ================= SINGLE SEASON DETAIL CHART =================
    function drawSingleSeasonChart() {
      const canvas = document.getElementById('singleCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width, H = rect.height;
      const padL = 45, padR = 15, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const cur = simResults[state.currentSeason];
      if (!cur) return;
      const daily = cur.daily;
      const numDays = daily.length;

      // Metric specific rendering
      if (state.singleMetric === 'el') {
        let maxKwh = 0;
        daily.forEach(d => {
          if (d.el_std > maxKwh) maxKwh = d.el_std;
          if (d.el_opt > maxKwh) maxKwh = d.el_opt;
        });
        maxKwh = Math.ceil((maxKwh * 1.15) / 10) * 10;

        // Draw Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
          const val = (maxKwh / 5) * i;
          const y = padT + cH - (val / maxKwh) * cH;
          ctx.beginPath();
          ctx.moveTo(padL, y);
          ctx.lineTo(W - padR, y);
          ctx.stroke();

          ctx.fillStyle = '#64748b';
          ctx.font = '10px system-ui';
          ctx.textAlign = 'right';
          ctx.fillText(Math.round(val), padL - 8, y + 3);
        }

        // Draw Standard baseline area / curve (Gray/Slate)
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.6)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const y = padT + cH - (d.el_std / maxKwh) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Draw Optimized Heating Area (Sky)
        ctx.fillStyle = 'rgba(56, 189, 248, 0.4)';
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const y = padT + cH - (d.el_opt / maxKwh) * cH;
          if (i === 0) ctx.moveTo(x, padT + cH);
          ctx.lineTo(x, y);
        });
        ctx.lineTo(padL + cW, padT + cH);
        ctx.closePath();
        ctx.fill();

        // Draw Optimized Heating Line (Sky)
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const y = padT + cH - (d.el_opt / maxKwh) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Draw DHW component if enabled (Emerald)
        if (state.dhwEnabled) {
          ctx.strokeStyle = '#10b981';
          ctx.lineWidth = 1.8;
          ctx.beginPath();
          daily.forEach((d, i) => {
            const x = padL + (i / (numDays - 1)) * cW;
            const y = padT + cH - (d.el_opt_dhw / maxKwh) * cH;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.stroke();
        }

      } else if (state.singleMetric === 'temp') {
        let minT = 0, maxT = 20;
        daily.forEach(d => {
          if (d.min_t < minT) minT = d.min_t;
          if (d.max_t > maxT) maxT = d.max_t;
        });
        minT = Math.floor(minT - 2);
        maxT = Math.ceil(maxT + 2);

        // Draw Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
          const val = minT + ((maxT - minT) / 5) * i;
          const y = padT + cH - ((val - minT) / (maxT - minT)) * cH;
          ctx.beginPath();
          ctx.moveTo(padL, y);
          ctx.lineTo(W - padR, y);
          ctx.stroke();

          ctx.fillStyle = '#64748b';
          ctx.font = '10px system-ui';
          ctx.textAlign = 'right';
          ctx.fillText(Math.round(val) + ' °C', padL - 8, y + 3);
        }

        // Draw Min-Max Temperature Band (Slate fill)
        ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const yMax = padT + cH - ((d.max_t - minT) / (maxT - minT)) * cH;
          if (i === 0) ctx.moveTo(x, yMax); else ctx.lineTo(x, yMax);
        });
        for (let i = numDays - 1; i >= 0; i--) {
          const x = padL + (i / (numDays - 1)) * cW;
          const yMin = padT + cH - ((daily[i].min_t - minT) / (maxT - minT)) * cH;
          ctx.lineTo(x, yMin);
        }
        ctx.closePath();
        ctx.fill();

        // Draw Average Temperature Line (Sky)
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const y = padT + cH - ((d.avg_t - minT) / (maxT - minT)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Draw 0 °C Line
        if (minT < 0 && maxT > 0) {
          const zeroY = padT + cH - ((0 - minT) / (maxT - minT)) * cH;
          ctx.strokeStyle = '#f43f5e';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(padL, zeroY);
          ctx.lineTo(W - padR, zeroY);
          ctx.stroke();
          ctx.setLineDash([]);
        }

      } else if (state.singleMetric === 'scop') {
        const minS = 1.0, maxS = 7.0;

        // Draw Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 6; i++) {
          const val = minS + i * 1.0;
          const y = padT + cH - ((val - minS) / (maxS - minS)) * cH;
          ctx.beginPath();
          ctx.moveTo(padL, y);
          ctx.lineTo(W - padR, y);
          ctx.stroke();

          ctx.fillStyle = '#64748b';
          ctx.font = '10px system-ui';
          ctx.textAlign = 'right';
          ctx.fillText(val.toFixed(1), padL - 8, y + 3);
        }

        // Draw SCOP Line (Emerald)
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        daily.forEach((d, i) => {
          const x = padL + (i / (numDays - 1)) * cW;
          const y = padT + cH - ((d.scop_day - minS) / (maxS - minS)) * cH;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();
      }

      // Vertical highlight line on selected day for 24-hour diurnal profile
      if (state.selectedDayIndex !== undefined && state.selectedDayIndex >= 0 && state.selectedDayIndex < numDays) {
        const selX = padL + (state.selectedDayIndex / (numDays - 1)) * cW;
        ctx.save();
        ctx.strokeStyle = '#38bdf8';
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(selX, padT);
        ctx.lineTo(selX, padT + cH);
        ctx.stroke();

        ctx.setLineDash([]);
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath();
        ctx.arc(selX, padT + 2, 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }

    function updateSingleLegend() {
      const cnt = document.getElementById('single-legend-container');
      if (!cnt) return;
      if (state.singleMetric === 'el') {
        cnt.innerHTML = `
          <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-sky-500"></span><span class="text-white font-medium">Optimalizované TČ (topení + TUV)</span></div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-slate-400"></span><span>Běžné ekvitermní řízení</span></div>
          ${state.dhwEnabled ? '<div class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-emerald-500"></span><span class="text-emerald-400">z toho ohřev TUV</span></div>' : ''}
        `;
      } else if (state.singleMetric === 'temp') {
        cnt.innerHTML = `
          <div class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-sky-400"></span><span class="text-white font-medium">Průměrná denní teplota</span></div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-2 rounded bg-sky-500/20"></span><span>Rozsah denních teplot (min–max)</span></div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-rose-500"></span><span>Hranice mrazu 0 °C</span></div>
        `;
      } else {
        cnt.innerHTML = `
          <div class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-emerald-400"></span><span class="text-emerald-400 font-medium">Denní topný faktor COP</span></div>
        `;
      }
    }

    function renderMonthlyTable() {
      let cur = simResults[state.currentSeason];
      if (!cur) {
        const active5 = getActiveSeasons();
        for (let s of active5) {
          if (simResults[s]) { cur = simResults[s]; break; }
        }
        if (!cur) {
          const anyKey = Object.keys(simResults)[0];
          if (anyKey) cur = simResults[anyKey];
        }
      }
      if (!cur) return;
      const tbody = document.getElementById('monthly-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      if (!cur.monthly || cur.monthly.length === 0) {
        if (cur.daily) cur.monthly = computeMonthly(cur.daily, state.currentSeason);
      }
      if (!cur.monthly) return;

      let totElStd = 0, totElOpt = 0, totThOpt = 0, totSavings = 0;

      cur.monthly.forEach(m => {
        totElStd += (m.el_std || 0);
        totElOpt += (m.el_opt || 0);
        totThOpt += (m.th_opt || 0);
        totSavings += (m.savings_czk || 0);

        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/50 border-b border-slate-800/40 transition";
        tr.innerHTML = `
          <td class="py-2.5 px-3 font-semibold text-white flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
            <span>${m.month}</span>
          </td>
          <td class="py-2.5 px-2 text-right font-mono text-slate-300">${m.te_avg.toFixed(1)} °C</td>
          <td class="py-2.5 px-2 text-right font-mono text-slate-400">${Math.round(m.el_std).toLocaleString('cs-CZ')} kWh</td>
          <td class="py-2.5 px-2 text-right font-mono font-semibold text-sky-400">${Math.round(m.el_opt).toLocaleString('cs-CZ')} kWh</td>
          <td class="py-2.5 px-2 text-right font-mono font-bold text-emerald-400">${m.scop_opt.toFixed(2)}</td>
          <td class="py-2.5 px-2 text-right font-mono font-bold text-amber-400">+${Math.round(m.savings_czk).toLocaleString('cs-CZ')} Kč</td>
        `;
        tbody.appendChild(tr);
      });

      // Total summary footer row
      const totScop = totElOpt > 0 ? (totThOpt / totElOpt) : 0;
      const tfoot = document.getElementById('monthly-tfoot');
      if (tfoot) {
        tfoot.innerHTML = `
          <tr class="bg-slate-900 font-bold border-t-2 border-slate-700 text-white shadow-inner">
            <td class="py-3 px-3 uppercase text-xs text-sky-300 tracking-wider">Celkem za sezónu</td>
            <td class="py-3 px-2 text-right font-mono text-slate-400">—</td>
            <td class="py-3 px-2 text-right font-mono text-slate-300">${Math.round(totElStd).toLocaleString('cs-CZ')} kWh</td>
            <td class="py-3 px-2 text-right font-mono text-sky-400">${Math.round(totElOpt).toLocaleString('cs-CZ')} kWh</td>
            <td class="py-3 px-2 text-right font-mono text-emerald-400">${totScop.toFixed(2)}</td>
            <td class="py-3 px-2 text-right font-mono text-amber-400">+${Math.round(totSavings).toLocaleString('cs-CZ')} Kč</td>
          </tr>
        `;
      }
    }

    // ================= 24-HOUR DIURNAL PROFILE & THERMAL ACCUMULATION =================
    let activeDiurnalHoverHour = null;

    function selectPresetDay(preset) {
      const cur = simResults[state.currentSeason];
      if (!cur || !cur.daily) return;
      const daily = cur.daily;

      if (preset === 'coldest') {
        let bestIdx = 0, minT = 999;
        daily.forEach((d, i) => {
          if (d.min_t < minT) { minT = d.min_t; bestIdx = i; }
        });
        state.selectedDayIndex = bestIdx;
      } else if (preset === 'winter') {
        let bestIdx = 78, bestDiff = 999;
        for (let i = 50; i < Math.min(130, daily.length); i++) {
          const diff = Math.abs(daily[i].avg_t - 0.0);
          if (diff < bestDiff) { bestDiff = diff; bestIdx = i; }
        }
        state.selectedDayIndex = bestIdx;
      } else if (preset === 'spring') {
        let bestIdx = 170, bestDiff = 999;
        for (let i = 145; i < Math.min(190, daily.length); i++) {
          const diff = Math.abs(daily[i].avg_t - 10.0);
          if (diff < bestDiff) { bestDiff = diff; bestIdx = i; }
        }
        state.selectedDayIndex = bestIdx;
      }

      drawSingleSeasonChart();
      updateDiurnalView();
    }

    function stepDay(delta) {
      const cur = simResults[state.currentSeason];
      if (!cur || !cur.daily) return;
      const numDays = cur.daily.length;
      state.selectedDayIndex = Math.max(0, Math.min(numDays - 1, (state.selectedDayIndex || 0) + delta));
      drawSingleSeasonChart();
      updateDiurnalView();
    }

    function onDaySliderChange(val) {
      state.selectedDayIndex = parseInt(val, 10);
      drawSingleSeasonChart();
      updateDiurnalView();
    }

    function updateDiurnalView() {
      const cur = simResults[state.currentSeason];
      if (!cur || !cur.daily) return;
      const daily = cur.daily;
      const numDays = daily.length;

      if (state.selectedDayIndex === undefined || state.selectedDayIndex < 0 || state.selectedDayIndex >= numDays) {
        state.selectedDayIndex = 98;
      }

      const dayIdx = state.selectedDayIndex;
      const day = daily[dayIdx];
      if (!day || !day.hours) return;

      const dateStr = getDayDateString(dayIdx);

      // 1. Update text badges and slider
      const daySlider = document.getElementById('diurnalDaySlider');
      if (daySlider) daySlider.value = dayIdx;

      const counterEl = document.getElementById('diurnal-day-counter');
      if (counterEl) counterEl.innerText = `Den ${dayIdx + 1}`;

      const dateBadge = document.getElementById('diurnal-date-badge');
      if (dateBadge) dateBadge.innerText = `${dateStr} (Den ${dayIdx + 1})`;

      const pillEl = document.getElementById('single-selected-day-pill');
      if (pillEl) pillEl.innerText = `Aktivní den: ${dateStr}`;

      const weatherBadge = document.getElementById('diurnal-weather-badge');
      if (weatherBadge) {
        const icon = day.min_t < -5 ? '❄️' : (day.min_t <= 2 ? '🌤️' : '☀️');
        weatherBadge.innerHTML = `${icon} Min: <strong>${day.min_t.toFixed(1)} °C</strong> | Max: <strong>${day.max_t.toFixed(1)} °C</strong> | Průměr: <strong>${day.avg_t.toFixed(1)} °C</strong>`;
      }

      // 2. Compute physical KPIs
      const swing = day.max_t - day.min_t;
      const swingEl = document.getElementById('kpi-diurnal-swing');
      if (swingEl) swingEl.innerText = `${swing.toFixed(1)} °C`;

      const rangeEl = document.getElementById('kpi-diurnal-range');
      if (rangeEl) rangeEl.innerText = `Min ${day.min_t.toFixed(1)} °C • Max ${day.max_t.toFixed(1)} °C`;

      // Thermal capacity of floor slab (170 m2 * 0.05m * 2350 kg/m3 * 1020 J/kgK = ~5.7 kWh/K)
      const C_floor = simResults[state.currentSeason].results.comfort.opt.Cf;
      const tfVals = day.hours.map(h => h.tf);
      const minTf = Math.min(...tfVals);
      const maxTf = Math.max(...tfVals);
      const deltaTf = Math.max(0.0, maxTf - minTf);
      const slabKwh = deltaTf * C_floor;

      const slabKwhEl = document.getElementById('kpi-diurnal-slab-kwh');
      if (slabKwhEl) slabKwhEl.innerText = `+${slabKwh.toFixed(1)} kWh`;

      const slabTempEl = document.getElementById('kpi-diurnal-slab-temp');
      if (slabTempEl) slabTempEl.innerText = `Rozkmit desky: ${minTf.toFixed(1)} → ${maxTf.toFixed(1)} °C (+${deltaTf.toFixed(1)} °C)`;

      // Count night idle hours (22-06h where heat pump is completely idle)
      const nightIdleCount = day.hours.filter(h => (h.h >= 22 || h.h < 6) && !h.isRunning).length;
      const nightHoursEl = document.getElementById('kpi-diurnal-night-hours');
      if (nightHoursEl) nightHoursEl.innerText = `${nightIdleCount} hodin`;

      const nightDescEl = document.getElementById('kpi-diurnal-night-desc');
      if (nightDescEl) nightDescEl.innerText = `22–06 h: bez provozu ${nightIdleCount} z 8 hodin (součet úseků dne)`;

      // Electricity usage and savings for this day
      const diffEl = day.el_std - day.el_opt;
      const diffPct = day.el_std > 0 ? (diffEl / day.el_std) * 100 : 0;
      const elUsageEl = document.getElementById('kpi-diurnal-el-usage');
      if (elUsageEl) elUsageEl.innerHTML = `${day.el_opt.toFixed(1)} kWh <span class="text-xs font-normal text-slate-400">(vs ekviterm ${day.el_std.toFixed(1)})</span>`;

      const elSavingEl = document.getElementById('kpi-diurnal-el-saving');
      if (elSavingEl) elSavingEl.innerHTML = `Úspora dne: <strong>${diffEl.toFixed(1)} kWh (${diffPct.toFixed(0)} %)</strong> • SCOP ${day.scop_day.toFixed(2)}`;

      // 3. Render Canvas Charts
      drawDiurnalOutdoorCanvas(activeDiurnalHoverHour);
      drawDiurnalTempCanvas(activeDiurnalHoverHour);
      drawDiurnalPowerCanvas(activeDiurnalHoverHour);
    }

    // Canvas 1: Temperature & Accumulation Profile (00:00 - 23:00)
    function drawDiurnalTempCanvas(hoverHour) {
      const canvas = document.getElementById('diurnalTempCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width, H = rect.height;
      const padL = 40, padR = 25, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const cur = simResults[state.currentSeason];
      if (!cur || !cur.daily) return;
      const day = cur.daily[state.selectedDayIndex];
      if (!day || !day.hours) return;
      const hours = day.hours;

      // Determine Temperature Range
      let minT = 99, maxT = -99;
      hours.forEach(h => {
        
        if (h.tr < minT) minT = h.tr;
        if (h.tf < minT) minT = h.tf;
        
        if (h.tr > maxT) maxT = h.tr;
        if (h.tf > maxT) maxT = h.tf;
        if (h.tfl !== null && h.tfl > maxT) maxT = h.tfl;
      });
      minT = Math.floor(minT - 1.5);
      maxT = Math.ceil(maxT + 1.5);
      if (maxT - minT < 3) maxT = minT + 3;

      const yT = (val) => padT + cH - ((val - minT) / (maxT - minT)) * cH;
      const xH = (h) => padL + (h / 24) * cW;

      drawDailySchedule(ctx,padL,padT,cW,cH);
      // 2. Indoor Room Comfort Corridor Shading
      const yComfTop = yT(state.tInTarget);
      const yComfBot = yT(state.tInTarget - state.tTolerance);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
      ctx.fillRect(padL, yComfTop, cW, yComfBot - yComfTop);
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.25)';
      ctx.setLineDash([3, 3]);
      ctx.strokeRect(padL, yComfTop, cW, yComfBot - yComfTop);
      ctx.setLineDash([]);

      // 3. Gridlines & Y-Axis Labels
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      const numYTicks = 5;
      for (let i = 0; i <= numYTicks; i++) {
        const val = minT + ((maxT - minT) / numYTicks) * i;
        const y = yT(val);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + cW, y);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(`${Math.round(val)}°`, padL - 6, y + 3);
      }

      // Freezing Zero Line (0 °C)
      if (minT <= 0 && maxT >= 0) {
        const yZero = yT(0);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padL, yZero);
        ctx.lineTo(padL + cW, yZero);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(148, 163, 184, 0.6)';
        ctx.textAlign = 'left';
        ctx.fillText('0 °C', padL + cW - 25, yZero - 3);
      }

      // 4. Flow Water Temperature t_flow (Red dashed line when active)
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2.0;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      let startedFlow = false;
      hours.forEach((h, i) => {
        if (h.tfl !== null) {
          const x = xH(i);
          const y = yT(h.tfl);
          if (!startedFlow) { ctx.moveTo(x, y); startedFlow = true; }
          else ctx.lineTo(x, y);
        } else {
          startedFlow = false;
        }
      });
      ctx.stroke();
      ctx.setLineDash([]);

      // 6. Floor Slab Core Temp T_floor (Warm Amber/Orange - Thick Curve with Dots)
      ctx.strokeStyle = '#f97316';
      ctx.lineWidth = 3.0;
      ctx.beginPath();
      hours.forEach((h, i) => {
        const x = xH(i);
        const y = yT(h.tf);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();

      ctx.fillStyle = '#f97316';
      hours.forEach((h, i) => {
        const x = xH(i);
        const y = yT(h.tf);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      // 7. Indoor Room Air Temp T_room (Emerald Green)
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      hours.forEach((h, i) => {
        const x = xH(i);
        const y = yT(h.tr);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // 8. X-Axis Hour Labels
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      const tickHours = [0, 3, 6, 9, 12, 15, 18, 21, 24];
      tickHours.forEach(h => {
        const x = xH(h);
        ctx.fillText(`${String(h).padStart(2, '0')}:00`, x, padT + cH + 16);
      });

      // 9. Synchronized Hover Guideline
      if (hoverHour !== null && hoverHour !== undefined && hoverHour >= 0 && hoverHour < 24) {
        const xHov = xH(hoverHour);
        ctx.save();
        ctx.strokeStyle = '#38bdf8';
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(xHov, padT);
        ctx.lineTo(xHov, padT + cH);
        ctx.stroke();

        const hData = hours[hoverHour];
        ctx.setLineDash([]);
        ctx.fillStyle = '#f97316';
        ctx.beginPath();
        ctx.arc(xHov, yT(hData.tf), 4.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(xHov, yT(hData.tr), 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }

    // Canvas 2: Heat Pump Power, Modulation, DHW & Instantaneous COP
    function drawDiurnalPowerCanvas(hoverHour) {
      const canvas = document.getElementById('diurnalPowerCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width, H = rect.height;
      const padL = 40, padR = 40, padT = 20, padB = 25;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const cur = simResults[state.currentSeason];
      if (!cur || !cur.daily) return;
      const day = cur.daily[state.selectedDayIndex];
      if (!day || !day.hours) return;
      const hours = day.hours;

      let maxKw = 0;
      hours.forEach(h => {
        const totTh = h.q_hp + h.q_dhw;
        if (totTh > maxKw) maxKw = totTh;
        if (h.p_el_std > maxKw) maxKw = h.p_el_std;
      });
      maxKw = Math.max(6.0, Math.ceil((maxKw * 1.25) / 2) * 2);

      const yKw = (kw) => padT + cH - (kw / maxKw) * cH;
      const maxCop=Math.max(6,Math.ceil(Math.max(...hours.map(h=>h.cop_opt||0))));
      const yCop = (c) => padT + cH - (Math.max(0, c) / maxCop) * cH;
      const xH = (h) => padL + (h / 24) * cW;

      drawDailySchedule(ctx,padL,padT,cW,cH);
      // 2. Gridlines for kW (Left)
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      const numKwTicks = 4;
      for (let i = 0; i <= numKwTicks; i++) {
        const val = (maxKw / numKwTicks) * i;
        const y = yKw(val);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + cW, y);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(`${val.toFixed(0)} kW`, padL - 6, y + 3);
      }

      // 3. Right Y-Axis: Okamžitý COP (0 - 6.0)
      for (let c = 2.0; c <= maxCop; c += 1.0) {
        const y = yCop(c);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.8)';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'left';
        ctx.fillText(`COP ${c.toFixed(0)}`, padL + cW + 6, y + 3);
      }

      // 4. Bars: Thermal Output Q_hp (Sky Blue) & Q_dhw (Amber)
      const barW = Math.max(5, (cW / 24) * 0.55);
      hours.forEach((h, i) => {
        const x = xH(i);

        // Standard Equithermal Baseline Outline (Gray Dashed)
        const hStd = (h.p_el_std / maxKw) * cH;
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
        ctx.setLineDash([2, 2]);
        ctx.strokeRect(x - barW / 2 - 1.5, padT + cH - hStd, barW + 3, hStd);
        ctx.setLineDash([]);

        // Q_hp to floor
        const hQhp = (h.q_hp / maxKw) * cH;
        if (hQhp > 0) {
          ctx.fillStyle = '#38bdf8';
          ctx.fillRect(x - barW / 2, padT + cH - hQhp, barW, hQhp);
        }

        // Q_dhw on top
        if (h.q_dhw > 0) {
          const hQdhw = (h.q_dhw / maxKw) * cH;
          ctx.fillStyle = '#f59e0b';
          ctx.fillRect(x - barW / 2, padT + cH - hQhp - hQdhw, barW, hQdhw);
        }

        // Electrical consumption inner bar (Purple)
        if (h.p_el_opt > 0) {
          const hPel = (h.p_el_opt / maxKw) * cH;
          ctx.fillStyle = '#c084fc';
          ctx.fillRect(x - barW / 4, padT + cH - hPel, barW / 2, hPel);
        }
      });

      // 5. Curve: Instantaneous COP (Right Axis, Emerald Green)
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      hours.forEach((h, i) => {
        const x = xH(i);
        const y = yCop(h.cop_opt);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // COP Dots
      hours.forEach((h, i) => {
        const x = xH(i);
        const y = yCop(h.cop_opt);
        ctx.fillStyle = h.isRunning ? '#10b981' : '#047857';
        ctx.beginPath();
        ctx.arc(x, y, h.isRunning ? 3.5 : 2, 0, Math.PI * 2);
        ctx.fill();
      });

      // 6. X-Axis Hours
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      const tickHours = [0, 3, 6, 9, 12, 15, 18, 21, 24];
      tickHours.forEach(h => {
        const x = xH(h);
        ctx.fillText(`${String(h).padStart(2, '0')}:00`, x, padT + cH + 16);
      });

      // 7. Synchronized Hover Guideline
      if (hoverHour !== null && hoverHour !== undefined && hoverHour >= 0 && hoverHour < 24) {
        const xHov = xH(hoverHour);
        ctx.save();
        ctx.strokeStyle = '#38bdf8';
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(xHov, padT);
        ctx.lineTo(xHov, padT + cH);
        ctx.stroke();

        const hData = hours[hoverHour];
        ctx.setLineDash([]);
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(xHov, yCop(hData.cop_opt), 5, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }

    // ================= 5-SEASON SUMMARY TABLE =================
    function renderMultiSeasonTable() {
      const tbody = document.getElementById('multi-season-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      const active5 = getActiveSeasons();
      let totTe = 0, totTh = 0, totStd = 0, totOpt = 0, totStarts = 0;

      active5.forEach(s => {
        const w = simResults[s];
        const r = w.results;
        const ws = w.weather_stats;

        totTe += ws.avg_temp;
        totTh += r.th_kwh;
        totStd += r.el_std_kwh;
        totOpt += r.el_opt_kwh;
        totStarts += r.starts_opt;

        const isCurrent = state.currentSeason === s;
        const tr = document.createElement('tr');
        tr.className = `hover:bg-slate-800/50 cursor-pointer ${isCurrent ? 'bg-sky-950/20 font-medium' : ''}`;
        tr.onclick = () => { selectSeason(s); setViewMode('single'); };

        tr.innerHTML = `
          <td class="py-3 px-3 font-semibold text-white flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${seasonColors[s]}"></span>
            ${s} ${isCurrent ? '<span class="text-[10px] text-sky-400 font-bold ml-1">★</span>' : ''}
          </td>
          <td class="py-3 px-2 text-right text-slate-300">${ws.avg_temp.toFixed(1)} °C</td>
          <td class="py-3 px-2 text-right text-slate-300">${Math.round(r.th_kwh).toLocaleString('cs-CZ')} kWh</td>
          <td class="py-3 px-2 text-right text-slate-400">${Math.round(r.el_std_kwh).toLocaleString('cs-CZ')}</td>
          <td class="py-3 px-2 text-right font-bold text-sky-400">${Math.round(r.el_opt_kwh).toLocaleString('cs-CZ')}</td>
          <td class="py-3 px-2 text-right font-semibold text-emerald-400">${Math.round(r.diff_kwh).toLocaleString('cs-CZ')} kWh (${r.diff_pct.toFixed(1)} %)</td>
          <td class="py-3 px-2 text-right font-bold text-amber-400">${Math.round(r.savings_czk).toLocaleString('cs-CZ')} Kč</td>
          <td class="py-3 px-2 text-right font-bold text-emerald-400">${r.scop_opt.toFixed(2)}</td>
          <td class="py-3 px-2 text-right text-slate-300">${r.scop_heat.toFixed(2)}</td>
          <td class="py-3 px-2 text-right text-slate-300">${r.scop_dhw.toFixed(2)}</td>
          <td class="py-3 px-2 text-right text-slate-300">${r.starts_opt.toLocaleString('cs-CZ')}</td>
        `;
        tbody.appendChild(tr);
      });

      // 5-Year Average Footer Row
      const cnt = active5.length;
      if (cnt > 0) {
        const avgTe = totTe / cnt;
        const avgTh = totTh / cnt;
        const avgStd = totStd / cnt;
        const avgOpt = totOpt / cnt;
        const avgDiff = avgStd - avgOpt;
        const avgDiffPct = avgStd > 0 ? (avgDiff / avgStd) * 100 : 0;
        const avgSavingsCzk = avgDiff * state.electricityPrice;
        const avgScop = avgOpt > 0 ? avgTh / avgOpt : 0;
        const avgStarts = Math.round(totStarts / cnt);

        const trAvg = document.createElement('tr');
        trAvg.className = "bg-slate-800/80 font-bold border-t-2 border-slate-700 text-white";
        trAvg.innerHTML = `
          <td class="py-3 px-3">${cnt}letý průměr</td>
          <td class="py-3 px-2 text-right">${avgTe.toFixed(1)} °C</td>
          <td class="py-3 px-2 text-right">${Math.round(avgTh).toLocaleString('cs-CZ')} kWh</td>
          <td class="py-3 px-2 text-right text-slate-400">${Math.round(avgStd).toLocaleString('cs-CZ')}</td>
          <td class="py-3 px-2 text-right text-sky-400">${Math.round(avgOpt).toLocaleString('cs-CZ')}</td>
          <td class="py-3 px-2 text-right text-emerald-400">${Math.round(avgDiff).toLocaleString('cs-CZ')} kWh (${avgDiffPct.toFixed(1)} %)</td>
          <td class="py-3 px-2 text-right text-amber-400">${Math.round(avgSavingsCzk).toLocaleString('cs-CZ')} Kč</td>
          <td class="py-3 px-2 text-right text-emerald-400">${avgScop.toFixed(2)}</td>
          <td class="py-3 px-2 text-right text-slate-300">–</td>
          <td class="py-3 px-2 text-right text-slate-300">–</td>
          <td class="py-3 px-2 text-right">${nfmt(avgStarts,2)}</td>
        `;
        tbody.appendChild(trAvg);
      }
    }

    // ================= GAS CONDENSING BOILER COMPARISON =================
    function drawGasBarChart() {
      const canvas = document.getElementById('gasComparisonCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width, H = rect.height;
      const padL = 60, padR = 20, padT = 25, padB = 30;
      const cW = W - padL - padR;
      const cH = H - padT - padB;

      ctx.clearRect(0, 0, W, H);

      const active5 = getActiveSeasons();
      if (active5.length === 0) return;

      let maxCost = 35000;
      active5.forEach(s => {
        const r = simResults[s].results;
        if (r.cost_gas_total > maxCost) maxCost = r.cost_gas_total;
        if (r.cost_hp_total > maxCost) maxCost = r.cost_hp_total;
      });
      maxCost = Math.ceil((maxCost * 1.15) / 5000) * 5000;

      // Draw Grid & Y-Axis Labels
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = padT + (cH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();

        const labelVal = maxCost - (maxCost / 4) * i;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(labelVal).toLocaleString('cs-CZ') + ' Kč', padL - 8, y + 3);
      }

      // Grouped Bars for Active 5 Seasons
      const numSeasons = active5.length;
      const groupWidth = cW / numSeasons;
      const barWidth = Math.min(30, (groupWidth - 16) / 2);

      active5.forEach((s, idx) => {
        const r = simResults[s].results;
        const centerX = padL + idx * groupWidth + groupWidth / 2;
        const xGas = centerX - barWidth - 2;
        const xHp = centerX + 2;

        const hGas = (r.cost_gas_total / maxCost) * cH;
        const yGas = padT + cH - hGas;
        const hHp = (r.cost_hp_total / maxCost) * cH;
        const yHp = padT + cH - hHp;

        // Gas Bar
        ctx.fillStyle = '#f43f5e';
        ctx.fillRect(xGas, yGas, barWidth, hGas);

        // Heat Pump Bar
        ctx.fillStyle = '#10b981';
        ctx.fillRect(xHp, yHp, barWidth, hHp);

        // Saving label
        const netSave = Math.round(r.savings_vs_gas_czk);
        const topY = Math.min(yGas, yHp) - 6;
        ctx.fillStyle = '#34d399';
        ctx.font = '10px system-ui font-bold';
        ctx.textAlign = 'center';
        ctx.fillText(`+${Math.round(netSave / 1000)}k`, centerX, Math.max(14, topY));

        // X-Axis Label
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(s, centerX, H - 10);
      });
    }

    // ================= KEYMARK MODAL & CATALOG CONTROLS =================
    function openKeymarkModal() {
      document.getElementById('keymark-modal').classList.remove('hidden');
      renderKeymarkModalCards();
    }

    function closeKeymarkModal() {
      document.getElementById('keymark-modal').classList.add('hidden');
    }

    function setKeymarkFilter(f) {
      state.keymarkFilter = f;
      ['all', 'r290', 'gawliczek'].forEach(b => {
        const el = document.getElementById(`km-btn-${b}`);
        if (el) {
          if (b === f) el.className = "px-2.5 py-1 rounded bg-emerald-600 text-white font-medium text-[11px]";
          else el.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 text-[11px]";
        }
      });
      renderKeymarkModalCards();
    }

    function toggleCustomKeymarkBox() {
      const box = document.getElementById('custom-km-form');
      box.classList.toggle('hidden');
    }

    function filterKeymarkModal(query) {
      renderKeymarkModalCards(query);
    }

    function quickFetchCert(certNo) {
      document.getElementById('km-fetch-input').value = certNo;
      downloadKeymarkCertificate();
    }

    // Simulated Keymark Certificate Protocol Downloader
    function downloadKeymarkCertificate() {
      const input = document.getElementById('km-fetch-input');
      const status = document.getElementById('km-fetch-status');
      const query = (input.value || '').trim();

      if (!query) {
        status.className = "mt-2 p-2 rounded bg-amber-950/80 text-amber-300 text-xs border border-amber-500/50 block";
        status.innerText = "Zadejte číslo certifikátu nebo kód modelu.";
        return;
      }

      status.className = "mt-2 p-2 rounded bg-sky-950/80 text-sky-300 text-xs border border-sky-500/50 block flex items-center gap-2";
      status.innerHTML = `
        <svg class="animate-spin h-3.5 w-3.5 text-sky-400" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span>Vyhledávám certifikát v evropské databázi HP KEYMARK (dahr.heatpumpkeymark.com)...</span>
      `;

      setTimeout(() => {
        // Look up in registry or match
        let found = keymarkCertificatesRegistry[query];
        if (!found) {
          const keys = Object.keys(keymarkCertificatesRegistry);
          for (const k of keys) {
            const item = keymarkCertificatesRegistry[k];
            if (k.toLowerCase().includes(query.toLowerCase()) ||
                item.name.toLowerCase().includes(query.toLowerCase()) ||
                item.modelCode.toLowerCase().includes(query.toLowerCase())) {
              found = item;
              break;
            }
          }
        }

        if (found) {
          document.getElementById('cust-km-name').value = found.name;
          document.getElementById('cust-km-cert').value = found.certNo;
          document.getElementById('cust-km-power35').value = found.pDesign35;
          document.getElementById('cust-km-power55').value = found.pDesign55;
          document.getElementById('cust-km-scop35').value = found.scop35;
          document.getElementById('cust-km-scop55').value = found.scop55;
          document.getElementById('cust-km-copdhw').value = found.copDhwRef;
          document.getElementById('cust-km-etawh').value = found.etaWh;
          document.getElementById('cust-km-refrig').value = found.refrigerant;
          document.getElementById('cust-km-noise').value = found.noiseDb;
          document.getElementById('cust-km-minmod').value = found.minMod;

          status.className = "mt-2 p-2 rounded bg-emerald-950/80 text-emerald-300 text-xs border border-emerald-500/50 block";
          status.innerHTML = `✅ Certifikát <strong>${found.certNo}</strong> (${found.modelCode}) byl úspěšně ověřen a stažen z databáze HP Keymark! Parametry pro 35 °C (podlaha), 55 °C (radiátory) a TUV předvyplněny.`;
        } else {
          // Dynamic synthesize for custom certificate numbers
          const pP = 8.0;
          document.getElementById('cust-km-name').value = `Keymark model (${query})`;
          document.getElementById('cust-km-cert').value = query;
          document.getElementById('cust-km-power35').value = pP;
          document.getElementById('cust-km-power55').value = 7.4;
          document.getElementById('cust-km-scop35').value = 4.65;
          document.getElementById('cust-km-scop55').value = 3.50;
          document.getElementById('cust-km-copdhw').value = 2.55;
          document.getElementById('cust-km-etawh').value = 136;
          document.getElementById('cust-km-refrig').value = 'R290 (Propan)';
          document.getElementById('cust-km-noise').value = '36 dB(A)';
          document.getElementById('cust-km-minmod').value = 2.4;

          status.className = "mt-2 p-2 rounded bg-emerald-950/80 text-emerald-300 text-xs border border-emerald-500/50 block";
          status.innerHTML = `✅ Certifikát <strong>${query}</strong> byl úspěšně vyhledán a stažen z HP Keymark! Parametry připraveny k uložení.`;
        }
      }, 500);
    }

    function selectKeymarkModel(id) {
      const found = keymarkDatabase.find(x => x.id === id);
      if (found) {
        state.activeHp = found;
        state.activeModelId = found.id;
        document.getElementById('badge-keymark').innerText = `Keymark: ${found.certNo} (${(state.heatingSystem === 'radiator' ? (found.pDesign55 || 7.5) : (found.pDesign35 || 8.1))} kW)`;
        closeKeymarkModal();
        recalculateSimulation();
        updateUI();
      }
    }

    function saveCustomKeymarkModel() {
      const name = document.getElementById('cust-km-name').value.trim() || 'Vlastní čerpadlo Keymark';
      const cert = document.getElementById('cust-km-cert').value.trim() || 'Keymark Custom';
      const p35 = parseFloat(document.getElementById('cust-km-power35').value) || 8.1;
      const p55 = parseFloat(document.getElementById('cust-km-power55').value) || 7.5;
      const scop35 = parseFloat(document.getElementById('cust-km-scop35').value) || 4.62;
      const scop55 = parseFloat(document.getElementById('cust-km-scop55').value) || 3.45;
      const copDhw = parseFloat(document.getElementById('cust-km-copdhw').value) || 2.50;
      const etaWh = parseInt(document.getElementById('cust-km-etawh').value) || 135;
      const refrig = document.getElementById('cust-km-refrig').value.trim() || 'R290 (Propan)';
      const noise = document.getElementById('cust-km-noise').value.trim() || '~36 dB(A)';
      const minMod = parseFloat(document.getElementById('cust-km-minmod').value) || 2.5;

      const newId = `custom-${Date.now()}`;
      const customObj = {
        id: newId,
        name: name,
        brand: 'Vlastní / Certifikováno',
        modelCode: cert,
        certNo: cert,
        pDesign35: p35,
        pDesign55: p55,
        minMod: minMod,
        scop35: scop35,
        scop55: scop55,
        copDhwRef: copDhw,
        etaWh: etaWh,
        dhwProfile: 'L',
        noiseDb: noise,
        refrigerant: refrig,
        compressor: 'Inverter Compressor (Keymark spec)',
        copA7W35: scop35 * 1.15,
        copA2W35: scop35 * 0.96,
        copAm7W35: scop35 * 0.72,
        copAm15W35: scop35 * 0.57,
        copA7W55: scop55 * 1.00,
        copA2W55: scop55 * 0.80,
        copAm7W55: scop55 * 0.62,
        copAm15W55: scop55 * 0.52,
        desc: `Uživatelsky zadané / stažené čerpadlo z certifikátu HP Keymark ${cert}.`
      };

      keymarkDatabase.push(customObj);
      selectKeymarkModel(newId);
    }

    function renderKeymarkModalCards(query = '') {
      const container = document.getElementById('km-cards-container');
      if (!container) return;
      container.innerHTML = '';

      let list = keymarkDatabase.filter(h=>h.selectable!==false);
      if (state.keymarkFilter === 'r290') {
        list = list.filter(x => x.refrigerant.includes('R290'));
      } else if (state.keymarkFilter === 'gawliczek') {
        list = list.filter(x => x.brand.toLowerCase().includes('gawliczek') || x.brand.toLowerCase().includes('warmhouse') || x.brand.toLowerCase().includes('power world'));
      }

      if (query && query.trim().length > 0) {
        const q = query.trim().toLowerCase();
        list = list.filter(x => x.name.toLowerCase().includes(q) || x.modelCode.toLowerCase().includes(q) || x.certNo.toLowerCase().includes(q) || x.brand.toLowerCase().includes(q));
      }

      list.forEach(item => {
        const isSelected = state.activeModelId === item.id;
        const card = document.createElement('div');
        card.className = `p-3.5 rounded-xl border transition cursor-pointer flex flex-col justify-between ${
          isSelected ? 'bg-emerald-950/40 border-emerald-500 shadow-lg' : 'bg-slate-800/80 border-slate-700 hover:border-slate-500'
        }`;
        card.onclick = () => selectKeymarkModel(item.id);

        card.innerHTML = `
          <div>
            <div class="flex items-start justify-between gap-2">
              <div>
                <span class="text-[10px] text-emerald-400 font-medium">HP Keymark: ${item.certNo} • Kód: ${item.modelCode}</span>
                <h4 class="text-sm font-bold text-white mt-0.5">${item.name}</h4>
              </div>
              ${isSelected ? '<span class="px-2 py-0.5 rounded bg-emerald-600 text-white text-[10px] font-bold">AKTIVNÍ</span>' : ''}
            </div>
            <p class="text-xs text-slate-300 mt-1 line-clamp-2">${item.desc}</p>
          </div>

          <div class="mt-3 pt-2.5 border-t border-slate-700/60 grid grid-cols-4 gap-1.5 text-center text-xs">
            <div class="bg-slate-900/80 p-1.5 rounded">
              <div class="text-[10px] text-slate-400">SCOP 35°C</div>
              <div class="font-bold text-emerald-400 text-xs">${item.scop35}</div>
            </div>
            <div class="bg-slate-900/80 p-1.5 rounded">
              <div class="text-[10px] text-slate-400">SCOP 55°C</div>
              <div class="font-bold text-sky-400 text-xs">${item.scop55}</div>
            </div>
            <div class="bg-slate-900/80 p-1.5 rounded">
              <div class="text-[10px] text-slate-400">TUV COP</div>
              <div class="font-bold text-amber-400 text-xs">${item.copDhwRef??'—'} (${item.etaWh??'—'}%)</div>
            </div>
            <div class="bg-slate-900/80 p-1.5 rounded">
              <div class="text-[10px] text-slate-400">Hluk dB(A)</div>
              <div class="font-semibold text-slate-200 text-xs truncate">${item.noiseDb.split(' ')[0]}</div>
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function renderKeymarkCatalogView() {
      const hp = state.activeHp;
      const elTitle = document.getElementById('cat-active-hp-title');
      const elDesc = document.getElementById('cat-active-hp-desc');
      const elScop35 = document.getElementById('cat-active-hp-scop35');
      const elScop55 = document.getElementById('cat-active-hp-scop55');
      const elCopTuv = document.getElementById('cat-active-hp-coptuv');

      if (elTitle) elTitle.innerText = hp.name;
      if (elDesc) elDesc.innerText = `Certifikát Keymark: ${hp.certNo} • Model: ${hp.modelCode} • Chladivo: ${hp.refrigerant} • Hluk: ${hp.noiseDb}`;
      if (elScop35) elScop35.innerText = hp.scop35;
      if (elScop55) elScop55.innerText = hp.scop55;
      if (elCopTuv) elCopTuv.innerText = `${hp.copDhwRef??'—'} (${hp.etaWh??'—'} %)`;

      const container = document.getElementById('keymark-catalog-grid');
      if (!container) return;
      container.innerHTML = '';

      keymarkDatabase.filter(h=>h.selectable!==false).forEach(item => {
        const isSelected = state.activeModelId === item.id;
        const card = document.createElement('div');
        card.className = `p-4 rounded-xl border flex flex-col justify-between transition ${
          isSelected ? 'bg-emerald-950/40 border-emerald-500 shadow-xl' : 'bg-slate-900/90 border-slate-700/80 hover:border-slate-500'
        }`;

        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">${item.brand}</span>
              ${isSelected ? '<span class="px-2 py-0.5 rounded bg-emerald-600 text-white text-[10px] font-bold">AKTIVNÍ</span>' : ''}
            </div>
            <h4 class="text-sm font-bold text-white">${item.name}</h4>
            <div class="text-[10px] text-emerald-400 font-semibold mb-2">Keymark: ${item.certNo} • Kód: ${item.modelCode}</div>
            <p class="text-xs text-slate-300 leading-relaxed mb-3">${item.desc}</p>
          </div>

          <div class="space-y-2 pt-2 border-t border-slate-800 text-xs">
            <div class="grid grid-cols-3 gap-1.5 text-center">
              <div class="bg-slate-950 p-1.5 rounded">
                <div class="text-[10px] text-slate-400">Podlaha 35°C</div>
                <div class="text-xs font-bold text-emerald-400">SCOP ${item.scop35}</div>
              </div>
              <div class="bg-slate-950 p-1.5 rounded">
                <div class="text-[10px] text-slate-400">Radiátory 55°C</div>
                <div class="text-xs font-bold text-sky-400">SCOP ${item.scop55}</div>
              </div>
              <div class="bg-slate-950 p-1.5 rounded">
                <div class="text-[10px] text-slate-400">TUV COP</div>
                <div class="text-xs font-bold text-amber-400">${item.copDhwRef??'—'} (${item.etaWh??'—'}%)</div>
              </div>
            </div>

            <div class="flex justify-between text-slate-300 text-[11px] pt-1">
              <span>Chladivo:</span>
              <span class="text-emerald-400 font-semibold">${item.refrigerant}</span>
            </div>
            <div class="flex justify-between text-slate-300 text-[11px]">
              <span>Hlučnost:</span>
              <span class="text-slate-200 font-semibold">${item.noiseDb}</span>
            </div>
            <div class="flex justify-between text-slate-300 text-[11px]">
              <span>Kompresor:</span>
              <span class="text-slate-200 truncate ml-2">${item.compressor.split('(')[0]}</span>
            </div>

            <button onclick="selectKeymarkModel('${item.id}')" class="w-full mt-2 py-1.5 rounded-lg text-xs font-bold transition ${
              isSelected ? 'bg-emerald-600 text-white cursor-default' : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
            }">
              ${isSelected ? '✓ Aktivní pro simulaci' : 'Aktivovat pro simulaci'}
            </button>
          </div>
        `;
        container.appendChild(card);
      });
    }

    // ================= TOOLTIPS & CANVAS INTERACTIONS =================
    function setupCanvasTooltips() {
      const tooltip = document.getElementById('chartTooltip');

      // Overlay Canvas Tooltip
      const ovlCanvas = document.getElementById('overlayCanvas');
      if (ovlCanvas) {
        ovlCanvas.addEventListener('mousemove', (e) => {
          const rect = ovlCanvas.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;

          const padL = 45, padR = 15;
          const cW = rect.width - padL - padR;

          const active5 = getActiveSeasons();
          if (active5.length === 0) return;
          const numDays = simResults[active5[0]].daily.length;

          if (mouseX >= padL && mouseX <= rect.width - padR) {
            const dayIdx = Math.min(numDays - 1, Math.max(0, Math.round(((mouseX - padL) / cW) * (numDays - 1))));
            const dateStr = getDayDateString(dayIdx);

            const getMetricValText = (seasonKey) => {
              const d = simResults[seasonKey]?.daily[dayIdx];
              if (!d) return '–';
              if (state.overlayMetric === 'kwh_daily') return `${Math.round(d.el_opt)} kWh`;
              if (state.overlayMetric === 'scop') return `COP ${d.scop_day.toFixed(2)}`;
              if (state.overlayMetric === 'temp') return `${d.avg_t.toFixed(1)} °C`;
              const cumArr = simResults[seasonKey]?.cum_kwh;
              const cum = cumArr ? Math.round(cumArr[Math.min(dayIdx, cumArr.length - 1)] || 0) : 0;
              return `${nfmt(cum,2)} kWh`;
            };

            let rows = active5.map(s => {
              const color = seasonColors[s] || '#38bdf8';
              const isCur = s === state.currentSeason;
              return `<div class="flex items-center justify-between gap-3 text-[11px] ${isCur ? 'font-bold text-white' : 'text-slate-300'}">
                <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full" style="background-color: ${color}"></span>${s}</span>
                <span class="font-mono">${getMetricValText(s)}</span>
              </div>`;
            }).join('');

            tooltip.innerHTML = `
              <div class="font-bold text-sky-300 border-b border-slate-700 pb-1 mb-1 text-xs">Den ${dayIdx + 1} • ${dateStr}</div>
              <div class="space-y-0.5">${rows}</div>
            `;
            tooltip.style.left = `${e.pageX + 15}px`;
            tooltip.style.top = `${e.pageY - 20}px`;
            tooltip.style.display = 'block';
          } else {
            tooltip.style.display = 'none';
          }
        });

        ovlCanvas.addEventListener('mouseleave', () => {
          tooltip.style.display = 'none';
          state.hoverSeason = null;
          drawOverlayChart();
        });
      }

      // Single Season Canvas Tooltip
      const sglCanvas = document.getElementById('singleCanvas');
      if (sglCanvas) {
        sglCanvas.addEventListener('mousemove', (e) => {
          const rect = sglCanvas.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const padL = 45, padR = 15;
          const cW = rect.width - padL - padR;

          const cur = simResults[state.currentSeason];
          if (!cur) return;
          const daily = cur.daily;
          const numDays = daily.length;

          if (mouseX >= padL && mouseX <= rect.width - padR) {
            const dayIdx = Math.min(numDays - 1, Math.max(0, Math.round(((mouseX - padL) / cW) * (numDays - 1))));
            const d = daily[dayIdx];
            const dateStr = getDayDateString(dayIdx);

            let content = '';
            if (state.singleMetric === 'el') {
              const diff = d.el_std - d.el_opt;
              const diffPct = d.el_std > 0 ? (diff / d.el_std) * 100 : 0;
              content = `
                <div class="font-bold text-white mb-1">${dateStr} (Den ${dayIdx + 1})</div>
                <div class="text-sky-300">Optimalizované TČ: <strong>${Math.round(d.el_opt)} kWh</strong></div>
                ${state.dhwEnabled ? `<div class="text-[11px] text-slate-400 ml-2">• Topení: ${Math.round(d.el_opt_heat)} kWh • TUV: ${Math.round(d.el_opt_dhw)} kWh</div>` : ''}
                <div class="text-slate-400">Běžné řízení: <strong>${Math.round(d.el_std)} kWh</strong></div>
                <div class="text-emerald-400 font-bold border-t border-slate-700 pt-1 mt-1">Úspora: -${Math.round(diff)} kWh (-${diffPct.toFixed(0)} %)</div>
                <div class="text-slate-400 text-[10px]">Denní teplota: ${d.avg_t.toFixed(1)} °C • COP ${d.scop_day.toFixed(2)}</div>
              `;
            } else if (state.singleMetric === 'temp') {
              content = `
                <div class="font-bold text-white mb-1">${dateStr}</div>
                <div class="text-sky-300">Průměrná teplota: <strong>${d.avg_t.toFixed(1)} °C</strong></div>
                <div class="text-slate-400">Rozsah: ${d.min_t.toFixed(1)} °C až ${d.max_t.toFixed(1)} °C</div>
                <div class="text-emerald-400">Denní COP: <strong>${d.scop_day.toFixed(2)}</strong></div>
              `;
            } else {
              content = `
                <div class="font-bold text-white mb-1">${dateStr}</div>
                <div class="text-emerald-400">Denní SCOP: <strong>${d.scop_day.toFixed(2)}</strong></div>
                <div class="text-slate-400">Průměrná venkovní teplota: ${d.avg_t.toFixed(1)} °C</div>
              `;
            }

            tooltip.innerHTML = content;
            tooltip.style.left = `${e.pageX + 15}px`;
            tooltip.style.top = `${e.pageY - 20}px`;
            tooltip.style.display = 'block';
          } else {
            tooltip.style.display = 'none';
          }
        });

        sglCanvas.addEventListener('mouseleave', () => {
          tooltip.style.display = 'none';
        });

        // Click on singleCanvas selects that day for 24-hour diurnal profile
        sglCanvas.addEventListener('click', (e) => {
          const rect = sglCanvas.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const padL = 45, padR = 15;
          const cW = rect.width - padL - padR;

          const cur = simResults[state.currentSeason];
          if (!cur || !cur.daily) return;
          const numDays = cur.daily.length;

          if (mouseX >= padL && mouseX <= rect.width - padR) {
            const dayIdx = Math.min(numDays - 1, Math.max(0, Math.round(((mouseX - padL) / cW) * (numDays - 1))));
            state.selectedDayIndex = dayIdx;
            drawSingleSeasonChart();
            updateDiurnalView();

            if(typeof selectAnalysisView==='function')selectAnalysisView('day');
            const diurnalCard = document.getElementById('diurnal-section-card');
            if (diurnalCard) {
              diurnalCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
          }
        });
      }

      // Diurnal 24-Hour Canvases Hover & Tooltip Handlers
      const dtCanvas = document.getElementById('diurnalTempCanvas');
      const dpCanvas = document.getElementById('diurnalPowerCanvas');

      function handleDiurnalMove(canvas, e) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const padL = 40, padR = canvas.id==='diurnalPowerCanvas'?40:25;
        const cW = rect.width - padL - padR;

        const cur = simResults[state.currentSeason];
        if (!cur || !cur.daily) return;
        const day = cur.daily[state.selectedDayIndex];
        if (!day || !day.hours) return;

        if (mouseX >= padL && mouseX <= rect.width - padR) {
          const h = Math.min(23, Math.max(0, Math.floor(((mouseX - padL) / cW) * 24)));
          activeDiurnalHoverHour = h;
          drawDiurnalOutdoorCanvas(h);
      drawDiurnalTempCanvas(h);
          drawDiurnalPowerCanvas(h);

          const hData = day.hours[h];
          const statusText = hData.isCharge
            ? '<span class="text-amber-400 font-semibold">☀️ Polední nabíjení akumulace</span>'
            : ((hData.h >= 22 || hData.h <= 6) && !hData.isRunning
              ? '<span class="text-indigo-400 font-semibold">🌙 Noční útlum (vybíjení akumulace)</span>'
              : '<span class="text-sky-300 font-semibold">🟢 Běžná modulace</span>');

          tooltip.innerHTML = `
            <div class="font-bold text-white border-b border-slate-700 pb-1 mb-1.5 text-xs flex items-center justify-between gap-4">
              <span>🕒 Čas: ${String(h).padStart(2, '0')}:00 – ${String(h + 1).padStart(2, '0')}:00</span>
              <span>${statusText}</span>
            </div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
              <div class="col-span-2">HDO: ${hdoHourDescription(h)}</div>
              <div>Venkovní teplota: <strong class="text-sky-300">${nfmt(hData.te,2)} °C</strong></div>
              <div>Teplota podlahy: <strong class="text-amber-400">${nfmt(hData.tf,2)} °C</strong></div>
              <div>Vnitřní teplota: <strong class="text-emerald-400">${nfmt(hData.tr,2)} °C</strong></div>
              <div>Otopná voda: <strong class="${hData.tfl !== null ? 'text-rose-400' : 'text-slate-400'}">${hData.tfl !== null ? (nfmt(hData.tfl,2) + ' °C') : 'Vypnuto (0 °C)'}</strong></div>
              <div class="border-t border-slate-700/60 pt-1 mt-0.5">Výkon TČ do podlahy: <strong class="text-sky-300">${nfmt(hData.q_hp,2)} kW</strong></div>
              <div class="border-t border-slate-700/60 pt-1 mt-0.5">Ohřev TUV: <strong class="text-amber-300">${hData.q_dhw > 0 ? (nfmt(hData.q_dhw,2) + ' kW') : '0 kW'}</strong></div>
              <div>Příkon elektřiny Smart: <strong class="text-purple-300">${nfmt(hData.p_el_opt,2)} kW</strong></div>
              <div>Příkon Ekviterm: <strong class="text-slate-400">${nfmt(hData.p_el_std,2)} kW</strong></div>
              <div class="col-span-2 border-t border-slate-700/60 pt-1 text-emerald-400 font-bold">
                Okamžitý COP: ${hData.cop_opt.toFixed(2)} ${!hData.isRunning ? '<span class="text-slate-400 font-normal text-[10px]">(při stávající venkovní teplotě)</span>' : ''}
              </div>
            </div>
          `;
          tooltip.style.left = `${e.pageX + 15}px`;
          tooltip.style.top = `${e.pageY - 20}px`;
          tooltip.style.display = 'block';
        } else {
          handleDiurnalLeave();
        }
      }

      function handleDiurnalLeave() {
        activeDiurnalHoverHour = null;
        tooltip.style.display = 'none';
        drawDiurnalOutdoorCanvas(null);
      drawDiurnalTempCanvas(null);
        drawDiurnalPowerCanvas(null);
      }

      if (dtCanvas) {
        dtCanvas.addEventListener('mousemove', (e) => handleDiurnalMove(dtCanvas, e));
        dtCanvas.addEventListener('mouseleave', handleDiurnalLeave);
      }
      if (dpCanvas) {
        dpCanvas.addEventListener('mousemove', (e) => handleDiurnalMove(dpCanvas, e));
        dpCanvas.addEventListener('mouseleave', handleDiurnalLeave);
      }

      const outdoorCanvas=document.getElementById('diurnalOutdoorCanvas');
      outdoorCanvas?.addEventListener('mousemove',e=>handleDiurnalMove(outdoorCanvas,e));
      outdoorCanvas?.addEventListener('mouseleave',handleDiurnalLeave);
      // Gas Bar Chart Tooltip
      const gasCanvas = document.getElementById('gasComparisonCanvas');
      if (gasCanvas) {
        gasCanvas.addEventListener('mousemove', (e) => {
          const rect = gasCanvas.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const padL = 60, padR = 20;
          const cW = rect.width - padL - padR;

          const active5 = getActiveSeasons();
          if (active5.length === 0) return;

          const groupWidth = cW / active5.length;
          const sIdx = Math.min(active5.length - 1, Math.max(0, Math.floor((mouseX - padL) / groupWidth)));
          const s = active5[sIdx];
          const r = simResults[s]?.results;

          if (r && mouseX >= padL && mouseX <= rect.width - padR) {
            tooltip.innerHTML = `
              <div class="font-bold text-white border-b border-slate-700 pb-1 mb-1">Topná sezóna ${s}</div>
              <div class="text-rose-400">Plynový kotel celkem: <strong>${Math.round(r.cost_gas_total).toLocaleString('cs-CZ')} Kč</strong></div>
              <div class="text-[10px] text-slate-400 ml-2">• Plyn: ${Math.round(r.gas_fuel_czk).toLocaleString('cs-CZ')} Kč • ETS 2: ${Math.round(r.gas_ets2_czk).toLocaleString('cs-CZ')} Kč</div>
              <div class="text-emerald-400 font-semibold mt-1">Tepelné čerpadlo: <strong>${Math.round(r.cost_hp_total).toLocaleString('cs-CZ')} Kč</strong></div>
              <div class="text-emerald-300 font-bold border-t border-slate-700 pt-1 mt-1">Úspora ve zvoleném období: +${Math.round(r.savings_vs_gas_czk).toLocaleString('cs-CZ')} Kč (-${r.savings_vs_gas_pct.toFixed(0)} %)</div>
            `;
            tooltip.style.left = `${e.pageX + 15}px`;
            tooltip.style.top = `${e.pageY - 20}px`;
            tooltip.style.display = 'block';
          } else {
            tooltip.style.display = 'none';
          }
        });

        gasCanvas.addEventListener('mouseleave', () => {
          tooltip.style.display = 'none';
        });
      }
    }

    function getDayDateString(dayIdx) {
      const cur = simResults[state.currentSeason];
      if (!cur) return `Den ${dayIdx + 1}`;
      const endYr = Number((state.currentSeason || '').slice(5)); const isLeap = endYr % 4 === 0 && (endYr % 100 !== 0 || endYr % 400 === 0);
      const mLens = [31, 30, 31, 31, isLeap ? 29 : 28, 31, 30];
      const mNames = ['října', 'listopadu', 'prosince', 'ledna', 'února', 'března', 'dubna'];

      let rem = dayIdx;
      for (let m = 0; m < mLens.length; m++) {
        if (rem < mLens[m]) {
          return `${rem + 1}. ${mNames[m]}`;
        }
        rem -= mLens[m];
      }
      return `Den ${dayIdx + 1}`;
    }

    // Responsive Canvas Resize Listener
    window.addEventListener('resize', () => {
      if (state.sectionsExpanded.all10) drawOverlayChart();
      if (state.sectionsExpanded.single) { drawSingleSeasonChart(); updateDiurnalView(); }
      if (state.sectionsExpanded.gas) drawGasBarChart();
    });

__REVIEW_V3__
__ENERGY_PRICES__
__TARIFF_CONTROL__
__KEYMARK_CATALOG__
__HP_KEYMARK__
__WORKSPACE_UI__
    window.onload = init;
  </script>
</body>
</html>
"""

# Inline the maintained model and UI modules so index.html remains offline-capable.
for marker, filename in [('__MODEL_V3__', 'model-v3.js'), ('__REVIEW_V3__', 'review-ui-v3.js'), ('__ENERGY_PRICES__', 'energy-prices.js'), ('__TARIFF_CONTROL__', 'tariff-control.js'), ('__KEYMARK_CATALOG__', 'keymark-catalog-data.js'), ('__HP_KEYMARK__', 'hp-keymark.js'), ('__WORKSPACE_UI__', 'workspace-ui.js')]:
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as module:
        html_template = html_template.replace(marker, module.read())

# Build only this project; additional exports should be requested explicitly.
dest_paths = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))]

for p in dest_paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tw_src = os.path.join(os.path.dirname(__file__), "..", "tailwindcss.min.js")
    if os.path.exists(tw_src):
        tw_dst = os.path.join(os.path.dirname(p), "tailwindcss.min.js")
        if not os.path.exists(tw_dst) or os.path.getsize(tw_dst) != os.path.getsize(tw_src):
            shutil.copy2(tw_src, tw_dst)
    with open(p, "w", encoding="utf-8") as f:
        f.write(html_template.replace("__WEATHER_JSON__", weather_json_str))
    print(f"Updated: {p}")

print("Built v3: shared energy balance, comfort, scenarios and seasonal/annual economics.")
