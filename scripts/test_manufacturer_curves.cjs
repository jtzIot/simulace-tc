const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const app=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(x=>x.includes('let rawWeather'));
const run=new Function('window','document',app+';return x=>eval(x)')({addEventListener(){}},{});
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9, `${a} != ${b}`);
run("state.activeModelId='gawliczek-pw-89';state.activeHp=keymarkDatabase.find(h=>h.id===state.activeModelId)");
near(run('getCapForActiveModel(-25,35)'),3.3);
near(run('getCopForActiveModel(-25,35,80,3.3)'),3.3/1.96);
near(run('getCapForActiveModel(-22.5,35)'),3.75);
near(run('getCapForActiveModel(-25.1,35)'),0);
near(run('getCapForActiveModel(-25,45)'),3.2);
near(run('getCapForActiveModel(-25,55)'),2.9);
near(run('getCapForActiveModel(-25,30)'),3.3);
for(const id of run('Object.keys(manufacturerCurves)')) {
 const p=run(`manufacturerPoint(${JSON.stringify(id)},-25,35)`);
 assert.ok(p.max>p.min&&p.min>0&&p.pmax>0&&p.pmin>0,id);
}
for(const [id,max,power] of [['gree-versati-8',4.34,2.78],['gree-versati-10',4.69,3.10]]) {
 const p=run(`manufacturerPoint(${JSON.stringify(id)},-25,35)`); near(p.max,max); near(p.pmax,power);
 assert.equal(run(`manufacturerPoint(${JSON.stringify(id)},-25,55)`),null);
 assert.ok(run(`manufacturerPoint(${JSON.stringify(id)},-20,55)`));
 run(`state.activeModelId=${JSON.stringify(id)};state.activeHp=keymarkDatabase.find(h=>h.id===state.activeModelId);state.tFlowDesign=35;state.dhwEnabled=false;state.qLossDesign=15`);
 const result=run('simulateController({t:Array(24).fill(-25),rh:Array(24).fill(80),sol:Array(24).fill(0)},"optimized")');
 assert.ok(result.heat>result.backup, id+' compressor operates at -25 °C');
 near(result.balanceError,0);
}
assert.equal(run("manufacturerPoint('gree-versati-8',-22,55)"),null);
console.log('PASS: source points, interpolation, water boundary and operation to -25 C.');
