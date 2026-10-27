// ČEZ Prodej / ČEZ Distribuce and GasNet, verified 2026-10-25.
// All editable amounts include 21% VAT. Unit prices are Kč/kWh.
const energySources = {
  electricity:'https://www.cez.cz/webpublic/file/edee/ceniky/moo_ele_cez_fix_na_3_roky_30012026_012026.pdf',
  gas:'https://www.cez.cz/webpublic/file/edee/ceniky/moo_mop_plyn_gasnet_fix_na_3_roky_17042026_012026.pdf'
};
const energyTariffs = {
  D01d:{supplyVT:3.25,supplyNT:3.25,distributionVT:3.22666,distributionNT:3.22666,ntShare:0,
    breakers:[60.50,95.59,119.79,150.04,191.18,239.58,300.08,377.52]},
  D25d:{supplyVT:3.37,supplyNT:3.13,distributionVT:2.72546,distributionNT:0.14097,ntShare:100/3,
    breakers:[129.47,208.12,260.15,325.49,416.24,520.30,649.77,819.17]},
  D26d:{supplyVT:3.37,supplyNT:3.13,distributionVT:1.45449,distributionNT:0.14097,ntShare:100/3,
    breakers:[175.45,279.51,349.69,438.02,560.23,699.38,874.83,1102.31]},
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
  return {tariff:'D25d',household:defaultHouseholdConfig(),referenceTariff:'D02d',breakerIndex:3,existingConnection:true,includeOtherFixed:false,annualEl:5000,
    supplyVT:3.37,supplyNT:3.13,distributionVT:2.72546,distributionNT:0.14097,ntShare:100/3,
    electricityTax:0.03424,systemServices:0.19873,poze:0,supplyFixed:163.35,networkFixed:15.57,breakerFixed:325.49,
    gasBand:3,annualGas:16000,gasSupply:1.06,gasDistribution:0.41324,gasOTE:0.00491,gasTax:0,
    gasSupplyFixed:163.35,gasDistributionFixed:268.85,custom:false};
}
function energyPrices(config) {
  const share=['D01d','D02d'].includes(config.tariff)?0:config.ntShare/100;
  const common=config.electricityTax+config.systemServices+config.poze;
  const vt=config.supplyVT+config.distributionVT+common, nt=config.supplyNT+config.distributionNT+common;
  const electricity=vt*(1-share)+nt*share;
  const referenceTariff=config.referenceTariff||'D02d';
  const referenceBreaker=energyTariffs[referenceTariff].breakers[config.breakerIndex];
  const breaker=config.breakerFixed-(config.existingConnection?referenceBreaker:0);
  const fixed=breaker; // Only heating-related breaker costs are included.
  const gas=config.gasSupply+config.gasDistribution+config.gasOTE+config.gasTax;
  const gasFixed=config.gasSupplyFixed+config.gasDistributionFixed;
  return {vt,nt,electricity,breaker,referenceBreaker,fixed,gas,gasFixed,
    averageEl:electricity+12*fixed/config.annualEl,averageGas:gas+12*gasFixed/config.annualGas};
}
const energyNumberBounds={annualEl:[1,1000000],annualGas:[1,1000000],ntShare:[0,100],
  supplyVT:[0,100],supplyNT:[0,100],distributionVT:[0,100],distributionNT:[0,100],electricityTax:[0,100],systemServices:[0,100],poze:[0,100],
  supplyFixed:[0,100000],networkFixed:[0,100000],breakerFixed:[0,100000],
  gasSupply:[0,100],gasDistribution:[0,100],gasOTE:[0,100],gasTax:[0,100],gasSupplyFixed:[0,100000],gasDistributionFixed:[0,100000]};
function validateEnergyConfig(value) {
  if(!value||!Object.hasOwn(energyTariffs,value.tariff))throw Error('Neplatná sazba elektřiny.');
  const referenceTariff=value.referenceTariff??'D02d';
  if(!['D01d','D02d'].includes(referenceTariff))throw Error('Neplatný referenční tarif.');
  const result={...defaultEnergyConfig(),tariff:value.tariff,referenceTariff};
  for(const [k,[lo,hi]] of Object.entries(energyNumberBounds)) {
    if(!Number.isFinite(value[k])||value[k]<lo||value[k]>hi)throw Error('Neplatná cena nebo spotřeba: '+k);
    result[k]=value[k];
  }
  for(const k of ['existingConnection','includeOtherFixed','custom']){if(typeof value[k]!=='boolean')throw Error('Neplatná volba energie.');result[k]=value[k];}
  for(const [k,max] of [['breakerIndex',7],['gasBand',5]]){if(!Number.isInteger(value[k])||value[k]<0||value[k]>max)throw Error('Neplatné pásmo.');result[k]=value[k];}
  if(value.ntWindows)result.ntWindows=parseNtWindows(formatNtWindows(value.ntWindows),value.tariff);
  result.household=validateHouseholdConfig(value.household??{...defaultHouseholdConfig(),enabled:false,mode:'manual',vt:2000,nt:1000});
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
    next.ntWindows=tariffProfiles[value].nt.map(x=>[...x]);
    Object.assign(next,{tariff:value,supplyVT:t.supplyVT,supplyNT:t.supplyNT,distributionVT:t.distributionVT,distributionNT:t.distributionNT,ntShare:t.ntShare,breakerFixed:t.breakers[next.breakerIndex]});
  } else if(key==='referenceTariff') {
    if(!['D01d','D02d'].includes(value))return;next.referenceTariff=value;
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
  if(key==='tariff')recalculateSimulation();
  else if(typeof recalculateEconomy==='function')recalculateEconomy();
  else recalculateSimulation();
  updateUI();
}
function resetEnergyPrices() {
  state.energy=defaultEnergyConfig();recalculateSimulation();updateUI();
}
function renderEnergySettings() {
  const box=document.getElementById('energy-form');if(!box||!state.energy)return;
  const e=state.energy, p=energyPrices(e);
  const field=(key,label,unit='Kč/kWh',step='0.00001')=>`<label class="energy-field" for="energy-${key}"><span>${label} <small>${unit}</small></span><input id="energy-${key}" type="number" min="${energyNumberBounds[key][0]}" max="${energyNumberBounds[key][1]}" step="${step}" onchange="changeEnergy('${key}',this.value)"></label>`;
  if(!box.dataset.ready){
    box.innerHTML=`<div class="energy-grid"><section class="config-subcard"><h3>⚡ Distribuční sazba a jistič (ČEZ)</h3>
    <p class="energy-note">Všechny ceny včetně 21 % DPH · ČEZ Fix na 3 roky · ČEZ Distribuce.</p>
    <label class="energy-field" for="energy-tariff"><span>Distribuční sazba</span><select id="energy-tariff" onchange="changeEnergy('tariff',this.value)">${['D01d','D02d','D25d','D26d','D57d'].map(t=>`<option>${t}</option>`).join('')}</select></label>
    <label class="energy-field" for="energy-breakerIndex"><span>Hlavní jistič</span><select id="energy-breakerIndex" onchange="changeEnergy('breakerIndex',this.value)">${breakerLabels.map((s,i)=>`<option value="${i}">${s}</option>`).join('')}</select></label>
    <label class="energy-check" style="display:none;"><input id="energy-existingConnection" type="checkbox" onchange="changeEnergy('existingConnection',this.checked)"> Elektro přípojku stejně používám pro dům (započítat jen rozdíl jističe)</label>
    <label id="energy-reference-field" class="energy-field" for="energy-referenceTariff"><span>Tarif, který bych používal s plynem</span><select id="energy-referenceTariff" onchange="changeEnergy('referenceTariff',this.value)"><option>D01d</option><option>D02d</option></select></label>
    <p id="energy-breaker-comparison" class="energy-note"></p>
    <div id="energy-electric-result" class="energy-result"></div>
    <details class="km-details"><summary>Upravit jednotkové ceny ceníku elektřiny (VT/NT, distribuce, POZE)</summary>
      ${field('supplyVT','Silová elektřina VT')}${field('distributionVT','Distribuce VT')}
      <div id="energy-nt-fields">${field('supplyNT','Silová elektřina NT')}${field('distributionNT','Distribuce NT')}<p class="energy-note">Spotřeba v NT/VT se počítá po 10 minutách podle provozu a rozvrhu v záložce Režimy řízení.</p></div>
      ${field('electricityTax','Daň z elektřiny')}${field('systemServices','Systémové služby')}${field('poze','POZE (účtovaná sazba)')}
      ${field('breakerFixed','Platba za jistič','Kč/měsíc','0.01')}
      ${field('annualEl','Roční spotřeba pro průměr','kWh/rok','1')}
      <p id="energy-recommendation" class="energy-note"></p>
    </details>
    <div class="energy-footer"><span id="energy-edited"></span><button type="button" class="workspace-button" onclick="resetEnergyPrices()">Obnovit ceníky ČEZ</button><button type="button" onclick="document.getElementById('energy-card').open=false">Minimalizovat</button></div>
    </section><section class="config-subcard"><h3>🔥 Ceník plynu (GasNet) a scénář ETS 2</h3>
    <label class="energy-field" for="energy-gasBand"><span>Roční odběrové pásmo GasNet</span><select id="energy-gasBand" onchange="changeEnergy('gasBand',this.value)">${gasBands.map((b,i)=>`<option value="${i}">${b.label}</option>`).join('')}</select></label>
    <p id="energy-gas-band-note" class="energy-note"></p>
    <div id="energy-gas-result" class="energy-result"></div>
    <label class="energy-check"><input id="energy-ets" type="checkbox" onchange="state.etsEnabled=this.checked;recalculateEconomy();updateUI()"> Zahrnout scénář ETS 2</label>
    <label class="energy-check"><input id="energy-retainGas" type="checkbox" onchange="state.retainGas=this.checked;recalculateEconomy();updateUI()"> Přípojku plynu ponechám i u TČ</label>
    <details class="km-details"><summary>Upravit jednotkové ceny plynu a stálé platby</summary>
      ${field('gasSupply','Dodávka plynu')}${field('gasDistribution','Distribuce plynu bez OTE')}${field('gasOTE','OTE')}${field('gasTax','Daň z plynu (domácnost: 0)')}
      ${field('gasSupplyFixed','Stálá platba dodavateli','Kč/měsíc','0.01')}${field('gasDistributionFixed','Stálá platba distribuci','Kč/měsíc','0.01')}${field('annualGas','Roční spotřeba pro průměr','kWh/rok','1')}
      <p class="energy-note"><a href="${energySources.electricity}" target="_blank" rel="noopener">Ceník elektřiny (30. 1. 2026)</a> · <a href="${energySources.gas}" target="_blank" rel="noopener">Ceník plynu (17. 4. 2026)</a> · regulované ceny od 1. 1. 2026.</p>
    </details>
    </section></div>`;
    box.dataset.ready='true';
  }
  for(const key of [...Object.keys(energyNumberBounds),'tariff','referenceTariff','breakerIndex','gasBand']){const input=document.getElementById('energy-'+key);if(input)input.value=e[key];}
  for(const key of ['existingConnection'])document.getElementById('energy-'+key).checked=e[key];
  document.getElementById('energy-ets').checked=state.etsEnabled;
  document.getElementById('energy-retainGas').checked=state.retainGas;
  document.getElementById('energy-breakerFixed').disabled=false;
  document.getElementById('energy-referenceTariff').value=e.referenceTariff||'D02d';
  const refFld=document.getElementById('energy-reference-field');if(refFld)refFld.hidden=false;
  document.getElementById('energy-breaker-comparison').textContent=`Jistič ${breakerLabels[e.breakerIndex]}: TČ (${e.tariff}) ${nfmt(e.breakerFixed,2)} Kč/měsíc · Plyn (${e.referenceTariff||'D02d'}) ${nfmt(p.referenceBreaker,2)} Kč/měsíc.`;
  const gasRefNote=document.getElementById('gas-reference-tariff-note');
  if(gasRefNote)gasRefNote.textContent=`Jistič ${breakerLabels[e.breakerIndex]} v sazbě ${e.referenceTariff||'D02d'}: ${nfmt(p.referenceBreaker,2)} Kč/měsíc (${nfmt(p.referenceBreaker*12,0)} Kč/rok).`;
  document.getElementById('energy-nt-fields').hidden=['D01d','D02d'].includes(e.tariff);
  document.getElementById('energy-summary').textContent=`${e.tariff} · ${nfmt(p.averageEl,2)} Kč/kWh`;
  document.getElementById('energy-electric-result').textContent=`VT ${nfmt(p.vt,2)} Kč/kWh${['D01d','D02d'].includes(e.tariff)?'':' · NT '+nfmt(p.nt,2)+' Kč/kWh'} · stálé platby do vytápění ${nfmt(p.fixed,2)} Kč/měsíc.`;
  document.getElementById('energy-gas-result').textContent=`Za odběr ${nfmt(p.gas,2)} Kč/kWh · stálé platby ${nfmt(p.gasFixed,2)} Kč/měsíc (průměr ${nfmt(p.averageGas,2)} Kč/kWh bez ETS 2).`;
  const limits=[1890,7560,15000,25000,45000,63000], band=limits.findIndex(v=>e.annualGas<=v);
  document.getElementById('energy-gas-band-note').textContent=band<0?'Nad 63 MWh je nutný kapacitní ceník; toto pásmo model nepokrývá.':band!==e.gasBand?'Zadaná roční spotřeba odpovídá jinému pásmu. Zvolte '+gasBands[band].label+'.':'Pásmo odpovídá zadané roční spotřebě.';
  document.getElementById('energy-recommendation').textContent='Sazby D25d a D26d vyžadují akumulační spotřebič; samotná podlahová akumulace s TČ nárok nedokládá. D57d je sazba pro elektrické vytápění. Volba zde není potvrzením nároku na sazbu.';
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

// Other household appliances are accounted for separately from heating and standing charges.
function defaultHouseholdConfig(){return {enabled:true,mode:'profiles',profiles:defaultApplianceProfiles().map(x=>({...x,kwh:x.kwh*2/3})),vt:4000/3,nt:2000/3,appliances:'Lednice a mrazák, pračka, myčka, vaření, osvětlení a elektronika'};}
function validateHouseholdConfig(h){
 if(!h||typeof h.enabled!=='boolean'||![h.vt,h.nt].every(n=>Number.isFinite(n)&&n>=0&&n<=1000000)||h.vt+h.nt>1000000||typeof h.appliances!=='string'||h.appliances.length>400)throw Error('Neplatná spotřeba zbytku domu.');
 const mode=h.mode??'manual';if(!['manual','profiles'].includes(mode))throw Error('Neplatný režim profilu.');
 const profiles=h.profiles??defaultApplianceProfiles();
 if(!Array.isArray(profiles)||profiles.length<1||profiles.length>24||profiles.some(x=>!x||!Object.hasOwn(applianceProfiles,x.type)||!Number.isFinite(x.kwh)||x.kwh<0||x.kwh>1000000)||profiles.reduce((a,x)=>a+x.kwh,0)>1000000)throw Error('Neplatné profily spotřebičů.');
 return {enabled:h.enabled,vt:h.vt,nt:h.nt,appliances:h.appliances,mode,profiles:profiles.map(x=>({type:x.type,kwh:x.kwh}))};
}
function householdEconomy(config=state.energy,fraction=1){
 const h=validateHouseholdConfig(config.household??defaultHouseholdConfig()),p=energyPrices(config),base=energyTariffs[config.referenceTariff||'D02d'];
 const baselineVT=base.supplyVT+base.distributionVT+config.electricityTax+config.systemServices+config.poze;
 const split=householdSplit(config);
 const annualKwh=h.enabled?split.total:0,ntKwh=h.enabled?split.nt:0,vtKwh=annualKwh-ntKwh;
 const annualHp=vtKwh*p.vt+ntKwh*p.nt,annualGas=annualKwh*baselineVT;
 return {annualKwh,vtKwh,ntKwh,baselineVT,annualHp,annualGas,annualSaving:annualGas-annualHp,hp:annualHp*fraction,gas:annualGas*fraction,saving:(annualGas-annualHp)*fraction};
}

// Illustrative daily profiles, not measured appliance curves. Annual kWh are user inputs.
const applianceProfiles={
 cold:{label:'Lednice a mrazák',description:'Rovnoměrně 24 hodin; kompresor ve skutečnosti cykluje.',weights:Array(24).fill(1)},
 standby:{label:'Trvalý odběr / ostatní',description:'Rovnoměrně 24 hodin.',weights:Array(24).fill(1)},
 washer:{label:'Pračka',description:'Příklad cyklu 09–11 h; bez automatického přesunu do NT.',weights:Array.from({length:24},(_,h)=>h>=9&&h<11?1:0)},
 dishwasher:{label:'Myčka',description:'Příklad cyklu 20–22 h; bez automatického přesunu do NT.',weights:Array.from({length:24},(_,h)=>h>=20&&h<22?1:0)},
 cooking:{label:'Vaření',description:'Příklad: 07–08 h, 12–13 h a nejvíce 18–20 h.',weights:Array.from({length:24},(_,h)=>h===7||h===12?1:h>=18&&h<20?2:0)},
 lighting:{label:'Osvětlení',description:'Příklad: ráno 06–08 h, večer 17–23 h.',weights:Array.from({length:24},(_,h)=>h>=6&&h<8||h>=17&&h<23?1:0)},
 electronics:{label:'Elektronika / TV / počítače',description:'Příklad: hlavní provoz 17–23 h, jinak malý odběr.',weights:Array.from({length:24},(_,h)=>h>=17&&h<23?1:.15)}
};
function defaultApplianceProfiles(){return [{type:'cold',kwh:400},{type:'washer',kwh:250},{type:'dishwasher',kwh:250},{type:'cooking',kwh:600},{type:'lighting',kwh:400},{type:'electronics',kwh:1100}];}
function applianceNtShare(type,config){
 const p=applianceProfiles[type],plan={...tariffProfiles[config.tariff],nt:config.ntWindows??tariffProfiles[config.tariff].nt};
 let total=0,nt=0;for(let step=0;step<144;step++){const w=p.weights[Math.floor(step/6)];total+=w;if(ntAt(step*10,plan))nt+=w;}
 return total?nt/total:0;
}
function householdSplit(config=state.energy){
 const h=validateHouseholdConfig(config.household??defaultHouseholdConfig());
 if(h.mode==='profiles'){
  const rows=h.profiles.map(x=>({...x,share:applianceNtShare(x.type,config)}));
  const total=rows.reduce((a,x)=>a+x.kwh,0),nt=rows.reduce((a,x)=>a+x.kwh*x.share,0);
  return {total,nt,vt:total-nt,rows};
 }
 const total=h.vt+h.nt,nt=['D01d','D02d'].includes(config.tariff)?0:h.nt;
 return {total,nt,vt:total-nt,rows:[]};
}
function householdApplianceNames(config=state.energy){const h=validateHouseholdConfig(config.household??defaultHouseholdConfig());return h.mode==='profiles'?[...new Set(h.profiles.filter(x=>x.kwh>0).map(x=>applianceProfiles[x.type].label))].join(', '):h.appliances;}
