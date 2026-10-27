const nfmt = (n, d = 0) => Number(n).toLocaleString('cs-CZ', {maximumFractionDigits: Math.min(2,d), minimumFractionDigits: Math.min(2,d)});
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inputStateMap = {'input-qloss':'qLossDesign','input-tflow':'tFlowDesign','input-area':'floorAreaM2','input-thickness':'floorThicknessMm',
  'input-tin':'tInTarget','input-tolerance':'tTolerance','input-price':'electricityPrice','input-dhw-liters':'dhwDailyLiters',
  'input-dhw-temp':'dhwTargetTemp','input-hp-service':'hpServiceYearly','input-gas-price':'gasPrice','input-co2-price':'co2AllowancePriceEur',
  'input-gas-service':'gasBoilerServiceYearly','input-gas-eff':'gasBoilerEfficiency','input-altitude':'altitude'};
const scenarioEnums = {automationLevel:['optimized'], heatingSystem:['floor','radiator'], floorMaterial:['beton','anhydrit'],
  floorCovering:['dlazba','vinyl','drevo'], dhwMode:['smart','standard'], economyPeriod:['season','annual','decade']};
const extraRanges = {gasMonthlyFixed:[0,5000],elMonthlyExtra:[-100000,100000],summerDhwCop:[1,7],centerYear:[1960,2026],weatherBaseAltitude:[-500,5000],tExtDesign:[-30,0],lat:[-90,90],lon:[-180,180]};
const scenarioBooleans = ['dhwEnabled','etsEnabled','retainGas','isCustomWeatherLoaded'];
let savedScenarios = {};
function scenarioPayload() {
  const settings = {};
  [...Object.values(inputStateMap),...Object.keys(scenarioEnums),...Object.keys(extraRanges),...scenarioBooleans,'activeModelId','currentSeason','locationName'].forEach(k => settings[k] = state[k]);
  settings.gasDhwEfficiency = state.gasDhwEfficiency ?? 86;
  settings.gasBoilerModel = state.gasBoilerModel || 'Protherm Gepard Condens 12 MKO';
  const seasons=getActiveSeasons(), costs=seasons.map(s=>economyFor(simResults[s].results,s));
  const r=simResults[state.currentSeason].results;
  const summary={season:state.currentSeason,period:state.economyPeriod,el:r.el_opt_kwh,under:r.comfort.opt.under,over:r.comfort.opt.over,
    cost:costs.reduce((a,c)=>a+c.hpTotal,0)/costs.length,saving:costs.reduce((a,c)=>a+c.saving,0)/costs.length};
  return {version:3, settings, summary, energy:state.energy, control:state.control||defaultControl(), heatPump:state.activeHp.km?{km:state.activeHp.km,minMod:state.activeHp.minMod,userEdited:!!state.activeHp.userEdited}:null, weather:state.isCustomWeatherLoaded ? rawWeather : null};
}
function applyScenario(payload) {
  if (payload?.version !== 3 || !payload.settings) throw Error('Nepodporovaný scénář.');
  const x = {...payload.settings}, next = {};
  // Old saved controller variants migrate to the single daytime mode.
  if (['baseline','timer','sgready','predictive'].includes(x.automationLevel)) x.automationLevel='optimized';
  Object.entries(inputStateMap).forEach(([id,key]) => {
    const el = document.getElementById(id), v = x[key];
    if (!Number.isFinite(v) || v < Number(el.min) || v > Number(el.max)) throw Error('Neplatná hodnota: '+key);
    next[key] = v;
  });
  Object.entries(scenarioEnums).forEach(([k, values]) => {if (!values.includes(x[k])) throw Error('Neplatná volba: '+k); next[k]=x[k];});
  Object.entries(extraRanges).forEach(([k, bounds]) => {if(['lat','lon'].includes(k)&&x[k]===null&&!x.isCustomWeatherLoaded){next[k]=null;return;}if (!Number.isFinite(x[k]) || x[k]<bounds[0] || x[k]>bounds[1]) throw Error('Neplatná hodnota: '+k); next[k]=x[k];});
  scenarioBooleans.forEach(k => {if (typeof x[k] !== 'boolean') throw Error('Neplatný přepínač: '+k); next[k]=x[k];});
  if (x.gasDhwEfficiency !== undefined) {
    if (!Number.isFinite(x.gasDhwEfficiency) || x.gasDhwEfficiency < 50 || x.gasDhwEfficiency > 100) throw Error('Neplatná účinnost TUV kotle.');
    next.gasDhwEfficiency = x.gasDhwEfficiency;
  }
  if (typeof x.gasBoilerModel === 'string') next.gasBoilerModel = x.gasBoilerModel.slice(0, 120);
  const hp = keymarkDatabase.find(h => h.id === x.activeModelId);
  if (!hp) throw Error('Model není v místním katalogu.');
  if (x.isCustomWeatherLoaded) {
    const w = payload.weather;
    if (!w || Object.keys(w).length > 80 || !Object.keys(w).length) throw Error('Chybí archiv počasí.');
    for (const [key, val] of Object.entries(w)) {
      if (!/^\d{4}-\d{4}$/.test(key) || !val || !Array.isArray(val.t) || ![5088,5112].includes(val.t.length)) throw Error('Neplatná sezóna.');
      for (const k of ['t','rh','sol']) if (!Array.isArray(val[k]) || val[k].length !== val.t.length || val[k].some(v => !Number.isFinite(v))) throw Error('Neúplné počasí.');
      if (val.t.some(v=>v < -80 || v > 60) || val.rh.some(v=>v<0 || v>100) || val.sol.some(v=>v<0 || v>20)) throw Error('Počasí mimo rozsah.');
    }
  }
  const weather = x.isCustomWeatherLoaded ? payload.weather : originalWeatherV3;
  if (!Object.hasOwn(weather, x.currentSeason)) throw Error('Sezóna není v archivu.');
  Object.assign(next,{activeHp:hp,activeModelId:hp.id,currentSeason:x.currentSeason,locationName:String(x.locationName).slice(0,100)});
  if(payload.control){const c={...payload.control,policy:migrateControlPolicy(payload.control.policy)};if(!['day','tariff','constant'].includes(c.policy)||!Number.isInteger(c.dayStart)||!Number.isInteger(c.dayEnd)||c.dayStart<0||c.dayEnd>24||c.dayStart>=c.dayEnd||!Number.isFinite(c.setback)||c.setback<0||c.setback>1||typeof c.blockCompressor!=='boolean')throw Error('Neplatné řízení.');next.control={...defaultControl(),...c};}else next.control=defaultControl();
  if(payload.heatPump){if(!hp.km)throw Error('Neshoda měřeného modelu.');const saved=payload.heatPump;if(saved.km?.cert!==hp.km.cert||saved.km?.model!==hp.km.model)throw Error('Neshoda certifikátu a sestavy.');if(!Number.isFinite(saved.minMod)||saved.minMod<.1||saved.minMod>Math.min(saved.km?.lt?.ratedHeat??0,saved.km?.mt?.ratedHeat??0))throw Error('Neplatná minimální modulace.');next.activeHp={...hp,km:validateKeymarkConfig(saved.km),minMod:saved.minMod,userEdited:!!saved.userEdited};}
  if(payload.energy) next.energy=validateEnergyConfig(payload.energy);
  else if(state.energy) {next.energy={...defaultEnergyConfig(),custom:true,supplyVT:x.electricityPrice,distributionVT:0,electricityTax:0,systemServices:0,poze:0,gasSupply:x.gasPrice,gasDistribution:0,gasOTE:0,gasSupplyFixed:x.gasMonthlyFixed,gasDistributionFixed:0,existingConnection:true,includeOtherFixed:true,supplyFixed:x.elMonthlyExtra,networkFixed:0};}
  Object.assign(state,next); rawWeather = weather;
  Object.entries(inputStateMap).forEach(([id,k]) => document.getElementById(id).value=state[k]);
  document.getElementById('input-dhw-enabled').checked=state.dhwEnabled;
  const gasModelEl = document.getElementById('gas-boiler-model');
  if (gasModelEl && state.gasBoilerModel) gasModelEl.value = state.gasBoilerModel;
  onParamChange(); renderSeasonPills(); renderOverlayLegend(); updateSingleLegend();
  setAutomationLevel(state.automationLevel);
  syncReviewControls();
}
function scenarioMessage(s) {const el=document.getElementById('scenario-status');if(el)el.textContent=s;}
function saveScenario(slot) {
  const payload=scenarioPayload(); savedScenarios[slot]=payload;
  try { localStorage.setItem('tc-scenario-'+slot, JSON.stringify(payload)); scenarioMessage('Scénář '+slot+' uložen v tomto prohlížeči.'); }
  catch {scenarioMessage('Scénář '+slot+' uložen pro toto otevření; trvalé úložiště není dostupné.');}
  renderScenarioComparison();
}
function restoreScenario(slot) {
  try {const payload=savedScenarios[slot] || JSON.parse(localStorage.getItem('tc-scenario-'+slot)); if(!payload) throw Error('Scénář '+slot+' zatím není uložen.'); applyScenario(payload); scenarioMessage('Načten scénář '+slot+'.');}
  catch(e){scenarioMessage(e.message);}
}
function exportScenario() {
  const blob=new Blob([JSON.stringify(scenarioPayload(),null,2)],{type:'application/json'}), url=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=url; a.download='simulace-tc-scenar.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function shareScenario() {
  if(state.isCustomWeatherLoaded) {scenarioMessage('Vlastní počasí přenesete exportem JSON včetně archivu.'); return;}
  const url=new URL(location.href); url.hash='scenario='+encodeURIComponent(JSON.stringify(scenarioPayload()));
  try {await navigator.clipboard.writeText(url.href); scenarioMessage('Odkaz na scénář zkopírován do schránky.');}
  catch {const linkEl=document.getElementById('scenario-link');if(linkEl){linkEl.value=url.href;linkEl.hidden=false;} scenarioMessage('Odkaz můžete zkopírovat z pole.');}
}
function renderScenarioComparison() {
  const box=document.getElementById('scenario-comparison'); if(!box)return;
  box.innerHTML=['A','B'].map(slot=>{let p=savedScenarios[slot]; try {p ||= JSON.parse(localStorage.getItem('tc-scenario-'+slot));} catch{}
    if(!p)return `<div class="scenario-slot-empty"><b>Scénář ${slot}:</b> dosud neuloženo</div>`; const x=p.settings;
    const s=p.summary;
    const numbers=s&&['el','under','over','cost','saving'].every(k=>Number.isFinite(s[k]));
    return `<div class="scenario-slot-item"><b>Scénář ${slot}:</b> ${esc(x.locationName)} · ${nfmt(x.qLossDesign,1)} kW · ${esc(p.energy?.tariff||'D25d')}${numbers?` · TČ <strong>${nfmt(s.cost)} Kč</strong> (úspora ${nfmt(s.saving)} Kč / ${s.period==='annual'?'rok':'sezónu'}, ${nfmt(s.el)} kWh)`:''}</div>`;
  }).join('');
}
function syncReviewControls() {
  ['economyPeriod','gasMonthlyFixed','elMonthlyExtra','summerDhwCop'].forEach(k=>{const e=document.getElementById('review-'+k);if(e)e.value=state[k];});
  ['etsEnabled','retainGas'].forEach(k=>{const e=document.getElementById('review-'+k);if(e)e.checked=state[k];});
  Object.entries(inputStateMap).forEach(([id])=>{const range=document.getElementById(id), input=document.getElementById(id+'-number');if(input)input.value=range.value;});
  const surcharge=state.co2AllowancePriceEur*25*0.00018*1.21;
  document.getElementById('calc-ets2-surcharge').textContent=`Scénář: +${nfmt(surcharge,2)} Kč/kWh; ${state.etsEnabled?'zahrnut':'nezahrnut'} v ekonomice.`;
  document.getElementById('input-center-year').value=state.centerYear;
  const selWin=document.getElementById('select-season-window');
  if(selWin){
    let opt=selWin.querySelector(`option[value="${state.centerYear}"]`);
    if(!opt){
      opt=selWin.querySelector('option[data-custom="1"]');
      if(!opt){opt=document.createElement('option');opt.dataset.custom='1';selWin.prepend(opt);}
      const sList=getActiveSeasons();
      opt.value=String(state.centerYear);
      opt.textContent=`Okolo roku ${state.centerYear} (${sList[0]?.slice(0,4)||''}–${sList.at(-1)?.slice(5)||''})`;
    }
    selWin.value=String(state.centerYear);
  }
}
function changeEconomy(key,value) {
  if (['etsEnabled','retainGas'].includes(key)) state[key]=Boolean(value);
  else if(key==='economyPeriod' && ['season','annual','decade'].includes(value))state[key]=value==='season'?'decade':value;
  else if(Object.hasOwn(extraRanges,key)) {const v=Number(value), [lo,hi]=extraRanges[key];if(!Number.isFinite(v)||v<lo||v>hi){syncReviewControls();return;}state[key]=v;}
  if(typeof recalculateEconomy==='function')recalculateEconomy();
  else recalculateSimulation();
  updateUI();
}
function renderReviewSummary() {
  const r=simResults[state.currentSeason]?.results; if(!r)return;
  controllerLevels.forEach(level=>{
    const el=document.querySelector('#btn-auto-'+level+' > div:last-child');if(!el)return;
    const a=controllerResults[state.currentSeason][level], b=controllerResults[state.currentSeason].baseline;
    const saving=b.el-a.el, pct=b.el?saving/b.el*100:0;
    el.textContent=`${state.currentSeason}: úspora ${nfmt(pct,1)} % (${nfmt(simResults[state.currentSeason].results.savings_czk)} Kč) · ${a.starts} sepnutí · mimo pásmo ${nfmt(a.under+a.over)} h`;
  });
  syncReviewControls();
}
function renderGasComparisonView() {
  const target=document.getElementById('view-gas-container'), seasons=getActiveSeasons(); if(!target||!seasons.length)return;
  // Preserve the canvas and its existing pointer listeners across renders.
  const canvas=document.getElementById('gasComparisonCanvas');
  const annual=true, isDecade=state.economyPeriod!=='annual', unit=isDecade?'průměr desetiletí':'modelový rok';
  const costs=seasons.map(s=>economyFor(simResults[s].results,s)), avg=k=>costs.reduce((a,c)=>a+c[k],0)/costs.length;
  target.innerHTML=`<div class="card review-panel"><h3>TČ a plynový kotel · ${unit}</h3><p>${annual?'Říjen–duben z hodinové simulace; květen–září pouze odhad TUV se zadaným COP. Nezahrnuje vytápění mimo říjen–duben.':'Říjen–duben; roční servis a paušály jsou poměrně kráceny podle délky sezóny.'} Obě varianty dodávají stejné teplo jako zvolený režim TČ.</p>
    <p><b>TČ ${nfmt(avg('hpTotal'))} Kč · plyn ${nfmt(avg('gasTotal'))} Kč · úspora ${nfmt(avg('saving'))} Kč / ${unit}</b></p>
    <p>Úspora bez ETS 2: ${nfmt(avg('saving')-avg('ets'))} Kč. Zvolený příplatek ETS 2: ${nfmt(avg('ets'))} Kč. Jde o cenový scénář, nikoli předpověď ceny.</p>
    <p>Započtené stálé platby elektřiny ${nfmt(state.elMonthlyExtra)} Kč/měsíc · plyn ${nfmt(state.gasMonthlyFixed)} Kč/měsíc · přípojka u TČ ${state.retainGas?'zůstává':'se ruší'}. Servis TČ / kotle: ${nfmt(state.hpServiceYearly)} / ${nfmt(state.gasBoilerServiceYearly)} Kč/rok.</p>
    <div id="gas-chart-v3" style="height:280px"></div><div class="review-scroll"><table><thead><tr><th>Sezóna</th><th>Teplo vč. TUV kWh</th><th>TČ el. kWh</th><th>TČ Kč</th><th>Plyn kWh</th><th>Plyn Kč</th><th>ETS 2 Kč</th><th>Úspora Kč</th></tr></thead><tbody>${seasons.map((s,i)=>{const c=costs[i];return `<tr><th>${s}</th>${['heat','electricity','hpTotal','gasKwh','gasTotal','ets','saving'].map(k=>`<td>${nfmt(c[k])}</td>`).join('')}</tr>`;}).join('')}<tr><th>Průměr</th>${['heat','electricity','hpTotal','gasKwh','gasTotal','ets','saving'].map(k=>`<td>${nfmt(avg(k))}</td>`).join('')}</tr></tbody></table></div>
    <p>Bez investice, dotace, financování a výměn zařízení. Celkové emise nelze určit bez emisního faktoru elektřiny. Průměr ${seasons.length} historických sezón není předpověď budoucího vývoje.</p></div>`;
  if(canvas)document.getElementById('gas-chart-v3').appendChild(canvas);
  drawGasBarChart();
}
const originalUpdateUIV3=updateUI;
updateUI=function(){originalUpdateUIV3();renderReviewSummary();renderGasOverview();renderSettingsHeatPump();renderLiveCosts();};
const originalToggleSectionV3=toggleSection;
toggleSection=function(mode,force){
  originalToggleSectionV3(mode,force);
  if(mode==='single') Array.from(document.getElementById('sec-single').children).slice(1).forEach(el=>el.classList.toggle('hidden',!state.sectionsExpanded.single));
};
const originalResetV3=resetDefaultParameters;
resetDefaultParameters=function(){Object.assign(state,{economyPeriod:'annual',centerYear:2022,etsEnabled:true,retainGas:false,gasMonthlyFixed:135,elMonthlyExtra:0,summerDhwCop:2.7});originalResetV3();};
const originalDiurnalV3=updateDiurnalView;
updateDiurnalView=function(){
  originalDiurnalV3();
  const day=simResults[state.currentSeason]?.daily[state.selectedDayIndex];if(!day)return;
  const idle=day.hours.filter(h=>(h.h>=22||h.h<6)&&!h.isRunning).length;
  document.getElementById('night-explanation-v3').textContent=`V tomto dni byl kompresor bez provozu ${idle} z 8 hodin mezi 22–06 h (součet úseků téhož kalendářního dne). ${idle<8?'Ve zbývajících hodinách bylo potřeba topit nebo ohřívat TUV.':'Podlahová a stavební akumulace pokryla celé vymezené období.'}`;
  const C=simResults[state.currentSeason].results.comfort.opt.Cf;
  document.getElementById('capacity-explanation-v3').textContent=`Kapacita desky ${nfmt(C,2)} kWh/K. Nastavený pokles o ${nfmt(state.tTolerance,1)} °C odpovídá ${nfmt(C*state.tTolerance,1)} kWh, tedy orientačně ${nfmt(C*state.tTolerance/state.qLossDesign,1)} h při návrhové ztrátě. Nejde o zaručenou dobu komfortu.`;
};
let lastSimPhysicalKey='';
function getPhysicalSimulationKey(){
  const elVal=(id,def)=>(typeof document?.getElementById==='function'?document.getElementById(id)?.value:undefined)??def;
  const elChk=(id,def)=>(typeof document?.getElementById==='function'?document.getElementById(id)?.checked:undefined)??def;
  return [
    state.heatingSystem,
    state.floorMaterial,
    state.floorCovering,
    state.dhwMode,
    state.activeModelId||state.activeHp?.id,
    parseFloat(elVal('input-qloss',state.qLossDesign)),
    parseFloat(elVal('input-tflow',state.tFlowDesign)),
    parseFloat(elVal('input-area',state.floorAreaM2)),
    parseInt(elVal('input-thickness',state.floorThicknessMm)),
    parseFloat(elVal('input-tin',state.tInTarget)),
    parseFloat(elVal('input-tolerance',state.tTolerance)),
    Boolean(elChk('input-dhw-enabled',state.dhwEnabled)),
    parseFloat(elVal('input-dhw-liters',state.dhwDailyLiters)),
    parseFloat(elVal('input-dhw-temp',state.dhwTargetTemp)),
    state.altitude,
    JSON.stringify(state.control||{})
  ].join('|');
}
const origRecalcSimV3=recalculateSimulation;
recalculateSimulation=function(){
  origRecalcSimV3();
  lastSimPhysicalKey=getPhysicalSimulationKey();
};
const originalWeatherV3=rawWeather;
const originalOnParamChangeV3=onParamChange;
onParamChange=function(){
  const currentKey=getPhysicalSimulationKey();
  const physSame=lastSimPhysicalKey!==''&&currentKey===lastSimPhysicalKey&&Object.keys(simResults||{}).length>0;
  if(physSame&&typeof recalculateEconomy==='function'){
    const savedRecalc=recalculateSimulation;
    recalculateSimulation=recalculateEconomy;
    try{originalOnParamChangeV3();}finally{recalculateSimulation=savedRecalc;}
  }else{
    originalOnParamChangeV3();
  }
};
const originalInitV3=init;
init=function(){
  Object.assign(state,{economyPeriod:'annual',centerYear:2022,etsEnabled:true,retainGas:false,gasMonthlyFixed:135,elMonthlyExtra:0,summerDhwCop:2.7,weatherBaseAltitude:211,gasBoilerModel:'Protherm Gepard Condens 12 MKO'});
  originalInitV3();
  onParamChange();
  ['single','table','dual','gas'].forEach(k=>toggleSection(k,false));
  Object.entries(inputStateMap).forEach(([id,key])=>{
    const range=document.getElementById(id), input=document.createElement('input');
    input.type='number';input.id=id+'-number';input.min=range.min;input.max=range.max;input.step=range.step;input.value=range.value;
    input.className='review-number';input.setAttribute('aria-label','Přesná hodnota: '+(range.closest('div')?.querySelector('label')?.textContent.trim()||key));
    input.onchange=()=>{const v=Number(input.value);if(input.value===''||!Number.isFinite(v)||v<Number(range.min)||v>Number(range.max)){input.value=range.value;return;}range.value=v;range.dispatchEvent(new Event('input',{bubbles:true}));syncReviewControls();};
    const row=document.createElement('div');row.className='slider-input-row';
    range.before(row);row.append(range,input);
    range.addEventListener('input',()=>input.value=range.value);
  });
  const scenarioFile=document.getElementById('scenario-file');
  if(scenarioFile)scenarioFile.onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>8e6)throw Error('Soubor je příliš velký.');applyScenario(JSON.parse(await file.text()));scenarioMessage('Scénář importován.');}catch(err){scenarioMessage(err.message);}e.target.value='';};
  if(location.hash.startsWith('#scenario=')){try{applyScenario(JSON.parse(decodeURIComponent(location.hash.slice(10))));scenarioMessage('Načten sdílený scénář.');}catch(e){scenarioMessage('Odkaz nelze načíst: '+e.message);}}
  renderScenarioComparison();
};

function renderGasOverview() {
  const target=document.getElementById('gas-overview');if(!target)return;
  const seasons=getActiveSeasons();if(!seasons.length)return;
  const costs=seasons.map(s=>economyFor(simResults[s].results,s));
  const avg=k=>costs.reduce((a,c)=>a+c[k],0)/costs.length;
  const saving=avg('saving'), unit=state.economyPeriod==='annual'?'modelový rok':'topnou sezónu';
  target.innerHTML=`<h2 class="text-xl font-bold text-white mb-2">Tepelné čerpadlo vs. plyn</h2>
    <p class="text-xs text-slate-400 mb-3">Průměr ${seasons.length} sezón · ${seasons[0]} až ${seasons.at(-1)} · stejné dodané teplo včetně TUV</p>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div><span class="text-sky-300">Tepelné čerpadlo</span><div class="text-2xl font-bold">${nfmt(avg('hpTotal'))} Kč</div></div>
      <div><span class="text-amber-300">Plynový kotel</span><div class="text-2xl font-bold">${nfmt(avg('gasTotal'))} Kč</div></div>
      <div><span>${saving>=0?'Úspora s TČ':'Vyšší náklady TČ'}</span><div class="text-2xl font-bold">${nfmt(Math.abs(saving))} Kč</div></div>
    </div><p class="text-xs text-slate-400 mt-3">Za ${unit}, včetně započtených paušálů a servisu. ETS 2 ${state.etsEnabled?'zahrnuto':'vypnuto'}. Bez investičních nákladů.</p>
    <button class="energy-button mt-3" onclick="toggleSection('gas',true);document.getElementById('sec-gas').scrollIntoView({behavior:'smooth'})">Podrobné srovnání s plynem ↓</button>`;
}

function renderSettingsHeatPump() {
  const select=document.getElementById('settings-hp-select'), box=document.getElementById('settings-hp-parameters');
  if(!select||!box)return;
  const hp=state.activeHp;
  const options=keymarkDatabase.filter(h=>h.selectable!==false).map(h=>`<option value="${esc(h.id)}">${esc(h.name)}</option>`).join('');
  if(select.dataset.options!==options){select.innerHTML=options;select.dataset.options=options;}
  select.value=state.activeModelId;
  const val=(v,d=2)=>Number.isFinite(v)?nfmt(v,d):'Neuvedeno';
  const edit=(key,label)=>`<input aria-label="${label}" type="number" min="${key.startsWith('cop')?1.2:0.1}" max="${key.startsWith('cop')?10:50}" step="0.01" value="${Number(hp[key].toFixed(2))}" class="review-number" onchange="editHeatPump('${key}',this.value)">`;
  const rows=[['+7','A7'],['+2','A2'],['−7','Am7'],['−15','Am15']];
  box.innerHTML=`<div class="review-scroll"><table class="w-full text-sm text-left"><thead><tr><th>Venkovní teplota</th><th>COP · voda 35 °C</th><th>COP · voda 55 °C (radiátory)</th></tr></thead><tbody>
    ${rows.map(([temp,key])=>`<tr><th>${temp} °C</th><td>${edit('cop'+key+'W35','COP A'+temp+' W35')}</td><td>${edit('cop'+key+'W55','COP A'+temp+' W55')}</td></tr>`).join('')}
    <tr><th>SCOP · sezónní údaj v databázi</th><td>${val(hp.scop35)}</td><td>${val(hp.scop55)}</td></tr>
    <tr><th>Návrhový výkon</th><td>${edit('pDesign35','Výkon pro vodu 35 °C')} kW</td><td>${edit('pDesign55','Výkon pro vodu 55 °C')} kW</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">Minimální modulovaný tepelný výkon: <b>${edit('minMod','Minimální modulovaný výkon')} kW</b> · Referenční COP TUV: <b>${val(hp.copDhwRef)}</b> · Profil TUV: <b>${esc(hp.dhwProfile||'Neuvedeno')}</b></p>
    <button class="text-xs text-sky-300 underline mt-2" onclick="selectKeymarkModel(state.activeModelId)">Obnovit parametry vybraného modelu</button><p class="text-xs text-amber-300 mt-2">${hp.userEdited?'Vlastní úpravy parametrů čerpadla':'Výchozí parametry databáze'}</p><p class="text-sm mt-2">Chladivo: ${esc(hp.refrigerant||'Neuvedeno')} · Model: ${esc(hp.modelCode||hp.name)}</p>
    <p class="text-xs text-slate-400 mt-2">COP, návrhové výkony a minimální modulaci lze upravit; změny ihned přepočítají spotřebu i náklady. SCOP a údaje TUV jsou informativní údaje databáze. Výběrem modelu se obnoví jeho původní parametry. COP je okamžitá účinnost při uvedené venkovní teplotě a teplotě vody; SCOP je sezónní údaj. Simulace z těchto bodů odvozuje COP podle počasí a teploty vody. Výše uvedený SCOP není výsledkem simulace.</p>
    <p class="text-xs text-sky-300 mt-2">Aktuální soustava: ${state.heatingSystem==='radiator'?'radiátory · křivka pro vodu 55 °C':'podlaha · křivka pro vodu 35 °C'}. Návrhová teplota vody ${val(state.tFlowDesign,1)} °C. Soustavu a teplotu vody nastavíte v záložce Nastavení domu.</p>`;
}

const editableHpKeys=['copA7W35','copA2W35','copAm7W35','copAm15W35','copA7W55','copA2W55','copAm7W55','copAm15W55','pDesign35','pDesign55','minMod'];
function editHeatPump(key,value) {
  if(!editableHpKeys.includes(key))return;
  const v=Number(value), cop=key.startsWith('cop');
  if(value===''||!Number.isFinite(v)||v<(cop?1.2:0.1)||v>(cop?10:50)){renderSettingsHeatPump();return;}
  const next={...state.activeHp,[key]:v,userEdited:true};
  if(next.minMod>Math.min(next.pDesign35,next.pDesign55)){alert('Minimální výkon nesmí překročit návrhový výkon.');renderSettingsHeatPump();return;}
  state.activeHp=next;recalculateSimulation();updateUI();
}
let costReference=null;
function currentCostSnapshot(){
 const isDecade=state.economyPeriod!=='annual';
 const allActive=getActiveSeasons();
 const seasons=isDecade?allActive:[state.currentSeason||allActive[Math.floor(allActive.length/2)]||'2022-2023'];
 const costs=seasons.map(s=>economyFor(simResults[s].results,s,'annual'));
 const avg=k=>costs.reduce((a,c)=>a+c[k],0)/(costs.length||1), p=energyPrices(state.energy);
 const seasonalFactor=avg('fraction'), household=householdEconomy(state.energy,seasonalFactor);
 const fullHpBreaker=(state.energy.breakerFixed||0)*12*seasonalFactor;
 const fullGasBreaker=(p.referenceBreaker||0)*12*seasonalFactor;
 const totalHp=avg('electricityCost')+fullHpBreaker+avg('hpService')+(state.retainGas?avg('gasFixed'):0)+household.hp;
 const totalGas=avg('gasFuel')+avg('ets')+avg('gasFixed')+avg('gasService')+fullGasBreaker+household.gas;
 return {hp:totalHp,gas:totalGas,totalHp,totalGas};
}
function setCostReference(){costReference=currentCostSnapshot();renderLiveCosts();}
function renderLiveCosts(){
 const box=document.getElementById('settings-live-costs');if(!box)return;
 const c=currentCostSnapshot();if(!costReference)costReference={...c};
 const delta=v=>(v>=0?'+':'−')+nfmt(Math.abs(v))+' Kč';
 box.innerHTML=`<div class="flex flex-wrap gap-3 justify-between"><div><b>TČ ${nfmt(c.hp)} Kč</b><br><small>Změna ${delta(c.hp-costReference.hp)}</small></div><div><b>Plyn ${nfmt(c.gas)} Kč</b><br><small>Změna ${delta(c.gas-costReference.gas)}</small></div><div><b>${c.gas>=c.hp?'Úspora s TČ':'Vícenáklady TČ'} ${nfmt(Math.abs(c.gas-c.hp))} Kč</b><br><small>Průměr vybraných sezón · ${state.economyPeriod==='annual'?'modelový rok':'průměr desetiletí'}</small></div></div><div class="text-xs text-slate-400 mt-2">Změna proti uloženému srovnání (zpočátku stav při načtení). <button class="text-sky-300 underline" onclick="setCostReference()">Porovnávat od nynějška</button></div>`;
}
