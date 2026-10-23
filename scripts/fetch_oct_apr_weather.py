import urllib.request
import json
import os
import time

lat = 49.73
lon = 13.46

url = f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2014-10-01&end_date=2024-04-30&hourly=temperature_2m,relative_humidity_2m,direct_normal_irradiance,diffuse_radiation'
print('Fetching 10 full heating seasons (Oct 1 to Apr 30) from Open-Meteo Archive...')
t0 = time.time()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=45) as resp:
    archive = json.loads(resp.read().decode('utf-8'))

print(f'Fetched in {time.time()-t0:.2f}s!')

times = archive['hourly']['time']
temps = archive['hourly']['temperature_2m']
rhs = archive['hourly']['relative_humidity_2m']
dnis = archive['hourly'].get('direct_normal_irradiance', [])
diffs = archive['hourly'].get('diffuse_radiation', [])

season_keys = [f'{y}-{y+1}' for y in range(2014, 2024)]
seasons = {s: {'time': [], 'temp': [], 'rh': [], 'dni': [], 'diffuse': []} for s in season_keys}

for i, t in enumerate(times):
    yr = int(t[:4])
    mo = int(t[5:7])
    if mo >= 10:
        s = f'{yr}-{yr+1}'
    elif mo <= 4:
        s = f'{yr-1}-{yr}'
    else:
        continue
    if s in seasons:
        seasons[s]['time'].append(t)
        seasons[s]['temp'].append(temps[i] if temps[i] is not None else 0.0)
        seasons[s]['rh'].append(rhs[i] if rhs[i] is not None else 80.0)
        seasons[s]['dni'].append(dnis[i] if i < len(dnis) and dnis[i] is not None else 0.0)
        seasons[s]['diffuse'].append(diffs[i] if i < len(diffs) and diffs[i] is not None else 0.0)

for p in [
    './sim_data/weather_10_winters.json',
    './sim_data/weather_10_winters.json'
]:
    if os.path.exists(os.path.dirname(p)):
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(seasons, f, ensure_ascii=False)
        print('Saved to', p)

for s in season_keys:
    cnt = len(seasons[s]['time'])
    print(f'  Season {s}: {cnt} hours ({cnt // 24} days) from {seasons[s]["time"][0]} to {seasons[s]["time"][-1]}')
