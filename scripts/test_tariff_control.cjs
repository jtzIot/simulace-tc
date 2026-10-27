const fs=require('fs'),assert=require('assert/strict');
const html=fs.readFileSync(require('path').join(__dirname,'../index.html'),'utf8');
const app=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(x=>x.includes('let rawWeather'));
const run=new Function('window','document',app+'\nreturn code=>eval(code);')({addEventListener(){}},{});
assert.equal(run('state.economyPeriod'),'annual');
run("state.energy=defaultEnergyConfig();state.control=defaultControl();state.economyPeriod='season';state.etsEnabled=true;applyEnergyPrices();");
const near=(a,b)=>assert(Math.abs(a-b)<1e-6,`${a} != ${b}`);
for(const code of ['D01d','D02d','D25d','D26d','D57d']){
 run(`Object.assign(state.energy,energyTariffs['${code}'],{tariff:'${code}',ntWindows:tariffProfiles['${code}'].nt});applyEnergyPrices();recalculateSimulation();`);
 const plan=run('tariffPlan()');near(plan.nt.reduce((s,[a,b])=>s+b-a,0),plan.hours*60);
 run(`parseNtWindows(formatNtWindows(tariffPlan().nt),'${code}')`);
 for(const [season,x] of Object.entries(run('simResults'))){
  const c=x.results.comfort.opt,p=run('energyPrices(state.energy)'),bill=run(`economyFor(simResults['${season}'].results,'${season}')`);
  near(c.elNT+c.elVT,c.e+c.de);near(bill.electricityCost,c.elNT*p.nt+c.elVT*p.vt);near(c.balanceError,0);
  near(bill.hpTotal,bill.electricityCost+bill.hpFixed);near(bill.gasTotal,bill.gasFuel+bill.ets+bill.gasFixed+bill.gasService);
  if(plan.hours)for(const h of c.hours)if(h.ntMinutes===0)near(h.q_dhw,0);
 }
}
assert.throws(()=>run("parseNtWindows('00:00–07:00','D25d')"));
assert.throws(()=>run("parseNtWindows('00:00–06:00,05:00–07:00','D25d')"));
assert.throws(()=>run("parseNtWindows('00:00–20:00','D57d')"));
run('state.qLossDesign=14;state.control.blockCompressor=true;recalculateSimulation()');
for(const x of Object.values(run('simResults')))for(const h of x.results.comfort.opt.hours)if(h.ntMinutes===0){near(h.q_hp+h.q_dhw+h.backup+h.dhwBackup,0);near(h.p_el_opt,run('kmIdlePower(true)'));}
run("state.control.blockCompressor=false;state.control.policy='tariff';recalculateSimulation()");
for(const x of Object.values(run('simResults')))for(const h of x.results.comfort.opt.hours){assert.equal(h.isCharge,h.ntMinutes>0);if(h.ntMinutes===0)near(h.backup+h.dhwBackup,0);}
const before=run("economyFor(simResults['2022-2023'].results,'2022-2023')");
run('state.gasDhwEfficiency=70');const after=run("economyFor(simResults['2022-2023'].results,'2022-2023')");
near(before.hpTotal,after.hpTotal);assert(after.gasTotal>before.gasTotal);
run("state.control.policy='constant';recalculateSimulation()");
assert(run("simResults['2022-2023'].results.comfort.opt.hours.every(h=>!h.isCharge&&!h.isDischarge)"));
console.log('PASS: five tariffs, NT/VT energy and invoices, HDO validation, DHW schedule, D57d compressor and auxiliary blocking, control targets, independent gas DHW efficiency.');
