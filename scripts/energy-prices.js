// ČEZ Prodej / ČEZ Distribuce and GasNet, verified 2026-10-25.
// All editable amounts include 21% VAT. Unit prices are Kč/kWh.
const energySources = {
  electricity:'https://www.cez.cz/webpublic/file/edee/ceniky/moo_ele_cez_fix_na_3_roky_30012026_012026.pdf',
  gas:'https://www.cez.cz/webpublic/file/edee/ceniky/moo_mop_plyn_gasnet_fix_na_3_roky_17042026_012026.pdf'
};
const energyTariffs = {
  D02d:{supplyVT:3.25,supplyNT:3.25,distributionVT:2.51508,distributionNT:2.51508,ntShare:0,
    breakers:[123.42,198.44,248.05,309.76,395.67,494.89,619.52,779.24]},
  D57d:{supplyVT:3.49,supplyNT:3.41,distributionVT:0.91327,distributionNT:0.14097,ntShare:83.333333,
    breakers:[268.62,429.55,537.24,671.55,859.10,1084.16,1559.69,2358.29]}
};
const breakerLabels=['3×10 A / 1×25 A','3×16 A','3×20 A','3×25 A','3×32 A','3×40 A','3×50 A','3×63 A'];
const gasBands=[
  {label:'Do 1,89 MWh/rok',distribution:0.90969,supplyFixed:113.74,distributionFixed:134.24},
  {label:'Nad 1,89 do 7,56 MWh/rok',distribution:0.49280,supplyFixed:125.84,distributionFixed:199.76},
  {label:'Nad 7,56 do 15 MWh/rok',distribution:0.44662,supplyFixed:163.35,distributionFixed:228.27},
  {label:'Nad 15 do 25 MWh/rok',distribution:0.41324,supplyFixed:163.35,distributionFixed:268.85},
  {label:'Nad 25 do 45 MWh/rok',distribution:0.34423,supplyFixed:163.35,distributionFixed:410.69},
  {label:'Nad 45 do 63 MWh/rok',distribution:0.27850,supplyFixed:163.35,distributionFixed:653.71}
];
function defaultEnergyConfig() {
  return {tariff:'D02d',breakerIndex:3,existingConnection:true,includeOtherFixed:false,annualEl:5000,
    supplyVT:3.25,supplyNT:3.25,distributionVT:2.51508,distributionNT:2.51508,ntShare:0,
    electricityTax:0.03424,systemServices:0.19873,poze:0,supplyFixed:163.35,networkFixed:15.57,breakerFixed:309.76,
    gasBand:3,annualGas:16000,gasSupply:1.06,gasDistribution:0.41324,gasOTE:0.00491,gasTax:0,
    gasSupplyFixed:163.35,gasDistributionFixed:268.85,custom:false};
}
function energyPrices(config) {
  const share=config.tariff==='D57d'?config.ntShare/100:0;
  const common=config.electricityTax+config.systemServices+config.poze;
  const vt=config.supplyVT+config.distributionVT+common, nt=config.supplyNT+config.distributionNT+common;
  const electricity=vt*(1-share)+nt*share;
  const breaker=config.existingConnection?0:config.breakerFixed;
  const fixed=breaker; // Only heating-related breaker costs are included.
  const gas=config.gasSupply+config.gasDistribution+config.gasOTE+config.gasTax;
  const gasFixed=config.gasSupplyFixed+config.gasDistributionFixed;
  return {vt,nt,electricity,breaker,fixed,gas,gasFixed,
    averageEl:electricity+12*fixed/config.annualEl,averageGas:gas+12*gasFixed/config.annualGas};
}
const energyNumberBounds={annualEl:[1,1000000],annualGas:[1,1000000],ntShare:[0,100],
  supplyVT:[0,100],supplyNT:[0,100],distributionVT:[0,100],distributionNT:[0,100],electricityTax:[0,100],systemServices:[0,100],poze:[0,100],
  supplyFixed:[0,100000],networkFixed:[0,100000],breakerFixed:[0,100000],
  gasSupply:[0,100],gasDistribution:[0,100],gasOTE:[0,100],gasTax:[0,100],gasSupplyFixed:[0,100000],gasDistributionFixed:[0,100000]};
function validateEnergyConfig(value) {
  if(!value||!Object.hasOwn(energyTariffs,value.tariff))throw Error('Neplatná sazba elektřiny.');
  const result={...defaultEnergyConfig(),tariff:value.tariff};
  for(const [k,[lo,hi]] of Object.entries(energyNumberBounds)) {
    if(!Number.isFinite(value[k])||value[k]<lo||value[k]>hi)throw Error('Neplatná cena nebo spotřeba: '+k);
    result[k]=value[k];
  }
  for(const k of ['existingConnection','includeOtherFixed','custom']){if(typeof value[k]!=='boolean')throw Error('Neplatná volba energie.');result[k]=value[k];}
  for(const [k,max] of [['breakerIndex',7],['gasBand',5]]){if(!Number.isInteger(value[k])||value[k]<0||value[k]>max)throw Error('Neplatné pásmo.');result[k]=value[k];}
  return result;
}
function applyEnergyPrices() {
  if(!state.energy)return;
  const prices=energyPrices(state.energy);
  state.electricityPrice=prices.electricity;state.elMonthlyExtra=prices.fixed;
  state.gasPrice=prices.gas;state.gasMonthlyFixed=prices.gasFixed;
}
function changeEnergy(key,value) {
  const next={...state.energy};
  if(key==='tariff'){
    if(!Object.hasOwn(energyTariffs,value))return;
    const t=energyTariffs[value];
    Object.assign(next,{tariff:value,supplyVT:t.supplyVT,supplyNT:t.supplyNT,distributionVT:t.distributionVT,distributionNT:t.distributionNT,ntShare:t.ntShare,breakerFixed:t.breakers[next.breakerIndex]});
  } else if(key==='breakerIndex') {
    const i=Number(value);if(!Number.isInteger(i)||i<0||i>7)return;
    next.breakerIndex=i;next.breakerFixed=energyTariffs[next.tariff].breakers[i];
  } else if(key==='gasBand') {
    const i=Number(value);if(!Number.isInteger(i)||i<0||i>5)return;
    const b=gasBands[i];Object.assign(next,{gasBand:i,gasDistribution:b.distribution,gasSupplyFixed:b.supplyFixed,gasDistributionFixed:b.distributionFixed});
  } else if(['existingConnection','includeOtherFixed'].includes(key))next[key]=Boolean(value);
  else if(Object.hasOwn(energyNumberBounds,key)){
    const [lo,hi]=energyNumberBounds[key], v=Number(value);
    if(value===''||!Number.isFinite(v)||v<lo||v>hi){renderEnergySettings();return;}
    next[key]=v;if(!['annualEl','annualGas','ntShare'].includes(key))next.custom=true;
  } else return;
  state.energy=validateEnergyConfig(next);
  recalculateSimulation();updateUI();
}
function resetEnergyPrices() {
  state.energy=defaultEnergyConfig();recalculateSimulation();updateUI();
}
function renderEnergySettings() {
  const box=document.getElementById('energy-form');if(!box||!state.energy)return;
  const e=state.energy, p=energyPrices(e);
  const field=(key,label,unit='Kč/kWh',step='0.00001')=>`<label class="energy-field" for="energy-${key}"><span>${label} <small>${unit}</small></span><input id="energy-${key}" type="number" min="${energyNumberBounds[key][0]}" max="${energyNumberBounds[key][1]}" step="${step}" onchange="changeEnergy('${key}',this.value)"></label>`;
  if(!box.dataset.ready){
    box.innerHTML=`<p class="energy-note">Všechny ceny včetně 21 % DPH. ČEZ Fix na 3 roky · ČEZ Distribuce / GasNet · ověřeno 25. 10. 2026. Výchozí jistič 3×25 A je předpoklad, upravte podle smlouvy.</p>
    <div class="energy-grid"><section><h3>Elektřina</h3>
    <label class="energy-field" for="energy-tariff"><span>Distribuční sazba</span><select id="energy-tariff" onchange="changeEnergy('tariff',this.value)"><option>D02d</option><option>D57d</option></select></label>
    <label class="energy-field" for="energy-breakerIndex"><span>Hlavní jistič</span><select id="energy-breakerIndex" onchange="changeEnergy('breakerIndex',this.value)">${breakerLabels.map((s,i)=>`<option value="${i}">${s}</option>`).join('')}</select></label>
    <label class="energy-check"><input id="energy-existingConnection" type="checkbox" onchange="changeEnergy('existingConnection',this.checked)"> Elektro přípojku stejně používám</label>
    <p class="energy-note">Zaškrtnutí vyřadí pouze poplatek za jistič ze srovnání vytápění. Na skutečné faktuře zůstává. Při změně sazby či jističe může vzniknout rozdíl plateb. Ostatní stálé platby elektřiny se do topení nezapočítávají.</p>
    ${field('supplyVT','Silová elektřina VT')}${field('distributionVT','Distribuce VT')}
    <div id="energy-nt-fields">${field('supplyNT','Silová elektřina NT')}${field('distributionNT','Distribuce NT')}${field('ntShare','Podíl spotřeby v NT','%','0.1')}<p class="energy-note">Výchozích 83,33 % je odhad, nikoli výsledek konkrétního HDO. Stejný podíl platí pro oba režimy řízení.</p></div>
    ${field('electricityTax','Daň z elektřiny')}${field('systemServices','Systémové služby')}${field('poze','POZE (účtovaná sazba)')}
    <p class="energy-note">POZE je v převzatém ceníku účtováno jako minimum varianty podle jističe a spotřeby; při nulové sazbě podle jističe vychází 0. Vlastní částku zde zadávejte jako výslednou sazbu.</p>
    ${field('breakerFixed','Platba za jistič','Kč/měsíc','0.01')}
    ${field('annualEl','Roční spotřeba pro průměr','kWh/rok','1')}
    <div id="energy-electric-result" class="energy-result"></div><p id="energy-recommendation" class="energy-note"></p>
    <p class="energy-note">D57d je určená pro elektrické vytápění / TČ při splnění podmínek distributora. Pro posouzení sazby použijte celou roční spotřebu domu. Bonusy a individuální nabídky nejsou zahrnuté.</p>
    </section><section><h3>Plyn</h3>
    <label class="energy-field" for="energy-gasBand"><span>Roční odběrové pásmo GasNet</span><select id="energy-gasBand" onchange="changeEnergy('gasBand',this.value)">${gasBands.map((b,i)=>`<option value="${i}">${b.label}</option>`).join('')}</select></label>
    ${field('gasSupply','Dodávka plynu')}${field('gasDistribution','Distribuce plynu bez OTE')}${field('gasOTE','OTE')}${field('gasTax','Daň z plynu (domácnost: 0)')}
    ${field('gasSupplyFixed','Stálá platba dodavateli','Kč/měsíc','0.01')}${field('gasDistributionFixed','Stálá platba distribuci','Kč/měsíc','0.01')}${field('annualGas','Roční spotřeba pro průměr','kWh/rok','1')}
    <div id="energy-gas-result" class="energy-result"></div><p id="energy-gas-band-note" class="energy-note"></p>
    <label class="energy-check"><input id="energy-ets" type="checkbox" onchange="state.etsEnabled=this.checked;recalculateSimulation();updateUI()"> Zahrnout scénář ETS 2</label>
    <p class="energy-note">Cenu povolenky nastavíte níže v této kartě. Základní ceník níže ETS 2 nezahrnuje.</p>
    <label class="energy-check"><input id="energy-retainGas" type="checkbox" onchange="state.retainGas=this.checked;recalculateSimulation();updateUI()"> Přípojku plynu ponechám i u TČ</label>
    <p class="energy-note">Při ponechání přípojky se její stálé platby započítají i k TČ.</p>
    <h3>Jak se ceny použijí</h3><p class="energy-note">Průměr v záhlaví = cena odebrané kWh + 12× započtené měsíční platby / zadaná roční spotřeba. Roční spotřeba zde slouží pouze k přepočtu této ceny. Simulace oceňuje skutečnou spotřebu a přičítá stálé platby zvlášť, nikdy dvakrát. V sezónním přehledu se platby poměrně krátí.</p>
    <p class="energy-note">Výchozí produkt Fix na 3 roky má nejnižší cenu komodity mezi porovnanými standardními nabídkami ČEZ Fix 3 roky, Online 1 rok a Na neurčito. Sjednání je podmíněno nabídkou pro odběrné místo a tříletým závazkem; nejde o záruku nejnižší celkové ceny pro každou domácnost.</p>
    <p class="energy-note"><a href="${energySources.electricity}" target="_blank" rel="noopener">Ceník elektřiny (30. 1. 2026)</a> · <a href="${energySources.gas}" target="_blank" rel="noopener">Ceník plynu (17. 4. 2026)</a> · regulované ceny od 1. 1. 2026.</p>
    </section></div><div class="energy-footer"><span id="energy-edited"></span><button type="button" onclick="resetEnergyPrices()">Obnovit ceníky ČEZ</button><button type="button" onclick="document.getElementById('energy-card').open=false">Minimalizovat</button></div>`;
    box.dataset.ready='true';
  }
  for(const key of [...Object.keys(energyNumberBounds),'tariff','breakerIndex','gasBand']){const input=document.getElementById('energy-'+key);if(input)input.value=e[key];}
  for(const key of ['existingConnection'])document.getElementById('energy-'+key).checked=e[key];
  document.getElementById('energy-ets').checked=state.etsEnabled;
  document.getElementById('energy-retainGas').checked=state.retainGas;
  document.getElementById('energy-breakerFixed').disabled=e.existingConnection;
  document.getElementById('energy-nt-fields').hidden=e.tariff!=='D57d';
  document.getElementById('energy-summary').textContent=`${e.tariff} · ${nfmt(p.averageEl,2)} Kč/kWh`;
  document.getElementById('energy-electric-result').textContent=`Za odběr ${nfmt(p.electricity,5)} Kč/kWh · stálé platby ${nfmt(p.fixed,2)} Kč/měsíc (z toho jistič ${nfmt(p.breaker,2)} Kč). Průměr ${nfmt(p.averageEl,2)} Kč/kWh.`;
  document.getElementById('energy-gas-result').textContent=`Za odběr ${nfmt(p.gas,5)} Kč/kWh · stálé platby ${nfmt(p.gasFixed,2)} Kč/měsíc. Průměr ${nfmt(p.averageGas,2)} Kč/kWh bez ETS 2.`;
  const limits=[1890,7560,15000,25000,45000,63000], band=limits.findIndex(v=>e.annualGas<=v);
  document.getElementById('energy-gas-band-note').textContent=band<0?'Nad 63 MWh je nutný kapacitní ceník; toto pásmo model nepokrývá.':band!==e.gasBand?'Zadaná roční spotřeba odpovídá jinému pásmu. Zvolte '+gasBands[band].label+'.':'Pásmo odpovídá zadané roční spotřebě.';
  const comparisons=Object.entries(energyTariffs).map(([tariff,t])=>{const config={...e,...t,tariff,breakerFixed:t.breakers[e.breakerIndex]};return {tariff,cost:energyPrices(config).averageEl*e.annualEl};}).sort((a,b)=>a.cost-b.cost);
  document.getElementById('energy-recommendation').textContent=`Při cenách Fix 3 roky a zadané spotřebě vychází z D02d/D57d levněji ${comparisons[0].tariff}, přibližně o ${nfmt(comparisons[1].cost-comparisons[0].cost)} Kč/rok. Pro D57d se zde předpokládá 83,33 % odběru v NT; nejde o individuální návrh tarifu.`;
  document.getElementById('energy-edited').textContent=e.custom?'Ceník obsahuje vlastní úpravy.':'Předvyplněno z ceníků ČEZ.';
  for(const [id,value] of [['input-price',p.electricity],['input-gas-price',p.gas]]){const input=document.getElementById(id);input.value=value;const numeric=document.getElementById(id+'-number');if(numeric)numeric.value=value;}
}
// Keep all existing cost views on the same derived prices, including resets.
const recalculateBeforeEnergy=recalculateSimulation;
recalculateSimulation=function(){state.automationLevel="optimized";applyEnergyPrices();recalculateBeforeEnergy();};
const updateBeforeEnergy=updateUI;
updateUI=function(){updateBeforeEnergy();renderEnergySettings();};
const initBeforeEnergy=init;
init=function(){state.energy=defaultEnergyConfig();initBeforeEnergy();renderEnergySettings();};
const resetBeforeEnergy=resetDefaultParameters;
resetDefaultParameters=function(){state.energy=defaultEnergyConfig();resetBeforeEnergy();};
