import re

with open(r'Simulace_TC\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract script part
script_match = re.search(r'<script.*?>([\s\S]*?)</script>', html, re.IGNORECASE)

ids = set(re.findall(r'document\.getElementById\([\'"]([^\'"]+)[\'"]\)', html))
print(f'Total getElementById IDs referenced: {len(ids)}')

missing_ids = []
for el_id in sorted(ids):
    pattern = f'id=[\'"]{re.escape(el_id)}[\'"]'
    if not re.search(pattern, html):
        missing_ids.append(el_id)

print(f'Missing IDs in HTML ({len(missing_ids)}):')
for m in missing_ids:
    print(' -', m)
