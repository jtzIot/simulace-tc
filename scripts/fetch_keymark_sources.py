from html.parser import HTMLParser
from pathlib import Path
import urllib.request,json,re,concurrent.futures,sys
class Node:
 def __init__(self,tag='',attrs=(),parent=None): self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def text(self):return ' '.join((' '.join(c.text().split()) if isinstance(c,Node) else c) for c in self.children).strip()
 def has(self,c):return c in self.attrs.get('class','').split()
 def all(self,c):return [n for n in self.walk() if n.has(c)]
 def walk(self):
  for c in self.children:
   if isinstance(c,Node):yield c;yield from c.walk()
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.root=Node();self.cur=self.root
 def handle_starttag(self,t,a):
  n=Node(t,a,self.cur);self.cur.children.append(n)
  if t not in ['br','hr','img','input','meta','link','source','wbr']:self.cur=n
 def handle_endtag(self,t):
  n=self.cur
  while n.parent:
   if n.tag==t:self.cur=n.parent;return
   n=n.parent
 def handle_data(self,d):self.cur.children.append(d)
def extract(s):
 p=Parser();p.feed(s);out={'meta':{},'models':[]}
 for row in p.root.all('info-coll'):
  labels=row.all('info-label');vals=row.all('info-data')
  if labels and vals and labels[0].text() in ['Registration number','Certificate Holder','Testing laboratory','Certification Date','Refrigerant','Mass of Refrigerant']:out['meta'].setdefault(labels[0].text(),vals[0].text())
 models=p.root.all('modelList')
 if not models:raise ValueError('No models')
 for panel in models[0].children:
  if not isinstance(panel,Node) or not panel.has('panel'):continue
  groups=[];mode='General'
  for n in panel.walk():
   if n.has('modeName'):mode=n.text()
   if n.has('group'):
    title=n.all('groupTitle');rows=[]
    for row in n.all('info-coll'):
     label=row.all('info-label');vals=row.all('info-data')
     if label:rows.append([label[0].text(),[v.text() for v in vals]])
    groups.append({'mode':mode,'title':title[0].text() if title else '', 'rows':rows})
  names=[v for g in groups for k,v in g['rows'] if k=='Model name']
  out['models'].append({'name':names[0][0] if names else '?','groups':groups})
 return out
def fetch(id):
 path=Path('review-update/sim_data/keymark')/f'{id}.html'
 if path.with_suffix('.json').exists() and '--refresh' not in sys.argv:
  print(id,'cached JSON');return
 url=f'https://www.heatpumpkeymark.com/en/?tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D={id}&type=109126'
 s=path.read_text(encoding='utf-8') if path.exists() else urllib.request.urlopen(url,timeout=150).read().decode()
 data=extract(s);data['url']=url;data['retrieved']='2026-10-27';path.with_suffix('.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(id,data['meta'].get('Registration number'),len(data['models']),[x['name'] for x in data['models'][:3]])
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(fetch,[7083,7084,2771,3812,4485,7353,8000,6973]))
