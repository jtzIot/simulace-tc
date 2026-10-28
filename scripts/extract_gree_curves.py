"""Extract Gree Versati heating tables from the supplied 55-page manual."""
import json, re, sys
from pathlib import Path
from pypdf import PdfReader

pdf = PdfReader(sys.argv[1])
tables = {}
for page_no, size in zip(range(12,14), (8,10)):
    text = pdf.pages[page_no].extract_text()
    assert f'Heating Capacity Correction_{size}' in text
    rows = {}
    for match in re.finditer(r'(?m)^(\d+)\s*\n(max[^\n]*)\n(norm[^\n]*)\n(min[^\n]*)',text):
        water = int(match.group(1))
        if not 25 <= water <= 80: continue
        levels = {}
        for label, line in zip(('max','norm','min'), match.group(2,3,4)):
            vals = line.split()[1:]
            if len(vals) != 42:
                raise ValueError((size,water,label,len(vals)))
            levels[label] = [[None if x=='/' else float(x) for x in vals[i:i+3]] for i in range(0,42,3)]
        rows[str(water)] = levels
    assert len(rows)==12, (size,len(rows))
    tables[f'gree-versati-{size}'] = {'air':[-25,-20,-15,-10,-7,-2,2,7,10,15,20,25,30,35], 'water':rows}
out=Path(__file__).with_name('gree-curves-data.js')
out.write_text('// Gree Versati V manual, heating tables, PDF pages 13–14.\nconst greeCurves = '+json.dumps(tables,separators=(',',':'))+';\n',encoding='utf-8')
print('Extracted',len(tables),'models to',out)
