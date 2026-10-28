const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('path').join(__dirname,'../index.html'),'utf8');
const app=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.includes('let rawWeather'));
const run=new Function('window','document',app+'\nreturn code=>eval(code)')({addEventListener(){}},{getElementById(){return null;}});
run('state.energy=defaultEnergyConfig();state.economyPeriod="annual";recalculateSimulation()');
for (const enabled of [true,false]) {
 run(`state.energy.household.enabled=${enabled}`);
 const data=run('buildReportData()');
 const rendered=run('generateReportHtml(buildReportData())');
 const row=rendered.match(/<tr class="avg-row">([\s\S]*?)<\/tr>/)[1];
 const cells=[...row.matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1].replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim());
 const average=k=>data.seasonRows.reduce((sum,r)=>sum+r[k],0)/data.seasonRows.length;
 const fmt=(v,d=0)=>Number(v).toLocaleString('cs-CZ',{maximumFractionDigits:d,minimumFractionDigits:d}).replace(/\s+/g,' ');
 assert.equal(cells[0],`Průměr (${data.seasonRows.length} sezón)`);
 for(const [index,key,suffix,digits] of [[1,'heatKwh',' kWh',0],[2,'elKwh',' kWh',0],[3,'scop','',2],[4,'costHp',' Kč',0],[5,'costGas',' Kč',0],[6,'saving',' Kč',0]]) {
  const expected=(key==='saving'&&average(key)>=0?'+':'')+fmt(average(key),digits)+suffix;
  assert.equal(cells[index],expected,key+' household='+enabled);
 }
 assert.ok(rendered.includes('Roční úspora TČ'));
}
run('state.economyPeriod="season"');
assert.ok(run('generateReportHtml(buildReportData())').includes('Sezónní úspora TČ'));
console.log('PASS: report averages match every displayed season, with and without household, annual and seasonal labels.');
