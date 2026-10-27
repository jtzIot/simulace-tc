// Tariff calendars are model assumptions, not downloaded HDO commands.
const tariffProfiles={
 D01d:{hours:0,nt:[],auxBlocked:false,dhwNT:false,label:'Jednotarif · malá spotřeba'},
 D02d:{hours:0,nt:[],auxBlocked:false,dhwNT:false,label:'Jednotarif · běžná spotřeba'},
 D25d:{hours:8,nt:[[0,360],[780,900]],auxBlocked:false,dhwNT:true,label:'Akumulace / bojler · 8 h NT'},
 D26d:{hours:8,nt:[[0,360],[780,900]],auxBlocked:false,dhwNT:true,label:'Akumulační vytápění · 8 h NT'},
 D57d:{hours:20,nt:[[0,420],[480,660],[720,1020],[1080,1200],[1260,1440]],auxBlocked:true,dhwNT:true,label:'Elektrické vytápění / TČ · 20 h NT'}
};
function defaultControl(){return {policy:'day',dayStart:10,dayEnd:16,setback:0.65,blockCompressor:false,dhwNT:true};}
function tariffPlan(){const code=state.energy?.tariff||'D02d';return {...tariffProfiles[code],code,nt:state.energy?.ntWindows||tariffProfiles[code].nt};}
function ntAt(minute,plan=tariffPlan()){return plan.nt.some(([a,b])=>minute>=a&&minute<b);}
function dailyDhwSlots(level,plan=tariffPlan()){
 const control=state.control||defaultControl();
 const restricted=plan.hours>0&&(plan.dhwNT||control.dhwNT);
 const allowed=Array.from({length:144},(_,i)=>i).filter(i=>!restricted||ntAt(i*10,plan));
 const smart=level!=='baseline'&&state.dhwMode==='smart';
 const desired=smart?[78,79,80,81,82,83,84,85,86,87,88,89]:[42,43,44,45,46,47,114,115,116,117,118,119];
 const distance=i=>Math.min(...desired.map(j=>Math.min(Math.abs(i-j),144-Math.abs(i-j))));
 return new Set(allowed.sort((a,b)=>distance(a)-distance(b)||a-b).slice(0,12));
}
function parseNtWindows(text,tariff){
 const profile=tariffProfiles[tariff];if(!profile)throw Error('Neznámá sazba.');
 if(!profile.hours)return [];
 const intervals=text.split(/[;,]/).filter(s=>s.trim()).map(part=>{
   const m=part.trim().match(/^(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})$/);
   if(!m)throw Error('Použijte HH:MM–HH:MM, intervaly oddělte čárkou.');
   const nums=m.slice(1).map(Number),a=nums[0]*60+nums[1],b=nums[2]*60+nums[3];
   if(nums[1]>=60||nums[3]>=60||a<0||b>1440||a>=b||a%10||b%10)throw Error('Časy zadávejte po 10 minutách, 00:00–24:00; přes půlnoc rozdělte interval na dva.');
   return [a,b];
 }).sort((a,b)=>a[0]-b[0]);
 if(intervals.some(([a,b],i)=>b-a<60||(i&&a<intervals[i-1][1])))throw Error('Intervaly se nesmějí překrývat a musí trvat alespoň hodinu.');
 if(intervals.reduce((s,[a,b])=>s+b-a,0)!==profile.hours*60)throw Error(`Pro ${tariff} nastavte celkem ${profile.hours} hodin NT.`);
 // First and last intervals touching midnight count as one cyclic block.
 const cyclic=intervals.length&&intervals[0][0]===0&&intervals.at(-1)[1]===1440;
 if(intervals.length-(cyclic?1:0)>(tariff==='D57d'?7:3))throw Error('Příliš mnoho intervalů NT pro tuto sazbu.');
 if(tariff==='D57d'){
  const gaps=intervals.slice(1).map((v,i)=>v[0]-intervals[i][1]);gaps.push(1440-intervals.at(-1)[1]+intervals[0][0]);
  if(gaps.some(n=>n>60))throw Error('D57d: souvislý vysoký tarif smí trvat nejvýše hodinu.');
 }
 return intervals;
}
function formatNtWindows(windows){const t=m=>`${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;return windows.map(([a,b])=>`${t(a)}–${t(b)}`).join(', ');}
function electricCost(energyNT,energyVT){if(!state.energy)return (energyNT+energyVT)*state.electricityPrice;const p=energyPrices(state.energy);return energyNT*p.nt+energyVT*p.vt;}

function controlLabel(){return {day:'Denní priorita',tariff:'Priorita nízkého tarifu',constant:'Stálá teplota'}[(state.control||defaultControl()).policy];}
function controlWindowLabel(){const c=state.control||defaultControl();return c.policy==='constant'?'stálý cíl 24 h':c.policy==='tariff'&&tariffPlan().hours?'podle rozvrhu NT':`priorita ${c.dayStart}–${c.dayEnd} h`;}

// Removed experimental policies in older saved scenarios migrate to daytime control.
function migrateControlPolicy(policy){return ['optimum','economic'].includes(policy)?'day':policy;}
