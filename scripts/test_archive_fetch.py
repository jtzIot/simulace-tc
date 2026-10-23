import urllib.request
import json
import time

lat = 49.73
lon = 13.46

# Can we fetch start_date=2014-11-01 to end_date=2024-03-31 in one call?
t0 = time.time()
url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2014-11-01&end_date=2024-03-31&hourly=temperature_2m,relative_humidity_2m,direct_normal_irradiance,diffuse_radiation"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Success! Fetched entire 10-year span ({len(data['hourly']['time'])} hours) in ONE single call ({time.time()-t0:.2f}s)!")
except Exception as e:
    print("Error:", e)
