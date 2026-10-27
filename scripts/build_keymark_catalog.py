from pathlib import Path
import json,re
base=Path(__file__).resolve().parent.parent
root=base/'sim_data'/'keymark'
def clean(x):return ' '.join(x.split())
def num(x):
 m=re.search(r'[-+]?\d+(?:[.,]\d+)?',x);return float(m.group().replace(',','.')) if m else None
def norm(x):return re.sub(r'[\s{}_]','',x).replace('\u2212','-')
def make(sid,model,id):
 d=json.loads((root/f'{sid}.json').read_text(encoding='utf-8'));m=next(x for x in d['models'] if x['name']==model)
 groups=m['groups'];rated=next(g for g in groups if g['title']=='EN 14511-2' and g['mode']=='Heating');season=next(g for g in groups if g['title']=='EN 14825' and g['mode']=='Average Climate');sound=next(g for g in groups if g['title']=='EN 12102-1' and g['mode']=='Average Climate')
 meta=d['meta'];out={'id':id,'model':model,'cert':clean(meta['Registration number']),'holder':clean(meta.get('Certificate Holder','')),'lab':clean(meta.get('Testing laboratory','Neuvedena')),'date':clean(meta.get('Certification Date','')),'refrigerant':meta.get('Refrigerant',''),'refrigerantKg':num(meta.get('Mass of Refrigerant','')),'source':d['url'],'climate':'Average Climate','usePartLoad':True,'useStandby':True,'useCycling':False,'externalPumpW':25}
 soundrow=next((v for k,v in sound['rows'] if 'outdoor' in k),['','']);out['soundPower']=num(soundrow[0])
 scalars={'prated':'Prated','scop':'SCOP','eta':'ηs','tbiv':'Tbiv','tol':'TOL','wtol':'WTOL','poff':'Poff','pto':'PTO','psb':'PSB','pck':'PCK','psup':'SupplementaryHeater:PSUP','qhe':'AnnualenergyconsumptionQhe'}
 for idx,key in enumerate(['lt','mt']):
  g={}
  for outkey,label in [('ratedHeat','Heat output'),('ratedInput','El input'),('ratedCop','COP')]:g[outkey]=num(next(v[idx] for k,v in rated['rows'] if k==label))
  for outkey,label in scalars.items():g[outkey]=next((num(v[idx]) for k,v in season['rows'] if norm(k)==label),None)
  ps={}
  for k,v in season['rows']:
   if not any(k.startswith(prefix) for prefix in ['Pdh T','COP T','Cdh T']):continue
   field='heat' if k.startswith('Pdh') else 'cop' if k.startswith('COP') else 'cdh'
   air=max(g['tol'],-10) if 'TOL' in k and 'Tdesignh' in k else g['tol'] if 'TOL' in k else g['tbiv'] if 'Tbiv' in k else num(k.split('=')[-1])
   if air is None:continue
   ps.setdefault(air,{'air':air})[field]=num(v[idx])
  def refwater(t):
   grid=[(-10,35,55),(-7,34,52),(2,30,42),(7,27,36),(12,24,30)]
   if t<=-10:return grid[0][1+idx]
   if t>=12:return grid[-1][1+idx]
   for a,b in zip(grid,grid[1:]):
    if a[0]<=t<=b[0]:return a[1+idx]+(b[1+idx]-a[1+idx])*(t-a[0])/(b[0]-a[0])
  g['points']=[dict(p,water=refwater(t),cdh=p.get('cdh')) for t,p in sorted(ps.items()) if p.get('heat') and p.get('cop')]
  out[key]=g
 dhw=next((g for g in groups if g['title']=='EN 16147' and g['mode']=='Average Climate'),None)
 if dhw:out['dhw']={k:v for k,v in dhw['rows'] if k}
 return out
spec=[
 (6304,'PW020-DKZLRS-E/S','gawliczek-pw-6'),
 (4026,'PW030-DKZLRS-E/S','gawliczek-pw-89'),
 (4034,'PW040-DKZLRS-E/S','gawliczek-pw-114'),
 (4027,'PW050-DKZLRS-E','gawliczek-pw-148'),
 (5421,'PW055-DKZLRS-E','gawliczek-pw-182'),
 (7083,'HM-M1-A1','gawliczek-10'),
 (7084,'HM-M2-A1','gawliczek-12'),
 (7085,'HM-M3-A1','gawliczek-16'),
 (6973,'Vitocal 250-A AWO-M-E-AC 251.A08','viessmann-8'),
 (2771,'S2125-8 1x230V','nibe-8'),
 (3812,'WH-SDC0509L3E5 / WH-WDG07LE5','panasonic-l-7'),
 (7353,'ERRA08EV3 / ELVH12S23E(6V/9W)','daikin-8'),
 (8000,'VWL 75/6 A 230V','vaillant-75'),
 (4485,'CS5800iAW 7 OR180 MCP-S','bosch-5800-7')
]
if __name__=='__main__':
 data=[make(*x) for x in spec]
 (base/'scripts'/'keymark-catalog-data.js').write_text('// Extracted from official HP KEYMARK, 2026-10-27. Exact models, average climate only.\nconst additionalKeymarkData='+json.dumps(data,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
 for d in data:print(d['id'],d['cert'],len(d['lt']['points']),len(d['mt']['points']),[k for k,v in d['lt'].items() if v is None])
