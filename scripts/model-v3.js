// Shared 10-minute energy balance for all four controllers. Weather is hourly.
const controllerLevels = ['baseline', 'timer', 'sgready', 'predictive'];
let controllerResults = {};
const bounded = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
function simulateController(weather, level) {
  const dt = 1 / 6, area = state.floorAreaM2 / 180;
  const concrete = state.floorMaterial === 'beton';
  const Cf = state.floorAreaM2 * state.floorThicknessMm / 1000 * (concrete ? 2350 * 1020 : 2150 * 1000) / 3600000;
  const Cr = 9.5 * area, G = (concrete ? 1.68 : 1.85) * area;
  const H = state.qLossDesign / (state.tInTarget - state.tExtDesign);
  const low = state.tInTarget - state.tTolerance, high = state.tInTarget + state.tTolerance;
  const radiator = state.heatingSystem === 'radiator';
  const correction = -0.0065 * (state.altitude - (state.weatherBaseAltitude ?? 392));
  const temps = weather.t.map(t => t + correction);
  const dhwDay = state.dhwEnabled ? state.dhwDailyLiters * 4.186 * (state.dhwTargetTemp - 10) / 3600 + 1.2 : 0;
  const smartDhw = level !== 'baseline' && state.dhwMode === 'smart';
  let tr = state.tInTarget, tf = tr + 1.5, running = false;
  let initialEnergy = 0, e = 0, heat = 0, de = 0, dq = 0, backup = 0, dhwBackup = 0, dhwUnmet = 0;
  let starts = 0, under = 0, over = 0, degreeUnder = 0, degreeOver = 0;
  let min = Infinity, max = -Infinity, roomSum = 0, netEnvironment = 0;
  const hours = [];
  // Seven-day warm-up using the first available week; excluded from totals.
  for (let i = -168; i < temps.length; i++) {
    const ix = i < 0 ? (i + 168) % Math.min(168, temps.length) : i;
    const h = ix % 24, te = temps[ix], rh = weather.rh[ix];
    const gains = weather.sol[ix] + 0.3;
    const cap = Math.max(0, getCapForActiveModel(te));
    const minMod = Math.min(cap, state.activeHp.minMod || 2.5);
    const dhwSlot = smartDhw ? (h === 13 || h === 14) : (h === 7 || h === 19);
    const requestedDhw = dhwSlot ? dhwDay / 2 : 0;
    const dhwHp = Math.min(requestedDhw, cap), dhwBk = Math.min(3, requestedDhw - dhwHp);
    const qdhw = dhwHp + dhwBk;
    const dhwEl = dhwHp / getCopDhwForActiveModel(te, state.dhwTargetTemp + 3, rh) + dhwBk;
    // DHW priority occupies a fraction of compressor time in this hour.
    const share = cap > 0 ? dhwHp / cap : 0;
    let charge = false, discharge = false;
    if (level !== 'baseline' && !radiator) {
      charge = h >= 10 && h < 16;
      discharge = h >= 22 || h < 6;
      if (level === 'sgready') charge = charge && (weather.sol[ix] >= 0.05 || (h >= 11 && h < 14));
      if (level === 'predictive') {
        let count = 0, future = 0;
        for (let j = ix; j < Math.min(temps.length, ix + 18); j++) { future += temps[j]; count++; }
        future /= count;
        charge = charge || te > future + 0.8;
        discharge = discharge && te < future;
      }
    }
    const target = state.tInTarget + (charge ? 0.65 : discharge ? -0.65 : 0) * state.tTolerance;
    let qHour = 0, eHour = 0, bkHour = 0, waterHour = 0, runHour = dhwHp > 0;
    if (i === 0) initialEnergy = Cf * tf + Cr * tr;
    for (let step = 0; step < 6; step++) {
      const loss = H * (tr - te), exchange = radiator ? 0 : G * (tf - tr);
      const need = Math.max(0, H * (target - te) - gains);
      const floorTarget = Math.min(29, target + need / G);
      const request = Math.max(0, radiator ? need + (target - tr) * Cr / 2 : need + (floorTarget - tf) * Cf / 2 + (target - tr) * Cr / 2);
      const available = cap * (1 - share);
      // Hysteresis on requested load avoids counting each active step as a start.
      const threshold = running ? minMod * 0.15 : minMod * 0.6;
      const enabled = request > threshold && tr < high && (radiator || tf < 29);
      const hp = enabled ? Math.min(available, Math.max(minMod * (1 - share), request)) : 0;
      const bk = tr < low && request > available ? Math.min(3 - dhwBk, request - available) : 0;
      const nowRunning = hp > 0 || dhwHp > 0;
      if (i >= 0 && nowRunning && !running) starts++;
      running = nowRunning;
      runHour ||= nowRunning;
      const load = bounded((state.tInTarget - te) / (state.tInTarget - state.tExtDesign), 0, 1);
      const covering = state.floorCovering === 'drevo' ? 2.5 : state.floorCovering === 'vinyl' ? 1 : 0;
      const curve = state.tInTarget + (state.tFlowDesign - state.tInTarget) * Math.pow(load, 0.9) + covering * load;
      const water = bounded(Math.max(curve, radiator ? curve : tf + 2 + hp / (2.5 * area)), 22, 55);
      const el = hp / getCopForActiveModel(te, water, rh) + bk + (hp + bk > 0 ? 0.025 : 0);
      // Both nodes use the SAME exchange, conserving energy exactly per step.
      tf += (radiator ? 0 : hp + bk - exchange) * dt / Cf;
      tr += (exchange + (radiator ? hp + bk : 0) + gains - loss) * dt / Cr;
      qHour += (hp + bk) * dt; eHour += el * dt; bkHour += bk * dt; waterHour += water * dt;
      if (i >= 0) {
        under += tr < low - 0.05 ? dt : 0; over += tr > high + 0.05 ? dt : 0;
        degreeUnder += Math.max(0, low - tr) * dt; degreeOver += Math.max(0, tr - high) * dt;
        min = Math.min(min, tr); max = Math.max(max, tr); roomSum += tr * dt;
        netEnvironment += (gains - loss) * dt;
      }
    }
    if (i < 0) continue;
    heat += qHour; e += eHour; de += dhwEl; dq += qdhw; backup += bkHour; dhwBackup += dhwBk; dhwUnmet += requestedDhw - qdhw;
    hours.push({h, te, tr, tf, tfl: waterHour, q_hp: qHour, q_dhw: qdhw,
      p_el_opt: eHour + dhwEl, cop_opt: eHour + dhwEl > 0 ? (qHour + qdhw) / (eHour + dhwEl) : 0,
      isRunning: runHour, isCharge: charge, isDischarge: discharge,
      heatEl: eHour, dhwEl, backup: bkHour, dhwBackup: dhwBk});
  }
  const storage = Cf * tf + Cr * tr - initialEnergy;
  return {hours, e, heat, de, dq, backup, dhwBackup, dhwUnmet, starts, under, over, degreeUnder, degreeOver,
    min, max, avg: roomSum / temps.length, storage, balanceError: storage - heat - netEnvironment, Cf};
}
function economyFor(r, season, mode = state.economyPeriod || 'season', elPrice = state.electricityPrice, gasPrice = state.gasPrice) {
  const year = Number(season.slice(5)), yearDays = new Date(year, 1, 29).getMonth() === 1 ? 366 : 365;
  const days = rawWeather[season].t.length / 24, annual = mode === 'annual';
  const fraction = annual ? 1 : days / yearDays;
  const summerDays = annual ? yearDays - days : 0;
  const summerHeat = state.dhwEnabled ? summerDays * (state.dhwDailyLiters * 4.186 * (state.dhwTargetTemp - 10) / 3600 + 1.2) : 0;
  const summerEl = summerHeat / (state.summerDhwCop || 2.7);
  const electricity = r.el_opt_kwh + summerEl;
  const gasKwh = r.th_opt_heat / (state.gasBoilerEfficiency / 100) + (r.th_opt_dhw + summerHeat) / 0.86;
  const surcharge = (state.etsEnabled ? state.co2AllowancePriceEur * 25 * 0.00018 * 1.21 : 0);
  const gasFixed = (state.gasMonthlyFixed ?? 135) * 12 * fraction;
  const hpFixed = ((state.elMonthlyExtra || 0) * 12 + state.hpServiceYearly) * fraction + (state.retainGas ? gasFixed : 0);
  const gasTotal = gasKwh * (gasPrice + surcharge) + gasFixed + state.gasBoilerServiceYearly * fraction;
  const hpTotal = electricity * elPrice + hpFixed;
  return {electricity, gasKwh, gasTotal, hpTotal, saving: gasTotal - hpTotal, ets: gasKwh * surcharge,
    heat: r.th_kwh + summerHeat, fraction, summerEl, hpFixed, gasFixed, surcharge};
}
function recalculateSimulation() {
  simResults = {}; controllerResults = {};
  Object.keys(rawWeather).forEach(s => {
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
        el_std: sum(std, h => h.p_el_opt), th_std: sum(std, h => h.q_hp + h.q_dhw), el_opt: el, th_opt: th,
        el_opt_heat: sum(hours, h => h.heatEl), el_opt_dhw: sum(hours, h => h.dhwEl), th_opt_heat: sum(hours, h => h.q_hp), th_opt_dhw: sum(hours, h => h.q_dhw),
        scop_day: el ? th / el : 0, tr_avg: sum(hours, h => h.tr) / 24, tf_avg: sum(hours, h => h.tf) / 24});
    }
    const r = {el_opt_kwh: o.e + o.de, el_std_kwh: b.e + b.de, el_opt_heat: o.e, el_opt_dhw: o.de,
      el_std_heat: b.e, el_std_dhw: b.de, th_kwh: o.heat + o.dq, th_opt_heat: o.heat, th_opt_dhw: o.dq,
      scop_opt: (o.heat + o.dq) / (o.e + o.de || 1), scop_std: (b.heat + b.dq) / (b.e + b.de || 1),
      scop_heat: o.heat / (o.e || 1), scop_dhw: o.dq / (o.de || 1), starts_opt: o.starts, starts_std: b.starts,
      diff_kwh: (b.e + b.de) - (o.e + o.de), comfort: {opt: o, baseline: b}};
    r.diff_pct = r.el_std_kwh ? r.diff_kwh / r.el_std_kwh * 100 : 0;
    r.savings_czk = r.diff_kwh * state.electricityPrice;
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
