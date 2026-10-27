with open('scripts/workspace-ui.js', 'r', encoding='utf-8') as f:
    code = f.read()

report_functions = '''
function buildReportData(){
 const seasons=getActiveSeasons(),costs=seasons.map(s=>economyFor(simResults[s].results,s));
 const avg=k=>costs.reduce((a,c)=>a+c[k],0)/(costs.length||1),p=energyPrices(state.energy);
 const hp=avg('hpTotal'),gas=avg('gasTotal'),saving=gas-hp;
 const r=simResults[state.currentSeason]?.results||{};
 const seasonalFactor=avg('fraction'),household=householdEconomy(state.energy,seasonalFactor);
 const includeHousehold=Boolean(state.energy.household?.enabled);
 const totalHp=hp+household.hp,totalGas=gas+household.gas,totalSaving=saving+household.saving;
 const heatElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_heat,0)/(seasons.length||1);
 const dhwElAvg=seasons.reduce((a,s)=>a+simResults[s].results.el_opt_dhw,0)/(seasons.length||1)+avg('summerEl');
 const plan=tariffPlan(),split=householdSplit(state.energy);
 const etsSur=state.co2AllowancePriceEur*25.0*0.00018*1.21;
 const activeHp=state.activeHp||{};
 const isRadiator=state.heatingSystem==='radiator';
 const locationEl=document.getElementById('badge-location');
 const locationName=locationEl?locationEl.textContent.replace(/^[📍\\s]+/,'').trim():'Ostrava';

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
   certNo:activeHp.certNo||'011-1W1325',
   pDesign:isRadiator?(activeHp.pDesign55||7.5):(activeHp.pDesign35||8.1),
   scop:isRadiator?(activeHp.scop55||3.62):(activeHp.scop35||4.87),
   refrigerant:activeHp.refrigerant||'R32',
   serviceCost:state.hpServiceYearly||0
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
   referenceVt:p.referenceVT
  },
  summary:{
   seasonsCount:seasons.length,
   seasonsRange:`${seasons[0]} až ${seasons.at(-1)}`,
   includeHousehold,
   totalHp,
   totalGas,
   totalSaving,
   savingPercent:totalGas>0?((totalSaving/totalGas)*100).toFixed(1):'0',
   heatingHp:hp,
   heatingGas:gas,
   heatingSaving:saving,
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
   return {
    season:s,
    heatKwh:sRes.th_opt,
    elKwh:sEco.electricity,
    scop:sRes.scop_opt,
    costHp:sEco.hpTotal,
    costGas:sEco.gasTotal,
    saving:sEco.saving
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
      <div class="sub">Vytápění + TUV: <b>${nfmt(d.summary.heatingHp)} Kč</b>${d.household.enabled?`<br>Ostatní spotřebiče domu: <b>${nfmt(d.household.costHp)} Kč</b>`:''}</div>
    </div>
    <div class="report-hero-card gas">
      <div class="label">🔥 Plynový kotel</div>
      <div class="value">${nfmt(d.summary.totalGas)} Kč/rok</div>
      <div class="sub">Plyn (topení + TUV): <b>${nfmt(d.summary.heatingGas)} Kč</b>${d.household.enabled?`<br>Ostatní spotřebiče domu: <b>${nfmt(d.household.costGas)} Kč</b>`:''}</div>
    </div>
    <div class="report-hero-card saving">
      <div class="label">💰 Roční úspora s TČ</div>
      <div class="value">${d.summary.totalSaving>=0?'+':''}${nfmt(d.summary.totalSaving)} Kč/rok</div>
      <div class="sub">${d.summary.totalSaving>=0?`Úspora <b>${d.summary.savingPercent} %</b> celkových nákladů`:'Vyšší provozní náklady s TČ'}<br>Jen topení a TUV: <b>${d.summary.heatingSaving>=0?'+':''}${nfmt(d.summary.heatingSaving)} Kč/rok</b></div>
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
      
      <div class="equipment-box">
        <h3><span>⚡ Tepelné čerpadlo vzduch-voda</span><span class="equipment-badge hp">Keymark</span></h3>
        <dl class="report-kv-list">
          <dt>Model čerpadla</dt><dd>${esc(d.heatPump.name)}</dd>
          <dt>Certifikace Keymark</dt><dd>${esc(d.heatPump.certNo)}</dd>
          <dt>Návrhový výkon (při návrhovém mrazu)</dt><dd>${nfmt(d.heatPump.pDesign,1)} kW</dd>
          <dt>Sezónní topný faktor (katalogový SCOP)</dt><dd>SCOP ${nfmt(d.heatPump.scop,2)}</dd>
          <dt>Chladivo / roční servis</dt><dd>${esc(d.heatPump.refrigerant)} · ${nfmt(d.heatPump.serviceCost,0)} Kč/rok</dd>
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
'''

# 1. Insert report functions before setupTheme
target_fn = 'function setupTheme(){'
if target_fn in code and 'function buildReportData' not in code:
    code = code.replace(target_fn, report_functions + '\n' + target_fn)
    print("Inserted report functions")
else:
    print("Note: report functions already present or target not found")

# 2. Add styles to workspaceStyles
styles_to_add = '''
/* Report Modal & CTA */
.report-cta-box .report-btn{background:linear-gradient(135deg,#0284c7 0%,#0369a1 100%);color:#ffffff!important;border:1px solid #38bdf8;border-radius:8px;font-weight:700;transition:all .15s ease;box-shadow:0 2px 6px rgba(2,132,199,.25)}
.report-cta-box .report-btn:hover{background:linear-gradient(135deg,#0369a1 0%,#075985 100%);border-color:#7dd3fc;box-shadow:0 4px 12px rgba(2,132,199,.35)}
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
'''

target_css = 'function installRefinementStyle(){'
if target_css in code and '#report-modal-backdrop' not in code:
    code = code.replace(target_css, styles_to_add + '\n' + target_css)
    print("Inserted modal CSS")

# 3. Add light theme style overrides
refinement_css = '''
html[data-theme=light] #btn-header-report{background:#ffffff!important;color:#0284c7!important;border:1.5px solid #0284c7!important;font-weight:700!important}
html[data-theme=light] #btn-header-report:hover{background:#f0f9ff!important}
html[data-theme=light] .report-cta-box .report-btn{background:linear-gradient(135deg,#0284c7 0%,#0369a1 100%)!important;color:#ffffff!important;border:1px solid #0284c7!important;box-shadow:0 2px 8px rgba(2,132,199,.25)!important}
'''
target_refine_end = 'document.head.append(refinementStyle);'
if target_refine_end in code and 'btn-header-report' not in code:
    code = code.replace(target_refine_end, refinement_css + '\n' + target_refine_end)
    print("Inserted refinement styles")

with open('scripts/workspace-ui.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated scripts/workspace-ui.js successfully")
