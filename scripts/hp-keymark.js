// Source: HP KEYMARK certificate 011-1W1325, model HM-M0-A1, retrieved 2026-10-27.
// EN 14825 values are part-load declarations, not maximum/minimum output maps.
const keymark1325Source='https://www.heatpumpkeymark.com/en/?cHash=e30201a2dfb606558afd1b027939d014&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=7863&type=109126';
const keymark1325={
 cert:'011-1W1325',model:'HM-M0-A1',holder:'Guangdong Warmhouse Technology Co., Ltd.',lab:'TÜV Rheinland (GuangDong) Ltd., CN',date:'25.08.2026',refrigerantKg:.57,soundPower:56,
 usePartLoad:true,useStandby:true,useCycling:false,externalPumpW:25,
 lt:{ratedHeat:7.02,ratedInput:1.49,ratedCop:4.71,prated:5.68,scop:4.73,eta:186,tbiv:-7,tol:-10,wtol:75,poff:10,pto:17,psb:10,pck:34,psup:.36,qhe:2482,
 points:[{air:-10,water:35,heat:5.32,cop:2.70,cdh:.99},{air:-7,water:34,heat:5.03,cop:3.15,cdh:.99},{air:2,water:30,heat:3.06,cop:4.40,cdh:.98},{air:7,water:27,heat:2.07,cop:6.41,cdh:.95},{air:12,water:24,heat:2.35,cop:8.95,cdh:.94}]},
 mt:{ratedHeat:6.55,ratedInput:2.17,ratedCop:3.02,prated:5.63,scop:3.56,eta:139,tbiv:-7,tol:-10,wtol:75,poff:10,pto:17,psb:10,pck:34,psup:.32,qhe:3267,
 points:[{air:-10,water:55,heat:5.31,cop:1.96,cdh:.99},{air:-7,water:52,heat:4.98,cop:2.24,cdh:.99},{air:2,water:42,heat:3.04,cop:3.42,cdh:.98},{air:7,water:36,heat:2.02,cop:4.67,cdh:.96},{air:12,water:30,heat:2.23,cop:6.64,cdh:.95}]}
};
const kmClone=x=>JSON.parse(JSON.stringify(x));
function validateKeymarkConfig(x){
 const original=keymarkOriginal(x);if(!original)throw Error('Neznámá měřená sestava.');const r=kmClone(original);
 for(const key of ['usePartLoad','useStandby','useCycling']){if(typeof x?.[key]!=='boolean')throw Error('Neplatný přepínač Keymark');r[key]=x[key];}
 if(!Number.isFinite(x.externalPumpW)||x.externalPumpW<0||x.externalPumpW>1000)throw Error('Neplatný externí příkon');r.externalPumpW=x.externalPumpW;
 for(const group of ['lt','mt']){
  const a=x[group];if(!a)throw Error('Chybí aplikace LT/MT');
  const ranges={ratedHeat:[.01,100],ratedInput:[.01,100],ratedCop:[1,20],prated:[.01,100],scop:[1,20],eta:[0,1000],tbiv:[-40,20],tol:[-40,20],wtol:[20,90],poff:[0,1000],pto:[0,1000],psb:[0,1000],pck:[0,1000],psup:[0,100],qhe:[0,100000]};
  for(const [key,[lo,hi]] of Object.entries(ranges)){if(a[key]===null&&original[group][key]===null){r[group][key]=null;continue;}if(!Number.isFinite(a[key])||a[key]<lo||a[key]>hi)throw Error('Neplatný údaj '+key);r[group][key]=a[key];}
  if(a.tol>a.tbiv)throw Error('TOL musí být nižší nebo rovna Tbiv');
  if(!Array.isArray(a.points)||a.points.length!==original[group].points.length)throw Error('Chybí zkušební body');
  r[group].points=a.points.map((p,i)=>{if(p.air!==original[group].points[i].air||![p.water,p.heat,p.cop].every(Number.isFinite)||(p.cdh!==null&&!Number.isFinite(p.cdh))||p.water<15||p.water>90||p.heat<=0||p.heat>100||p.cop<1||p.cop>20||(p.cdh===null?original[group].points[i].cdh!==null:p.cdh<=0||p.cdh>1))throw Error('Neplatný zkušební bod');return {air:p.air,water:p.water,heat:p.heat,cop:p.cop,cdh:p.cdh};});
 }
 return r;
}
const measuredModel1325={...keymarkDatabase[0],id:'warmhouse-hm-m0-a1-keymark1325',name:'Gawliczek / Warmhouse 8,1 kW R290 Ultra tiché · HM-M0-A1',brand:'Gawliczek / Warmhouse',modelCode:'HM-M0-A1',certNo:'011-1W1325',pDesign35:5.68,pDesign55:5.63,scop35:4.73,scop55:3.56,minMod:2.3,noiseDb:'56 dB(A) LWA',compressor:'Panasonic Full Inverter (dvouvačkový R290)',refrigerant:'R290',copDhwRef:null,etaWh:null,dhwProfile:'Ve veřejném certifikátu není EN 16147',km:kmClone(keymark1325),desc:'Ověřený záznam HM-M0-A1 (řada Gawliczek R290 Ultra tiché); částečná zatížení EN 14825 oddělená od EN 14511.'};
keymarkDatabase.unshift(measuredModel1325);
state.activeModelId=measuredModel1325.id;state.activeHp=measuredModel1325;
function kmLerp(a,b,f){return a+(b-a)*Math.max(0,Math.min(1,f));}
const kmInterpolationCache=new WeakMap();
function kmAt(group,air){
 let cache=kmInterpolationCache.get(group);if(!cache){cache=new Map();kmInterpolationCache.set(group,cache);}if(cache.has(air))return cache.get(air);
 const ps=group.points;if(air<=ps[0].air)return {...ps[0]};if(air>=ps.at(-1).air)return {...ps.at(-1)};
 const b=ps.findIndex(p=>p.air>=air),p=ps[b-1],q=ps[b],f=(air-p.air)/(q.air-p.air),out={air};
 // Interpolate thermal and electric power, then derive COP; exact measured knots are retained.
 for(const key of ['heat','water','cdh'])out[key]=kmLerp(p[key]??1,q[key]??1,f);
 out.cop=out.heat/kmLerp(p.heat/p.cop,q.heat/q.cop,f);cache.set(air,out);return out;
}
function kmWaterFraction(k,water){return Math.max(0,Math.min(1,(water-35)/20));}
function kmCapacity(k,air,water=state.tFlowDesign){
 const f=kmWaterFraction(k,water),tol=kmLerp(k.lt.tol,k.mt.tol,f),wtol=kmLerp(k.lt.wtol,k.mt.wtol,f);
 if(air<tol||water>wtol)return 0;
 // Only cold-end declaration and EN14511 A7 rating are known. This envelope is an estimate.
 const curve=g=>kmLerp(g.points[0].heat,Math.max(g.ratedHeat,...g.points.map(p=>p.heat)),(air-g.points[0].air)/(7-g.points[0].air));
 return kmLerp(curve(k.lt),curve(k.mt),f);
}
function kmPartLoad(k,air,water){
 const a=kmAt(k.lt,air),b=kmAt(k.mt,air),f=Math.max(0,Math.min(1,(water-a.water)/(b.water-a.water)));
 // Outside the assumed LT/MT water bracket, a bounded model correction is used.
 const clampWater=kmLerp(a.water,b.water,f),correction=Math.max(.3,1+.02*(clampWater-water));
 return {cop:Math.max(1,kmLerp(a.cop,b.cop,f)*correction),heat:kmLerp(a.heat,b.heat,f),cdh:kmLerp(a.cdh??1,b.cdh??1,f)};
}
function kmFullLoadCop(k,air,water){
 const f=kmWaterFraction(k,water),a=kmAt(k.lt,air),a7=kmAt(k.lt,7),b=kmAt(k.mt,air),b7=kmAt(k.mt,7);
 // Cold/warm temperature shape comes from part-load tests; fixed-water full-load map is unavailable.
 const c=kmLerp(k.lt.ratedCop*a.cop/a7.cop,k.mt.ratedCop*b.cop/b7.cop,f);
 return Math.max(1,c*Math.max(.3,1+.02*(kmLerp(35,55,f)-water)));
}
function kmCop(k,air,water,heat=null,dhw=false){
 const part=kmPartLoad(k,air,water),full=kmFullLoadCop(k,air,water);
 if(dhw||!k.usePartLoad)return full;
 const cap=kmCapacity(k,air,water),blend=heat==null?0:Math.max(0,Math.min(1,(heat-part.heat)/Math.max(.01,cap-part.heat)));
 let cop=kmLerp(part.cop,full,blend);
 if(k.useCycling&&heat>0&&heat<part.heat){const ratio=heat/part.heat;cop*=ratio/(part.cdh*ratio+1-part.cdh);}
 return Math.max(1,cop);
}
const copBeforeMeasured=getCopForActiveModel,dhwCopBeforeMeasured=getCopDhwForActiveModel,capBeforeMeasured=getCapForActiveModel;
getCopForActiveModel=function(te,tf,rh,heat=null){return state.activeHp.km?kmCop(state.activeHp.km,te,tf,heat):copBeforeMeasured(te,tf,rh);};
getCopDhwForActiveModel=function(te,tf,rh){return state.activeHp.km?kmCop(state.activeHp.km,te,tf,null,true):dhwCopBeforeMeasured(te,tf,rh);};
getCapForActiveModel=function(te,tf=state.tFlowDesign){return state.activeHp.km?kmCapacity(state.activeHp.km,te,tf):capBeforeMeasured(te);};
function kmIdlePower(blocked){const k=state.activeHp.km;if(!k?.useStandby)return 0;return (blocked?k.lt.poff:k.lt.psb)/1000;}
function kmExternalPumpPower(){return state.activeHp.km?state.activeHp.km.externalPumpW/1000:.025;}
const settingsBeforeKeymark=renderSettingsHeatPump;
renderSettingsHeatPump=function(){
 const badge=document.getElementById('badge-keymark');if(badge)badge.textContent=state.activeHp.km?'Keymark: '+state.activeHp.certNo+' · '+state.activeHp.modelCode:'Původní neověřený katalog: '+state.activeHp.modelCode;
 if(!state.activeHp.km){settingsBeforeKeymark();const box=document.getElementById('settings-hp-parameters');if(box)box.insertAdjacentHTML('afterbegin','<p class="km-warning">Tento původní katalogový záznam nemá v aplikaci ověřenou úplnou sadu měření. Ověřené a neověřené části jsou uvedené zvlášť.</p>');return;}
 const select=document.getElementById('settings-hp-select'),box=document.getElementById('settings-hp-parameters');if(!select||!box)return;
 select.innerHTML=keymarkDatabase.filter(h=>h.selectable!==false).map(h=>`<option value="${esc(h.id)}">${h.km?'Ověřený zdroj · ':'Původní odhad · '}${esc(h.name)}</option>`).join('');select.value=state.activeModelId;
 const hp=state.activeHp,k=hp.km;
 const edit=(group,key,value)=>`<input aria-label="${group} ${key}" type="number" step="0.01" value="${value==null?'':Number(value.toFixed(2))}" onchange="editKmScalar('${group}','${key}',this.value)">`;
 const pointEdit=(group,index,key,value)=>`<input aria-label="${group} ${k[group].points[index].air} ${key}" type="number" step="0.01" value="${value==null?'':Number(value.toFixed(2))}" onchange="editKmPoint('${group}',${index},'${key}',this.value)">`;
 const scalarRows=[['ratedHeat','EN 14511 · tepelný výkon A7 [kW]','Výkonový bod pro odhad kapacity'],['ratedInput','EN 14511 · elektrický příkon A7 [kW]','Kontrola P/COP; při změně se přepočte COP'],['ratedCop','EN 14511 · COP A7','Pevná voda W35/W55; kotva odhadu plného zatížení'],['prated','Prated · návrhové zatížení [kW]','Referenční budova Keymark; nejde o maximum TČ'],['tbiv','Tbiv [°C]','Referenční bivalence; skutečné dotápění určí bilance domu'],['tol','TOL [°C]','Pod mezí se kompresor v modelu vypne'],['wtol','WTOL [°C]','Nad mezí vody se kompresor v modelu vypne'],['psb','PSB · pohotovost [W]','Při nečinnosti, pokud je zapnuto níže'],['poff','Poff · vypnutý stav [W]','Při blokování kompresoru, pokud je zapnuto níže'],['pto','PTO · thermostat-off [W]','Informace; tento stav není zvlášť simulován'],['pck','PCK · ohřev klikové skříně [W]','Informace; chybí podmínky sepnutí, nepřičítá se podruhé'],['psup','PSUP [kW]','Referenční doplněk EN 14825, ne příkon instalované patrony'],['scop','SCOP','Referenční sezónní výsledek; nevynucuje výsledek modelu'],['eta','ηs [%]','Referenční sezónní účinnost'],['qhe','QHE [kWh/rok]','Referenční roční elektřina pro normové podmínky']];
 box.innerHTML=`<div class="km-source"><div class="flex flex-wrap items-center justify-between gap-2"><b>${esc(k.model)} · Certifikát ${esc(k.cert)}</b><a href="${k.source||keymark1325Source}" target="_blank" rel="noopener">Ověřený veřejný záznam HP KEYMARK ↗</a></div><p>${esc(k.holder)} · ${esc(k.lab)} (${esc(k.date)}) · ${hp.userEdited?'<span class="text-amber-300 font-semibold">Vlastní úpravy hodnot</span>':'Ověřené výchozí hodnoty z certifikátu'}</p></div>
 <div class="km-summary-grid">
   <div class="km-stat-tile"><span>Výkon A7 (W35 / W55)</span><strong>${nfmt(k.lt.ratedHeat,2)} / ${nfmt(k.mt.ratedHeat,2)} kW</strong><small>COP A7: ${nfmt(k.lt.ratedCop,2)} / ${nfmt(k.mt.ratedCop,2)}</small></div>
   <div class="km-stat-tile"><span>Normový SCOP (LT / MT)</span><strong>${nfmt(k.lt.scop,2)} / ${nfmt(k.mt.scop,2)}</strong><small>Prated: ${nfmt(k.lt.prated,2)} / ${nfmt(k.mt.prated,2)} kW</small></div>
   <div class="km-stat-tile"><span>Chladivo a akustika</span><strong>${esc(k.refrigerant||hp.refrigerant)} (${nfmt(k.refrigerantKg,2)} kg)</strong><small>Akustický výkon LWA ${nfmt(k.soundPower,0)} dB(A)</small></div>
   <div class="km-stat-tile"><span>Meze provozu (TOL / WTOL)</span><strong>${nfmt(k.lt.tol,0)} °C / ${nfmt(k.lt.wtol,0)} °C</strong><small>Tbiv ${nfmt(k.lt.tbiv,0)} °C · PSB ${nfmt(k.lt.psb,0)} W</small></div>
 </div>
 <div class="config-subcard">
   <h3>⚙️ Instalační předpoklady a volby výpočtu</h3>
   <div class="two-fields"><label class="workspace-field">Minimální modulace [kW] (předpoklad)<input type="number" min="0.1" max="50" step="0.01" value="${nfmt(hp.minMod,2).replace(',','.')}" onchange="editKmMinMod(this.value)"></label><label class="workspace-field">Externí oběhové čerpadlo [W]<input type="number" min="0" max="1000" step="0.01" value="${k.externalPumpW}" onchange="editKmScalar('installation','externalPumpW',this.value)"></label></div>
   <label class="energy-check"><input type="checkbox" ${k.usePartLoad?'checked':''} onchange="editKmFlag('usePartLoad',this.checked)"> Použít body částečného zatížení EN 14825 pro odhad COP</label>
   <label class="energy-check"><input type="checkbox" ${k.useStandby?'checked':''} onchange="editKmFlag('useStandby',this.checked)"> Zahrnout klidový příkon PSB/Poff v topné sezóně</label>
   <label class="energy-check"><input type="checkbox" ${k.useCycling?'checked':''} onchange="editKmFlag('useCycling',this.checked)"> Navíc snižovat COP pod zkušebním Pdh pomocí Cdh (výchozí vypnuto)</label>
   <button class="workspace-button" onclick="selectKeymarkModel(state.activeModelId)">Obnovit ověřený soubor a výchozí předpoklady</button>
 </div>
 <details class="km-details"><summary>🔬 Zkušební body částečného zatížení EN 14825 (LT a MT tabulky)</summary>
   <p class="config-note">LT a MT jsou nízkoteplotní a středněteplotní aplikace (proměnná teplota vody). T_vody je upravitelný modelový předpoklad.</p>
   ${['lt','mt'].map(group=>`<h4>${group.toUpperCase()} · ${group==='lt'?'nízkoteplotní':'středněteplotní'} aplikace</h4><div class="km-table-scroll"><table class="km-points"><thead><tr><th>Vzduch °C</th><th>Pdh kW</th><th>COP</th><th>Cdh</th><th>Příkon kW<br>(výpočet)</th><th>T_vody °C<br>(předpoklad)</th></tr></thead><tbody>${k[group].points.map((p,i)=>`<tr><th>${nfmt(p.air,2)}${p.air===k[group].tol?' · TOL':p.air===k[group].tbiv?' · Tbiv':''}</th><td>${pointEdit(group,i,'heat',p.heat)}</td><td>${pointEdit(group,i,'cop',p.cop)}</td><td>${pointEdit(group,i,'cdh',p.cdh)}</td><td>${nfmt(p.heat/p.cop,2)}</td><td>${pointEdit(group,i,'water',p.water)}</td></tr>`).join('')}</tbody></table></div>`).join('')}
 </details>
 <details class="km-details"><summary>📋 Jmenovité hodnoty EN 14511, provozní meze a pomocné příkony</summary><div class="km-table-scroll"><table class="km-scalars"><thead><tr><th>Parametr</th><th>LT / W35</th><th>MT / W55</th><th>Použití</th></tr></thead><tbody>${scalarRows.map(([key,label,use])=>`<tr><th>${label}</th><td>${edit('lt',key,k.lt[key])}</td><td>${edit('mt',key,k.mt[key])}</td><td>${use}</td></tr>`).join('')}</tbody></table></div><p class="config-note">EN 14511: A7/W35 a A7/W55 jsou samostatné jmenovité zkoušky. Editací výkonu/příkonu se COP sjednotí; editací COP se upraví příkon.</p></details>
 ${k.dhw?`<details class="km-details"><summary>🚿 EN 16147 · TUV přesné uvedené sestavy</summary><table class="calculation-table"><tbody>${Object.entries(k.dhw).map(([label,values])=>`<tr><th>${esc(label)}</th><td>${esc(values.join(' / '))}</td></tr>`).join('')}</tbody></table><p class="config-note">Jde o zkoušku konkrétního vnitřního zásobníku. Výpočet TUV v této aplikaci používá topnou mapu s korekcí.</p></details>`:''}
 <details class="km-details"><summary>ℹ️ Metodika interpolace, omezení certifikátu a bivalence</summary><p class="km-warning">Veřejný certifikát nedokládá minimální modulaci, úplnou maximální výkonovou mapu ani přesné teploty vody každého bodu. Patrona zůstává modelem instalovaných 3 kW; PSUP ze štítku ji nenahrazuje.</p><p>Mezi venkovními teplotami se interpoluje Pdh a příkon Pdh/COP; mezi vodními teplotami LT/MT se interpoluje COP (mimo rozsah korekce 2 %/K). Pod TOL nebo nad WTOL je kapacita kompresoru nulová.</p></details>`;
};
function setKmConfig(config){
 try{const km=validateKeymarkConfig(config);state.activeHp={...state.activeHp,km,userEdited:true,pDesign35:km.lt.prated,pDesign55:km.mt.prated,scop35:km.lt.scop,scop55:km.mt.scop};recalculateSimulation();updateUI();}
 catch(e){alert(e.message);renderSettingsHeatPump();}
}
function editKmPoint(group,index,key,value){if(!['lt','mt'].includes(group)||!['heat','cop','cdh','water'].includes(key)||value==='')return;const k=kmClone(state.activeHp.km);if(!k[group].points[index])return;k[group].points[index][key]=Number(value);setKmConfig(k);}
function editKmScalar(group,key,value){if(value==='')return;const k=kmClone(state.activeHp.km),v=Number(value);if(group==='installation'&&key==='externalPumpW')k.externalPumpW=v;else if(['lt','mt'].includes(group)&&Object.hasOwn(k[group],key)&&key!=='points'){k[group][key]=v;if(['ratedHeat','ratedInput'].includes(key))k[group].ratedCop=k[group].ratedHeat/k[group].ratedInput;if(key==='ratedCop')k[group].ratedInput=k[group].ratedHeat/v;}else return;setKmConfig(k);}
function editKmFlag(key,value){if(!['usePartLoad','useStandby','useCycling'].includes(key))return;const k=kmClone(state.activeHp.km);k[key]=Boolean(value);setKmConfig(k);}
function editKmMinMod(value){const v=Number(value);if(value===''||!Number.isFinite(v)||v<.1||v>Math.min(state.activeHp.km.lt.ratedHeat,state.activeHp.km.mt.ratedHeat)){renderSettingsHeatPump();return;}state.activeHp={...state.activeHp,minMod:v,userEdited:true};recalculateSimulation();updateUI();}
const kmUiStyles=`.km-source{font-size:12px;line-height:1.6;border-left:3px solid #38bdf8;padding:10px 14px;background:rgba(14,165,233,.07);border-radius:0 8px 8px 0}.km-source p{margin:4px 0 0}.km-summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:12px 0}.km-stat-tile{background:rgba(15,23,42,.55);border:1px solid #334155;border-radius:9px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}.km-stat-tile span{font-size:11px;color:#94a3b8}.km-stat-tile strong{font-size:15px;color:#f8fafc;font-weight:700}.km-stat-tile small{font-size:10px;color:#38bdf8}.km-warning{font-size:11px;line-height:1.6;color:#fbbf24;border-left:3px solid #f59e0b;padding:8px 12px;margin:8px 0}.km-table-scroll{overflow:auto;margin:8px 0 12px}.km-points,.km-scalars{width:100%;border-collapse:collapse;font-size:11px}.km-points th,.km-points td,.km-scalars th,.km-scalars td{padding:6px 5px;border-bottom:1px solid #334155;text-align:left}.km-points input{width:72px!important;padding:4px 6px!important}.km-scalars input{width:78px!important}.km-scalars td:last-child{min-width:140px}.km-details{font-size:12px;line-height:1.6;border:1px solid #334155;border-radius:9px;background:rgba(15,23,42,.35);margin:8px 0;padding:8px 12px}.km-details summary{cursor:pointer;color:#7dd3fc;font-weight:600;padding:2px 0}.km-details p{margin:8px 0}html[data-theme=light] .km-stat-tile{background:#f8fafc;border-color:#cbd5e1}html[data-theme=light] .km-stat-tile small{color:#0284c7}html[data-theme=light] .km-details{background:#f8fafc;border-color:#cbd5e1}html[data-theme=light] .km-warning{color:#92400e}html[data-theme=light] .km-details summary{color:#0369a1}`;
const initBeforeKmStyles=init;
init=function(){const style=document.createElement('style');style.textContent=kmUiStyles;document.head.append(style);initBeforeKmStyles();};

// Compatibility fields for the old model picker; only A7/W35 and A7/W55 are fixed-water measurements.
Object.assign(measuredModel1325,{copA7W35:4.71,copA7W55:3.02,copA2W35:kmFullLoadCop(keymark1325,2,35),copA2W55:kmFullLoadCop(keymark1325,2,55),copAm7W35:kmFullLoadCop(keymark1325,-7,35),copAm7W55:kmFullLoadCop(keymark1325,-7,55),copAm15W35:kmFullLoadCop(keymark1325,-15,35),copAm15W55:kmFullLoadCop(keymark1325,-15,55)});

function keymarkOriginal(x){return [keymark1325,...additionalKeymarkData].find(k=>k.cert===x?.cert&&k.model===x?.model);}
keymark1325.source=keymark1325Source;keymark1325.climate='Average Climate';keymark1325.refrigerant='R290';
measuredModel1325.km=kmClone(keymark1325);
for(const k of additionalKeymarkData){
 const hp=keymarkDatabase.find(h=>h.id===k.id);if(!hp)continue;
 const displayName=(hp.id.startsWith('gawliczek')||hp.id.startsWith('gree'))?hp.name:(hp.brand.split(' ')[0]+' '+k.model);
 Object.assign(hp,{name:displayName,modelCode:k.model,certNo:k.cert,km:kmClone(k),pDesign35:k.lt.prated,pDesign55:k.mt.prated,scop35:k.lt.scop,scop55:k.mt.scop,refrigerant:k.refrigerant,noiseDb:k.soundPower+' dB(A) LWA',copDhwRef:null,etaWh:null,dhwProfile:'Viz přesná sestava ve zdroji',desc:hp.id.startsWith('gawliczek')?hp.desc:'HP KEYMARK – přesná sestava, průměrné klima. Kapacita a minimální modulace zůstávají modelovým předpokladem.'});
 for(const [suffix,water] of [['W35',35],['W55',55]])for(const [air,prefix] of [[7,'A7'],[2,'A2'],[-7,'Am7'],[-15,'Am15']])hp['cop'+prefix+suffix]=kmFullLoadCop(k,air,water);
}
const unidentifiedHp=keymarkDatabase.find(h=>h.id==='gawliczek-81');if(unidentifiedHp)unidentifiedHp.selectable=false;
