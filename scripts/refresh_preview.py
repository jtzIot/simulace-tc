from pathlib import Path
import ast, re
root=Path(__file__).resolve().parent.parent
source=(root/'scripts/build_full_interactive_app.py').read_text(encoding='utf-8')
tree=ast.parse(source)
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='html_template' for t in n.targets))
html=ast.literal_eval(node.value)
old=(root/'index.html').read_text(encoding='utf-8')
weather=re.search(r'let rawWeather = (.*);',old).group(1)
for marker,filename in [('__MODEL_V3__','model-v3.js'),('__REVIEW_V3__','review-ui-v3.js'),('__ENERGY_PRICES__','energy-prices.js'),('__TARIFF_CONTROL__','tariff-control.js'),('__KEYMARK_CATALOG__','keymark-catalog-data.js'),('__HP_KEYMARK__','hp-keymark.js'),('__WORKSPACE_UI__','workspace-ui.js')]:
    html=html.replace(marker,(root/'scripts'/filename).read_text(encoding='utf-8'))
(root/'index.html').write_text(html.replace('__WEATHER_JSON__',weather),encoding='utf-8')
print('Preview refreshed from generator template and modules.')
