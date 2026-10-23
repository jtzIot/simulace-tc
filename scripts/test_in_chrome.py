import asyncio
import json
import subprocess
import sys
import time
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def test_page():
    proc = subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless',
        '--remote-debugging-port=9222',
        '--disable-gpu',
        r'file:///./index.html'
    ])
    try:
        await asyncio.sleep(2)
        req = urllib.request.urlopen('http://127.0.0.1:9222/json')
        targets = json.loads(req.read().decode())
        page_target = [t for t in targets if t['type'] == 'page'][0]
        ws_url = page_target['webSocketDebuggerUrl']
        
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            await ws.send(json.dumps({'id': 2, 'method': 'Log.enable'}))
            
            async def evaluate(expr):
                await ws.send(json.dumps({
                    'id': 100,
                    'method': 'Runtime.evaluate',
                    'params': {'expression': expr, 'returnByValue': True}
                }))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get('id') == 100:
                        if 'exceptionDetails' in msg.get('result', {}):
                            print(f"EVAL EXCEPTION for '{expr}':", msg['result']['exceptionDetails'])
                        return msg.get('result', {}).get('result', {}).get('value')

            print('=== 1. Checking Default State & Parameters ===')
            html_class = await evaluate("document.documentElement.className")
            html_bg = await evaluate("window.getComputedStyle(document.documentElement).backgroundColor")
            body_bg = await evaluate("window.getComputedStyle(document.body).backgroundColor")
            body_color = await evaluate("window.getComputedStyle(document.body).color")
            card_bg = await evaluate("window.getComputedStyle(document.querySelector('.card')).backgroundColor")
            print(f'Dark theme check -> HTML class: "{html_class}", HTML bg: {html_bg}, Body bg: {body_bg}, Body text: {body_color}, Card bg: {card_bg}')

            q_loss = await evaluate("state.qLossDesign")
            t_flow = await evaluate("state.tFlowDesign")
            t_in = await evaluate("state.tInTarget")
            area = await evaluate("state.floorAreaM2")
            dhw_liters = await evaluate("state.dhwDailyLiters")
            dhw_temp = await evaluate("state.dhwTargetTemp")
            el_price = await evaluate("state.electricityPrice")
            gas_price = await evaluate("state.gasPrice")
            center_year = await evaluate("state.centerYear")
            current_season = await evaluate("state.currentSeason")
            active_hp = await evaluate("state.activeHp.name")
            active_cert = await evaluate("state.activeHp.certNo")

            print(f'qLoss: {q_loss} kW, tFlow: {t_flow} °C, tIn: {t_in} °C, Area: {area} m²')
            print(f'DHW: {dhw_liters} l/den @ {dhw_temp} °C, El: {el_price} Kč, Gas: {gas_price} Kč')
            print(f'Center Year: {center_year}, Current Season: {current_season}')
            print(f'Active HP: {active_hp} ({active_cert})')

            print('\n=== 2. Checking 5-Seasons Windowing ===')
            active5 = await evaluate("getActiveSeasons()")
            pills_text = await evaluate("document.getElementById('season-buttons').innerText")
            print(f'Active 5 Seasons: {active5}')
            print(f'Rendered Pills in DOM: {pills_text}')

            print('\n=== 3. Checking Simulation Results for 2016-2017 ===')
            await evaluate("selectSeason('2016-2017')")
            kpi_text = await evaluate("document.getElementById('season-kpi-container').innerText")
            print('KPI card content:\n' + kpi_text)

            print('\n=== 4. Checking Year Selection Stepper / Window Change ===')
            await evaluate("setCenterYear(2018)")
            active5_2018 = await evaluate("getActiveSeasons()")
            pills_2018 = await evaluate("document.getElementById('season-buttons').innerText")
            print(f'When centerYear=2018, Active 5: {active5_2018}')
            print(f'Pills for 2018: {pills_2018}')

            print('\n=== 5. Checking Absence of Prices in Heat Pump Cards ===')
            spec_price = await evaluate("document.getElementById('spec-hp-price')")
            cat_html = await evaluate("document.getElementById('view-dual-container').innerHTML")
            has_price_kwh = 'Kč' in cat_html and ('bez DPH' in cat_html or 'Cena:' in cat_html)
            print(f'spec-hp-price element exists: {spec_price is not None}')
            print(f'Contains "bez DPH" or "Cena:" in catalog: {has_price_kwh}')

            print('\n=== 6. Checking Absence of "ČEZ" in Visible Texts ===')
            body_text = await evaluate("document.body.innerText")
            cez_in_body = 'ČEZ' in body_text or 'CEZ' in body_text or 'D57d' in body_text
            print(f'Mentions of ČEZ / D57d in visible body: {cez_in_body}')

            print('\n=== 7. Checking Minimum Flow Temp Slider (min 26.0) ===')
            tflow_min = await evaluate("document.getElementById('input-tflow').min")
            print(f'tFlow slider min attribute: {tflow_min}')

            print('\n=== 8. Checking Keymark Certificate Downloader in Modal ===')
            await evaluate("""
                openKeymarkModal();
                toggleCustomKeymarkBox();
                quickFetchCert('012-C70025');
            """)
            await asyncio.sleep(1)
            downloaded_name = await evaluate("document.getElementById('cust-km-name').value")
            downloaded_cert = await evaluate("document.getElementById('cust-km-cert').value")
            downloaded_scop35 = await evaluate("document.getElementById('cust-km-scop35').value")
            downloaded_scop55 = await evaluate("document.getElementById('cust-km-scop55').value")
            downloaded_tuv = await evaluate("document.getElementById('cust-km-copdhw').value")
            status_text = await evaluate("document.getElementById('km-fetch-status').innerText")
            print(f'Downloaded: {downloaded_name} | Cert: {downloaded_cert}')
            print(f'SCOP 35: {downloaded_scop35} | SCOP 55: {downloaded_scop55} | TUV COP: {downloaded_tuv}')
            print(f'Status message: {status_text}')

            print('\n=== 9. Checking Heating System Toggle (Floor 35 °C vs Radiator 55 °C) ===')
            await evaluate("setHeatingSystem('radiator')")
            rad_tflow = await evaluate("state.tFlowDesign")
            rad_kpi = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'After switching to Radiator (55 °C): tFlow={rad_tflow} °C')
            print('Radiator KPI snippet:\n' + rad_kpi[:220])

            print('\n=== 10. Checking 24-Hour Diurnal Profile & Accumulation ===')
            await evaluate("setHeatingSystem('floor'); selectSeason('2016-2017'); setViewMode('single')")
            await asyncio.sleep(0.5)

            view_mode = await evaluate("state.viewMode")
            container_classes = await evaluate("document.getElementById('view-single-container').className")
            view_single_vis = await evaluate("!document.getElementById('view-single-container').classList.contains('hidden')")
            diurnal_card_vis = await evaluate("document.getElementById('diurnal-section-card') !== null")
            print(f'state.viewMode: {view_mode}, Container class: "{container_classes}"')
            print(f'View Single is visible: {view_single_vis}, Diurnal section card exists: {diurnal_card_vis}')

            # 10a. Check preset 'coldest'
            await evaluate("selectPresetDay('coldest')")
            coldest_idx = await evaluate("state.selectedDayIndex")
            date_badge = await evaluate("document.getElementById('diurnal-date-badge').innerText")
            weather_badge = await evaluate("document.getElementById('diurnal-weather-badge').innerText")
            swing_val = await evaluate("document.getElementById('kpi-diurnal-swing').innerText")
            slab_kwh = await evaluate("document.getElementById('kpi-diurnal-slab-kwh').innerText")
            slab_temp = await evaluate("document.getElementById('kpi-diurnal-slab-temp').innerText")
            night_hours = await evaluate("document.getElementById('kpi-diurnal-night-hours').innerText")
            el_usage = await evaluate("document.getElementById('kpi-diurnal-el-usage').innerText")
            el_saving = await evaluate("document.getElementById('kpi-diurnal-el-saving').innerText")

            print(f'Preset Coldest Day: Index {coldest_idx}')
            print(f'Date badge: {date_badge}')
            print(f'Weather badge: {weather_badge}')
            print(f'KPI Swing: {swing_val} | Slab kWh: {slab_kwh} ({slab_temp})')
            print(f'KPI Night silence: {night_hours} | El Usage: {el_usage} | Savings: {el_saving}')

            # 10b. Check 24 hourly physical logs
            hours_len = await evaluate("simResults['2016-2017'].daily[state.selectedDayIndex].hours.length")
            hour_0_state = await evaluate("JSON.stringify(simResults['2016-2017'].daily[state.selectedDayIndex].hours[0])")
            hour_12_state = await evaluate("JSON.stringify(simResults['2016-2017'].daily[state.selectedDayIndex].hours[12])")
            hour_13_state = await evaluate("JSON.stringify(simResults['2016-2017'].daily[state.selectedDayIndex].hours[13])")
            print(f'Hourly records count: {hours_len}')
            print(f'00:00 telemetry: {hour_0_state}')
            print(f'12:00 telemetry: {hour_12_state}')
            print(f'13:00 telemetry (DHW slot): {hour_13_state}')

            # 10c. Check preset 'winter' and 'spring'
            await evaluate("selectPresetDay('winter')")
            winter_idx = await evaluate("state.selectedDayIndex")
            winter_date = await evaluate("document.getElementById('diurnal-date-badge').innerText")
            winter_weather = await evaluate("document.getElementById('diurnal-weather-badge').innerText")
            print(f'Preset Winter Day: Index {winter_idx} | {winter_date} | {winter_weather}')

            await evaluate("selectPresetDay('spring')")
            spring_idx = await evaluate("state.selectedDayIndex")
            spring_date = await evaluate("document.getElementById('diurnal-date-badge').innerText")
            spring_weather = await evaluate("document.getElementById('diurnal-weather-badge').innerText")
            print(f'Preset Spring Day: Index {spring_idx} | {spring_date} | {spring_weather}')

            # 10d. Check canvas dimensions and drawing
            t_canvas_w = await evaluate("document.getElementById('diurnalTempCanvas').width")
            t_canvas_h = await evaluate("document.getElementById('diurnalTempCanvas').height")
            p_canvas_w = await evaluate("document.getElementById('diurnalPowerCanvas').width")
            p_canvas_h = await evaluate("document.getElementById('diurnalPowerCanvas').height")
            print(f'diurnalTempCanvas size: {t_canvas_w}x{t_canvas_h} px')
            print(f'diurnalPowerCanvas size: {p_canvas_w}x{p_canvas_h} px')

            print('\n=== 11. Checking Switchable Automation Levels ===')
            initial_level = await evaluate("state.automationLevel")
            initial_kpi = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'Initial automation level: {initial_level}')
            print('Initial (Level C - Predictive) KPI snippet:\n' + initial_kpi[:240])

            # 11a. Switch to Level B (SG Ready)
            await evaluate("setAutomationLevel('sgready')")
            level_b = await evaluate("state.automationLevel")
            badge_b = await evaluate("document.getElementById('badge-auto-level').innerText")
            kpi_b = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'\nSwitched to: {level_b} | Badge: {badge_b}')
            print('Level B (SG Ready) KPI snippet:\n' + kpi_b[:240])

            # 11b. Switch to Level A (Timer)
            await evaluate("setAutomationLevel('timer')")
            level_a = await evaluate("state.automationLevel")
            badge_a = await evaluate("document.getElementById('badge-auto-level').innerText")
            kpi_a = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'\nSwitched to: {level_a} | Badge: {badge_a}')
            print('Level A (Timer) KPI snippet:\n' + kpi_a[:240])

            # 11c. Switch to Level 0 (Baseline)
            await evaluate("setAutomationLevel('baseline')")
            level_0 = await evaluate("state.automationLevel")
            badge_0 = await evaluate("document.getElementById('badge-auto-level').innerText")
            kpi_0 = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'\nSwitched to: {level_0} | Badge: {badge_0}')
            print('Level 0 (Baseline) KPI snippet:\n' + kpi_0[:240])

            # 11d. Switch back to Level C (Predictive)
            await evaluate("setAutomationLevel('predictive')")
            level_c = await evaluate("state.automationLevel")
            badge_c = await evaluate("document.getElementById('badge-auto-level').innerText")
            kpi_c = await evaluate("document.getElementById('season-kpi-container').innerText")
            print(f'\nSwitched back to: {level_c} | Badge: {badge_c}')
            print('Level C (Predictive) KPI snippet:\n' + kpi_c[:240])

    finally:
        proc.terminate()

asyncio.run(test_page())
