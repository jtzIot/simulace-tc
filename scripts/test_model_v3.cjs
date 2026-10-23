const fs=require('fs'), vm=require('vm'), assert=require('assert/strict'), path=require('path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
scripts.forEach(s=>new vm.Script(s));
const app=scripts.find(s=>s.includes('let rawWeather'));
const run=new Function('window','document',app+'\nreturn code => eval(code);')({addEventListener(){}},{});
run("Object.assign(state,{economyPeriod:'season',etsEnabled:false,retainGas:false,gasMonthlyFixed:135,elMonthlyExtra:0,summerDhwCop:2.7,weatherBaseAltitude:392}); recalculateSimulation();");
const results=run('simResults');
for(const [season,x] of Object.entries(results)) {
  const r=x.results;
  assert(Number.isFinite(r.el_opt_kwh)&&r.el_opt_kwh>0,season);
  assert(Math.abs(x.daily.reduce((a,d)=>a+d.el_opt,0)-r.el_opt_kwh)<1e-6,'daily energy');
  for(const c of Object.values(r.comfort)) {
    assert(Math.abs(c.balanceError)<1e-7,'energy conservation '+season);
    assert(c.starts>0 && c.starts<c.hours.length*6,'transition count');
    assert(c.under+c.over<=c.hours.length+1e-5,'comfort hours');
  }
}
const gas=run("economyFor(simResults['2022-2023'].results,'2022-2023')");
assert.equal(gas.ets,0);
run('state.etsEnabled=true');
const ets=run("economyFor(simResults['2022-2023'].results,'2022-2023')");
assert(Math.abs(ets.saving-gas.saving-ets.ets)<1e-8,'ETS isolated');
run("state.etsEnabled=false; state.automationLevel='baseline'; recalculateSimulation()");
for(const x of Object.values(run('simResults'))) assert.equal(x.results.diff_kwh,0,'baseline identity');
const annual=run("economyFor(simResults['2022-2023'].results,'2022-2023','annual')");
const season=run("economyFor(simResults['2022-2023'].results,'2022-2023','season')");
assert(annual.electricity>season.electricity&&annual.gasTotal>season.gasTotal,'summer included');
run("state.dhwEnabled=false;state.automationLevel='predictive';recalculateSimulation()");
for(const x of Object.values(run('simResults')))assert.equal(x.results.el_opt_dhw,0,'DHW disabled');
run('state.dhwEnabled=true;state.dhwMode="standard";recalculateSimulation()');
for(const x of Object.values(run('simResults')))assert.equal(x.results.el_opt_dhw,x.results.el_std_dhw,'standard DHW respected');
run('state.qLossDesign=15;state.tTolerance=0.1;recalculateSimulation()');
assert(Object.values(run('simResults')).some(x=>x.results.comfort.opt.min<21.9),'no free temperature clamp');
assert(Object.values(run('simResults')).some(x=>x.results.comfort.opt.backup>0),'backup consumed');
run('state.heatingSystem="radiator";recalculateSimulation()');
for(const x of Object.values(run('simResults')))assert(Math.abs(x.results.comfort.opt.balanceError)<1e-7,'radiator balance');
console.log('PASS: syntax, 10 seasons, energy balance, aggregation, baseline identity, ETS, annual TUV, DHW off/standard, cold load and radiator.');
console.log(JSON.stringify(Object.fromEntries(Object.entries(results).map(([s,x])=>[s,{kWh:Math.round(x.results.el_opt_kwh),saving:Math.round(x.results.savings_czk),min:x.results.comfort.opt.min,under:x.results.comfort.opt.under,starts:x.results.starts_opt}])) ,null,2));
