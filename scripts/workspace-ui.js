/* Local configuration workspace: original controls are moved, never cloned. */
const configurationTabs=[
  ['location','1. Lokace'],
  ['house','2. Nastavení domu'],
  ['hp','3. Konfigurace TČ'],
  ['gas','4. Plynový kotel'],
  ['tariffs','5. Tarify energie a spotřeba domácnosti'],
  ['control','6. Režimy řízení']
];
let workspaceMounted=false;
let uiMode='simple';
let activeConfigTab='house';
let analysisExpanded=false;
let simpleSlotMoves=[];

function sliderFieldBlock(id){
 const el=document.getElementById(id);
 if(!el)return null;
 const row=el.closest('.slider-input-row');
 return row?row.parentElement:el.parentElement;
}

function setupWorkspace(){
 if(workspaceMounted)return;
 const style=document.createElement('style');style.textContent=workspaceStyles;document.head.append(style);
 const root=document.createElement('section');root.id='configuration-workspace';root.dataset.uiMode=uiMode;
 root.innerHTML=`<div class="workspace-heading">
   <div>
     <span class="eyebrow">SIMULACE VYTÁPĚNÍ RD · VERZE 2026.10.27.11</span>
     <h1>Tepelné čerpadlo nebo plyn?</h1>
     <p id="workspace-mode-desc">Zjednodušený režim: zadejte jen klíčové parametry lokality, domu a zdroje tepla. Výsledné náklady vidíte okamžitě vpravo.</p>
   </div>
   <div class="workspace-heading-actions">
     <div class="mode-switch" role="group" aria-label="Režim zobrazení konfigurace a výsledků">
       <button type="button" id="btn-mode-simple" class="mode-btn active" aria-pressed="true" onclick="setUiMode('simple')">⚡ Zjednodušený režim</button>
       <button type="button" id="btn-mode-advanced" class="mode-btn" aria-pressed="false" onclick="setUiMode('advanced')">🔧 Podrobný režim</button>
     </div>
     <button id="theme-toggle" class="workspace-button" onclick="toggleTheme()">Denní téma</button>
     <button class="workspace-button" onclick="resetDefaultParameters()">Obnovit výchozí nastavení</button>
   </div>
 </div>
 <div class="workspace-grid">
   <div class="configuration-shell">
     <nav id="config-tabs-nav" class="configuration-tabs" role="tablist" aria-label="Nastavení simulace" hidden>${configurationTabs.map(([id,label])=>`<button id="tab-${id}" role="tab" aria-controls="panel-${id}" aria-selected="${id==='house'}" tabindex="${id==='house'?0:-1}" onclick="selectConfigTab('${id}')">${label}</button>`).join('')}</nav>
     <section id="panel-simple" role="region" aria-label="Zjednodušená konfigurace">
       <div class="panel-header simple-panel-header">
         <div>
           <h2>⚡ Základní parametry pro rychlý výpočet</h2>
           <p class="config-note">Zadejte lokalitu, tepelnou ztrátu domu, otopnou soustavu, spotřebu TUV, zdroj tepla a ostatní spotřebiče domácnosti (výpočet probíhá pro nejnovějších 10 sezón). Detailní parametry upravíte přepnutím na podrobný režim v záhlaví.</p>
         </div>
       </div>
       <div class="config-content">
         <div class="simple-section-block">
           <div class="simple-section-title">1. Lokalita</div>
           <div class="two-col-cards">
             <div id="slot-simple-loc-left" class="slot-anchor"></div>
             <div id="slot-simple-loc-right" class="slot-anchor"></div>
           </div>
         </div>
         <div class="simple-section-block">
           <div class="simple-section-title">2. Dům, otopná soustava a ohřev TUV</div>
           <div class="house-grid">
             <div id="slot-simple-house-0" class="slot-anchor"></div>
             <div id="slot-simple-comfort-card" class="config-subcard house-card-item">
               <div class="font-semibold text-slate-200 border-b border-slate-700/60 pb-1.5 mb-2">
                 <span>🌡️ Pokojová teplota a tolerance (nekomfort)</span>
               </div>
               <div id="slot-simple-comfort" class="slot-anchor"></div>
             </div>
             <div id="slot-simple-house-3" class="slot-anchor"></div>
           </div>
         </div>
         <div class="simple-section-block">
           <div class="simple-section-title">3. Zdroj tepla – tepelné čerpadlo a plynový kotel</div>
           <div class="two-col-cards">
             <div id="slot-simple-hp-select" class="slot-anchor"></div>
             <div class="config-subcard">
               <h3>🔥 Plynový kotel a povolenka EU ETS 2</h3>
               <div id="slot-simple-gas-eff" class="slot-anchor"></div>
               <div id="slot-simple-ets-check" class="slot-anchor"></div>
               <div id="slot-simple-ets-price" class="slot-anchor"></div>
             </div>
           </div>
         </div>
         <div class="simple-section-block">
           <div class="simple-section-title">4. Ostatní spotřebiče domácnosti</div>
           <div id="slot-simple-household" class="slot-anchor"></div>
         </div>
       </div>
     </section>
     ${configurationTabs.map(([id,label])=>`<section id="panel-${id}" role="tabpanel" aria-labelledby="tab-${id}" hidden><div class="panel-header"><h2>${label}</h2></div><div id="content-${id}" class="config-content"></div></section>`).join('')}
   </div>
   <aside class="calculation-shell" aria-label="Průběžný výpočet"><div id="workspace-result"></div></aside>
 </div>`;
 document.body.prepend(root);
 setupTheme();
 document.getElementById('sec-dual')?.setAttribute('hidden','');
 const move=(id,to)=>{const el=document.getElementById(id);if(el)document.getElementById('content-'+to).append(el);return el;};

 // 1. Location tab
 const location=document.getElementById('content-location');
 location.innerHTML=`<div class="two-col-cards">
   <div id="slot-adv-loc-left" class="slot-anchor">
     <div id="loc-left-card" class="config-subcard">
       <h3>📍 Vyhledání obce a nadmořská výška</h3>
       <p class="config-note">Vyberte obec z nabídky pro automatické stažení historického počasí (ERA5). Bez výběru se používá referenční archiv pro Ostravu (1960–2026).</p>
     </div>
   </div>
   <div id="slot-adv-loc-right" class="slot-anchor">
     <div id="loc-right-card" class="config-subcard">
       <h3>🌤️ Aktivní meteorologický profil</h3>
       <div id="loc-badges-box" class="loc-badges-box"></div>
     </div>
   </div>
 </div>`;
 const locLeftCard=document.getElementById('loc-left-card');
 const locRightCard=document.getElementById('loc-right-card');
 const search=document.getElementById('geo-search-input').parentElement;search.className='relative w-full';
 locLeftCard.append(search);
 const altBlock=sliderFieldBlock('input-altitude');
 if(altBlock)locLeftCard.append(altBlock);
 const fBar=document.getElementById('fetch-status-bar');if(fBar)locLeftCard.append(fBar);
 ['badge-location','badge-altitude','badge-te-design','badge-weather-source'].forEach(id=>{
   const el=document.getElementById(id);if(el)document.getElementById('loc-badges-box').append(el);
 });
 const seasonSelector=document.getElementById('season-selector-wrapper');
 if(seasonSelector){
   const sBox=document.createElement('div');sBox.id='season-window-box';sBox.className='mt-3 pt-3 border-t border-slate-700/60';
   sBox.innerHTML='<h3>📅 Období simulovaných sezón (10leté okno okolo zadaného roku, 1960–2026)</h3>';
   sBox.append(seasonSelector);
   locRightCard.append(sBox);
 }

 // 2. House tab
 const grid=document.querySelector('#settings-drawer > .grid'),columns=[...grid.children];
 const house=document.getElementById('content-house');house.classList.add('house-grid');
 columns.slice(0,4).forEach(x=>x.classList.add('house-card-item'));
 const dhwWrap=document.getElementById('dhw-controls-wrapper');
 if(dhwWrap){
   [...dhwWrap.children].slice(1).forEach(el=>el.classList.add('dhw-advanced-only'));
 }
 const tinContainer=document.getElementById('val-tin')?.parentElement?.parentElement;
 if(tinContainer){
   const twoGrid=tinContainer.querySelector('.grid-cols-2');
   if(twoGrid){
     twoGrid.className='comfort-sliders-stack';
     const tinRow=document.getElementById('input-tin')?.closest('.slider-input-row');
     const tolRow=document.getElementById('input-tolerance')?.closest('.slider-input-row');
     if(tinRow&&!tinRow.previousElementSibling?.classList?.contains('comfort-sublabel')){
       const lbl1=document.createElement('div');lbl1.className='comfort-sublabel';lbl1.textContent='Cílová pokojová teplota (°C):';
       tinRow.before(lbl1);
     }
     if(tolRow&&!tolRow.previousElementSibling?.classList?.contains('comfort-sublabel')){
       const lbl2=document.createElement('div');lbl2.className='comfort-sublabel';
       lbl2.textContent='Hystereze směrem dolů – povolený pokles teploty (nekomfort) (°C):';
       tolRow.before(lbl2);
     }
   }
   const slotAdvComfort=document.createElement('div');slotAdvComfort.id='slot-adv-comfort';slotAdvComfort.className='slot-anchor';
   tinContainer.before(slotAdvComfort);
   slotAdvComfort.append(tinContainer);
 }
 const slotAdvHouse0=document.createElement('div');slotAdvHouse0.id='slot-adv-house-0';slotAdvHouse0.className='slot-anchor';slotAdvHouse0.append(columns[0]);
 const slotAdvHouse3=document.createElement('div');slotAdvHouse3.id='slot-adv-house-3';slotAdvHouse3.className='slot-anchor';slotAdvHouse3.append(columns[3]);
 house.append(slotAdvHouse0,columns[1],columns[2],slotAdvHouse3);

 // 3. Heat Pump tab
 const hpContent=document.getElementById('content-hp');
 const hpTopBar=document.createElement('div');hpTopBar.className='hp-top-grid';
 const slotAdvHpSelect=document.createElement('div');slotAdvHpSelect.id='slot-adv-hp-select';slotAdvHpSelect.className='slot-anchor';
 const hpSelectCard=document.createElement('div');hpSelectCard.className='config-subcard';
 hpSelectCard.innerHTML='<div class="flex flex-wrap items-center justify-between gap-2 mb-2"><h3>🏷️ Výběr modelu tepelného čerpadla</h3><span id="hp-badge-slot"></span></div>';
 const badgeKm=document.getElementById('badge-keymark');if(badgeKm)hpSelectCard.querySelector('#hp-badge-slot').append(badgeKm);
 const hpDetails=document.getElementById('hp-settings-details');
 const hpSelectEl=document.getElementById('settings-hp-select');
 if(hpSelectEl)hpSelectCard.append(hpSelectEl);
 slotAdvHpSelect.append(hpSelectCard);
 const hpServiceCard=document.createElement('div');hpServiceCard.className='config-subcard';
 hpServiceCard.innerHTML='<h3>🛠️ Pravidelný servis TČ</h3>';
 const hpServiceBlock=sliderFieldBlock('input-hp-service');
 if(hpServiceBlock)hpServiceCard.append(hpServiceBlock);
 hpTopBar.append(slotAdvHpSelect,hpServiceCard);
 hpContent.append(hpTopBar);
 if(hpDetails){
   hpDetails.open=true;
   const sumEl=hpDetails.querySelector('summary');if(sumEl)sumEl.hidden=true;
   const lblEl=hpDetails.querySelector('label[for="settings-hp-select"]');if(lblEl)lblEl.hidden=true;
   hpContent.append(hpDetails);
 }

 // 4. Gas Boiler tab
 const gasContent=document.getElementById('content-gas');
 gasContent.classList.add('two-col-cards');
 const gasBoilerCard=document.createElement('div');gasBoilerCard.id='gas-boiler-card';gasBoilerCard.className='config-subcard';
 gasBoilerCard.innerHTML=`<h3>🔥 Parametry kondenzačního kotle</h3>
 <label class="workspace-field">Model plynového kotle<input id="gas-boiler-model" type="text" value="${esc(state.gasBoilerModel||'Protherm Gepard Condens 12 MKO')}" onchange="state.gasBoilerModel=this.value" style="width:100%"></label>
 <p class="config-note">Referenční kondenzační kotel dodává stejné teplo jako TČ. Účinnosti níže jsou sezónní předpoklady vůči fakturovanému spalnému teplu Hs (94 % Hs ≈ 104,3 % Hi dle katalogu).</p>
 <label class="workspace-field">Účinnost přípravy TUV (Hs) <span><input id="gas-dhw-efficiency" type="number" min="50" max="100" step="1" onchange="setWorkspaceNumber('gasDhwEfficiency',this.value,50,100)"> % <small id="gas-dhw-hi-hint" class="text-slate-400"></small></span></label>`;
 const gasEffBlock=sliderFieldBlock('input-gas-eff');
 const slotAdvGasEff=document.createElement('div');slotAdvGasEff.id='slot-adv-gas-eff';slotAdvGasEff.className='slot-anchor';
 if(gasEffBlock){
   gasEffBlock.before(slotAdvGasEff);
   slotAdvGasEff.append(gasEffBlock);
 }
 gasBoilerCard.append(columns[5]);
 const etsControl=sliderFieldBlock('input-co2-price');
 const slotAdvEtsPrice=document.createElement('div');slotAdvEtsPrice.id='slot-adv-ets-price';slotAdvEtsPrice.className='slot-anchor';
 if(etsControl)slotAdvEtsPrice.append(etsControl);
 gasBoilerCard.append(slotAdvEtsPrice);
 gasBoilerCard.insertAdjacentHTML('beforeend',`<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-slate-700/60">
   <a class="workspace-button" href="https://protherm.cz/files/downloads/projekcni-podklady/pp-1-6-gepard-condens-verze-2-09032023-2605641.pdf" target="_blank" rel="noopener">Technické údaje Protherm ↗</a>
   <a class="workspace-button" href="https://eprel.ec.europa.eu/screen/product/spaceheaters" target="_blank" rel="noopener">Databáze kotlů EPREL ↗</a>
 </div>`);
 gasContent.append(gasBoilerCard);
  const gasElectricCard=document.createElement('div');gasElectricCard.id='gas-electric-card';gasElectricCard.className='config-subcard';
  gasElectricCard.innerHTML=`<h3>⚡ Elektřina v domě s plynovým kotlem</h3>
  <p class="config-note">I dům vytápěný plynem potřebuje elektrickou přípojku pro běžné spotřebiče a provoz kotle (např. sazba D01d nebo D02d, včetně stálé platby za jistič). Celý dům se počítá v tomto referenčním tarifu.</p>`;
  const refField=document.getElementById('energy-reference-field');
  if(refField){
    refField.classList.remove('energy-field');
    refField.classList.add('workspace-field');
    gasElectricCard.append(refField);
  }
  gasElectricCard.insertAdjacentHTML('beforeend',`<p id="gas-reference-tariff-note" class="energy-note"></p>`);
  gasContent.append(gasElectricCard);

 // 5. Tariffs & Household tab
 const energy=move('energy-card','tariffs');energy.open=true;energy.querySelector('summary').hidden=true;
 const gasSection=document.querySelector('#energy-form .energy-grid > section:nth-child(2)');
 const etsCheckLabel=document.getElementById('energy-ets')?.closest('label');
 const slotAdvEtsCheck=document.createElement('div');slotAdvEtsCheck.id='slot-adv-ets-check';slotAdvEtsCheck.className='slot-anchor';
 if(etsCheckLabel){
   etsCheckLabel.before(slotAdvEtsCheck);
   slotAdvEtsCheck.append(etsCheckLabel);
 }
 document.querySelectorAll('#energy-form .energy-footer button').forEach(b=>{if(b.textContent==='Minimalizovat')b.hidden=true;});

 simpleSlotMoves=[
   [locLeftCard,'slot-simple-loc-left','slot-adv-loc-left'],
   [locRightCard,'slot-simple-loc-right','slot-adv-loc-right'],
   [columns[0],'slot-simple-house-0','slot-adv-house-0'],
   [tinContainer,'slot-simple-comfort','slot-adv-comfort'],
   [columns[3],'slot-simple-house-3','slot-adv-house-3'],
   [hpSelectCard,'slot-simple-hp-select','slot-adv-hp-select'],
   [gasEffBlock,'slot-simple-gas-eff','slot-adv-gas-eff'],
   [etsCheckLabel,'slot-simple-ets-check','slot-adv-ets-check'],
   [etsControl,'slot-simple-ets-price','slot-adv-ets-price']
 ];

 // 6. Control tab
 const control=document.getElementById('content-control');
 control.classList.add('two-col-cards');
 control.innerHTML=`<div class="config-subcard">
   <h3>🎛️ Strategie vytápění a teplotní komfort</h3>
   <label class="workspace-field">Strategie vytápění<select id="control-policy" onchange="setControlValue('policy',this.value)"><option value="day">Denní priorita · vyšší COP v teplejší části dne</option><option value="tariff">Priorita nízkého tarifu (NT)</option><option value="constant">Stálá teplota · bez časového útlumu</option></select></label>
   <label class="workspace-field">Synchronizovaný tarif energie<select id="control-tariff" onchange="changeEnergy('tariff',this.value)">${Object.keys(energyTariffs).map(t=>`<option>${t}</option>`).join('')}</select></label>
   <div id="control-comfort" class="control-comfort-box"></div>
   <div class="two-fields" id="control-day-window">
     <label class="workspace-field">Začátek denního okna (h)<input id="control-dayStart" type="number" min="0" max="23" step="1" onchange="setControlValue('dayStart',this.value)"></label>
     <label class="workspace-field">Konec denního okna (h)<input id="control-dayEnd" type="number" min="1" max="24" step="1" onchange="setControlValue('dayEnd',this.value)"></label>
   </div>
   <label class="workspace-field">Využití povoleného poklesu mimo prioritu <span><input id="control-setback" type="number" min="0" max="100" step="5" onchange="setControlValue('setback',Number(this.value)/100)"> % tolerance</span></label>
   <p class="config-note">Denní priorita nabíjí podlahu v teplejší části dne (vyšší COP) a mimo okno dovolí pokles teploty v rámci nastavené tolerance. U radiátorů se akumulace potěru neuplatňuje.</p>
 </div>
 <div class="config-subcard hdo-panel">
   <h3>🕒 Tarif a modelový rozvrh HDO (24 h)</h3>
   <p id="control-tariff-info" class="energy-result"></p>
   <div id="hdo-timeline" aria-label="Denní rozvrh NT a VT"></div>
   <label class="energy-check"><input id="control-blockCompressor" type="checkbox" onchange="setControlValue('blockCompressor',this.checked)"> Blokovat také kompresor ve VT (vlastní zapojení)</label>
   <p id="control-blocking-note" class="config-note"></p>
   <details class="km-details"><summary>Upravit intervaly nízkého tarifu (HDO)</summary>
     <label class="workspace-field">Intervaly nízkého tarifu<textarea id="control-ntWindows" rows="2" placeholder="00:00–06:00, 13:00–15:00"></textarea></label>
     <p class="config-note">Časy zadávejte po 10 minutách; rozvrh se opakuje každý den.</p>
     <div class="flex gap-2 mt-2"><button class="workspace-button" onclick="applyHdoWindows()">Použít rozvrh</button><button class="workspace-button" onclick="resetHdoWindows()">Obnovit vzor</button></div>
     <p id="hdo-error" role="alert"></p>
   </details>
   <p class="config-note">U dvoutarifu model plánuje ohřev TUV do oken NT. <a href="https://www.cezdistribuce.cz/file/edee/distribuce/ceniky/ceniky-a-podminky/podminky_distribucnich_sazeb_domacnost.pdf" target="_blank" rel="noopener">Podmínky sazeb ČEZ Distribuce ↗</a></p>
 </div>`;

 updateControlComfortSummary();

 setupHouseholdControls();
 setupHouseGuidance();
 setupAnalysisLayout();
 setupSeasonSummary();

 document.getElementById('badge-auto-level').closest('.card').hidden=true;
 document.getElementById('gas-overview').hidden=true;
 document.getElementById('settings-live-costs').hidden=true;
 document.querySelector('header').hidden=true;
 const explanation=[...document.querySelectorAll('body > .card')].find(x=>x.textContent.includes('Proč vzniká úspora'));
 if(explanation)explanation.hidden=true;

 const bFloor=document.getElementById('btn-sys-floor');
 if(bFloor&&!bFloor.dataset.bound){bFloor.dataset.bound='1';bFloor.addEventListener('click',()=>setHeatingSystem('floor'));}
 const bRad=document.getElementById('btn-sys-rad');
 if(bRad&&!bRad.dataset.bound){bRad.dataset.bound='1';bRad.addEventListener('click',()=>setHeatingSystem('radiator'));}

 document.querySelector('.configuration-tabs').addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();
  const i=configurationTabs.findIndex(([id])=>'tab-'+id===document.activeElement.id);
  const j=e.key==='Home'?0:e.key==='End'?5:(i+(e.key==='ArrowRight'?1:5))%6;
  selectConfigTab(configurationTabs[j][0]);document.getElementById('tab-'+configurationTabs[j][0]).focus();
 });
 syncUiModeLayout();
 workspaceMounted=true;renderWorkspace();
}

function syncUiModeLayout(){
 const isSimple=uiMode==='simple';
 const root=document.getElementById('configuration-workspace');
 if(root)root.dataset.uiMode=uiMode;
 const btnSimple=document.getElementById('btn-mode-simple');
 const btnAdv=document.getElementById('btn-mode-advanced');
 if(btnSimple){btnSimple.classList.toggle('active',isSimple);btnSimple.setAttribute('aria-pressed',String(isSimple));}
 if(btnAdv){btnAdv.classList.toggle('active',!isSimple);btnAdv.setAttribute('aria-pressed',String(!isSimple));}
 const desc=document.getElementById('workspace-mode-desc');
 if(desc)desc.textContent=isSimple
   ?'Zjednodušený režim: zadejte jen klíčové parametry lokality, domu a zdroje tepla. Výsledné náklady vidíte okamžitě vpravo.'
   :'Nastavte parametry domu, zdroje tepla a tarifů v 6 krocích. Výsledné náklady a komfort se okamžitě přepočítávají vpravo.';
 const tabsNav=document.getElementById('config-tabs-nav');
 if(tabsNav)tabsNav.hidden=isSimple;
 const panelSimple=document.getElementById('panel-simple');
 if(panelSimple)panelSimple.hidden=!isSimple;
 for(const [el,simpleSlotId,advSlotId] of simpleSlotMoves){
  const target=document.getElementById(isSimple?simpleSlotId:advSlotId);
  if(el&&target&&el.parentElement!==target)target.append(el);
 }
 for(const [key] of configurationTabs){
  const button=document.getElementById('tab-'+key);
  const active=!isSimple&&key===activeConfigTab;
  if(button){button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;}
  const panel=document.getElementById('panel-'+key);
  if(panel)panel.hidden=!active;
 }
}

function setUiMode(mode){
 if(!['simple','advanced'].includes(mode))return;
 uiMode=mode;
 if(mode==='simple'&&state.centerYear!==2022&&typeof setCenterYear==='function'){
  setCenterYear(2022);
 }
 syncUiModeLayout();
 if(workspaceMounted)renderCalculation();
}

function selectConfigTab(id){
 if(!configurationTabs.some(([key])=>key===id))return;
 activeConfigTab=id;
 if(uiMode!=='advanced')uiMode='advanced';
 syncUiModeLayout();
 if(workspaceMounted)renderCalculation();
}

function setWorkspaceNumber(key,value,min,max){
 const n=Number(value);
 if(value!==''&&Number.isFinite(n)&&n>=min&&n<=max)state[key]=n;
 if(key==='gasDhwEfficiency'&&typeof recalculateEconomy==='function')recalculateEconomy();
 else recalculateSimulation();
 updateUI();
}

function setControlValue(key,value){
 const next={...(state.control||defaultControl())};
 if(key==='policy'){if(!['day','tariff','constant'].includes(value))return;next.policy=value;}
 else if(key==='blockCompressor')next[key]=Boolean(value);
 else if(['dayStart','dayEnd','setback'].includes(key)){if(value==='')return;next[key]=Number(value);}
 else return;
 if(!Number.isInteger(next.dayStart)||!Number.isInteger(next.dayEnd)||!Number.isFinite(next.setback)||next.dayStart<0||next.dayEnd>24||next.dayEnd<=next.dayStart||next.setback<0||next.setback>1){renderWorkspace();return;}
 state.control=next;recalculateSimulation();updateUI();
}

function applyHdoWindows(){
 try{state.energy.ntWindows=parseNtWindows(document.getElementById('control-ntWindows').value,state.energy.tariff);document.getElementById('hdo-error').textContent='';recalculateSimulation();updateUI();}
 catch(e){document.getElementById('hdo-error').textContent=e.message;}
}

function resetHdoWindows(){
 state.energy.ntWindows=tariffProfiles[state.energy.tariff].nt.map(x=>[...x]);
 document.getElementById('hdo-error').textContent='';recalculateSimulation();updateUI();
}

function syncAltitudeDisplay(){
 const altSlider=document.getElementById('input-altitude');
 if(altSlider){
  if(state.altitude<Number(altSlider.min))altSlider.min=String(Math.max(0,state.altitude));
  if(state.altitude>Number(altSlider.max))altSlider.max=String(state.altitude);
  altSlider.value=state.altitude;
 }
 const altNum=document.getElementById('input-altitude-number');
 if(altNum){
  if(altSlider){altNum.min=altSlider.min;altNum.max=altSlider.max;}
  altNum.value=state.altitude;
 }
 const valAlt=document.getElementById('val-altitude');
 if(valAlt)valAlt.textContent=`${state.altitude} m n. m.`;
 const badgeAlt=document.getElementById('badge-altitude');
 if(badgeAlt)badgeAlt.textContent=`⛰️ ${state.altitude} m n. m.`;
}

function syncHeatingSystemButtons(){
 const isFloor=state.heatingSystem!=='radiator';
 const btnFloor=document.getElementById('btn-sys-floor');
 const btnRad=document.getElementById('btn-sys-rad');
 if(btnFloor){
  btnFloor.classList.toggle('active',isFloor);
  btnFloor.setAttribute('aria-pressed',String(isFloor));
 }
 if(btnRad){
  btnRad.classList.toggle('active',!isFloor);
  btnRad.setAttribute('aria-pressed',String(!isFloor));
 }
}


function updateControlComfortSummary(){
  const box=document.getElementById('control-comfort');
  if(!box)return;
  const tMin=(state.tInTarget-state.tTolerance).toFixed(1);
  const tMax=state.tInTarget.toFixed(1);
  box.innerHTML=`<div>
    <div class="flex items-center justify-between gap-2 flex-wrap">
      <span><b>🏠 Komfort nastavený u domu:</b> Cíl <b>${nfmt(state.tInTarget,1)} °C</b>, hystereze poklesu <b>−${nfmt(state.tTolerance,1)} °C</b></span>
      <button type="button" class="workspace-button text-xs" onclick="selectConfigTab('house')">Upravit v Nastavení domu ↗</button>
    </div>
    <div class="text-[11px] text-slate-400 mt-1">Pásmo tolerované teploty (nekomfort): ${tMin} – ${tMax} °C · Využití povoleného poklesu níže čerpá z této tolerance.</div>
  </div>`;
}

function renderWorkspace(){
 if(!workspaceMounted)return;
 syncAltitudeDisplay();
 syncHeatingSystemButtons();
 const c=state.control||defaultControl(),plan=tariffPlan(),p=energyPrices(state.energy);
 document.getElementById('control-tariff').value=state.energy.tariff;
 document.getElementById('control-day-window').hidden=c.policy!=='day' && !(c.policy==='tariff'&&!plan.hours);
 document.getElementById('control-setback').disabled=c.policy==='constant';
 for(const key of ['policy','dayStart','dayEnd'])document.getElementById('control-'+key).value=c[key];
 document.getElementById('control-setback').value=Math.round(c.setback*100);
 document.getElementById('control-blockCompressor').checked=c.blockCompressor;
 document.getElementById('control-blockCompressor').disabled=!plan.hours;
 const dhwEff=state.gasDhwEfficiency??86;
 document.getElementById('gas-dhw-efficiency').value=dhwEff;
 const dhwHiHint=document.getElementById('gas-dhw-hi-hint');
 if(dhwHiHint)dhwHiHint.textContent=`(≈ ${nfmt(dhwEff*1.11,1)} % Hi)`;
 const valGasEff=document.getElementById('val-gas-eff');
 if(valGasEff)valGasEff.textContent=`${state.gasBoilerEfficiency} % Hs (≈ ${nfmt(state.gasBoilerEfficiency*1.11,1)} % Hi)`;
 const gasModelInput=document.getElementById('gas-boiler-model');
 if(gasModelInput&&state.gasBoilerModel)gasModelInput.value=state.gasBoilerModel;
 document.getElementById('control-ntWindows').value=formatNtWindows(plan.nt);
 document.getElementById('control-ntWindows').disabled=!plan.hours;
 document.getElementById('control-tariff-info').textContent=`${plan.code} · ${plan.label} · VT ${nfmt(p.vt,2)} Kč/kWh${plan.hours?' · NT '+nfmt(p.nt,2)+' Kč/kWh':''}`;
 document.getElementById('control-blocking-note').textContent=plan.code==='D57d'?'D57d: ve VT se blokuje přímotopná patrona. Kompresor je podle podmínek sazby vyňat; vlastní blokování výše je volitelné.':plan.hours?'TUV je v modelu přesunuta do NT. D25d/D26d blokují akumulační spotřebiče, nikoli automaticky kompresor TČ.':'Jednotarif: bez cenových pásem a blokování HDO. Priorita NT se chová jako denní priorita.';
 document.getElementById('hdo-timeline').innerHTML=Array.from({length:24},(_,h)=>{const fraction=Array.from({length:6},(_,s)=>ntAt(h*60+s*10,plan)?1:0).reduce((a,b)=>a+b,0)/6;return `<span title="${h}:00–${h+1}:00: ${Math.round(fraction*60)} min NT" style="background:linear-gradient(to right,#059669 ${fraction*100}%,#334155 ${fraction*100}%)">${h}</span>`;}).join('')+'<p class="config-note">Zelená = nízký tarif (NT) · šedá = vysoký tarif (VT)</p>';
 const lossNote=document.getElementById('house-loss-guidance');if(lossNote)lossNote.textContent=`Při výpočtové venkovní teplotě ${nfmt(state.tExtDesign,1)} °C a pokojovém cíli ${nfmt(state.tInTarget,1)} °C.`;
  const gasRefNote=document.getElementById('gas-reference-tariff-note');
  if(gasRefNote){
    const refT=state.energy.referenceTariff||'D02d';
    const bIndex=state.energy.breakerIndex??3;
    gasRefNote.textContent=`Platba za jistič ${breakerLabels[bIndex]} v sazbě ${refT}: ${nfmt(p.referenceBreaker,2)} Kč/měsíc (${nfmt(p.referenceBreaker*12,0)} Kč/rok).`;
  }
 renderHouseholdControls();
 renderSeasonSummary();
 updateControlComfortSummary();
 renderCalculation();
}

function renderCalculation(){
 const detailOpen=document.querySelector('.calculation-detail')?.open??false;
 const refOpen=document.querySelector('.reference-explanation')?.open??false;
 const isDecade=state.economyPeriod!=='annual';
 const allActive=getActiveSeasons();
 const seasons=isDecade?allActive:[state.currentSeason||allActive[Math.floor(allActive.length/2)]||'2022-2023'];
 const costs=seasons.map(s=>economyFor(simResults[s].results,s,'annual'));if(!costs.length)return;
 const avg=k=>costs.reduce((a,c)=>a+c[k],0)/costs.length,p=energyPrices(state.energy);
 const r=simResults[state.currentSeason]?.results||simResults[seasons[0]].results;
 const unit=isDecade?'průměr desetiletí':`modelový rok (${seasons[0]})`;
 const delta=v=>(v>=0?'+':'−')+nfmt(Math.abs(v))+' Kč';
 const row=(label,a,b)=>`<tr><th>${label}</th><td>${nfmt(a)}</td><td>${nfmt(b)}</td></tr>`;
 const backup=r.comfort.opt.backup+r.comfort.opt.dhwBackup;
 const missing=r.comfort.opt.dhwUnmet;
 const warning=r.comfort.opt.under>0.1||r.comfort.opt.over>0.1||missing>0.01;
 const seasonalFactor=avg('fraction'),household=householdEconomy(state.energy,seasonalFactor);
 const applianceNames=householdApplianceNames();
 const includeHousehold=Boolean(state.energy.household?.enabled);

 const fullHpBreaker=(state.energy.breakerFixed||0)*12*seasonalFactor;
 const fullGasBreaker=(p.referenceBreaker||0)*12*seasonalFactor;
 const hpElCost=avg('electricityCost');
 const hpService=avg('hpService');
 const hpRetainGas=state.retainGas?avg('gasFixed'):0;
 const gasFuel=avg('gasFuel');
 const gasEts=avg('ets');
 const gasFixed=avg('gasFixed');
 const gasService=avg('gasService');
 const hpHousehold=household.hp;
 const gasHousehold=household.gas;

 const totalHp=hpElCost+fullHpBreaker+hpService+hpRetainGas+hpHousehold;
 const totalGas=gasFuel+gasEts+gasFixed+gasService+fullGasBreaker+gasHousehold;
 const totalSaving=totalGas-totalHp;

 const heatingDiff=(gasFuel+gasEts+gasFixed+gasService)-(hpElCost+hpService+hpRetainGas);
 const breakerDiff=fullGasBreaker-fullHpBreaker;
 const heatElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_heat,0)/seasons.length;
 const dhwElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_dhw,0)/seasons.length+avg('summerEl');
 const avgStarts=seasons.reduce((a,s)=>a+simResults[s].results.starts_opt,0)/seasons.length;

 const subtitleText=isDecade?(allActive[0]==='2016-2017'&&allActive.at(-1)==='2025-2026'?'Průměr 10 sezón (2016-2017 až 2025-2026)':`Průměr ${allActive.length} sezón (${allActive[0]} až ${allActive.at(-1)})`):`Modelový rok (${seasons[0]})`;
 document.getElementById('workspace-result').innerHTML=`<div class="result-header">
   <div>
     <span class="eyebrow">PRŮBĚŽNÝ VÝPOČET</span>
      <div class="result-subtitle">${subtitleText}</div>
   </div>
    <select aria-label="Období nákladů" onchange="changeEconomy('economyPeriod',this.value)">
      <option value="decade" ${isDecade?'selected':''}>Průměr desetiletí</option>
      <option value="annual" ${!isDecade?'selected':''}>Modelový rok</option>
    </select>
 </div>

 <section class="whole-house-cost" aria-label="Celkové náklady domácnosti" aria-live="polite">
   <div class="whole-house-heading">CELKOVÝ PROVOZ CELÉHO DOMU (VYTÁPĚNÍ + TUV + ELEKTŘINA DOMÁCNOSTI)</div>
   <div class="hero-cost-grid">
     <div class="hero-cost-box hp">
       <span>⚡ S tepelným čerpadlem</span>
       <strong>${nfmt(totalHp)} <small>Kč</small></strong>
       <small class="hero-sub">
         Elektřina TČ: <b>${nfmt(hpElCost)} Kč</b><br>
         Spotřebiče (${state.energy.tariff}): <b>${nfmt(hpHousehold)} Kč</b><br>
         Jistič (${state.energy.tariff}): <b>${nfmt(fullHpBreaker)} Kč</b>
       </small>
     </div>
     <div class="hero-cost-box gas">
       <span>🔥 S plynovým kotlem</span>
       <strong>${nfmt(totalGas)} <small>Kč</small></strong>
       <small class="hero-sub">
         Plyn (teplo+TUV+paušál): <b>${nfmt(gasFuel+gasEts+gasFixed)} Kč</b><br>
         Spotřebiče (${state.energy.referenceTariff||'D02d'}): <b>${nfmt(gasHousehold)} Kč</b><br>
         Jistič (${state.energy.referenceTariff||'D02d'}): <b>${nfmt(fullGasBreaker)} Kč</b>
       </small>
     </div>
   </div>
   <div class="result-saving ${totalSaving<0?'negative':''}">
     <span>${totalSaving>=0?'Celková roční úspora s TČ':'Vícenáklady TČ'} za ${unit}</span>
     <b>${nfmt(Math.abs(totalSaving))} Kč</b>
   </div>
   <div class="saving-breakdown">
     <span>Vytápění a TUV: <b>${heatingDiff>=0?'úspora':'vícenáklady'} ${nfmt(Math.abs(heatingDiff))} Kč</b></span>
     <span>Spotřebiče (${state.energy.referenceTariff||'D02d'} → ${state.energy.tariff}): <b>${household.saving>=0?'úspora':'vícenáklady'} ${nfmt(Math.abs(household.saving))} Kč</b></span>
     <span>Rozdíl jističe: <b>${breakerDiff>=0?'úspora':'vícenáklady'} ${nfmt(Math.abs(breakerDiff))} Kč</b></span>
   </div>
 </section>

 <div class="report-cta-box my-2">
   <button type="button" class="workspace-button report-btn w-full justify-center text-xs py-2 font-bold" onclick="openReportModal()" title="Vytvořit a vytisknout PDF protokol s konfigurací a výsledky">
     📄 Vytvořit report (PDF)
   </button>
 </div>

 <div class="metrics-grid" ${uiMode==='simple'?'hidden':''}>
   <div class="metric-tile heating-electricity">
     <span class="metric-label">⚡ Elektřina TČ (topení + TUV)</span>
     <strong>${nfmt(avg('electricity'),0)} <small>kWh</small></strong>
     <small>VT ${nfmt(avg('electricityVT'),0)} · NT ${nfmt(avg('electricityNT'),0)} kWh<br>Topení ${nfmt(heatElAvg,0)} · TUV ${nfmt(dhwElAvg,0)} kWh</small>
   </div>
   <div class="metric-tile">
     <span class="metric-label">📈 Efektivita a teplo</span>
     <strong>SCOP ${nfmt(r.scop_opt,2)}</strong>
     <small>Dodané teplo: ${nfmt(avg('heat'),0)} kWh<br>Topení ${nfmt(r.scop_heat,2)} · TUV ${state.dhwEnabled?nfmt(r.scop_dhw,2):'—'}</small>
   </div>
   <div class="metric-tile comfort-result ${warning?'warning':''}">
     <span class="metric-label">🌡️ Komfort (${state.currentSeason})</span>
     <strong>${nfmt(r.comfort.opt.min,1)} – ${nfmt(r.comfort.opt.max,1)} °C</strong>
     <small>Pod pásmem ${nfmt(r.comfort.opt.under,1)} h · nad ${nfmt(r.comfort.opt.over,1)} h<br>Patrona ${nfmt(backup,0)} kWh${missing>0.01?` · chybí TUV ${nfmt(missing,1)} kWh`:''}</small>
   </div>
   <div class="metric-tile starts-result">
     <span class="metric-label">🔄 Starty TČ (${state.currentSeason})</span>
     <strong>${nfmt(r.starts_opt)} <small>/ sezónu</small></strong>
     <small>Průměr ${seasons.length} sezón: ${nfmt(avgStarts,0)} startů<br>Krok simulace 10 min (bez léta)</small>
   </div>
 </div>

 <div class="household-result" id="household-result" hidden>
   <b>Ostatní spotřebiče · ${state.energy.referenceTariff||'D02d'} → ${state.energy.tariff}</b>
   ${includeHousehold?`<p>${household.saving>=0?'Další úspora':'Vyšší náklady'} <strong>${nfmt(Math.abs(household.saving))} Kč</strong> / ${unit}</p><p>${esc(applianceNames)||'Spotřebiče neuvedeny'}</p><small>${nfmt(household.annualKwh,2)} kWh/rok · VT ${nfmt(household.vtKwh,2)} / NT ${nfmt(household.ntKwh,2)} kWh.</small>`:'<p>Nezahrnuto.</p>'}
 </div>

 <details class="calculation-detail" ${detailOpen?'open':''} ${uiMode==='simple'?'hidden':''}><summary>📊 Jak vznikla cena (položkový rozpad a vzorce)</summary>
   <table class="calculation-table"><thead><tr><th>Položka (Kč / ${unit})</th><th>TČ (${state.energy.tariff})</th><th>Plyn (${state.energy.referenceTariff||'D02d'})</th></tr></thead><tbody>
   ${row('Energie vytápění a TUV (elektřina / plyn)',hpElCost,gasFuel)}
   ${row('Stálá platba za jistič elektřiny',fullHpBreaker,fullGasBreaker)}
   ${row('Stálá platba za plynoměr',hpRetainGas,gasFixed)}
   ${row('Ostatní spotřebiče domácnosti',hpHousehold,gasHousehold)}
   ${row('Pravidelný roční servis',hpService,gasService)}
   ${row('Povolenka EU ETS 2',0,gasEts)}
   <tr class="font-bold border-t border-slate-600"><th>Celkem provoz celého domu</th><td>${nfmt(totalHp)}</td><td>${nfmt(totalGas)}</td></tr>
   </tbody></table>
   ${includeHousehold?`<p class="config-note">Ostatní spotřebiče (${esc(applianceNames)}): s TČ ${nfmt(household.vtKwh,0)} kWh VT × ${nfmt(p.vt,2)} + ${nfmt(household.ntKwh,0)} kWh NT × ${nfmt(p.nt,2)} = ${nfmt(household.annualHp)} Kč/rok; s plynem ${nfmt(household.annualKwh,0)} kWh × ${nfmt(household.baselineVT,2)} (${state.energy.referenceTariff}) = ${nfmt(household.annualGas)} Kč/rok.</p>`:''}
   <div class="calculation-equations"><p><b>Elektřina TČ:</b><br>${nfmt(avg('electricityVT'))} kWh VT × ${nfmt(p.vt,2)} Kč${avg('electricityNT')>0?'<br>+ '+nfmt(avg('electricityNT'))+' kWh NT × '+nfmt(p.nt,2)+' Kč':''}<br>= ${nfmt(avg('electricityCost'))} Kč (průměr ${nfmt(avg('electricityCost')/Math.max(0.001,avg('electricity')),2)} Kč/kWh)</p><p><b>Plyn:</b><br>${nfmt(avg('gasHeatKwh'))} kWh topení + ${nfmt(avg('gasDhwKwh'))} kWh TUV<br>× ${nfmt(p.gas,2)} Kč = ${nfmt(avg('gasFuel'))} Kč</p></div>
   <p class="config-note">Jistič ${breakerLabels[state.energy.breakerIndex]}: TČ (${state.energy.tariff}) ${nfmt(state.energy.breakerFixed,2)} Kč/měsíc vs. Plyn (${state.energy.referenceTariff||'D02d'}) ${nfmt(p.referenceBreaker,2)} Kč/měsíc. Účinnost kotle (Hs): topení ${nfmt(state.gasBoilerEfficiency)} %, TUV ${nfmt(state.gasDhwEfficiency??86)} %. ETS 2: ${state.etsEnabled?nfmt(state.co2AllowancePriceEur)+' €/t (+'+nfmt(avg('surcharge'),2)+' Kč/kWh)':'vypnuto'}. Koeficient období × ${nfmt(seasonalFactor,2)}.</p>
 </details>

 <details class="reference-explanation" ${refOpen?'open':''} ${uiMode==='simple'?'hidden':''}><summary>🔄 Srovnání změn a Scénáře A/B (Export / Import)</summary>
   <div class="result-totals" aria-live="polite">
     <div><span>TČ (celý dům)</span><strong>${nfmt(totalHp)} Kč</strong><small>${delta(totalHp-(costReference?.totalHp??costReference?.hp??totalHp))} proti uložené referenci</small></div>
     <div><span>Plyn (celý dům)</span><strong>${nfmt(totalGas)} Kč</strong><small>${delta(totalGas-(costReference?.totalGas??costReference?.gas??totalGas))} proti uložené referenci</small></div>
   </div>
   <div class="flex flex-wrap gap-1.5 my-2">
     <button class="workspace-button" onclick="setCostReference();renderCalculation()">📌 Porovnávat od nynějška</button>
     <button class="workspace-button" onclick="saveScenario('A')">Uložit A</button>
     <button class="workspace-button" onclick="restoreScenario('A')">Načíst A</button>
     <button class="workspace-button" onclick="saveScenario('B')">Uložit B</button>
     <button class="workspace-button" onclick="restoreScenario('B')">Načíst B</button>
     <button class="workspace-button" onclick="exportScenario()">⬇️ Export JSON</button>
     <button class="workspace-button" onclick="shareScenario()">🔗 Odkaz</button>
     <label class="workspace-button cursor-pointer">⬆️ Import JSON<input id="scenario-file" type="file" accept=".json,application/json" hidden></label>
   </div>
   <input id="scenario-link" type="text" readonly hidden class="w-full p-1.5 text-xs rounded bg-slate-900 border border-slate-700 mt-1">
   <p id="scenario-status" class="text-xs text-sky-300 my-1"></p>
   <div id="scenario-comparison" class="text-xs space-y-1 mt-1"></div>
 </details>`;

 const scenarioFile=document.getElementById('scenario-file');
 if(scenarioFile&&!scenarioFile.dataset.bound){
   scenarioFile.dataset.bound='1';
   scenarioFile.onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>8e6)throw Error('Soubor je příliš velký.');applyScenario(JSON.parse(await file.text()));scenarioMessage('Scénář importován.');}catch(err){scenarioMessage(err.message);}e.target.value='';};
 }
 renderScenarioComparison();
}

const updateBeforeWorkspace=updateUI;
updateUI=function(){updateBeforeWorkspace();renderWorkspace();};
const initBeforeWorkspace=init;
init=function(){initBeforeWorkspace();setupWorkspace();};
const selectGeoBeforeWorkspace=typeof selectGeoLocation==='function'?selectGeoLocation:null;
if(selectGeoBeforeWorkspace){
 selectGeoLocation=function(item){
  selectGeoBeforeWorkspace(item);
  syncAltitudeDisplay();
  renderWorkspace();
 };
}
const altSliderBeforeWorkspace=typeof onAltitudeSliderChange==='function'?onAltitudeSliderChange:null;
if(altSliderBeforeWorkspace){
 onAltitudeSliderChange=function(){
  altSliderBeforeWorkspace();
  syncAltitudeDisplay();
 };
}
const resetBeforeWorkspace=resetDefaultParameters;
resetDefaultParameters=function(){
 state.control=defaultControl();
 state.gasDhwEfficiency=86;
 state.gasBoilerModel='Protherm Gepard Condens 12 MKO';
 const gasName=document.getElementById('gas-boiler-model');
 if(gasName)gasName.value=state.gasBoilerModel;
 const geoIn=document.getElementById('geo-search-input');
 if(geoIn)geoIn.value='';
 costReference=null;
 resetBeforeWorkspace();
 syncAltitudeDisplay();
 renderWorkspace();
};

function hdoHourDescription(hour){
 const plan=tariffPlan();if(!plan.hours)return 'jednotarif · bez spínání';
 const n=Array.from({length:6},(_,s)=>ntAt(hour*60+s*10,plan)?10:0).reduce((a,b)=>a+b,0);
 return `${n} min NT / ${60-n} min VT`;
}

function drawDailySchedule(ctx,left,top,width,height){
 const plan=tariffPlan(),c=state.control||defaultControl();
 ctx.save();
 const priority=minute=>c.policy==='constant'?false:c.policy==='tariff'&&plan.hours?ntAt(minute,plan):minute>=c.dayStart*60&&minute<c.dayEnd*60;
 for(let i=0;i<144;i++){
  const x=left+i/144*width,nt=ntAt(i*10,plan);
  if(priority(i*10)){ctx.fillStyle='rgba(245,158,11,.08)';ctx.fillRect(x,top,width/144+0.5,height);}
  ctx.fillStyle=plan.hours&&nt?'#059669':'#64748b';ctx.fillRect(x,top+height-6,width/144+0.5,6);
  if(plan.hours&&i>0&&nt!==ntAt((i-1)*10,plan)){
   ctx.strokeStyle='#059669';ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+height);ctx.stroke();
  }
 }
 ctx.restore();
}

function drawDiurnalOutdoorCanvas(hoverHour){
 const canvas=document.getElementById('diurnalOutdoorCanvas');if(!canvas)return;
 const hours=simResults[state.currentSeason]?.daily[state.selectedDayIndex]?.hours;if(!hours?.length)return;
 const rect=canvas.getBoundingClientRect();if(!rect.width)return;
 const dpr=window.devicePixelRatio||1;canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;
 const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
 const left=40,top=20,w=rect.width-65,h=rect.height-45;
 const min=Math.floor(Math.min(...hours.map(x=>x.te))-1),max=Math.ceil(Math.max(...hours.map(x=>x.te))+1);
 const x=t=>left+t/24*w,y=t=>top+h-(t-min)/(max-min)*h;
 drawDailySchedule(ctx,left,top,w,h);
 ctx.font='10px system-ui';ctx.fillStyle='#64748b';
 for(let i=0;i<=4;i++){const t=min+(max-min)*i/4;ctx.fillText(nfmt(t,2)+'°',2,y(t)+3);ctx.strokeStyle='rgba(100,116,139,.3)';ctx.beginPath();ctx.moveTo(left,y(t));ctx.lineTo(left+w,y(t));ctx.stroke();}
 ctx.strokeStyle='#0284c7';ctx.lineWidth=2;ctx.beginPath();hours.forEach((v,i)=>i?ctx.lineTo(x(i),y(v.te)):ctx.moveTo(x(i),y(v.te)));ctx.stroke();
 ctx.textAlign='center';ctx.fillStyle='#64748b';for(let i=0;i<=24;i+=3)ctx.fillText(String(i).padStart(2,'0')+':00',x(i),top+h+17);
 if(hoverHour!=null){ctx.strokeStyle='#0284c7';ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(x(hoverHour),top);ctx.lineTo(x(hoverHour),top+h);ctx.stroke();}
}


function buildReportData(){
 const seasons=getActiveSeasons(),costs=seasons.map(s=>economyFor(simResults[s].results,s));
 const avg=k=>costs.reduce((a,c)=>a+c[k],0)/(costs.length||1),p=energyPrices(state.energy);
 const r=simResults[state.currentSeason]?.results||{};
 const seasonalFactor=avg('fraction'),household=householdEconomy(state.energy,seasonalFactor);
 const includeHousehold=Boolean(state.energy.household?.enabled);
 const fullHpBreaker=(state.energy.breakerFixed||0)*12*seasonalFactor;
 const fullGasBreaker=(p.referenceBreaker||0)*12*seasonalFactor;
 const hpElCost=avg('electricityCost'),hpService=avg('hpService'),hpRetainGas=state.retainGas?avg('gasFixed'):0;
 const gasFuel=avg('gasFuel'),gasEts=avg('ets'),gasFixed=avg('gasFixed'),gasService=avg('gasService');
 const hpHousehold=household.hp,gasHousehold=household.gas;
 const totalHp=hpElCost+fullHpBreaker+hpService+hpRetainGas+hpHousehold;
 const totalGas=gasFuel+gasEts+gasFixed+gasService+fullGasBreaker+gasHousehold;
 const totalSaving=totalGas-totalHp;
 const heatingHp=hpElCost+fullHpBreaker+hpService+hpRetainGas;
 const heatingGas=gasFuel+gasEts+gasFixed+gasService+fullGasBreaker;
 const heatingSaving=heatingGas-heatingHp;
 const heatElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_heat,0)/(seasons.length||1);
 const dhwElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_dhw,0)/(seasons.length||1)+avg('summerEl');
 const plan=tariffPlan(),split=householdSplit(state.energy);
 const etsSur=state.co2AllowancePriceEur*25.0*0.00018*1.21;
 const activeHp=state.activeHp||{};
 const isRadiator=state.heatingSystem==='radiator';
 const km=activeHp.km;
 const ltPoints=km?.lt?.points||[];
 const mtPoints=km?.mt?.points||[];
 const activePoints=isRadiator?mtPoints:ltPoints;
 const pDesign35=activeHp.pDesign35||km?.lt?.prated||5.68;
 const pDesign55=activeHp.pDesign55||km?.mt?.prated||5.63;
 const scop35=activeHp.scop35||km?.lt?.scop||4.73;
 const scop55=activeHp.scop55||km?.mt?.scop||3.56;
 const eta35=km?.lt?.eta||(scop35?Math.round(scop35/2.5*100):null);
 const eta55=km?.mt?.eta||(scop55?Math.round(scop55/2.5*100):null);
 const energyClass35=(eta35>=175||scop35>=4.4)?'A+++':(eta35>=150?'A++':'A+');
 const energyClass55=(eta55>=150||scop55>=3.75)?'A+++':(eta55>=125?'A++':'A+');
 const locationEl=document.getElementById('badge-location');
 const locationName=locationEl?locationEl.textContent.replace(/^[📍\s]+/,'').trim():'Ostrava';

 return {
  generatedAt:new Date().toLocaleString('cs-CZ',{dateStyle:'medium',timeStyle:'short'}),
  location:{
   name:locationName,
   altitude:state.altitude,
   tExtDesign:state.tExtDesign,
   weatherSource:'Referenční archiv Open-Meteo ERA5 (1960–2026)'
  },
  house:{
   qLossDesign:state.qLossDesign,
   heatingSystem:isRadiator?'Radiátory (křivka W55, bez akumulace potěru)':'Podlahové topení (křivka W35, s akumulací potěru)',
   isRadiator,
   tFlowDesign:state.tFlowDesign,
   floorAreaM2:state.floorAreaM2,
   floorThicknessMm:state.floorThicknessMm,
   floorMaterial:state.floorMaterial==='beton'?'Beton':'Anhydrit',
   floorCovering:state.floorCovering==='dlazba'?'Dlažba':(state.floorCovering==='vinyl'?'Vinyl':'Dřevo'),
   tInTarget:state.tInTarget,
   tTolerance:state.tTolerance
  },
  dhw:{
   enabled:state.dhwEnabled,
   liters:state.dhwDailyLiters,
   temp:state.dhwTargetTemp,
   mode:state.dhwMode==='smart'?'Chytrý polední ohřev / NT':'Průběžný ohřev'
  },
  household:{
   enabled:includeHousehold,
   annualKwh:split.total,
   vtKwh:split.vt,
   ntKwh:split.nt,
   costHp:household.hp,
   costGas:household.gas,
   saving:household.saving,
   appliances:householdApplianceNames()
  },
  heatPump:{
   name:activeHp.name||'Warmhouse HM-M0-A1',
   modelCode:activeHp.modelCode||km?.model||'HM-M0-A1',
   brand:activeHp.brand||(km?.holder?km.holder.split(' ')[0]:'Gawliczek / Warmhouse'),
   certNo:activeHp.certNo||km?.cert||'011-1W1325',
   lab:km?.lab||null,
   holder:km?.holder||null,
   compressor:activeHp.compressor||'Invertorový kompresor',
   refrigerant:activeHp.refrigerant||km?.refrigerant||'R290',
   refrigerantKg:km?.refrigerantKg?`${nfmt(km.refrigerantKg,2)} kg`:null,
   noiseDb:activeHp.noiseDb||(km?.soundPower?`${km.soundPower} dB(A) LWA`:null),
   minMod:activeHp.minMod?`${nfmt(activeHp.minMod,1)} kW`:null,
   pDesign:isRadiator?pDesign55:pDesign35,
   scop:isRadiator?scop55:scop35,
   pDesign35,
   pDesign55,
   scop35,
   scop55,
   eta35,
   eta55,
   energyClass35,
   energyClass55,
   tbiv:(isRadiator?km?.mt?.tbiv:km?.lt?.tbiv)??(km?.lt?.tbiv??-7),
   tol:(isRadiator?km?.mt?.tol:km?.lt?.tol)??(km?.lt?.tol??-10),
   wtol:(isRadiator?km?.mt?.wtol:km?.lt?.wtol)??(km?.lt?.wtol??75),
   standbyW:km?.lt?.psb??null,
   crankcaseW:km?.lt?.pck??null,
   thermostatW:km?.lt?.pto??null,
   extPumpW:km?.externalPumpW??null,
   serviceCost:state.hpServiceYearly||0,
   testPoints:activePoints.map(p=>({air:p.air,water:p.water,heat:p.heat,cop:p.cop})),
   dhwProfile:activeHp.dhwProfile||null,
   copDhwRef:activeHp.copDhwRef||null
  },
  gasBoiler:{
   model:state.gasBoilerModel||'Protherm Gepard Condens 12 MKO',
   effHeatHs:state.gasBoilerEfficiency||94,
   effHeatHi:Number(((state.gasBoilerEfficiency||94)*1.11).toFixed(1)),
   effDhwHs:state.gasDhwEfficiency??86,
   effDhwHi:Number(((state.gasDhwEfficiency??86)*1.11).toFixed(1)),
   ets2Enabled:state.etsEnabled,
   ets2PriceEur:state.co2AllowancePriceEur,
   ets2SurchargeCzk:etsSur,
   serviceCost:state.gasBoilerServiceYearly||1500
  },
  tariffs:{
   planCode:plan.code,
   planLabel:plan.label,
   vtPrice:p.vt,
   ntPrice:p.nt,
   gasPrice:p.gas,
   gasMonthlyFixed:state.gasMonthlyFixed,
   referenceTariff:state.energy.referenceTariff||'D02d',
   referenceVt:energyPrices({...state.energy,tariff:state.energy.referenceTariff||'D02d'}).vt
  },
  summary:{
   seasonsCount:seasons.length,
   seasonsRange:`${seasons[0]} až ${seasons.at(-1)}`,
   includeHousehold,
   totalHp,
   totalGas,
   totalSaving,
   savingPercent:totalGas>0?((totalSaving/totalGas)*100).toFixed(1):'0',
   heatingHp,
   heatingGas,
   heatingSaving,
   hpElCost,
   fullHpBreaker,
   gasFuelTotal:gasFuel+gasEts+gasFixed,
   fullGasBreaker,
   hpElectricityTotal:avg('electricity'),
   hpElectricityVT:avg('electricityVT'),
   hpElectricityNT:avg('electricityNT'),
   hpElectricityHeat:heatElAvg,
   hpElectricityDhw:dhwElAvg,
   gasKwhTotal:avg('gasKwh'),
   gasM3Total:avg('gasKwh')/10.55,
   heatTotal:avg('heat'),
   scopAvg:r.scop_opt||avg('scop_opt')||4.5,
   backupKwh:(r.comfort?.opt?.backup||0)+(r.comfort?.opt?.dhwBackup||0),
   hoursUnder:r.comfort?.opt?.under||0
  },
  seasonRows:seasons.map(s=>{
   const sRes=simResults[s].results,sEco=economyFor(sRes,s);
   const sHpBreaker=(state.energy.breakerFixed||0)*12*sEco.fraction;
   const sGasBreaker=(p.referenceBreaker||0)*12*sEco.fraction;
   const sHousehold=householdEconomy(state.energy,sEco.fraction);
   const sTotalHp=sEco.electricityCost+sHpBreaker+sEco.hpService+(state.retainGas?sEco.gasFixed:0)+sHousehold.hp;
   const sTotalGas=sEco.gasFuel+sEco.ets+sEco.gasFixed+sEco.gasService+sGasBreaker+sHousehold.gas;
   return {
    season:s,
    heatKwh:sEco.heat||sRes.th_kwh,
    elKwh:sEco.electricity,
    scop:sRes.scop_opt,
    costHp:sTotalHp,
    costGas:sTotalGas,
    saving:sTotalGas-sTotalHp
   };
  })
 };
}

function generateReportHtml(d){
 return `<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Protokol srovnání vytápění: TČ vs. Plynový kotel (${esc(d.location.name)})</title>
<style>
@page { size: A4 portrait; margin: 10mm 12mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; color: #0f172a; background: #ffffff; font-size: 11px; line-height: 1.45; }
.report-page { max-width: 800px; margin: 0 auto; padding: 8px; }
.report-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0284c7; padding-bottom: 8px; margin-bottom: 10px; }
.report-title-box h1 { font-size: 17px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px; }
.report-title-box p { font-size: 11px; color: #64748b; margin-top: 2px; }
.report-meta { text-align: right; font-size: 10px; color: #64748b; line-height: 1.4; }
.report-meta strong { color: #0f172a; }

/* 3 Hero Cards */
.report-hero-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
.report-hero-card { border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 9px 12px; background: #f8fafc; }
.report-hero-card.hp { border-color: #34d399; background: #f0fdf4; }
.report-hero-card.gas { border-color: #cbd5e1; background: #f8fafc; }
.report-hero-card.saving { border-color: #0284c7; background: #f0f9ff; }
.report-hero-card .label { font-size: 10px; font-weight: 750; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; display: flex; align-items: center; gap: 4px; }
.report-hero-card.hp .label { color: #059669; }
.report-hero-card.gas .label { color: #d97706; }
.report-hero-card.saving .label { color: #0284c7; }
.report-hero-card .value { font-size: 20px; font-weight: 800; line-height: 1.15; color: #0f172a; }
.report-hero-card .sub { font-size: 9.5px; color: #64748b; margin-top: 3px; line-height: 1.35; }

/* 2-Column Grid */
.report-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.report-section { border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 11px; background: #ffffff; }
.report-section h2 { font-size: 11.5px; font-weight: 750; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 6px; display: flex; align-items: center; gap: 5px; }
.report-kv-list { display: grid; grid-template-columns: auto 1fr; gap: 3px 8px; font-size: 10px; }
.report-kv-list dt { color: #64748b; font-weight: 500; }
.report-kv-list dd { color: #0f172a; font-weight: 600; text-align: right; }

/* Simplified Equipment Box */
.equipment-box { border: 1px solid #e2e8f0; border-radius: 6px; padding: 7px 9px; margin-bottom: 6px; background: #f8fafc; }
.equipment-box:last-child { margin-bottom: 0; }
.equipment-box h3 { font-size: 10.5px; font-weight: 700; color: #1e293b; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
.equipment-badge { font-size: 9px; padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.equipment-badge.hp { background: #dcfce7; color: #166534; }
.equipment-badge.gas { background: #fef3c7; color: #92400e; }
.hp-points-line { font-size: 8px; line-height: 1.35; color: #334155; text-align: right; }
.hp-points-line span { white-space: nowrap; }

/* 4-Strip Metrics */
.metrics-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 10px; }
.metric-box { border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; background: #f8fafc; text-align: center; }
.metric-box .m-label { font-size: 9px; font-weight: 600; color: #64748b; text-transform: uppercase; }
.metric-box .m-val { font-size: 13.5px; font-weight: 800; color: #0f172a; margin: 1px 0; }
.metric-box .m-sub { font-size: 8.5px; color: #64748b; }

/* Table */
.report-table-box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; background: #ffffff; margin-bottom: 10px; }
.report-table-box h2 { font-size: 11.5px; font-weight: 750; color: #0f172a; margin-bottom: 4px; }
.report-table { width: 100%; border-collapse: collapse; font-size: 9.5px; }
.report-table th, .report-table td { padding: 3px 5px; text-align: right; border-bottom: 1px solid #e2e8f0; }
.report-table th:first-child, .report-table td:first-child { text-align: left; }
.report-table th { background: #f1f5f9; font-weight: 700; color: #475569; }
.report-table tr.avg-row { background: #f8fafc; font-weight: 800; border-top: 1.5px solid #cbd5e1; }
.report-table tr.avg-row td { color: #0f172a; font-size: 10px; }

/* Tariffs Note */
.tariffs-note { font-size: 9px; color: #64748b; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 8px; margin-bottom: 8px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 3px 10px; }

/* Footer */
.report-footer { border-top: 1px solid #e2e8f0; padding-top: 6px; margin-top: 8px; display: flex; justify-content: space-between; font-size: 8.5px; color: #94a3b8; }

@media print {
  body { background: #ffffff !important; color: #000000 !important; }
  .no-print { display: none !important; }
  .report-page { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
  .report-hero-card, .report-section, .report-table-box { break-inside: avoid; }
}
</style>
</head>
<body>
<div class="report-page">
  <div class="report-header">
    <div class="report-title-box">
      <h1>🏡 PROTOKOL HODNOCENÍ VYTÁPĚNÍ RD</h1>
      <p>Srovnání nákladů: Tepelné čerpadlo vs. Kondenzační plynový kotel</p>
    </div>
    <div class="report-meta">
      <div>Lokalita: <strong>${esc(d.location.name)}</strong></div>
      <div>Vygenerováno: <strong>${d.generatedAt}</strong></div>
      <div>Období: <strong>10 sezón (${d.summary.seasonsRange})</strong></div>
    </div>
  </div>

  <div class="report-hero-grid">
    <div class="report-hero-card hp">
      <div class="label">⚡ Tepelné čerpadlo</div>
      <div class="value">${nfmt(d.summary.totalHp)} Kč/rok</div>
      <div class="sub">Vytápění + TUV: <b>${nfmt(d.summary.hpElCost)} Kč</b><br>Spotřebiče (${d.tariffs.planCode}): <b>${nfmt(d.household.costHp)} Kč</b><br>Jistič elektro (${d.tariffs.planCode}): <b>${nfmt(d.summary.fullHpBreaker)} Kč</b></div>
    </div>
    <div class="report-hero-card gas">
      <div class="label">🔥 Plynový kotel</div>
      <div class="value">${nfmt(d.summary.totalGas)} Kč/rok</div>
      <div class="sub">Plyn (topení + TUV + paušál): <b>${nfmt(d.summary.gasFuelTotal)} Kč</b><br>Spotřebiče (${d.tariffs.referenceTariff}): <b>${nfmt(d.household.costGas)} Kč</b><br>Jistič elektro (${d.tariffs.referenceTariff}): <b>${nfmt(d.summary.fullGasBreaker)} Kč</b></div>
    </div>
    <div class="report-hero-card saving">
      <div class="label">💰 Roční úspora s TČ</div>
      <div class="value">${d.summary.totalSaving>=0?'+':''}${nfmt(d.summary.totalSaving)} Kč/rok</div>
      <div class="sub">${d.summary.totalSaving>=0?`Úspora <b>${d.summary.savingPercent} %</b> celkových nákladů`:'Vyšší provozní náklady s TČ'}<br>Vytápění a TUV: <b>${nfmt(d.summary.heatingSaving)} Kč</b><br>Spotřebiče (${d.tariffs.referenceTariff} → ${d.tariffs.planCode}): <b>${d.household.saving>=0?'+':''}${nfmt(d.household.saving)} Kč</b></div>
    </div>
  </div>

  <div class="report-grid-2">
    <!-- Sloupec 1: Dům, lokalita a spotřebiče -->
    <div class="report-section">
      <h2>🏠 Dům, lokalita a spotřeba</h2>
      <dl class="report-kv-list">
        <dt>Obec a nadmořská výška</dt><dd>${esc(d.location.name)} (${d.location.altitude} m n. m.)</dd>
        <dt>Návrhová venkovní teplota (t_e)</dt><dd>${nfmt(d.location.tExtDesign,0)} °C</dd>
        <dt>Výpočtová tepelná ztráta domu</dt><dd>${nfmt(d.house.qLossDesign,2)} kW (při t_e)</dd>
        <dt>Otopná soustava</dt><dd>${d.house.heatingSystem}</dd>
        <dt>Návrhová teplota topné vody</dt><dd>${nfmt(d.house.tFlowDesign,1)} °C</dd>
        <dt>Vytápěná plocha a potěr</dt><dd>${d.house.floorAreaM2} m² · ${d.house.floorMaterial} ${d.house.floorThicknessMm} mm</dd>
        <dt>Pokojová teplota a tolerance</dt><dd>${nfmt(d.house.tInTarget,1)} °C (tolerance -${nfmt(d.house.tTolerance,1)} °C)</dd>
        <dt>Příprava teplé vody (TUV)</dt><dd>${d.dhw.enabled?`${d.dhw.liters} l/den při ${d.dhw.temp} °C (${d.dhw.mode})`:'Vypnuto'}</dd>
        <dt>Ostatní spotřebiče domácnosti</dt><dd>${d.household.enabled?`${nfmt(d.household.annualKwh,0)} kWh/rok (VT ${nfmt(d.household.vtKwh,0)} / NT ${nfmt(d.household.ntKwh,0)})`:'Nezahrnuto do bilance'}</dd>
      </dl>
    </div>

    <!-- Sloupec 2: Zjednodušená konfigurace zdrojů -->
    <div class="report-section">
      <h2>⚙️ Zjednodušená konfigurace zdrojů tepla</h2>
      
      <div class="equipment-box hp-detail-box">
        <h3><span>⚡ Tepelné čerpadlo vzduch-voda</span><span class="equipment-badge hp">Keymark: ${esc(d.heatPump.certNo)}</span></h3>
        <dl class="report-kv-list">
          <dt>Vybraný model TČ</dt><dd><b>${esc(d.heatPump.name)}</b></dd>
          ${d.heatPump.modelCode && d.heatPump.modelCode !== d.heatPump.name ? `<dt>Kód modelu a značka</dt><dd>${esc(d.heatPump.modelCode)}${d.heatPump.brand ? ' · ' + esc(d.heatPump.brand) : ''}</dd>` : ''}
          <dt>Certifikát HP Keymark</dt><dd>${esc(d.heatPump.certNo)}${d.heatPump.lab ? ' (' + esc(d.heatPump.lab.split(',')[0].trim()) + ')' : ''}</dd>
          <dt>Kompresor</dt><dd>${esc(d.heatPump.compressor)}</dd>
          <dt>Chladivo a náplň</dt><dd>${esc(d.heatPump.refrigerant)}${d.heatPump.refrigerantKg ? ' (náplň ' + d.heatPump.refrigerantKg + ')' : ''}</dd>
          ${d.heatPump.noiseDb ? `<dt>Akustický výkon L_WA (hlučnost)</dt><dd>${esc(d.heatPump.noiseDb)}</dd>` : ''}
          ${d.heatPump.minMod ? `<dt>Minimální modulace výkonu</dt><dd>${d.heatPump.minMod}</dd>` : ''}
          <dt>Výkon a SCOP (podlaha W35)</dt><dd>Pdesignh <b>${nfmt(d.heatPump.pDesign35, 1)} kW</b> · SCOP <b>${nfmt(d.heatPump.scop35, 2)}</b> (η_s ${d.heatPump.eta35} %, ${d.heatPump.energyClass35})</dd>
          <dt>Výkon a SCOP (radiátory W55)</dt><dd>Pdesignh <b>${nfmt(d.heatPump.pDesign55, 1)} kW</b> · SCOP <b>${nfmt(d.heatPump.scop55, 2)}</b> (η_s ${d.heatPump.eta55} %, ${d.heatPump.energyClass55})</dd>
          <dt>Teplotní limity (T_biv / T_OL / WTOL)</dt><dd>T_biv ${d.heatPump.tbiv} °C · T_OL ${d.heatPump.tol} °C · WTOL ${d.heatPump.wtol} °C</dd>
          ${d.heatPump.standbyW !== null ? `<dt>Pomocný příkon (standby / karter)</dt><dd>standby ${d.heatPump.standbyW} W${d.heatPump.crankcaseW ? ' · karter ' + d.heatPump.crankcaseW + ' W' : ''}${d.heatPump.extPumpW ? ' · čerpadlo ' + d.heatPump.extPumpW + ' W' : ''}</dd>` : ''}
          ${d.heatPump.testPoints && d.heatPump.testPoints.length ? `<dt>Zkušební body EN 14825 (${d.house.isRadiator ? 'W55' : 'W35'})</dt><dd class="hp-points-line">${d.heatPump.testPoints.map(p => `<span>A${p.air > 0 ? '+' : ''}${p.air}: <b>${nfmt(p.heat, 1)} kW</b> (COP ${nfmt(p.cop, 2)})</span>`).join(' · ')}</dd>` : ''}
          <dt>Pravidelný roční servis TČ</dt><dd>${nfmt(d.heatPump.serviceCost, 0)} Kč/rok</dd>
        </dl>
      </div>

      <div class="equipment-box">
        <h3><span>🔥 Kondenzační plynový kotel</span><span class="equipment-badge gas">Hs / Hi</span></h3>
        <dl class="report-kv-list">
          <dt>Model plynového kotle</dt><dd>${esc(d.gasBoiler.model)}</dd>
          <dt>Sezónní účinnost vytápění</dt><dd>${d.gasBoiler.effHeatHs} % Hs (≈ ${d.gasBoiler.effHeatHi} % Hi)</dd>
          <dt>Sezónní účinnost přípravy TUV</dt><dd>${d.gasBoiler.effDhwHs} % Hs (≈ ${d.gasBoiler.effDhwHi} % Hi)</dd>
          <dt>Povolenka EU ETS 2</dt><dd>${d.gasBoiler.ets2PriceEur} €/t CO₂ (+${nfmt(d.gasBoiler.ets2SurchargeCzk,2)} Kč/kWh)</dd>
          <dt>Roční servis a revize spalin</dt><dd>${nfmt(d.gasBoiler.serviceCost,0)} Kč/rok</dd>
        </dl>
      </div>
    </div>
  </div>

  <div class="tariffs-note">
    <span><b>Elektřina s TČ:</b> sazba ${d.tariffs.planCode} (${d.tariffs.planLabel}) · VT ${nfmt(d.tariffs.vtPrice,2)} Kč/kWh · NT ${nfmt(d.tariffs.ntPrice,2)} Kč/kWh</span>
    <span><b>Plyn:</b> ${nfmt(d.tariffs.gasPrice,2)} Kč/kWh (spalné teplo) + ${nfmt(d.tariffs.gasMonthlyFixed,0)} Kč/měs.</span>
    <span><b>Srovnávací sazba pro dům s plynem:</b> ${d.tariffs.referenceTariff} (VT ${nfmt(d.tariffs.referenceVt,2)} Kč/kWh)</span>
  </div>

  <div class="metrics-strip">
    <div class="metric-box">
      <div class="m-label">Spotřeba elektřiny TČ</div>
      <div class="m-val">${nfmt(d.summary.hpElectricityTotal,0)} kWh</div>
      <div class="m-sub">Topení ${nfmt(d.summary.hpElectricityHeat,0)} · TUV ${nfmt(d.summary.hpElectricityDhw,0)} kWh</div>
    </div>
    <div class="metric-box">
      <div class="m-label">Spotřeba plynu kotle</div>
      <div class="m-val">${nfmt(d.summary.gasKwhTotal,0)} kWh</div>
      <div class="m-sub">cca ${nfmt(d.summary.gasM3Total,0)} m³ zemního plynu</div>
    </div>
    <div class="metric-box">
      <div class="m-label">Sezónní faktor SCOP</div>
      <div class="m-val">SCOP ${nfmt(d.summary.scopAvg,2)}</div>
      <div class="m-sub">Dodané teplo domu: ${nfmt(d.summary.heatTotal,0)} kWh</div>
    </div>
    <div class="metric-box">
      <div class="m-label">Záložní patrona a komfort</div>
      <div class="m-val">${d.summary.backupKwh<0.1?'0 kWh (100 % TČ)':nfmt(d.summary.backupKwh,0)+' kWh'}</div>
      <div class="m-sub">Pokles pod toleranci: ${nfmt(d.summary.hoursUnder,1)} h</div>
    </div>
  </div>

  <div class="report-table-box">
    <h2>📊 Víceletá bilance – srovnání 10 historických sezón (Open-Meteo ERA5)</h2>
    <table class="report-table">
      <thead>
        <tr>
          <th>Topná sezóna</th>
          <th>Dodané teplo</th>
          <th>Elektřina TČ</th>
          <th>SCOP</th>
          <th>Náklady TČ</th>
          <th>Náklady Plyn</th>
          <th>Roční úspora TČ</th>
        </tr>
      </thead>
      <tbody>
        ${d.seasonRows.map(row=>`<tr>
          <td><b>${row.season}</b></td>
          <td>${nfmt(row.heatKwh,0)} kWh</td>
          <td>${nfmt(row.elKwh,0)} kWh</td>
          <td>${nfmt(row.scop,2)}</td>
          <td>${nfmt(row.costHp,0)} Kč</td>
          <td>${nfmt(row.costGas,0)} Kč</td>
          <td style="font-weight:700;color:${row.saving>=0?'#059669':'#be123c'}">${row.saving>=0?'+':''}${nfmt(row.saving,0)} Kč</td>
        </tr>`).join('')}
        <tr class="avg-row">
          <td>Průměr (10 sezón)</td>
          <td>${nfmt(d.summary.heatTotal,0)} kWh</td>
          <td>${nfmt(d.summary.hpElectricityTotal,0)} kWh</td>
          <td>${nfmt(d.summary.scopAvg,2)}</td>
          <td>${nfmt(d.summary.heatingHp,0)} Kč</td>
          <td>${nfmt(d.summary.heatingGas,0)} Kč</td>
          <td style="font-weight:800;color:${d.summary.heatingSaving>=0?'#059669':'#be123c'}">${d.summary.heatingSaving>=0?'+':''}${nfmt(d.summary.heatingSaving,0)} Kč</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="report-footer">
    <span>Protokol vygenerován aplikací Simulace vytápění RD (Open-Meteo ERA5 data, certifikovaná měření Keymark).</span>
    <span>Platnost k ${d.generatedAt}</span>
  </div>
</div>
</body>
</html>`;
}

function openReportModal(){
 const d=buildReportData();
 const html=generateReportHtml(d);
 let modal=document.getElementById('report-modal');
 if(!modal){
  modal=document.createElement('div');
  modal.id='report-modal';
  document.body.append(modal);
 }
 modal.innerHTML=`<div id="report-modal-backdrop" onclick="if(event.target===this)closeReportModal()">
   <div id="report-modal-dialog">
     <div class="report-modal-header">
       <h3>📄 Protokol hodnocení vytápění RD: TČ vs. Plynový kotel</h3>
       <div class="report-modal-actions">
         <button type="button" class="btn-print" onclick="printReport()">🖨️ Uložit jako PDF / Vytisknout</button>
         <button type="button" class="btn-secondary" onclick="downloadReportHtml()">⬇️ Stáhnout HTML</button>
         <button type="button" class="btn-secondary" onclick="closeReportModal()">✕ Zavřít</button>
       </div>
     </div>
     <div class="report-modal-body">
       <div class="report-paper-preview">
         <iframe id="report-preview-frame" style="width:100%;height:680px;border:none;background:#ffffff"></iframe>
       </div>
     </div>
   </div>
 </div>`;
 const frame=document.getElementById('report-preview-frame');
 if(frame){
  frame.contentWindow.document.open();
  frame.contentWindow.document.write(html);
  frame.contentWindow.document.close();
 }
}

function closeReportModal(){
 const modal=document.getElementById('report-modal');
 if(modal)modal.remove();
}

function printReport(){
 const d=buildReportData();
 const html=generateReportHtml(d);
 let frame=document.getElementById('report-print-frame');
 if(!frame){
  frame=document.createElement('iframe');
  frame.id='report-print-frame';
  frame.style.position='fixed';
  frame.style.right='0';
  frame.style.bottom='0';
  frame.style.width='0';
  frame.style.height='0';
  frame.style.border='0';
  document.body.append(frame);
 }
 const doc=frame.contentWindow.document;
 doc.open();
 doc.write(html);
 doc.close();
 frame.contentWindow.focus();
 setTimeout(()=>{
  try{
   frame.contentWindow.print();
  }catch(err){
   const w=window.open('','_blank');
   if(w){w.document.write(html);w.document.close();w.focus();w.print();}
  }
 },300);
}

function downloadReportHtml(){
 const d=buildReportData();
 const html=generateReportHtml(d);
 const blob=new Blob([html],{type:'text/html;charset=utf-8'});
 const a=document.createElement('a');
 a.href=URL.createObjectURL(blob);
 a.download=`protokol-vytapeni-tc-vs-plyn-${new Date().toISOString().slice(0,10)}.html`;
 a.click();
 URL.revokeObjectURL(a.href);
}

function setupTheme(){
 installRefinementStyle();
 let theme='dark';try{theme=localStorage.getItem('heating-theme')||'dark';}catch{}
 applyTheme(theme);
}
function toggleTheme(){applyTheme(document.documentElement.dataset.theme==='light'?'dark':'light');}
function applyTheme(theme){
 const light=theme==='light';document.documentElement.dataset.theme=light?'light':'dark';document.documentElement.classList.toggle('dark',!light);
 const button=document.getElementById('theme-toggle');if(button){button.textContent=light?'🌙 Noční téma':'☀️ Denní téma';button.setAttribute('aria-pressed',String(light));}
 try{localStorage.setItem('heating-theme',light?'light':'dark');}catch{}
 if(workspaceMounted){updateUI();}
}

function setupGasBoiler(){}

function setupHouseholdControls(){
 const box=document.createElement('section');box.id='household-controls';box.className='config-subcard household-controls';
 box.innerHTML=`<h3>🏠 Elektřina pro ostatní spotřebiče domu</h3>
 <label class="energy-check"><input id="household-enabled" type="checkbox" onchange="changeHousehold('enabled',this.checked)"> Zbytek domu spotřebuje (zahrnout do celkových nákladů domu)</label>
 <fieldset id="household-fields">
   <div class="two-fields">
     <label class="workspace-field">Celkem za rok (mimo TČ)<span><input id="household-annual" type="number" min="0" max="1000000" step="0.01" onchange="changeHousehold('annual',this.value)"> kWh/rok</span></label>
     <div class="two-fields">
       <label class="workspace-field">Z toho ve VT<span><input id="household-vt" type="number" min="0" max="1000000" step="0.01" onchange="changeHousehold('vt',this.value)"> kWh</span></label>
       <label class="workspace-field">Z toho v NT<span><input id="household-nt" type="number" min="0" max="1000000" step="0.01" onchange="changeHousehold('nt',this.value)"> kWh</span></label>
     </div>
   </div>
   <div class="household-advanced-only">
     <label class="energy-check"><input id="household-profile-mode" type="checkbox" onchange="setHouseholdProfileMode(this.checked)"> Rozpočítej dle typického profilu spotřebiče (integrace s HDO po 10 min)</label>
     <div id="household-profile-editor" hidden>
       <div id="household-profile-rows"></div>
       <button class="workspace-button mt-2" onclick="addHouseholdProfile()">+ Přidat spotřebič</button>
       <p class="config-note">Každá roční spotřeba se rozpočítá podle typického denního profilu a aktuálního rozvrhu HDO.</p>
     </div>
     <label class="workspace-field" id="household-appliances-wrap">Zahrnuté spotřebiče<textarea id="household-appliances" rows="2" maxlength="400" onchange="changeHousehold('appliances',this.value)"></textarea></label>
     <p id="household-baseline" class="config-note"></p>
   </div>
 </fieldset>`;
 const energyGrid=document.querySelector('#energy-form .energy-grid');
 const slotAdvHousehold=document.createElement('div');slotAdvHousehold.id='slot-adv-household';slotAdvHousehold.className='slot-anchor';
 slotAdvHousehold.append(box);
 if(energyGrid)energyGrid.append(slotAdvHousehold);
 else document.getElementById('content-tariffs').append(slotAdvHousehold);
 simpleSlotMoves.push([box,'slot-simple-household','slot-adv-household']);
}

function changeHousehold(key,value){
 const next=validateHouseholdConfig(state.energy.household||defaultHouseholdConfig());
 if(key==='enabled')next.enabled=Boolean(value);
 else if(key==='appliances')next.appliances=String(value).slice(0,400);
 else{
  const n=Number(value);if(value===''||!Number.isFinite(n)||n<0||n>1000000){renderHouseholdControls();return;}
  if(key==='annual'){if(next.mode==='profiles'){const old=next.profiles.reduce((a,x)=>a+x.kwh,0);next.profiles=next.profiles.map((x,i)=>({...x,kwh:old?n*x.kwh/old:i===0?n:0}));}else{const old=next.vt+next.nt,share=old?next.nt/old:1/3;next.nt=n*share;next.vt=n-next.nt;}}
  else if(['vt','nt'].includes(key)){if(next.mode==='profiles')return;next[key]=n;}else return;
 }
 try{state.energy.household=validateHouseholdConfig(next);}catch{renderHouseholdControls();return;}
 renderWorkspace();
}

function renderHouseholdControls(){
 const h=validateHouseholdConfig(state.energy.household||defaultHouseholdConfig()),cost=householdEconomy(state.energy),split=householdSplit(state.energy);
 const refEl=document.getElementById('energy-reference-field');if(refEl)refEl.hidden=false;
 document.getElementById('household-enabled').checked=h.enabled;document.getElementById('household-fields').disabled=!h.enabled;
 for(const [key,value] of Object.entries({annual:Number(split.total.toFixed(2)),vt:Number(split.vt.toFixed(2)),nt:Number(split.nt.toFixed(2)),appliances:householdApplianceNames()}))document.getElementById('household-'+key).value=value;
 document.getElementById('household-profile-mode').checked=h.mode==='profiles';
 document.getElementById('household-profile-editor').hidden=h.mode!=='profiles';
 const appWrap=document.getElementById('household-appliances-wrap');if(appWrap)appWrap.hidden=h.mode==='profiles';
 for(const key of ['vt','nt','appliances'])document.getElementById('household-'+key).disabled=h.mode==='profiles';
 renderHouseholdProfiles(h,split);
 document.getElementById('household-baseline').textContent=`Srovnávací sazba s plynem: ${state.energy.referenceTariff||'D02d'} (${nfmt(cost.baselineVT,2)} Kč/kWh). Roční účet spotřebičů: s TČ ${nfmt(cost.annualHp)} Kč vs. s plynem ${nfmt(cost.annualGas)} Kč.`;
}

function setupHouseGuidance(){
 const qlossBlock=sliderFieldBlock('input-qloss');
 if(qlossBlock&&qlossBlock.lastElementChild)qlossBlock.lastElementChild.id='house-loss-guidance';
 const panel=document.getElementById('content-house');
 panel.insertAdjacentHTML('afterbegin',`<details class="house-guidance"><summary>ℹ️ Nápověda: Jak vyplnit tepelnou ztrátu, teplotu vody a akumulaci podlahy</summary><p><b>Tepelná ztráta domu:</b> Zadejte výpočtovou ztrátu z PENB nebo projektu pro návrhový mráz lokace (nejde o jmenovitý výkon kotle).</p><p><b>Teplota topné vody:</b> Požadovaný výstup z TČ při návrhovém mrazu (bod topné křivky). Za teplejšího počasí model teplotu vody automaticky snižuje.</p><p><b>Akumulace podlahy:</b> Zadejte vytápěnou plochu místností a tloušťku akumulačního potěru (beton/anhydrit) nad izolací. <b>Akumulace a teplotní profil:</b> Zadejte vytápěnou plochu místností, tloušťku akumulačního potěru (beton/anhydrit), cílovou pokojovou teplotu a hysterezi směrem dolů (povolený pokles teploty – toleranci nekomfortu).</p></details>`);
}

function setHouseholdProfileMode(enabled){
 const h=validateHouseholdConfig(state.energy.household||defaultHouseholdConfig()),split=householdSplit();
 if(enabled&&h.mode!=='profiles'){
  const sum=h.profiles.reduce((a,x)=>a+x.kwh,0);
  h.profiles=h.profiles.map((x,i)=>({...x,kwh:sum?split.total*x.kwh/sum:i===0?split.total:0}));h.mode='profiles';
 }else if(!enabled){h.vt=split.vt;h.nt=split.nt;h.mode='manual';h.appliances=householdApplianceNames();}
 state.energy.household=validateHouseholdConfig(h);renderWorkspace();
}

function editHouseholdProfile(index,key,value){
 const h=validateHouseholdConfig(state.energy.household||defaultHouseholdConfig());if(!h.profiles[index])return;
 if(key==='type'){if(!Object.hasOwn(applianceProfiles,value))return;h.profiles[index].type=value;}
 else if(key==='kwh'){const n=Number(value);if(value===''||!Number.isFinite(n)||n<0||n>1000000){renderWorkspace();return;}h.profiles[index].kwh=n;}
 else if(key==='remove'){if(h.profiles.length<=1)return;h.profiles.splice(index,1);}else return;
 try{state.energy.household=validateHouseholdConfig(h);}catch{renderWorkspace();return;}renderWorkspace();
}

function addHouseholdProfile(){
 const h=validateHouseholdConfig(state.energy.household||defaultHouseholdConfig());if(h.profiles.length>=24)return;
 h.profiles.push({type:'standby',kwh:0});state.energy.household=h;renderWorkspace();
}

function renderHouseholdProfiles(h,split){
 const box=document.getElementById('household-profile-rows');if(!box||h.mode!=='profiles')return;
 box.innerHTML=h.profiles.map((x,i)=>{
   const share=split.rows[i].share,p=applianceProfiles[x.type];
   return `<div class="appliance-profile-row" title="${esc(p.description)}">
     <label>Spotřebič<select aria-label="Spotřebič ${i+1}" onchange="editHouseholdProfile(${i},'type',this.value)">${Object.entries(applianceProfiles).map(([id,p])=>`<option value="${id}" ${id===x.type?'selected':''}>${p.label}</option>`).join('')}</select></label>
     <label>kWh/rok<input aria-label="Roční spotřeba ${i+1}" type="number" min="0" max="1000000" step="0.01" value="${Number(x.kwh.toFixed(2))}" onchange="editHouseholdProfile(${i},'kwh',this.value)"></label>
     <div class="profile-share"><b>NT ${nfmt(share*100,0)} %</b><span>VT ${nfmt(x.kwh*(1-share),0)} · NT ${nfmt(x.kwh*share,0)} kWh</span></div>
     <button type="button" class="workspace-button" aria-label="Odebrat spotřebič ${i+1}" ${h.profiles.length===1?'disabled':''} onclick="editHouseholdProfile(${i},'remove')">×</button>
   </div>`;
 }).join('');
}

function setupSeasonSummary(){
 const body=document.getElementById('analysis-body');
 const kpi=document.getElementById('season-kpi-container');
 const tabs=body?.querySelector('.analysis-tabs');
 if(body&&kpi&&tabs){
   tabs.before(kpi);
 }
}

function renderSeasonSummary(){
 const select=document.getElementById('summary-season');if(!select)return;
 const seasons=getActiveSeasons();
 select.innerHTML=seasons.map(s=>`<option ${s===state.currentSeason?'selected':''}>${s}</option>`).join('');
}

let activeAnalysisView='day';
function setupAnalysisLayout(){
 const oldNav=document.getElementById('view-mode-all10')?.parentElement;if(oldNav)oldNav.parentElement.hidden=true;
 const first=document.getElementById('sec-all10'),layout=document.createElement('div');layout.id='analysis-layout';
 layout.innerHTML=`<div class="analysis-heading" onclick="if(!event.target.closest('.analysis-season-bar'))toggleAnalysisSection()">
   <div>
     <span class="eyebrow">GRAFY A PODROBNÉ VÝSLEDKY</span>
     <h2>Detailní průběh dne, sezóny a víceleté bilance</h2>
   </div>
   <div class="analysis-heading-controls">
     <div class="analysis-season-bar" id="analysis-season-bar" hidden onclick="event.stopPropagation()">
       <label for="summary-season" class="text-xs text-slate-400">Zobrazená sezóna:</label>
       <select id="summary-season" aria-label="Sezóna souhrnných ukazatelů" onchange="selectSeason(this.value)"></select>
     </div>
     <button type="button" id="btn-toggle-analysis" class="workspace-button analysis-toggle-btn" aria-expanded="false" aria-controls="analysis-body" onclick="event.stopPropagation();toggleAnalysisSection()">▼ Rozbalit grafy a podrobné výsledky</button>
   </div>
 </div>
 <div id="analysis-body" hidden>
   <nav class="analysis-tabs" aria-label="Zobrazení grafů">${[
     ['day','🕒 Den · teploty, výkon a HDO'],
     ['single','📅 Sezóna · denní spotřeba'],
     ['all10','📈 Porovnání 10 sezón'],
     ['table','📊 Souhrnné tabulky'],
     ['gas','🔥 Srovnání TČ a plynu'],
     ['all','📖 Vše pod sebou']
   ].map(([id,label])=>`<button id="analysis-tab-${id}" class="workspace-button" aria-pressed="false" onclick="selectAnalysisView('${id}')">${label}</button>`).join('')}</nav>
 </div>`;
 first.before(layout);
 const body=document.getElementById('analysis-body');
 const day=document.createElement('section');day.id='sec-day';day.append(document.getElementById('diurnal-section-card'));day.firstElementChild.classList.remove('hidden');body.append(day);
 const monthly=document.getElementById('monthly-tbody').closest('.card');monthly.classList.remove('hidden');document.getElementById('view-table-container').prepend(monthly);
 for(const key of ['single','all10','table','gas'])body.append(document.getElementById('sec-'+key));
 const temp=document.getElementById('diurnalTempCanvas').parentElement.parentElement,outdoor=document.getElementById('diurnalOutdoorCanvas').parentElement.parentElement;
 const temperatures=document.createElement('div');temperatures.className='daily-temperature-grid';temp.before(temperatures);temperatures.append(temp,outdoor);
 const power=document.getElementById('diurnalPowerCanvas').parentElement.parentElement;power.classList.add('daily-power-chart');
 const mechanism=[...document.querySelectorAll('#diurnal-section-card > .grid')].find(x=>x.textContent.includes('Noční útlum'));
 if(mechanism){const details=document.createElement('details');details.className='daily-explanation';details.innerHTML='<summary>ℹ️ Jak číst akumulaci a provozní období dne</summary>';mechanism.before(details);details.append(mechanism);}
 selectAnalysisView('day');
}

function toggleAnalysisSection(force){
 analysisExpanded=typeof force==='boolean'?force:!analysisExpanded;
 const body=document.getElementById('analysis-body');
 const seasonBar=document.getElementById('analysis-season-bar');
 const btn=document.getElementById('btn-toggle-analysis');
 const heading=document.querySelector('#analysis-layout .analysis-heading');
 if(body)body.hidden=!analysisExpanded;
 if(seasonBar)seasonBar.hidden=!analysisExpanded;
 if(heading)heading.classList.toggle('expanded',analysisExpanded);
 if(btn){
   btn.setAttribute('aria-expanded',String(analysisExpanded));
   btn.textContent=analysisExpanded?'▲ Sbalit grafy a podrobné výsledky':'▼ Rozbalit grafy a podrobné výsledky';
 }
 if(analysisExpanded){
   selectAnalysisView(activeAnalysisView);
   requestAnimationFrame(()=>{
     if(typeof drawOverlayChart==='function'&&state.sectionsExpanded?.all10)drawOverlayChart();
     if(typeof drawSingleSeasonChart==='function'&&state.sectionsExpanded?.single)drawSingleSeasonChart();
     if(typeof updateDiurnalView==='function')updateDiurnalView();
     if(typeof drawGasBarChart==='function'&&state.sectionsExpanded?.gas)drawGasBarChart();
   });
 }
}

function selectAnalysisView(view){
 if(!['day','single','all10','table','gas','all'].includes(view))return;activeAnalysisView=view;
 for(const key of ['day','single','all10','table','gas'])document.getElementById('sec-'+key).hidden=view!=='all'&&view!==key;
 for(const key of ['single','all10','table','gas'])toggleSection(key,view==='all'||view===key||(view==='day'&&key==='single'));
 for(const button of document.querySelectorAll('.analysis-tabs button'))button.setAttribute('aria-pressed',String(button.id==='analysis-tab-'+view));
 requestAnimationFrame(()=>{if(view==='day'||view==='all')updateDiurnalView();});
}

const workspaceStyles=`
[hidden]{display:none!important}
.slot-anchor{display:contents!important}
#configuration-workspace[data-ui-mode="simple"] .dhw-advanced-only,
#configuration-workspace[data-ui-mode="simple"] #season-window-box,
#configuration-workspace[data-ui-mode="simple"] .household-advanced-only{display:none!important}
#configuration-workspace{max-width:1540px;margin:0 auto 24px;color:#e2e8f0}
.workspace-heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #1e293b}
.workspace-heading h1{font-size:26px;font-weight:800;color:#f8fafc;margin:2px 0;letter-spacing:-0.3px}
.workspace-heading p,.config-note{font-size:12px;line-height:1.55;color:#94a3b8;margin:4px 0}
.workspace-heading-actions{display:flex;align-items:center;gap:8px;flex-shrink:0;flex-wrap:wrap}
.eyebrow{font-size:10px;font-weight:700;letter-spacing:1.4px;color:#38bdf8;text-transform:uppercase}

/* Mode Switcher in Header */
.mode-switch{display:inline-flex;gap:4px;background:#0f1a2e;border:1px solid #26354d;border-radius:9px;padding:3px}
.mode-btn{padding:6px 11px;border-radius:6px;font-size:12px;font-weight:650;color:#94a3b8;transition:all .15s;border:1px solid transparent}
.mode-btn:hover{color:#e2e8f0}
.mode-btn.active{background:#0c4a6e;color:#f0f9ff;border-color:#0284c7;box-shadow:0 1px 4px rgba(0,0,0,.3)}

/* Clean 2-Column Workspace Layout without nested scroll traps */
.workspace-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(380px,430px);gap:20px;align-items:start}
.configuration-shell,.calculation-shell{background:#0b1322;border:1px solid #26354d;border-radius:14px;box-shadow:0 10px 30px -10px rgba(0,0,0,.45)}
.configuration-shell{display:flex;flex-direction:column;overflow:visible}

/* Step Navigation Tabs */
.configuration-tabs{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px;padding:10px;background:#0f1a2e;border-bottom:1px solid #26354d;border-radius:14px 14px 0 0}
.configuration-tabs button{padding:9px 8px;border-radius:8px;font-size:12px;font-weight:600;color:#94a3b8;text-align:center;transition:all .15s;border:1px solid transparent;line-height:1.3}
.configuration-tabs button:hover{color:#e2e8f0;background:rgba(56,189,248,.06)}
.configuration-tabs button[aria-selected=true]{background:#0c4a6e;color:#f0f9ff;border-color:#0284c7;box-shadow:0 2px 8px rgba(2,132,199,.25)}
.configuration-tabs button:focus-visible,.workspace-button:focus-visible,.mode-btn:focus-visible{outline:2px solid #7dd3fc;outline-offset:2px}

.configuration-shell [role=tabpanel],#panel-simple{padding:20px}
.panel-header{margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #1e293b}
.simple-panel-header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
.simple-section-block{display:flex;flex-direction:column;gap:8px}
.simple-section-title{font-size:12px;font-weight:750;letter-spacing:.5px;text-transform:uppercase;color:#38bdf8;padding-left:2px}
.configuration-shell h2{font-size:18px;font-weight:750;color:#f8fafc;margin:0}
.configuration-shell h3{font-size:14px;font-weight:700;color:#f1f5f9;margin:0 0 10px}
.configuration-shell h4{font-size:12px;font-weight:700;color:#cbd5e1;margin:12px 0 6px}
.config-content{display:flex;flex-direction:column;gap:16px}

/* Subcards & Grids inside Tabs */
.config-subcard{background:#111d32;border:1px solid #293850;border-radius:11px;padding:16px;display:flex;flex-direction:column;gap:10px;min-width:0}
.two-col-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.hp-top-grid{display:grid;grid-template-columns:1.35fr 1fr;gap:16px;align-items:stretch}
.house-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:stretch}
.house-grid .house-card-item{min-width:0;background:#111d32!important;border:1px solid #293850!important;border-radius:11px!important;padding:16px!important}
.house-guidance{grid-column:1/-1;font-size:12px;line-height:1.6;border:1px solid #293850;background:#111d32;border-radius:9px;padding:10px 14px}
.house-guidance summary{cursor:pointer;color:#7dd3fc;font-weight:600}
.house-guidance p{margin-top:6px;color:#cbd5e1}

/* Unified Slider + Number Input Row (prevent any overflow/overlap) */
.slider-input-row{display:flex;align-items:center;gap:10px;margin-top:6px;width:100%;min-width:0}
.slider-input-row input[type=range]{flex:1 1 auto;min-width:0;width:100%;margin:0!important}
.slider-input-row .review-number{width:74px!important;margin:0!important;padding:4px 6px!important;font-size:12px;font-weight:600;text-align:right;background:#0b1322;border:1px solid #475569;border-radius:6px;color:#f8fafc;flex:0 0 74px}
.comfort-sliders-stack{display:flex;flex-direction:column;gap:8px;margin:8px 0}
.comfort-sublabel{font-size:11px;color:#cbd5e1;font-weight:500;margin-top:2px}
.sys-btn,.mat-btn,.cover-btn,.dhw-mode-btn{cursor:pointer;user-select:none;transition:all .15s ease}
.sys-btn.active{background-color:#059669!important;color:#ffffff!important;font-weight:700!important;box-shadow:0 1px 4px rgba(0,0,0,.3)!important}

/* Energy & Household in Tab 5 */
.config-content #energy-card{padding:0;border:0;background:none;margin:0}
.config-content #energy-form{margin:0;padding:0;border:0}
.config-content .energy-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.config-content #hp-settings-details{margin:0;padding:0;border:0;background:none}
.config-content input[type=number],.config-content input[type=text],.config-content select,.config-content textarea{max-width:100%;background:#0b1322;border:1px solid #3b4d66;border-radius:7px;padding:7px 9px;color:#f1f5f9;font-size:12px}
.workspace-field{display:flex;flex-direction:column;gap:5px;font-size:12px;color:#cbd5e1;font-weight:500}
.workspace-field input[type=number]{width:110px}
.workspace-field span{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.two-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.workspace-button{border:1px solid #3b4d66;background:#16243d;border-radius:7px;padding:7px 11px;color:#e2e8f0;font-size:12px;font-weight:600;transition:all .15s;display:inline-flex;align-items:center;gap:5px}
.workspace-button:hover{background:#1e3252;border-color:#526b8c}
.loc-badges-box{display:flex;flex-direction:column;gap:8px;padding:10px;background:#0b1322;border:1px solid #26354d;border-radius:8px;font-size:12px}
.control-comfort-box>div{padding:12px;background:#0b1322;border:1px solid #26354d;border-radius:8px;font-size:12px}

/* HDO Timeline */
#hdo-timeline{display:grid;grid-template-columns:repeat(12,1fr);gap:3px;margin:6px 0}
#hdo-timeline span{text-align:center;font-size:10px;font-weight:600;padding:5px 0;border-radius:4px;color:#fff}
#hdo-timeline p{grid-column:1/-1}
#hdo-error{color:#fda4af;font-size:12px;margin:6px 0}

/* Household Profile Rows */
.household-controls fieldset{display:flex;flex-direction:column;gap:10px;margin:4px 0}
.household-controls fieldset:disabled{opacity:.5}
.appliance-profile-row{display:grid;grid-template-columns:minmax(130px,1.5fr) 88px minmax(110px,1fr) 32px;align-items:end;gap:8px;padding:8px 0;border-bottom:1px solid #26354d}
.appliance-profile-row label{font-size:11px;display:flex;flex-direction:column;gap:4px;color:#cbd5e1}
.appliance-profile-row input[type=number]{width:100%!important}
.profile-share{font-size:11px;display:flex;flex-direction:column;gap:2px}
.profile-share b{color:#34d399}
.profile-share span{font-size:10px;color:#94a3b8}
.appliance-profile-row button{padding:6px;justify-content:center}

/* Right Sticky Calculation Panel */
.calculation-shell{position:sticky;top:16px;padding:18px}
.result-header{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px}
.result-subtitle{font-size:11px;color:#94a3b8;margin-top:2px}
.result-header select{background:#16243d;border:1px solid #3b4d66;border-radius:7px;padding:6px 9px;font-size:12px;font-weight:600;color:#f1f5f9}

/* Scope Switch (Include/Exclude Household Appliances) */
.scope-switch{display:grid;grid-template-columns:1fr 1fr;gap:4px;background:#0f1a2e;border:1px solid #26354d;border-radius:9px;padding:4px;margin-bottom:10px}
.scope-btn{padding:6px 8px;border-radius:6px;font-size:11px;font-weight:650;color:#94a3b8;text-align:center;transition:all .15s;border:1px solid transparent}
.scope-btn:hover{color:#e2e8f0}
.scope-btn.active{background:#0c4a6e;color:#f0f9ff;border-color:#0284c7;box-shadow:0 1px 4px rgba(0,0,0,.3)}

/* Hero Cost Card */
.whole-house-cost{background:linear-gradient(145deg,#092e2c,#0b1d2e);border:1px solid #14b8a6;border-radius:12px;padding:14px;margin-bottom:0;color:#f0fdfa}
#configuration-workspace[data-ui-mode="advanced"] .whole-house-cost{margin-bottom:12px}
.whole-house-heading{font-size:10px;letter-spacing:1px;font-weight:800;color:#5eead4;margin-bottom:10px}
.hero-cost-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.hero-cost-box{background:rgba(15,23,42,.55);border:1px solid rgba(255,255,255,.1);border-radius:9px;padding:10px 12px;display:flex;flex-direction:column;gap:3px}
.hero-cost-box.hp{border-color:rgba(45,212,191,.4);background:rgba(6,78,59,.4)}
.hero-cost-box>span{font-size:11px;font-weight:600;color:#cbd5e1}
.hero-cost-box strong{font-size:24px;font-weight:800;color:#fff;line-height:1.15;white-space:nowrap}
.hero-cost-box strong small{font-size:13px;font-weight:600;color:#cbd5e1}
.hero-sub{font-size:10px;line-height:1.45;color:#94a3b8;margin-top:2px}
.hero-sub b{color:#e2e8f0}
.result-saving{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:10px;padding:9px 12px;background:rgba(16,185,129,.16);border:1px solid rgba(52,211,153,.35);border-radius:8px;color:#6ee7b7;font-size:12px;font-weight:600}
.result-saving b{font-size:18px;font-weight:800;color:#ecfdf5;white-space:nowrap}
.result-saving.negative{background:rgba(244,63,94,.15);border-color:rgba(251,113,133,.4);color:#fda4af}
.saving-breakdown{display:flex;flex-direction:column;gap:2px;font-size:11px;color:#cbd5e1;margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.1)}
.saving-breakdown b{color:#fff}

/* 2x2 Key Metrics Grid */
.metrics-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:12px}
.metric-tile{background:#111d32;border:1px solid #26354d;border-radius:9px;padding:9px 11px;display:flex;flex-direction:column;gap:2px}
.metric-tile .metric-label{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.4px}
.metric-tile strong{font-size:16px;font-weight:800;color:#f8fafc}
.metric-tile strong small{font-size:11px;font-weight:500;color:#94a3b8}
.metric-tile small{font-size:10px;line-height:1.4;color:#94a3b8}
.metric-tile.heating-electricity{border-color:#0369a1;background:rgba(14,165,233,.08)}
.metric-tile.heating-electricity strong{color:#7dd3fc}
.metric-tile.comfort-result.warning{border-color:#f59e0b;background:rgba(245,158,11,.08)}

/* Collapsible Details in Right Panel */
.calculation-detail,.reference-explanation{margin-top:8px;border:1px solid #26354d;background:#111d32;border-radius:9px;padding:9px 12px;font-size:11px}
.calculation-detail summary,.reference-explanation summary{cursor:pointer;color:#7dd3fc;font-size:12px;font-weight:650;text-decoration:none}
.calculation-table{width:100%;margin:10px 0;font-size:11px;border-collapse:collapse}
.calculation-table td,.calculation-table th{padding:6px 4px;border-bottom:1px solid #26354d;text-align:right}
.calculation-table th:first-child{text-align:left;font-weight:500;color:#cbd5e1}
.calculation-table tr:last-child{font-weight:700;color:#fff}
.calculation-equations{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:11px;line-height:1.55;background:#0b1322;padding:8px 10px;border-radius:7px;margin:8px 0}
.result-totals{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}
.result-totals>div{background:#0b1322;border:1px solid #26354d;border-radius:8px;padding:8px 10px}
.result-totals span,.result-totals small{display:block;font-size:10px;color:#94a3b8}
.result-totals strong{display:block;font-size:16px;font-weight:750;color:#fff;margin:2px 0}
.scenario-slot-item,.scenario-slot-empty{padding:5px 8px;background:#0b1322;border-radius:6px;border:1px solid #1e293b;color:#cbd5e1}

/* Bottom Analysis Section (Collapsible) */
#analysis-layout{max-width:1540px;margin:0 auto 36px}
.analysis-heading{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin:16px 0 14px;padding:14px 18px;background:#0b1322;border:1px solid #26354d;border-radius:14px;cursor:pointer;transition:border-color .15s,background .15s;box-shadow:0 6px 20px -10px rgba(0,0,0,.4)}
.analysis-heading:hover{border-color:#0284c7;background:#0f1a2e}
.analysis-heading h2{font-size:18px;font-weight:750;margin-top:2px;color:#f8fafc}
.analysis-heading-controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.analysis-toggle-btn{background:#0c4a6e;border-color:#0284c7;color:#f0f9ff;padding:8px 14px}
.analysis-toggle-btn:hover{background:#0369a1;border-color:#38bdf8}
.analysis-season-bar{display:flex;align-items:center;gap:8px;background:#0f1a2e;border:1px solid #26354d;padding:6px 12px;border-radius:9px}
.analysis-season-bar select{background:#16243d;border:1px solid #3b4d66;border-radius:6px;padding:4px 8px;font-size:12px;font-weight:700;color:#38bdf8}
#season-kpi-container{display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:14px}
#season-kpi-container .card{padding:12px 14px;line-height:1.45}
#season-kpi-container .text-2xl{font-size:21px}
.analysis-tabs{display:flex;flex-wrap:wrap;gap:8px;padding:10px;background:#0b1322;border:1px solid #26354d;border-radius:12px;margin-bottom:16px}
.analysis-tabs button[aria-pressed=true]{background:#0c4a6e;color:#fff;border-color:#0284c7}
.analysis-tabs button{font-size:12px}
#analysis-body>section>div[onclick]{display:none}
.daily-temperature-grid{display:grid;grid-template-columns:3fr 2fr;gap:16px}
.daily-temperature-grid>div{min-width:0;border:1px solid #26354d;border-radius:10px;padding:12px}
.daily-temperature-grid canvas{min-height:210px}
.daily-temperature-grid>div>div:has(canvas){height:250px}
.daily-power-chart{border:1px solid #26354d;border-radius:10px;padding:12px}
.daily-explanation{font-size:12px;padding:10px;border-top:1px solid #26354d}
.daily-explanation summary{cursor:pointer;color:#7dd3fc;font-weight:600}
.config-content a{color:#7dd3fc}
#loc-left-card .relative{z-index:3}

@media(max-width:1200px){
  .workspace-grid{grid-template-columns:minmax(0,1fr) 360px}
  .configuration-tabs{grid-template-columns:repeat(3,1fr)}
  .two-col-cards,.config-content .energy-grid,.hp-top-grid{grid-template-columns:1fr}
  #season-kpi-container{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
}
@media(max-width:900px){
  .workspace-grid{display:flex;flex-direction:column}
  .calculation-shell{position:static;width:100%;order:-1}
  .configuration-shell{width:100%}
  .house-grid,.daily-temperature-grid{grid-template-columns:1fr}
}
@media(max-width:640px){
  .workspace-heading{flex-direction:column;align-items:flex-start;gap:10px}
  .configuration-tabs{grid-template-columns:repeat(2,1fr)}
  .hero-cost-grid,.metrics-grid,.two-fields,.calculation-equations{grid-template-columns:1fr}
}
/* Report Modal & CTA */
.report-cta-box .report-btn{background:linear-gradient(135deg,#0284c7 0%,#0369a1 100%);color:#ffffff!important;border:1px solid #38bdf8;border-radius:8px;font-weight:700;transition:all .15s ease;box-shadow:0 2px 6px rgba(2,132,199,.25)}
.report-cta-box .report-btn:hover{background:linear-gradient(135deg,#0369a1 0%,#075985 100%);border-color:#7dd3fc;box-shadow:0 4px 12px rgba(2,132,199,.35)}
#btn-header-report{background:#0284c7;color:#ffffff;border:1px solid #38bdf8;font-weight:700;border-radius:8px;padding:6px 14px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;font-size:12px;transition:all .15s}
#btn-header-report:hover{background:#0369a1;border-color:#7dd3fc}
#report-modal-backdrop{position:fixed;inset:0;background:rgba(15,23,42,.75);backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px}
#report-modal-dialog{background:#ffffff;color:#0f172a;border-radius:14px;box-shadow:0 25px 50px -12px rgba(0,0,0,.5);max-width:920px;width:100%;max-height:92vh;display:flex;flex-direction:column;overflow:hidden;border:1px solid #cbd5e1}
.report-modal-header{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#0f172a;color:#f8fafc;border-bottom:1px solid #334155}
.report-modal-header h3{font-size:15px;font-weight:750;margin:0;color:#f8fafc;display:flex;align-items:center;gap:6px}
.report-modal-actions{display:flex;align-items:center;gap:8px}
.report-modal-actions button{border-radius:7px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:4px}
.report-modal-actions .btn-print{background:#0284c7;color:#ffffff;border:1px solid #38bdf8}
.report-modal-actions .btn-print:hover{background:#0369a1}
.report-modal-actions .btn-secondary{background:#334155;color:#e2e8f0;border:1px solid #475569}
.report-modal-actions .btn-secondary:hover{background:#475569}
.report-modal-body{overflow-y:auto;padding:16px;background:#f1f5f9;flex:1 1 auto}
.report-paper-preview{background:#ffffff;max-width:820px;margin:0 auto;border-radius:8px;box-shadow:0 4px 20px -2px rgba(15,23,42,.1);overflow:hidden}
`;

function installRefinementStyle(){
 const refinementStyle=document.createElement('style');
 refinementStyle.textContent=`
#sec-dual{display:none!important}
html[data-theme=light]{color-scheme:light;background:#f8fafc}
html[data-theme=dark]{color-scheme:dark}
html[data-theme=light] body{background:#f8fafc!important;color:#0f172a!important}
html[data-theme=light] #configuration-workspace{color:#0f172a}

/* Typography & Headings in Light Theme */
html[data-theme=light] .workspace-heading{border-bottom:1px solid #e2e8f0!important}
html[data-theme=light] .workspace-heading h1{color:#0f172a!important}
html[data-theme=light] .workspace-heading p{color:#64748b!important}
html[data-theme=light] .eyebrow{color:#0284c7!important}
html[data-theme=light] .simple-section-title{color:#0284c7!important;border-bottom:2px solid #e0f2fe!important;padding-bottom:3px!important;display:inline-block!important}
html[data-theme=light] h2{color:#0f172a!important}
html[data-theme=light] h3{color:#1e293b!important}
html[data-theme=light] h4{color:#334155!important}
html[data-theme=light] .config-note{color:#64748b!important}
html[data-theme=light] .panel-header{border-bottom:1px solid #e2e8f0!important}
html[data-theme=light] .result-subtitle{color:#64748b!important}

/* Containers & Shells */
html[data-theme=light] :is(.configuration-shell,.calculation-shell,.card,#analysis-layout .analysis-heading){background:#ffffff!important;border:1px solid #e2e8f0!important;border-radius:14px!important;color:#0f172a!important;box-shadow:0 4px 20px -2px rgba(15,23,42,.05),0 2px 6px -1px rgba(15,23,42,.03)!important}
html[data-theme=light] :is(.config-subcard,.house-grid .house-card-item,.house-guidance){background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:12px!important;box-shadow:0 1px 3px rgba(15,23,42,.02)!important}

/* Segmented Switches (Mode, Scope, Heating System) */
html[data-theme=light] :is(.mode-switch,.scope-switch){background:#e2e8f0!important;border:1px solid #cbd5e1!important;border-radius:9px!important;padding:3px!important;gap:3px!important}
html[data-theme=light] :is(.mode-btn,.scope-btn){background:transparent!important;color:#475569!important;font-weight:600!important;border:none!important;border-radius:6px!important;transition:all .15s ease!important}
html[data-theme=light] :is(.mode-btn:hover,.scope-btn:hover){color:#0f172a!important}
html[data-theme=light] :is(.mode-btn.active,.scope-btn.active){background:#ffffff!important;color:#0284c7!important;font-weight:750!important;box-shadow:0 1px 4px rgba(0,0,0,.1)!important;border:none!important}

/* System selection buttons (Podlahové topení / Radiátory, etc.) */
html[data-theme=light] .grid:has(> .sys-btn),
html[data-theme=light] .grid:has(> .mat-btn),
html[data-theme=light] .grid:has(> .cover-btn),
html[data-theme=light] .grid:has(> .dhw-mode-btn){background:#e2e8f0!important;border:1px solid #cbd5e1!important;border-radius:9px!important;padding:3px!important}
html[data-theme=light] :is(.sys-btn,.mat-btn,.cover-btn,.dhw-mode-btn){color:#475569!important;font-weight:600!important;background:transparent!important;border:none!important;border-radius:6px!important;transition:all .15s ease!important}
html[data-theme=light] :is(.sys-btn:hover,.mat-btn:hover,.cover-btn:hover,.dhw-mode-btn:hover){color:#0f172a!important}
html[data-theme=light] :is(.sys-btn.active,.mat-btn.active,.cover-btn.active,.dhw-mode-btn.active){background:#0284c7!important;color:#ffffff!important;font-weight:750!important;box-shadow:0 1px 4px rgba(2,132,199,.35)!important}

/* Sliders & Numeric Inputs */
html[data-theme=light] input[type=range]{accent-color:#0284c7!important}
html[data-theme=light] .slider-input-row .review-number{background:#ffffff!important;color:#0f172a!important;border:1.5px solid #cbd5e1!important;border-radius:7px!important;font-size:13px!important;font-weight:700!important;box-shadow:inset 0 1px 2px rgba(0,0,0,.04)!important}
html[data-theme=light] .slider-input-row .review-number:focus{border-color:#0284c7!important;outline:2px solid rgba(2,132,199,.2)!important}
html[data-theme=light] :is(#val-qloss,#val-tflow,#val-altitude,#val-dhw-liters,#val-dhw-temp,#val-gas-eff){color:#0284c7!important;font-weight:800!important}
html[data-theme=light] #val-tin{color:#d97706!important;font-weight:800!important}
html[data-theme=light] #val-thickness{color:#059669!important;font-weight:800!important}

/* Text Inputs, Dropdowns & Search */
html[data-theme=light] :is(#geo-search-input,input[type=text],input[type=number],select,textarea){background:#ffffff!important;color:#0f172a!important;border:1.5px solid #cbd5e1!important;border-radius:8px!important;font-size:12px!important}
html[data-theme=light] :is(#geo-search-input,input[type=text],input[type=number],select,textarea):focus{border-color:#0284c7!important;outline:2px solid rgba(2,132,199,.2)!important}
html[data-theme=light] #geo-dropdown{background:#ffffff!important;border:1.5px solid #cbd5e1!important;box-shadow:0 10px 25px -5px rgba(0,0,0,.1)!important}
html[data-theme=light] #geo-dropdown>div{border-bottom:1px solid #f1f5f9!important}
html[data-theme=light] #geo-dropdown>div:hover{background:#f8fafc!important}
html[data-theme=light] #geo-dropdown span.font-semibold{color:#0f172a!important}

/* Location Badges */
html[data-theme=light] .loc-badges-box{background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important}
html[data-theme=light] .control-comfort-box>div{background:#f8fafc!important;border:1.5px solid #cbd5e1!important;color:#0f172a!important}
html[data-theme=light] .comfort-sublabel{color:#475569!important;font-weight:600!important}
html[data-theme=light] #badge-location{color:#0284c7!important;font-weight:700!important}
html[data-theme=light] :is(#badge-altitude,#badge-te-design){background:#e2e8f0!important;color:#1e293b!important;border:1px solid #cbd5e1!important;border-radius:6px!important;font-weight:600!important}
html[data-theme=light] #badge-keymark{background:#dcfce7!important;color:#166534!important;border:1px solid #86efac!important;border-radius:6px!important;font-weight:700!important}
html[data-theme=light] #badge-weather-source{color:#64748b!important}

/* DHW Toggle Switch */
html[data-theme=light] input#input-dhw-enabled~div{background-color:#cbd5e1!important}
html[data-theme=light] input#input-dhw-enabled:checked~div{background-color:#10b981!important}
html[data-theme=light] input#input-dhw-enabled~div:after{background-color:#ffffff!important;border-color:#cbd5e1!important;box-shadow:0 1px 3px rgba(0,0,0,.2)!important}

/* Action Buttons */
html[data-theme=light] .workspace-button{background:#ffffff!important;color:#334155!important;border:1.5px solid #cbd5e1!important;border-radius:8px!important;font-weight:600!important;box-shadow:0 1px 2px rgba(0,0,0,.04)!important}
html[data-theme=light] .workspace-button:hover{background:#f1f5f9!important;color:#0f172a!important;border-color:#94a3b8!important}
html[data-theme=light] .analysis-toggle-btn{background:#0284c7!important;color:#ffffff!important;border-color:#0284c7!important;font-weight:700!important;box-shadow:0 2px 6px rgba(2,132,199,.25)!important}
html[data-theme=light] .analysis-toggle-btn:hover{background:#0369a1!important;color:#ffffff!important}

/* Hero Cost Summary Card (.whole-house-cost) */
html[data-theme=light] .whole-house-cost{background:linear-gradient(135deg,#ecfdf5 0%,#f0fdf4 40%,#f0f9ff 100%)!important;border:1.5px solid #a7f3d0!important;border-radius:14px!important;padding:16px!important;box-shadow:0 4px 16px -2px rgba(16,185,129,.12)!important}
html[data-theme=light] .whole-house-heading{color:#047857!important;font-weight:800!important;font-size:11px!important;letter-spacing:.8px!important}
html[data-theme=light] .hero-cost-box{background:#ffffff!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;box-shadow:0 2px 6px rgba(0,0,0,.03)!important}
html[data-theme=light] .hero-cost-box.hp{border-color:#34d399!important;box-shadow:0 2px 8px rgba(16,185,129,.08)!important}
html[data-theme=light] .hero-cost-box.hp>span{color:#059669!important;font-weight:700!important;font-size:11px!important}
html[data-theme=light] .hero-cost-box.gas>span{color:#d97706!important;font-weight:700!important;font-size:11px!important}
html[data-theme=light] .hero-cost-box strong{color:#0f172a!important;font-weight:800!important;font-size:24px!important}
html[data-theme=light] .hero-cost-box strong small{color:#64748b!important;font-size:13px!important;font-weight:600!important}
html[data-theme=light] .hero-sub{color:#64748b!important;font-size:11px!important}
html[data-theme=light] .hero-sub b{color:#0f172a!important}
html[data-theme=light] .result-saving{background:#dcfce7!important;border:1.5px solid #86efac!important;border-radius:9px!important;padding:10px 14px!important;color:#15803d!important;font-size:12px!important;font-weight:650!important}
html[data-theme=light] .result-saving b{color:#166534!important;font-size:20px!important;font-weight:800!important}
html[data-theme=light] .result-saving.negative{background:#ffe4e6!important;border-color:#fda4af!important;color:#be123c!important}
html[data-theme=light] .result-saving.negative b{color:#9f1239!important}
html[data-theme=light] .saving-breakdown{border-top:1px solid rgba(16,185,129,.25)!important;color:#475569!important;font-size:11px!important}
html[data-theme=light] .saving-breakdown b{color:#0f172a!important}

/* Advanced Configuration Tabs & Panels */
html[data-theme=light] .configuration-tabs{background:#f8fafc!important;border-bottom:1px solid #e2e8f0!important}
html[data-theme=light] .configuration-tabs button{color:#64748b!important;font-weight:600!important}
html[data-theme=light] .configuration-tabs button:hover{color:#0f172a!important;background:#e2e8f0!important}
html[data-theme=light] .configuration-tabs button[aria-selected=true]{background:#0284c7!important;color:#ffffff!important;border-color:#0284c7!important;font-weight:700!important;box-shadow:0 2px 6px rgba(2,132,199,.25)!important}

/* Metric Tiles (Advanced Mode) */
html[data-theme=light] .metric-tile{background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important}
html[data-theme=light] .metric-tile .metric-label{color:#64748b!important}
html[data-theme=light] .metric-tile strong{color:#0f172a!important}
html[data-theme=light] .metric-tile small{color:#64748b!important}
html[data-theme=light] .metric-tile.heating-electricity{background:#f0f9ff!important;border-color:#bae6fd!important}
html[data-theme=light] .metric-tile.heating-electricity strong{color:#0284c7!important}
html[data-theme=light] .metric-tile.comfort-result.warning{background:#fffbeb!important;border-color:#fde68a!important}

/* Details & Tables in Right Panel */
html[data-theme=light] :is(.calculation-detail,.reference-explanation){background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important}
html[data-theme=light] :is(.calculation-detail summary,.reference-explanation summary,.house-guidance summary){color:#0284c7!important}
html[data-theme=light] .calculation-table th,html[data-theme=light] .calculation-table td{border-bottom:1px solid #e2e8f0!important;color:#1e293b!important}
html[data-theme=light] .calculation-table th:first-child{color:#475569!important}
html[data-theme=light] .calculation-table tr:last-child{color:#0f172a!important;font-weight:800!important}
html[data-theme=light] .calculation-equations{background:#ffffff!important;border:1px solid #e2e8f0!important;color:#334155!important}
html[data-theme=light] .result-totals>div{background:#ffffff!important;border:1px solid #e2e8f0!important}
html[data-theme=light] .result-totals strong{color:#0f172a!important}
html[data-theme=light] .result-totals span,html[data-theme=light] .result-totals small{color:#64748b!important}
html[data-theme=light] .scenario-slot-item{background:#ffffff!important;border:1px solid #e2e8f0!important;color:#1e293b!important}
html[data-theme=light] .scenario-slot-empty{background:#f8fafc!important;border:1px dashed #cbd5e1!important;color:#94a3b8!important}

/* Analysis Layout (Collapsible Section at Bottom) */
html[data-theme=light] #analysis-layout .analysis-heading{background:#ffffff!important;border:1px solid #e2e8f0!important;box-shadow:0 2px 8px rgba(0,0,0,.04)!important}
html[data-theme=light] #analysis-layout .analysis-heading:hover{background:#f8fafc!important;border-color:#0284c7!important}
html[data-theme=light] .analysis-tabs{background:#f8fafc!important;border:1.5px solid #e2e8f0!important}
html[data-theme=light] .analysis-tabs button{background:#ffffff!important;color:#475569!important;border:1.5px solid #cbd5e1!important;border-radius:8px!important;font-weight:600!important}
html[data-theme=light] .analysis-tabs button:hover{background:#f1f5f9!important;color:#0f172a!important}
html[data-theme=light] .analysis-tabs button[aria-pressed=true]{background:#0284c7!important;color:#ffffff!important;border-color:#0284c7!important;font-weight:700!important;box-shadow:0 2px 6px rgba(2,132,199,.25)!important}
html[data-theme=light] .analysis-season-bar{background:#f8fafc!important;border:1.5px solid #e2e8f0!important}
html[data-theme=light] .analysis-season-bar select{background:#ffffff!important;color:#0284c7!important;border:1.5px solid #cbd5e1!important;font-weight:700!important}
html[data-theme=light] .daily-temperature-grid>div,html[data-theme=light] .daily-power-chart{background:#ffffff!important;border:1.5px solid #e2e8f0!important;border-radius:12px!important}
html[data-theme=light] .daily-explanation{border-top:1px solid #e2e8f0!important}
html[data-theme=light] #season-kpi-container .card{background:#ffffff!important;border:1.5px solid #e2e8f0!important;box-shadow:0 1px 3px rgba(0,0,0,.04)!important}

/* Chart Tooltip & HDO Timeline */
html[data-theme=light] #hdo-timeline span{color:#ffffff!important}
html[data-theme=light] .chart-tooltip{background:#ffffff!important;color:#0f172a!important;border:1.5px solid #cbd5e1!important;box-shadow:0 10px 25px -5px rgba(0,0,0,.15)!important}
html[data-theme=light] .config-content a{color:#0284c7!important}
html[data-theme=light] #btn-header-report{background:#0284c7!important;color:#ffffff!important;border:1px solid #0284c7!important;font-weight:700!important}
html[data-theme=light] #btn-header-report:hover{background:#0369a1!important}
`;
 document.head.append(refinementStyle);
}
