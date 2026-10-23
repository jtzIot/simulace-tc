const nfmt = (n, d = 0) => Number(n).toLocaleString('cs-CZ', {maximumFractionDigits: d, minimumFractionDigits: d});
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inputStateMap = {'input-qloss':'qLossDesign','input-tflow':'tFlowDesign','input-area':'floorAreaM2','input-thickness':'floorThicknessMm',
  'input-tin':'tInTarget','input-tolerance':'tTolerance','input-price':'electricityPrice','input-dhw-liters':'dhwDailyLiters',
  'input-dhw-temp':'dhwTargetTemp','input-hp-service':'hpServiceYearly','input-gas-price':'gasPrice','input-co2-price':'co2AllowancePriceEur',
  'input-gas-service':'gasBoilerServiceYearly','input-gas-eff':'gasBoilerEfficiency','input-altitude':'altitude'};
const scenarioEnums = {automationLevel:controllerLevels, heatingSystem:['floor','radiator'], floorMaterial:['beton','anhydrit'],
  floorCovering:['dlazba','vinyl','drevo'], dhwMode:['smart','standard'], economyPeriod:['season','annual']};
const extraRanges = {gasMonthlyFixed:[0,5000],elMonthlyExtra:[0,5000],summerDhwCop:[1,7],centerYear:[2016,2022],weatherBaseAltitude:[-500,5000],tExtDesign:[-30,0],lat:[-90,90],lon:[-180,180]};
const scenarioBooleans = ['dhwEnabled','etsEnabled','retainGas','isCustomWeatherLoaded'];
let savedScenarios = {};
function scenarioPayload() {
  const settings = {};
  [...Object.values(inputStateMap),...Object.keys(scenarioEnums),...Object.keys(extraRanges),...scenarioBooleans,'activeModelId','currentSeason','locationName'].forEach(k => settings[k] = state[k]);
  const seasons=getActiveSeasons(), costs=seasons.map(s=>economyFor(simResults[s].results,s));
  const r=simResults[state.currentSeason].results;
  const summary={season:state.currentSeason,period:state.economyPeriod,el:r.el_opt_kwh,under:r.comfort.opt.under,over:r.comfort.opt.over,
    cost:costs.reduce((a,c)=>a+c.hpTotal,0)/costs.length,saving:costs.reduce((a,c)=>a+c.saving,0)/costs.length};
  return {version:3, settings, summary, weather:state.isCustomWeatherLoaded ? rawWeather : null};
}
function applyScenario(payload) {
  if (payload?.version !== 3 || !payload.settings) throw Error('Nepodporovaný scénář.');
  const x = payload.settings, next = {};
  Object.entries(inputStateMap).forEach(([id,key]) => {
    const el = document.getElementById(id), v = x[key];
    if (!Number.isFinite(v) || v < Number(el.min) || v > Number(el.max)) throw Error('Neplatná hodnota: '+key);
    next[key] = v;
  });
  Object.entries(scenarioEnums).forEach(([k, values]) => {if (!values.includes(x[k])) throw Error('Neplatná volba: '+k); next[k]=x[k];});
  Object.entries(extraRanges).forEach(([k, bounds]) => {if (!Number.isFinite(x[k]) || x[k]<bounds[0] || x[k]>bounds[1]) throw Error('Neplatná hodnota: '+k); next[k]=x[k];});
  scenarioBooleans.forEach(k => {if (typeof x[k] !== 'boolean') throw Error('Neplatný přepínač: '+k); next[k]=x[k];});
  const hp = keymarkDatabase.find(h => h.id === x.activeModelId);
  if (!hp) throw Error('Model není v místním katalogu.');
  if (x.isCustomWeatherLoaded) {
    const w = payload.weather;
    if (!w || Object.keys(w).length > 30 || !Object.keys(w).length) throw Error('Chybí archiv počasí.');
    for (const [key, val] of Object.entries(w)) {
      if (!/^\d{4}-\d{4}$/.test(key) || !val || !Array.isArray(val.t) || ![5088,5112].includes(val.t.length)) throw Error('Neplatná sezóna.');
      for (const k of ['t','rh','sol']) if (!Array.isArray(val[k]) || val[k].length !== val.t.length || val[k].some(v => !Number.isFinite(v))) throw Error('Neúplné počasí.');
      if (val.t.some(v=>v < -80 || v > 60) || val.rh.some(v=>v<0 || v>100) || val.sol.some(v=>v<0 || v>20)) throw Error('Počasí mimo rozsah.');
    }
  }
  const weather = x.isCustomWeatherLoaded ? payload.weather : originalWeatherV3;
  if (!Object.hasOwn(weather, x.currentSeason)) throw Error('Sezóna není v archivu.');
  Object.assign(next,{activeHp:hp,activeModelId:hp.id,currentSeason:x.currentSeason,locationName:String(x.locationName).slice(0,100)});
  Object.assign(state,next); rawWeather = weather;
  Object.entries(inputStateMap).forEach(([id,k]) => document.getElementById(id).value=state[k]);
  document.getElementById('input-dhw-enabled').checked=state.dhwEnabled;
  onParamChange(); renderSeasonPills(); renderOverlayLegend(); updateSingleLegend();
  setAutomationLevel(state.automationLevel);
  syncReviewControls();
}
function scenarioMessage(s) {document.getElementById('scenario-status').textContent=s;}
function saveScenario(slot) {
  const payload=scenarioPayload(); savedScenarios[slot]=payload;
  try { localStorage.setItem('tc-scenario-'+slot, JSON.stringify(payload)); scenarioMessage('Scénář '+slot+' uložen v tomto prohlížeči.'); }
  catch {scenarioMessage('Scénář '+slot+' uložen pro toto otevření; trvalé úložiště není dostupné.');}
  renderScenarioComparison();
}
function restoreScenario(slot) {
  try {const payload=savedScenarios[slot] || JSON.parse(localStorage.getItem('tc-scenario-'+slot)); if(!payload) throw Error('Scénář není uložen.'); applyScenario(payload); scenarioMessage('Načten scénář '+slot+'.');}
  catch(e){scenarioMessage(e.message);}
}
function exportScenario() {
  const blob=new Blob([JSON.stringify(scenarioPayload(),null,2)],{type:'application/json'}), url=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=url; a.download='simulace-tc-scenar.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function shareScenario() {
  if(state.isCustomWeatherLoaded) {scenarioMessage('Vlastní počasí přenesete exportem JSON včetně archivu.'); return;}
  const url=new URL(location.href); url.hash='scenario='+encodeURIComponent(JSON.stringify(scenarioPayload()));
  try {await navigator.clipboard.writeText(url.href); scenarioMessage('Odkaz na scénář zkopírován.');}
  catch {document.getElementById('scenario-link').value=url.href; document.getElementById('scenario-link').hidden=false; scenarioMessage('Odkaz můžete zkopírovat z pole.');}
}
function renderScenarioComparison() {
  const box=document.getElementById('scenario-comparison'); if(!box)return;
  // Saved settings remain independently reproducible; compare the key inputs here.
  box.innerHTML=['A','B'].map(slot=>{let p=savedScenarios[slot]; try {p ||= JSON.parse(localStorage.getItem('tc-scenario-'+slot));} catch{}
    if(!p)return '<p>'+slot+': dosud neuloženo</p>'; const x=p.settings;
    const s=p.summary;
    const numbers=s&&['el','under','over','cost','saving'].every(k=>Number.isFinite(s[k]));
    return `<p><b>${slot}</b>: ${esc(x.locationName)} · ${nfmt(x.qLossDesign,1)} kW · ${esc(x.automationLevel)} · elektřina ${nfmt(x.electricityPrice,2)} / plyn ${nfmt(x.gasPrice,2)} Kč/kWh.</p>${numbers?`<p>Uloženo: sezóna ${esc(s.season)} · ${nfmt(s.el)} kWh · komfort pod/nad ${nfmt(s.under,1)}/${nfmt(s.over,1)} h. Průměr nákladů TČ ${nfmt(s.cost)} Kč a úspora proti plynu ${nfmt(s.saving)} Kč / ${s.period==='annual'?'modelový rok':'sezónu'}.</p>`:'<p>Načtením přepočtete výsledky.</p>'}`;
  }).join('');
}
function syncReviewControls() {
  ['economyPeriod','gasMonthlyFixed','elMonthlyExtra','summerDhwCop'].forEach(k=>{const e=document.getElementById('review-'+k);if(e)e.value=state[k];});
  ['etsEnabled','retainGas'].forEach(k=>{const e=document.getElementById('review-'+k);if(e)e.checked=state[k];});
  Object.entries(inputStateMap).forEach(([id])=>{const range=document.getElementById(id), input=document.getElementById(id+'-number');if(input)input.value=range.value;});
  const surcharge=state.co2AllowancePriceEur*25*0.00018*1.21;
  document.getElementById('calc-ets2-surcharge').textContent=`Scénář: +${nfmt(surcharge,2)} Kč/kWh; ${state.etsEnabled?'zahrnut':'nezahrnut'} v ekonomice.`;
  document.getElementById('input-center-year').value=state.centerYear;
  document.getElementById('select-season-window').value=state.centerYear;
}
function changeEconomy(key,value) {
  if (['etsEnabled','retainGas'].includes(key)) state[key]=Boolean(value);
  else if(key==='economyPeriod' && ['season','annual'].includes(value))state[key]=value;
  else if(Object.hasOwn(extraRanges,key)) {const v=Number(value), [lo,hi]=extraRanges[key];if(!Number.isFinite(v)||v<lo||v>hi){syncReviewControls();return;}state[key]=v;}
  recalculateSimulation(); updateUI();
}
function renderReviewSummary() {
  const r=simResults[state.currentSeason]?.results; if(!r)return;
  const seasons=getActiveSeasons();
  controllerLevels.forEach(level=>{
    const el=document.querySelector('#btn-auto-'+level+' > div:last-child');if(!el)return;
    const a=controllerResults[state.currentSeason][level], b=controllerResults[state.currentSeason].baseline;
    const saving=b.el-a.el, pct=b.el?saving/b.el*100:0;
    el.textContent=`${state.currentSeason}: úspora ${nfmt(pct,1)} % (${nfmt(saving*state.electricityPrice)} Kč) · ${a.starts} sepnutí · mimo pásmo ${nfmt(a.under+a.over)} h`;
  });
  const c= r.comfort, row=(name,x)=>`<tr><th>${name}</th><td>${nfmt(x.avg,2)}</td><td>${nfmt(x.min,2)} / ${nfmt(x.max,2)}</td><td>${nfmt(x.under,1)} / ${nfmt(x.over,1)}</td><td>${nfmt(x.degreeUnder,1)} / ${nfmt(x.degreeOver,1)}</td><td>${nfmt(x.heat)}</td><td>${nfmt(x.backup+x.dhwBackup,1)}</td></tr>`;
  document.getElementById('comfort-review').innerHTML=`<h3>Komfort a energie · ${state.currentSeason}</h3><div class="review-scroll"><table><thead><tr><th>Řízení</th><th>Průměr °C</th><th>Min / max °C</th><th>Pod / nad pásmem h</th><th>Odchylka K·h</th><th>Teplo topení kWh</th><th>Patrona vč. TUV kWh</th></tr></thead><tbody>${row('Zvolené',c.opt)}${row('Ekviterm',c.baseline)}</tbody></table></div>
    <p>Úspora vytápění: <b>${nfmt(r.el_std_heat-r.el_opt_heat)} kWh</b> · přesun TUV: <b>${nfmt(r.el_std_dhw-r.el_opt_dhw)} kWh</b>. Záporná úspora znamená vyšší spotřebu.</p>
    ${c.opt.dhwUnmet+c.baseline.dhwUnmet>0.01?`<p>⚠ Nedodaná energie TUV: zvolený režim ${nfmt(c.opt.dhwUnmet,1)} kWh / ekviterm ${nfmt(c.baseline.dhwUnmet,1)} kWh. V těchto podmínkách nestačí výkon ve vyhrazených hodinách; rozdíl spotřeby není úsporou při stejné službě.</p>`:''}
    <p>${c.opt.under+c.opt.over>0?'⚠ Zvolený režim nedodržuje komfortní pásmo po celou sezónu. Porovnejte teploty a dodané teplo.':'Komfortní pásmo je dodrženo s tolerancí měření 0,05 °C.'} Změna energie v domě: ${nfmt(c.opt.storage,1)} kWh; chyba energetické bilance ${nfmt(Math.abs(c.opt.balanceError)<0.000001?0:c.opt.balanceError,6)} kWh.</p>`;
  const costs=seasons.map(s=>economyFor(simResults[s].results,s));
  const avg=k=>costs.reduce((a,c)=>a+c[k],0)/costs.length;
  document.getElementById('decision-review').textContent=`Průměr ${seasons.length} sezón: TČ ${nfmt(avg('hpTotal'))} Kč, plyn ${nfmt(avg('gasTotal'))} Kč; úspora ${nfmt(avg('saving'))} Kč / ${state.economyPeriod==='annual'?'modelový rok':'topnou sezónu'}.`;
  const per=[-0.3,0,0.3], gasPrices=per.map(f=>state.gasPrice*(1+f)), elPrices=per.map(f=>state.electricityPrice*(1+f));
  document.getElementById('sensitivity-review').innerHTML=`<h3>Citlivost úspory proti plynu · průměr ${seasons.length} sezón</h3><p>Ceny ±30 % kolem zadání. Kladná hodnota zvýhodňuje TČ. Stejný provoz a zvolené ekonomické období; ETS 2 podle přepínače.</p><div class="review-scroll"><table><tr><th>Elektřina ↓ / plyn → Kč/kWh</th>${gasPrices.map(g=>`<th>${nfmt(g,2)}</th>`).join('')}</tr>${elPrices.map(e=>`<tr><th>${nfmt(e,2)}</th>${gasPrices.map(g=>{const v=seasons.reduce((a,s)=>a+economyFor(simResults[s].results,s,state.economyPeriod,e,g).saving,0)/seasons.length;return `<td class="${v>=0?'review-positive':'review-negative'}">${nfmt(v)} Kč</td>`;}).join('')}</tr>`).join('')}</table></div><p>Hraniční cena elektřiny: <b>${nfmt((avg('gasTotal')-avg('hpFixed'))/avg('electricity'),2)} Kč/kWh</b> při zadané ceně plynu a stejném provozu.</p>`;
  const sorted=[...seasons].sort((a,b)=>simResults[a].weather_stats.avg_temp-simResults[b].weather_stats.avg_temp);
  document.getElementById('weather-review').textContent=[['Studená',sorted[0]],['Prostřední',sorted[Math.floor(sorted.length/2)]],['Mírná',sorted.at(-1)]].map(([label,s])=>`${label}: ${s}, ${nfmt(simResults[s].weather_stats.avg_temp,1)} °C, ${nfmt(simResults[s].results.el_opt_kwh)} kWh`).join(' · ');
  syncReviewControls();
}
function renderGasComparisonView() {
  const target=document.getElementById('view-gas-container'), seasons=getActiveSeasons(); if(!target||!seasons.length)return;
  // Preserve the canvas and its existing pointer listeners across renders.
  const canvas=document.getElementById('gasComparisonCanvas');
  const annual=state.economyPeriod==='annual', unit=annual?'modelový rok':'topnou sezónu';
  const costs=seasons.map(s=>economyFor(simResults[s].results,s)), avg=k=>costs.reduce((a,c)=>a+c[k],0)/costs.length;
  target.innerHTML=`<div class="card review-panel"><h3>TČ a plynový kotel · ${unit}</h3><p>${annual?'Říjen–duben z hodinové simulace; květen–září pouze odhad TUV se zadaným COP. Nezahrnuje vytápění mimo říjen–duben.':'Říjen–duben; roční servis a paušály jsou poměrně kráceny podle délky sezóny.'} Obě varianty dodávají stejné teplo jako zvolený režim TČ.</p>
    <p><b>TČ ${nfmt(avg('hpTotal'))} Kč · plyn ${nfmt(avg('gasTotal'))} Kč · úspora ${nfmt(avg('saving'))} Kč / ${unit}</b></p>
    <p>Úspora bez ETS 2: ${nfmt(avg('saving')-avg('ets'))} Kč. Zvolený příplatek ETS 2: ${nfmt(avg('ets'))} Kč. Jde o cenový scénář, nikoli předpověď ceny.</p>
    <p>Rozdíl paušálu elektřiny ${nfmt(state.elMonthlyExtra)} Kč/měsíc · plyn ${nfmt(state.gasMonthlyFixed)} Kč/měsíc · přípojka u TČ ${state.retainGas?'zůstává':'se ruší'}. Servis TČ / kotle: ${nfmt(state.hpServiceYearly)} / ${nfmt(state.gasBoilerServiceYearly)} Kč/rok.</p>
    <div id="gas-chart-v3" style="height:280px"></div><div class="review-scroll"><table><thead><tr><th>Sezóna</th><th>Teplo vč. TUV kWh</th><th>TČ el. kWh</th><th>TČ Kč</th><th>Plyn kWh</th><th>Plyn Kč</th><th>ETS 2 Kč</th><th>Úspora Kč</th></tr></thead><tbody>${seasons.map((s,i)=>{const c=costs[i];return `<tr><th>${s}</th>${['heat','electricity','hpTotal','gasKwh','gasTotal','ets','saving'].map(k=>`<td>${nfmt(c[k])}</td>`).join('')}</tr>`;}).join('')}<tr><th>Průměr</th>${['heat','electricity','hpTotal','gasKwh','gasTotal','ets','saving'].map(k=>`<td>${nfmt(avg(k))}</td>`).join('')}</tr></tbody></table></div>
    <p>Bez investice, dotace, financování a výměn zařízení. Celkové emise nelze určit bez emisního faktoru elektřiny. Součet pěti historických sezón není předpověď budoucích pěti let.</p></div>`;
  if(canvas)document.getElementById('gas-chart-v3').appendChild(canvas);
  drawGasBarChart();
}
const originalUpdateUIV3=updateUI;
updateUI=function(){originalUpdateUIV3();renderReviewSummary();};
const originalToggleSectionV3=toggleSection;
toggleSection=function(mode,force){
  originalToggleSectionV3(mode,force);
  if(mode==='single') Array.from(document.getElementById('sec-single').children).slice(1).forEach(el=>el.classList.toggle('hidden',!state.sectionsExpanded.single));
};
const originalResetV3=resetDefaultParameters;
resetDefaultParameters=function(){Object.assign(state,{economyPeriod:'season',etsEnabled:false,retainGas:false,gasMonthlyFixed:135,elMonthlyExtra:0,summerDhwCop:2.7});originalResetV3();};
const originalDiurnalV3=updateDiurnalView;
updateDiurnalView=function(){
  originalDiurnalV3();
  const day=simResults[state.currentSeason]?.daily[state.selectedDayIndex];if(!day)return;
  const idle=day.hours.filter(h=>(h.h>=22||h.h<6)&&!h.isRunning).length;
  document.getElementById('night-explanation-v3').textContent=`V tomto dni byl kompresor bez provozu ${idle} z 8 hodin mezi 22–06 h (součet úseků téhož kalendářního dne). ${idle<8?'Ve zbývajících hodinách bylo potřeba topit nebo ohřívat TUV.':'Podlahová a stavební akumulace pokryla celé vymezené období.'}`;
  const C=simResults[state.currentSeason].results.comfort.opt.Cf;
  document.getElementById('capacity-explanation-v3').textContent=`Kapacita desky ${nfmt(C,2)} kWh/K. Rozkmit o 2 °C odpovídá ${nfmt(C*2,1)} kWh, tedy orientačně ${nfmt(C*2/state.qLossDesign,1)} h při návrhové ztrátě. Nejde o zaručenou dobu komfortu.`;
};
const originalWeatherV3=rawWeather;
const originalInitV3=init;
init=function(){
  Object.assign(state,{economyPeriod:'season',etsEnabled:false,retainGas:false,gasMonthlyFixed:135,elMonthlyExtra:0,summerDhwCop:2.7,weatherBaseAltitude:392});
  originalInitV3();
  onParamChange();
  ['single','table','dual','gas'].forEach(k=>toggleSection(k,false));
  Object.entries(inputStateMap).forEach(([id,key])=>{
    const range=document.getElementById(id), input=document.createElement('input');
    input.type='number';input.id=id+'-number';input.min=range.min;input.max=range.max;input.step=range.step;input.value=range.value;
    input.className='review-number';input.setAttribute('aria-label','Přesná hodnota: '+(range.closest('div')?.querySelector('label')?.textContent.trim()||key));
    input.onchange=()=>{const v=Number(input.value);if(input.value===''||!Number.isFinite(v)||v<Number(range.min)||v>Number(range.max)){input.value=range.value;return;}range.value=v;range.dispatchEvent(new Event('input',{bubbles:true}));syncReviewControls();};
    range.after(input);range.addEventListener('input',()=>input.value=range.value);
  });
  document.getElementById('scenario-file').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>8e6)throw Error('Soubor je příliš velký.');applyScenario(JSON.parse(await file.text()));scenarioMessage('Scénář importován.');}catch(err){scenarioMessage(err.message);}e.target.value='';};
  if(location.hash.startsWith('#scenario=')){try{applyScenario(JSON.parse(decodeURIComponent(location.hash.slice(10))));scenarioMessage('Načten sdílený scénář.');}catch(e){scenarioMessage('Odkaz nelze načíst: '+e.message);}}
  renderScenarioComparison();
};
