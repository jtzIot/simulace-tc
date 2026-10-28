// Shared 10-minute energy balance, including a daily model HDO calendar.
const controllerLevels = ['baseline', 'optimized'];
let controllerResults = {};
const bounded = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
function simulateController(weather, level) {
  const dt=1/6,area=state.floorAreaM2/180,concrete=state.floorMaterial==='beton';
  const Cf=state.floorAreaM2*state.floorThicknessMm/1000*(concrete?2350*1020:2150*1000)/3600000;
  const Cr=9.5*area,G=(concrete?1.68:1.85)*area,H=state.qLossDesign/(state.tInTarget-state.tExtDesign);
  const low=state.tInTarget-state.tTolerance,high=state.tInTarget,radiator=state.heatingSystem==='radiator';
  const correction=-0.0065*(state.altitude-(state.weatherBaseAltitude??211));
  const temps=weather.t.map(t=>t+correction),plan=tariffPlan(),control=state.control||defaultControl();
  const ntSteps=Array.from({length:144},(_,s)=>ntAt(s*10,plan));
  const dhwDay=state.dhwEnabled?state.dhwDailyLiters*4.186*(state.dhwTargetTemp-10)/3600+1.2:0;
  const slots=dailyDhwSlots(level,plan);
  let tr=state.tInTarget,tf=tr+1.5,running=false;
  let initialEnergy=0,e=0,heat=0,de=0,dq=0,backup=0,dhwBackup=0,dhwUnmet=0,elNT=0,elVT=0;
  let starts=0,under=0,over=0,degreeUnder=0,degreeOver=0,min=Infinity,max=-Infinity,roomSum=0,netEnvironment=0;
  const hours=[];
  for(let i=-168;i<temps.length;i++){
    const ix=i<0?(i+168)%Math.min(168,temps.length):i,h=ix%24,te=temps[ix],rh=weather.rh[ix];
    const gains=weather.sol[ix]+0.3,cap=Math.max(0,getCapForActiveModel(te)),curveMin=typeof manufacturerPoint==='function'?manufacturerPoint(state.activeModelId,te,state.tFlowDesign)?.min:null,minMod=Math.min(cap,curveMin??state.activeHp.minMod??2.5);
    let qHour=0,eHour=0,bkHour=0,waterHour=0,runHour=false,dhwQ=0,dhwE=0,dhwB=0,dhwMissing=0,ntE=0,vtE=0,ntMinutes=0,targetSum=0,chargeSteps=0;
    if(i===0)initialEnergy=Cf*tf+Cr*tr;
    for(let step=0;step<6;step++){
      const nt=ntSteps[h*6+step],minute=h*60+step*10;
      const compressorAllowed=!(plan.hours>0&&control.blockCompressor&&!nt);
      const auxAllowed=!(plan.auxBlocked&&!nt);
      let charge=false,discharge=false;
      if(level==='optimized'&&control.policy!=='constant'){
        charge=control.policy==='tariff'&&plan.hours>0?nt:minute>=control.dayStart*60&&minute<control.dayEnd*60;
        discharge=!charge;
      }
      const target=state.tInTarget-(discharge?control.setback:0)*state.tTolerance;
      const requestedDhw=slots.has(h*6+step)?dhwDay/(slots.size*dt):0;
      const dhwHp=compressorAllowed?Math.min(requestedDhw,getCapForActiveModel(te,state.dhwTargetTemp+3)):0;
      const dhwBk=auxAllowed?Math.min(3,requestedDhw-dhwHp):0;
      const dhwCapacity=getCapForActiveModel(te,state.dhwTargetTemp+3);
      const share=dhwCapacity>0?Math.min(1,dhwHp/dhwCapacity):0;
      const loss=H*(tr-te),exchange=radiator?0:G*(tf-tr);
      const need=Math.max(0,H*(target-te)-gains),floorTarget=Math.min(29,target+need/G);
      const request=Math.max(0,radiator?need+(target-tr)*Cr/2:need+(floorTarget-tf)*Cf/2+(target-tr)*Cr/2);
      const available=compressorAllowed?cap*(1-share):0,threshold=running?minMod*0.15:minMod*0.6;
      const enabled=compressorAllowed&&request>threshold&&tr<high&&(radiator||tf<29);
      let hp=enabled?Math.min(available,Math.max(minMod*(1-share),request)):0;
      let bk=auxAllowed&&tr<low&&request>available?Math.min(3-dhwBk,request-available):0;
      const load=bounded((state.tInTarget-te)/(state.tInTarget-state.tExtDesign),0,1);
      const covering=state.floorCovering==='drevo'?2.5:state.floorCovering==='vinyl'?1:0;
      const curve=state.tInTarget+(state.tFlowDesign-state.tInTarget)*Math.pow(load,0.9)+covering*load;
      const water=bounded(Math.max(curve,radiator?curve:tf+2+hp/(2.5*area)),22,55);
      if(state.activeHp.km||(typeof manufacturerCurves!=='undefined'&&manufacturerCurves[state.activeModelId])){const actualCap=getCapForActiveModel(te,water)*(1-share);hp=Math.min(hp,actualCap);if(tr<low&&auxAllowed&&request>actualCap)bk=Math.min(3-dhwBk,request-actualCap);}
      const nowRunning=hp>0||dhwHp>0;if(i>=0&&nowRunning&&!running)starts++;running=nowRunning;runHour||=nowRunning;
      const el=hp/getCopForActiveModel(te,water,rh,hp)+bk+(hp+bk>0?kmExternalPumpPower():0)+(nowRunning?0:kmIdlePower(!compressorAllowed));
      const dhwEl=dhwHp/getCopDhwForActiveModel(te,state.dhwTargetTemp+3,rh)+dhwBk;
      tf+=(radiator?0:hp+bk-exchange)*dt/Cf;
      tr+=(exchange+(radiator?hp+bk:0)+gains-loss)*dt/Cr;
      qHour+=(hp+bk)*dt;eHour+=el*dt;bkHour+=bk*dt;waterHour+=water*dt;
      dhwQ+=(dhwHp+dhwBk)*dt;dhwE+=dhwEl*dt;dhwB+=dhwBk*dt;dhwMissing+=(requestedDhw-dhwHp-dhwBk)*dt;
      if(nt){ntE+=(el+dhwEl)*dt;ntMinutes+=10;}else vtE+=(el+dhwEl)*dt;
      targetSum+=target;if(charge)chargeSteps++;
      if(i>=0){under+=tr<low-0.05?dt:0;over+=tr>high+0.05?dt:0;degreeUnder+=Math.max(0,low-tr)*dt;degreeOver+=Math.max(0,tr-high)*dt;min=Math.min(min,tr);max=Math.max(max,tr);roomSum+=tr*dt;netEnvironment+=(gains-loss)*dt;}
    }
    if(i<0)continue;
    heat+=qHour;e+=eHour;de+=dhwE;dq+=dhwQ;backup+=bkHour;dhwBackup+=dhwB;dhwUnmet+=dhwMissing;elNT+=ntE;elVT+=vtE;
    hours.push({h,te,tr,tf,controlTarget:targetSum/6,tfl:waterHour,q_hp:qHour,q_dhw:dhwQ,p_el_opt:eHour+dhwE,
      cop_opt:eHour+dhwE>0?(qHour+dhwQ)/(eHour+dhwE):0,isRunning:runHour,isCharge:chargeSteps>0,
      isDischarge:level==='optimized'&&control.policy!=='constant'&&chargeSteps<6,
      heatEl:eHour,dhwEl:dhwE,backup:bkHour,dhwBackup:dhwB,elNT:ntE,elVT:vtE,ntMinutes,cost:electricCost(ntE,vtE)});
  }
  const storage=Cf*tf+Cr*tr-initialEnergy;
  return {hours,e,heat,de,dq,backup,dhwBackup,dhwUnmet,elNT,elVT,starts,under,over,degreeUnder,degreeOver,min,max,avg:roomSum/temps.length,storage,balanceError:storage-heat-netEnvironment,Cf};
}
function economyFor(r,season,mode=state.economyPeriod||'season',elPrice=state.electricityPrice,gasPrice=state.gasPrice){
 const year=Number(season.slice(5)),yearDays=new Date(year,1,29).getMonth()===1?366:365;
 const days=rawWeather[season].t.length/24,annual=mode==='annual'||mode==='decade',fraction=annual?1:days/yearDays;
 const summerDays=annual?yearDays-days:0;
 const summerHeat=state.dhwEnabled?summerDays*(state.dhwDailyLiters*4.186*(state.dhwTargetTemp-10)/3600+1.2):0;
 const summerEl=summerHeat/(state.summerDhwCop||2.7),slots=[...dailyDhwSlots('optimized')];
 const summerNTFraction=slots.length?slots.filter(s=>ntAt(s*10)).length/slots.length:0;
 const electricityNT=(r.comfort.opt.elNT||0)+summerEl*summerNTFraction;
 const electricityVT=(r.comfort.opt.elVT??r.el_opt_kwh)+summerEl*(1-summerNTFraction);
 const electricity=electricityNT+electricityVT;
 const scale=state.electricityPrice>0?elPrice/state.electricityPrice:1;
 const electricityCost=electricCost(electricityNT,electricityVT)*scale;
 const gasHeatKwh=r.th_opt_heat/(state.gasBoilerEfficiency/100),gasDhwKwh=(r.th_opt_dhw+summerHeat)/((state.gasDhwEfficiency??86)/100);
 const gasKwh=gasHeatKwh+gasDhwKwh;
 const surcharge=state.etsEnabled?state.co2AllowancePriceEur*25*0.00018*1.21:0;
 const gasFixed=(state.gasMonthlyFixed??135)*12*fraction;
 const hpBreaker=(state.elMonthlyExtra||0)*12*fraction,hpService=state.hpServiceYearly*fraction,gasService=state.gasBoilerServiceYearly*fraction;
 const hpFixed=hpBreaker+hpService+(state.retainGas?gasFixed:0),gasFuel=gasKwh*gasPrice,ets=gasKwh*surcharge;
 const gasTotal=gasFuel+ets+gasFixed+gasService,hpTotal=electricityCost+hpFixed;
 return {electricity,electricityNT,electricityVT,electricityCost,gasHeatKwh,gasDhwKwh,gasKwh,gasFuel,gasTotal,hpTotal,saving:gasTotal-hpTotal,ets,
   heat:r.th_kwh+summerHeat,fraction,summerEl,hpFixed,gasFixed,surcharge,hpBreaker,hpService,gasService};
}

function updateSeasonEconomy(s) {
  const entry = simResults[s];
  if (!entry) return;
  const r = entry.results, b = r.comfort.baseline, o = r.comfort.opt;
  entry.daily.forEach((d, idx) => {
    const hours = o.hours.slice(idx * 24, idx * 24 + 24);
    const std = b.hours.slice(idx * 24, idx * 24 + 24);
    hours.forEach(h => { h.cost = electricCost(h.elNT, h.elVT); });
    std.forEach(h => { h.cost = electricCost(h.elNT, h.elVT); });
    d.cost_opt = hours.reduce((v, h) => v + h.cost, 0);
    d.cost_std = std.reduce((v, h) => v + h.cost, 0);
  });
  r.savings_czk = electricCost(b.elNT, b.elVT) - electricCost(o.elNT, o.elVT);
  const c = economyFor(r, s);
  Object.assign(r, {
    gas_kwh: c.gasKwh,
    gas_fuel_czk: c.gasKwh * state.gasPrice,
    gas_ets2_czk: c.ets,
    cost_gas_total: c.gasTotal,
    cost_hp_total: c.hpTotal,
    savings_vs_gas_czk: c.saving,
    savings_vs_gas_pct: c.gasTotal ? c.saving / c.gasTotal * 100 : 0
  });
}

function recalculateEconomy() {
  if (!simResults || !Object.keys(simResults).length) {
    recalculateSimulation();
    return;
  }
  if (typeof applyEnergyPrices === 'function') applyEnergyPrices();
  Object.keys(simResults).forEach(updateSeasonEconomy);
}

function recalculateSimulation() {
  if(state.control)state.control.policy=migrateControlPolicy(state.control.policy);
  simResults = {}; controllerResults = {};
  const activeSeasons = typeof getActiveSeasons === 'function' ? getActiveSeasons() : Object.keys(rawWeather);
  if (activeSeasons.length && !activeSeasons.includes(state.currentSeason)) {
    state.currentSeason = activeSeasons[Math.min(activeSeasons.length - 1, Math.floor(activeSeasons.length / 2))];
  }
  activeSeasons.forEach(s => {
    const runs = {};
    controllerLevels.forEach(level => runs[level] = simulateController(rawWeather[s], level));
    controllerResults[s] = Object.fromEntries(controllerLevels.map(level => {
      const x = runs[level];
      return [level, {el: x.e + x.de, starts: x.starts, under: x.under, over: x.over}];
    }));
    const b = runs.baseline, o = runs[state.automationLevel];
    const daily = [];
    for (let i = 0; i < o.hours.length; i += 24) {
      const hours = o.hours.slice(i, i + 24), std = b.hours.slice(i, i + 24);
      hours.forEach((h, j) => { h.p_el_std = std[j].p_el_opt; h.cop_std = std[j].cop_opt; });
      const sum = (a, fn) => a.reduce((v, h) => v + fn(h), 0);
      const el = sum(hours, h => h.p_el_opt), th = sum(hours, h => h.q_hp + h.q_dhw);
      daily.push({hours, avg_t: sum(hours, h => h.te) / 24, min_t: Math.min(...hours.map(h => h.te)), max_t: Math.max(...hours.map(h => h.te)),
        cost_std: sum(std,h=>h.cost),cost_opt:sum(hours,h=>h.cost),el_std: sum(std, h => h.p_el_opt), th_std: sum(std, h => h.q_hp + h.q_dhw), el_opt: el, th_opt: th,
        el_opt_heat: sum(hours, h => h.heatEl), el_opt_dhw: sum(hours, h => h.dhwEl), th_opt_heat: sum(hours, h => h.q_hp), th_opt_dhw: sum(hours, h => h.q_dhw),
        scop_day: el ? th / el : 0, tr_avg: sum(hours, h => h.tr) / 24, tf_avg: sum(hours, h => h.tf) / 24});
    }
    const r = {el_opt_kwh: o.e + o.de, el_std_kwh: b.e + b.de, el_opt_heat: o.e, el_opt_dhw: o.de,
      el_std_heat: b.e, el_std_dhw: b.de, th_kwh: o.heat + o.dq, th_opt_heat: o.heat, th_opt_dhw: o.dq,
      scop_opt: (o.heat + o.dq) / (o.e + o.de || 1), scop_std: (b.heat + b.dq) / (b.e + b.de || 1),
      scop_heat: o.heat / (o.e || 1), scop_dhw: o.dq / (o.de || 1), starts_opt: o.starts, starts_std: b.starts,
      diff_kwh: (b.e + b.de) - (o.e + o.de), comfort: {opt: o, baseline: b}};
    r.diff_pct = r.el_std_kwh ? r.diff_kwh / r.el_std_kwh * 100 : 0;
    r.savings_czk = electricCost(b.elNT,b.elVT)-electricCost(o.elNT,o.elVT);
    const c = economyFor(r, s);
    Object.assign(r, {gas_kwh: c.gasKwh, gas_fuel_czk: c.gasKwh * state.gasPrice, gas_ets2_czk: c.ets,
      cost_gas_total: c.gasTotal, cost_hp_total: c.hpTotal, savings_vs_gas_czk: c.saving,
      savings_vs_gas_pct: c.gasTotal ? c.saving / c.gasTotal * 100 : 0});
    let cumulative = 0;
    simResults[s] = {results: r, daily, cum_kwh: daily.map(d => cumulative += d.el_opt), monthly: computeMonthly(daily, s),
      weather_stats: {avg_temp: o.hours.reduce((a, h) => a + h.te, 0) / o.hours.length,
        min_temp: Math.min(...o.hours.map(h => h.te)), max_temp: Math.max(...o.hours.map(h => h.te))}};
  });
}
