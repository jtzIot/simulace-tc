const fs=require('fs'),assert=require('node:assert/strict'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const app=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(x=>x.includes('let rawWeather'));
const run=new Function('window','document',app+';return x=>eval(x)')({addEventListener(){}},{});
const near=(a,b,msg)=>assert(Math.abs(a-b)<1e-7,msg+': '+a+' != '+b);
assert.equal(run('keymarkDatabase.filter(h=>h.selectable!==false).length'),19);
assert(run('keymarkDatabase.filter(h=>h.selectable!==false).every(h=>!!h.km&&!!validateKeymarkConfig(h.km))'));
const all=run('keymarkDatabase.filter(h=>h.selectable!==false)');
for(const h of all){
 assert(h.km.cert===h.certNo&&h.km.model===h.modelCode,'source identity '+h.id);
 for(const group of ['lt','mt'])for(const p of h.km[group].points){
  near(run(`kmAt(keymarkDatabase.find(h=>h.id===${JSON.stringify(h.id)}).km.${group},${p.air}).cop`),p.cop,'measured knot '+h.id);
 }
}
assert.equal(run('defaultHouseholdConfig().enabled'),true);assert.equal(run('defaultHouseholdConfig().mode'),'profiles');
near(run('householdSplit(defaultEnergyConfig()).total'),2000,'default annual consumption');
assert.equal(run('migrateControlPolicy("optimum")'),'day');
assert.equal(run('migrateControlPolicy("economic")'),'day');
assert.equal(run('migrateControlPolicy("tariff")'),'tariff');
assert(!html.includes('chooseTheoreticalRun'));
assert(!html.includes('theoretical-summary'));
assert(!html.includes('value="optimum"'));
run('state.control={...defaultControl(),policy:"optimum"};recalculateSimulation()');
assert.equal(run('state.control.policy'),'day');
console.log('PASS: all 19 model identities and measured knots, 2 MWh profile defaults, removed theoretical engine and migration of older policies.');
