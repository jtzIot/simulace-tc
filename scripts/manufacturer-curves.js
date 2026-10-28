// Manufacturer tables: maximum/minimum heating output and input at W35/W45/W55.
const manufacturerCurves = {"gawliczek-pw-6":{"source":"https://ed773b3b-78d1-4b45-9d93-4ac9ec493ed7.usrfiles.com/ugd/ed773b_7729724c0e93478f9ec602e76bec1613.pdf","rows":[[[2.5,3.1,3.7,4.2,4.4,4.6,4.8,5.2,5.3,5.7,6,6.2,6.3,6.4,6.8],[1.38,1.47,1.53,1.58,1.58,1.58,1.58,1.58,1.57,1.48,1.44,1.45,1.42,1.39,1.32]],[[1,1.3,1.6,1.7,1.8,2,2.1,2.3,2.4,2.5,2.5,2.6,2.6,2.7,2.7],[0.41,0.45,0.48,0.49,0.5,0.5,0.51,0.51,0.5,0.49,0.48,0.48,0.47,0.46,0.44]],[[2.4,2.9,3.5,3.9,4.1,4.3,4.5,4.9,5,5.4,5.6,5.8,5.9,6,6.4],[1.56,1.66,1.72,1.79,1.79,1.79,1.79,1.79,1.77,1.67,1.63,1.64,1.61,1.57,1.5]],[[1,1.2,1.5,1.6,1.8,1.9,2,2.2,2.3,2.4,2.4,2.5,2.5,2.6,2.7],[0.47,0.51,0.55,0.56,0.57,0.57,0.58,0.59,0.57,0.56,0.55,0.55,0.54,0.53,0.5]],[[2.2,2.7,3.2,3.6,3.8,4,4.1,4.5,4.6,4.9,5.2,5.3,5.4,5.5,5.8],[1.71,1.82,1.89,1.96,1.96,1.96,1.96,1.96,1.95,1.83,1.79,1.8,1.76,1.72,1.64]],[[0.9,1.1,1.4,1.5,1.6,1.8,1.8,2,2.1,2.2,2.2,2.3,2.3,2.4,2.4],[0.52,0.56,0.6,0.62,0.62,0.63,0.64,0.64,0.63,0.61,0.6,0.6,0.59,0.58,0.55]]]},"gawliczek-pw-89":{"source":"https://ed773b3b-78d1-4b45-9d93-4ac9ec493ed7.usrfiles.com/ugd/ed773b_29b791735f6b497981bedbd4ca86d04c.pdf","rows":[[[3.3,4.2,5,5.5,5.9,6.4,6.8,7.7,7.9,8.5,8.9,9.2,9.3,9.5,9.8],[1.96,1.99,2.03,2.05,2.07,2.08,2.09,2.11,2.11,2.12,2.13,2.14,2.1,2.05,1.94]],[[1.7,2,2.2,2.4,2.5,2.7,2.8,3.1,3.2,3.5,3.6,3.7,3.8,3.9,4],[0.63,0.64,0.65,0.66,0.66,0.66,0.67,0.67,0.67,0.68,0.68,0.68,0.67,0.65,0.62]],[[3.2,4,4.8,5.3,5.7,6.2,6.5,7.4,7.7,8.2,8.6,8.9,9,9.2,9.4],[2.21,2.25,2.29,2.32,2.33,2.35,2.36,2.38,2.39,2.39,2.41,2.42,2.38,2.32,2.19]],[[1.6,1.9,2.2,2.3,2.4,2.6,2.7,3,3.1,3.3,3.5,3.6,3.6,3.7,3.8],[0.71,0.72,0.74,0.75,0.75,0.76,0.76,0.77,0.77,0.77,0.78,0.78,0.77,0.75,0.71]],[[2.9,3.7,4.4,4.8,5.2,5.6,6,6.7,7,7.5,7.8,8.1,8.2,8.4,8.6],[2.43,2.47,2.51,2.55,2.56,2.58,2.59,2.61,2.62,2.63,2.64,2.66,2.61,2.54,2.4]],[[1.5,1.7,2,2.1,2.2,2.4,2.5,2.7,2.8,3,3.2,3.3,3.3,3.4,3.5],[0.78,0.79,0.81,0.82,0.82,0.83,0.83,0.84,0.84,0.85,0.85,0.86,0.84,0.82,0.77]]]},"gawliczek-pw-114":{"source":"https://ed773b3b-78d1-4b45-9d93-4ac9ec493ed7.usrfiles.com/ugd/ed773b_317125f422324e348f005d2597d80492.pdf","rows":[[[4.7,5.9,7.1,7.8,8.3,9.1,9.5,10.6,10.8,11.2,11.4,11.8,12,12.2,12.5],[2.48,2.62,2.76,2.87,2.9,2.93,2.95,2.95,2.9,2.82,2.76,2.78,2.73,2.66,2.54]],[[1.8,2.3,2.8,3.1,3.3,3.6,3.7,4.2,4.2,4.4,4.5,4.7,4.7,4.8,4.9],[0.73,0.79,0.85,0.88,0.88,0.89,0.9,0.91,0.89,0.87,0.85,0.86,0.84,0.82,0.77]],[[4.4,5.6,6.7,7.4,7.9,8.6,9,10.1,10.2,10.6,10.8,11.2,11.4,11.6,11.9],[2.81,2.96,3.12,3.24,3.27,3.31,3.34,3.34,3.27,3.18,3.12,3.14,3.08,3,2.87]],[[1.8,2.2,2.7,3,3.2,3.5,3.6,4,4.1,4.3,4.3,4.5,4.6,4.6,4.8],[0.83,0.9,0.97,1,1.01,1.02,1.03,1.04,1.02,0.99,0.97,0.97,0.96,0.93,0.88]],[[4,5.1,6.1,6.7,7.1,7.8,8.1,9.1,9.2,9.6,9.8,10.2,10.3,10.5,10.8],[3.08,3.25,3.42,3.56,3.59,3.63,3.66,3.66,3.59,3.49,3.42,3.44,3.38,3.29,3.15]],[[1.6,2,2.5,2.7,2.9,3.2,3.3,3.7,3.7,3.9,4,4.1,4.2,4.2,4.4],[0.91,0.99,1.06,1.09,1.11,1.12,1.13,1.14,1.12,1.08,1.06,1.07,1.05,1.02,0.97]]]},"gawliczek-pw-148":{"source":"https://ed773b3b-78d1-4b45-9d93-4ac9ec493ed7.usrfiles.com/ugd/ed773b_e3aef9a6c9c043b2875e1eb516934431.pdf","rows":[[[5.5,6.9,8.3,9.2,9.8,10.6,11.2,12.7,13.2,14.1,14.8,15.3,15.5,15.8,16.3],[3.25,3.3,3.36,3.4,3.42,3.44,3.46,3.49,3.5,3.51,3.53,3.55,3.49,3.4,3.21]],[[2.8,3.2,3.7,3.9,4.1,4.5,4.6,5.1,5.3,5.7,5.9,6.1,6.2,6.3,6.5],[1.02,1.04,1.06,1.07,1.08,1.08,1.09,1.1,1.1,1.1,1.11,1.12,1.1,1.07,1.01]],[[5.3,6.7,8,8.8,9.4,10.3,10.9,12.3,12.7,13.7,14.3,14.8,15,15.3,15.7],[3.67,3.73,3.8,3.85,3.87,3.89,3.91,3.95,3.96,3.97,3.99,4.01,3.94,3.84,3.63]],[[2.7,3.1,3.5,3.8,4,4.3,4.5,4.9,5.1,5.5,5.7,5.9,6,6.1,6.3],[1.16,1.18,1.2,1.22,1.23,1.23,1.24,1.25,1.26,1.26,1.27,1.27,1.25,1.22,1.15]],[[4.9,6.1,7.3,8.1,8.6,9.4,9.9,11.2,11.6,12.5,13,13.5,13.7,13.9,14.3],[4.03,4.09,4.17,4.22,4.25,4.27,4.29,4.33,4.34,4.36,4.38,4.4,4.32,4.21,3.98]],[[2.4,2.8,3.2,3.4,3.6,3.9,4.1,4.5,4.7,5,5.2,5.4,5.5,5.6,5.7],[1.28,1.3,1.32,1.34,1.35,1.35,1.36,1.37,1.38,1.38,1.39,1.4,1.37,1.33,1.26]]]},"gawliczek-pw-182":{"source":"https://ed773b3b-78d1-4b45-9d93-4ac9ec493ed7.usrfiles.com/ugd/ed773b_d21e492c047743229c5e5fca48c4b6e9.pdf","rows":[[[7.5,9.4,11.3,12.4,13.2,14.5,15.1,16.9,17.2,17.8,18.2,18.9,19.1,19.5,20],[3.95,4.17,4.39,4.57,4.61,4.65,4.7,4.7,4.61,4.48,4.39,4.42,4.34,4.22,4.04]],[[3,3.7,4.5,4.9,5.2,5.7,6,6.7,6.8,7.1,7.2,7.5,7.6,7.7,7.9],[1.19,1.28,1.38,1.42,1.44,1.45,1.46,1.48,1.45,1.41,1.38,1.39,1.36,1.33,1.26]],[[7.1,8.9,10.7,11.8,12.6,13.8,14.3,16.1,16.3,16.9,17.3,17.9,18.2,18.5,19],[4.46,4.71,4.96,5.16,5.21,5.26,5.31,5.31,5.21,5.06,4.96,4.99,4.9,4.77,4.56]],[[2.8,3.6,4.3,4.7,5.1,5.5,5.8,6.5,6.6,6.8,6.9,7.2,7.3,7.4,7.6],[1.35,1.46,1.57,1.62,1.64,1.65,1.67,1.68,1.65,1.6,1.57,1.58,1.55,1.51,1.43]],[[6.4,8.1,9.7,10.7,11.4,12.5,13,14.6,14.8,15.3,15.7,16.2,16.4,16.8,17.2],[4.9,5.17,5.44,5.66,5.72,5.77,5.82,5.82,5.72,5.55,5.44,5.48,5.38,5.24,5.01]],[[2.6,3.3,3.9,4.3,4.6,5,5.3,5.9,6,6.2,6.3,6.6,6.7,6.8,7],[1.48,1.6,1.73,1.78,1.79,1.81,1.83,1.85,1.81,1.76,1.73,1.74,1.7,1.66,1.57]]]}};
for(const id of Object.keys(greeCurves)) manufacturerCurves[id]={kind:'gree'};
for (const hp of keymarkDatabase) hp.selectable = !!hp.certNo && Object.hasOwn(manufacturerCurves,hp.id);
state.activeModelId='gawliczek-pw-89';
state.activeHp=keymarkDatabase.find(h=>h.id===state.activeModelId);
const curveAir = [-25,-20,-15,-12,-10,-7,-5,0,2,5,7,10,12,15,21];
function curveLerp(axis, values, x) {
  if(x<=axis[0]) return values[0];
  if(x>=axis.at(-1)) return values.at(-1);
  const i=axis.findIndex(v=>v>=x), f=(x-axis[i-1])/(axis[i]-axis[i-1]);
  return values[i-1]+f*(values[i]-values[i-1]);
}
function manufacturerPoint(id, air, water) {
  const map=manufacturerCurves[id];
  if(!map || air < -25) return null;
  if(map.kind==='gree') return greePoint(id,air,water);
  const rows=map.rows.map(row=>row.map(values=>curveLerp(curveAir,values,air)));
  const w=bounded(water,35,55), temps=[35,45,55];
  const col=n=>curveLerp(temps,[rows[n][0],rows[n+2][0],rows[n+4][0]],w);
  const input=n=>curveLerp(temps,[rows[n][1],rows[n+2][1],rows[n+4][1]],w);
  return {max:col(0), min:col(1), pmax:input(0), pmin:input(1)};
}
function greePoint(id,air,water) {
 const m=greeCurves[id], axis=m.air, waters=Object.keys(m.water).map(Number).sort((a,b)=>a-b);
 if(air < axis[0] || air > axis.at(-1) || water > waters.at(-1)) return null;
 const w=Math.max(waters[0],water);
 function bracket(a,x) {const hi=a.findIndex(v=>v>=x); if(hi<=0)return [0,0,0];if(a[hi]===x)return [hi,hi,0];return [hi-1,hi,(x-a[hi-1])/(a[hi]-a[hi-1])];}
 const [a,b,fa]=bracket(axis,air),[c,d,fw]=bracket(waters,w);
 const interpolate=(level,col)=>{
  const value=i=>{const row=m.water[String(waters[i])][level];const x=row[a][col],y=row[b][col];return x===null||(b!==a&&fa>0&&y===null)?null:x+(y-x)*fa;};
  const x=value(c),y=value(d);return x===null||(d!==c&&fw>0&&y===null)?null:x+(y-x)*fw;
 };
 const vals=[interpolate('max',0),interpolate('min',0),interpolate('max',1),interpolate('min',1)];
 if(vals.some(v=>v===null)) return null;
 return {max:vals[0],min:vals[1],pmax:vals[2],pmin:vals[3]};
}
const capacityBeforeCurves=getCapForActiveModel, copBeforeCurves=getCopForActiveModel, dhwBeforeCurves=getCopDhwForActiveModel;
getCapForActiveModel=function(air,water=state.tFlowDesign) {
  if(!manufacturerCurves[state.activeModelId]) return capacityBeforeCurves(air,water);
  return manufacturerPoint(state.activeModelId,air,water)?.max ?? 0;
};
getCopForActiveModel=function(air,water,rh,heat=null) {
  if(!manufacturerCurves[state.activeModelId]) return copBeforeCurves(air,water,rh,heat);
  const p=manufacturerPoint(state.activeModelId,air,water);
  if(!p) return 1;
  const q=bounded(heat??p.max,p.min,p.max), f=p.max>p.min?(q-p.min)/(p.max-p.min):1;
  return q/(p.pmin+f*(p.pmax-p.pmin));
};
getCopDhwForActiveModel=function(air,water,rh) {
  if(!manufacturerCurves[state.activeModelId]) return dhwBeforeCurves(air,water,rh);
  return getCopForActiveModel(air,water,rh);
};
const settingsBeforeCurves=renderSettingsHeatPump;
renderSettingsHeatPump=function() {
  const map=manufacturerCurves[state.activeModelId], box=document.getElementById('settings-hp-parameters');
  if(map?.kind==='gree'&&!state.activeHp.km) {
   const hp=state.activeHp,select=document.getElementById('settings-hp-select');
   if(select){select.innerHTML=keymarkDatabase.filter(h=>h.selectable).map(h=>`<option value="${esc(h.id)}">${esc(h.name)}</option>`).join('');select.value=hp.id;}
   const badge=document.getElementById('badge-keymark');if(badge)badge.textContent='Keymark: '+hp.certNo+' · '+hp.modelCode;
   if(box)box.innerHTML=`<p class="km-source"><a href="${hp.certSource}" target="_blank" rel="noopener">HP KEYMARK ${hp.certNo} · ${esc(hp.modelCode)}</a></p><p>EN 14511 A7/W35 COP ${hp.copA7W35}; A7/W55 COP ${hp.copA7W55}. Normová sezónní data nejsou v aplikaci doplněna.</p>`;
  } else settingsBeforeCurves();
  if(map&&box) box.insertAdjacentHTML('afterbegin',map.kind==='gree'?'<p class="km-warning">Výkon a příkon: manuál Gree Versati V, tabulky vytápění, strany 10–13. Rozsah −25 až +35 °C; pod 25 °C vody je použita hodnota pro 25 °C. Chybějící kombinace teplot jsou nedostupné; TUV je odhad z topné mapy.</p>':`<p class="km-warning">Výpočet používá <a href="${map.source}" target="_blank" rel="noopener">výkonové tabulky výrobce</a> pro −25 až +21 °C, vodu 35–55 °C a minimální až maximální výkon. Mimo rozsah vody se použije nejbližší tabulková teplota; pod −25 °C se kompresor vypne. TUV je odhad z topné mapy.</p>`);
};
