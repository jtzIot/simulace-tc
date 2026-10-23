import urllib.request
import json

towns = ['Plzeň', 'Rokycany', 'Trutnov', 'Pec pod Sněžkou', 'Znojmo']
for t in towns:
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(t)}&count=2&language=cs&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('results', [])
            if results:
                r = results[0]
                print(f"{t}: {r['name']} ({r.get('admin1', '')}), lat={r['latitude']}, lon={r['longitude']}, elev={r.get('elevation')}m")
            else:
                print(f"{t}: no result")
    except Exception as e:
        print(f"{t}: error {e}")
