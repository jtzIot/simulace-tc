import json

with open(r'.\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('rawWeather = ')
start = html.find('{', idx)
raw, _ = json.JSONDecoder().raw_decode(html[start:])

hp = {
    'pDesign': 8.1,
    'minMod': 2.5,
    'copA7W35': 5.30,
    'copA2W35': 4.45,
    'copAm7W35': 3.35,
    'copAm15W35': 2.65
}

def getCop(te, tf, rh):
    if te >= 7.0: c = hp['copA7W35'] + (te - 7.0) * 0.08
    elif te >= 2.0: c = hp['copA2W35'] + (te - 2.0) * (hp['copA7W35'] - hp['copA2W35']) / 5.0
    elif te >= -7.0: c = hp['copAm7W35'] + (te + 7.0) * (hp['copA2W35'] - hp['copAm7W35']) / 9.0
    elif te >= -15.0: c = hp['copAm15W35'] + (te + 15.0) * (hp['copAm7W35'] - hp['copAm15W35']) / 8.0
    else: c = max(1.8, hp['copAm15W35'] - 0.45 + (te + 20.0) * 0.45 / 5.0)
    c *= (1.0 + 0.022 * (35.0 - tf))
    if te >= -3.5 and te <= 3.5 and rh > 75.0:
        c *= (1.0 - 0.07 * (rh / 100.0))
    return max(1.2, c)

def getCap(te):
    p = hp['pDesign']
    if te >= 7.0: return p
    if te >= 2.0: return p * 0.92 + (te - 2.0) * (p - p * 0.92) / 5.0
    if te >= -7.0: return p * 0.78 + (te + 7.0) * (p * 0.92 - p * 0.78) / 9.0
    if te >= -15.0: return p * 0.65 + (te + 15.0) * (p * 0.78 - p * 0.65) / 8.0
    return max(3.0, p * 0.54 + (te + 20.0) * (p * 0.65 - p * 0.54) / 5.0)

wData = raw['2016-2017']
rawT = wData['t']
rhs = wData['rh']
sols = wData['sol']
N = len(rawT)

# Test DHW calculation
tFlow = 32.0
tInTarget = 21.0
tExtDesign = -12.0
qLossDesign = 5.80
H_loss = qLossDesign / (tInTarget - tExtDesign)
u_pipe = 2.50
C_floor = (180 * 0.05 * 2350 * 1020) / 3600000.0
C_room = 9.5
U_floor_room = 1.68

# DHW parameters:
dhwLiters = 160.0 # liters/day
dhwTarget = 52.0  # °C
tCold = 10.0      # °C
q_dhw_net_day = (dhwLiters * 4.186 * (dhwTarget - tCold)) / 3600.0 # kWh/day
q_dhw_loss_day = 1.2 # kWh/day standing cylinder loss
q_dhw_total_day = q_dhw_net_day + q_dhw_loss_day # ~9.0 kWh/day
tFlowDhw = dhwTarget + 3.0 # 55 °C

print(f'DHW daily heat: net={q_dhw_net_day:.2f} kWh, loss={q_dhw_loss_day:.2f} kWh, total={q_dhw_total_day:.2f} kWh/day')

for dhwEnabled in [False, True]:
    for dhwMode in (['smart', 'standard'] if dhwEnabled else ['none']):
        el_std_heat = 0.0; el_opt_heat = 0.0; th_heat = 0.0
        el_std_dhw = 0.0; el_opt_dhw = 0.0; th_dhw = 0.0
        T_r_opt = tInTarget; T_f_opt = tInTarget + 1.5

        for i in range(N):
            te = rawT[i]; rh = rhs[i]; q_gain = sols[i] + 0.3; hour = i % 24
            
            # 1. Heating Standard
            q_need_std = max(0.0, H_loss * (tInTarget - te) - q_gain)
            loadFactor = max(0.0, min(1.0, (tInTarget - te) / (tInTarget - tExtDesign)))
            t_flow_std = min(45.0, max(24.0, tInTarget + (tFlow - tInTarget) * (loadFactor**0.9) + 1.0 * loadFactor))
            cop_std_val = getCop(te, t_flow_std, rh)
            if q_need_std > 0:
                if q_need_std < 2.5:
                    duty = q_need_std / 2.5
                    el_std_heat += q_need_std / (cop_std_val * (0.88 + 0.12 * duty))
                else:
                    maxCap = getCap(te); q_hp = min(q_need_std, maxCap)
                    el_std_heat += q_hp / cop_std_val + (q_need_std - q_hp)

            # 2. Heating Optimized
            winStart = max(0, i - 6); winEnd = min(N, i + 18)
            avgWin = sum(rawT[winStart:winEnd]) / (winEnd - winStart)
            isCharge = (hour >= 10 and hour <= 16) or (te > avgWin + 0.8)
            isDischarge = (hour >= 22 or hour <= 6) and (te < avgWin)
            target_tr = (tInTarget + 0.9) if isCharge else ((tInTarget - 0.9) if isDischarge else tInTarget)
            q_fl_rm = U_floor_room * (T_f_opt - T_r_opt); q_loss_opt = H_loss * (T_r_opt - te)
            Tr_cand = T_r_opt + (q_fl_rm + q_gain - q_loss_opt) / C_room
            maxCap = getCap(te); q_hp_opt = 0.0
            if Tr_cand < target_tr:
                defic = max(0.0, (target_tr - Tr_cand) * C_room + (target_tr + 1.8 - T_f_opt) * C_floor)
                if defic < 1.2 and not isCharge and T_r_opt > (tInTarget - 0.6): q_hp_opt = 0.0
                else: q_hp_opt = max(2.5, min(maxCap, defic))
            actual_q_hp = min(q_hp_opt, maxCap); q_bk_opt = max(0.0, q_hp_opt - maxCap)
            T_f_opt += (actual_q_hp + q_bk_opt - q_fl_rm) / C_floor
            T_r_opt += (U_floor_room * (T_f_opt - T_r_opt) + q_gain - q_loss_opt) / C_room
            if T_r_opt < 20.0: T_r_opt = 20.0
            if actual_q_hp > 0:
                t_flow_ekv = tInTarget + (tFlow - tInTarget) * (loadFactor**0.85) + 1.0 * loadFactor
                chargeLift = max(0.0, (actual_q_hp - q_loss_opt) / (u_pipe * 2.5))
                tfl = min(52.0, max(22.0, t_flow_ekv + chargeLift))
                cop_opt_val = getCop(te, tfl, rh)
                el_opt_heat += actual_q_hp / cop_opt_val + q_bk_opt
                th_heat += actual_q_hp + q_bk_opt

            # 3. DHW Heating
            if dhwEnabled:
                # Standard DHW: heated in morning (7:00) and evening (19:00), 2 equal slots of q_dhw_total_day / 2
                if hour == 7 or hour == 19:
                    q_slot = q_dhw_total_day / 2.0
                    cop_dhw_std = getCop(te, tFlowDhw, rh)
                    el_std_dhw += q_slot / cop_dhw_std

                # Smart DHW: heated during warmest midday hours (13:00 and 14:00)
                if dhwMode == 'smart':
                    if hour == 13 or hour == 14:
                        q_slot = q_dhw_total_day / 2.0
                        cop_dhw_opt = getCop(te, tFlowDhw, rh)
                        el_opt_dhw += q_slot / cop_dhw_opt
                        th_dhw += q_slot
                else: # standard DHW mode
                    if hour == 7 or hour == 19:
                        q_slot = q_dhw_total_day / 2.0
                        cop_dhw_opt = getCop(te, tFlowDhw, rh)
                        el_opt_dhw += q_slot / cop_dhw_opt
                        th_dhw += q_slot

        tot_el_std = el_std_heat + el_std_dhw
        tot_el_opt = el_opt_heat + el_opt_dhw
        tot_th_opt = th_heat + th_dhw
        scop_tot = tot_th_opt / tot_el_opt if tot_el_opt > 0 else 0
        scop_dhw = th_dhw / el_opt_dhw if el_opt_dhw > 0 else 0
        diff = tot_el_std - tot_el_opt
        pct = (diff / tot_el_std) * 100.0 if tot_el_std > 0 else 0
        print(f'Enabled={dhwEnabled:5} Mode={dhwMode:8} | Heat_el={round(el_opt_heat)} kWh | DHW_el={round(el_opt_dhw)} kWh (SCOP_dhw={scop_dhw:.2f}) | Total_el={round(tot_el_opt)} kWh | Savings={round(diff)} kWh ({pct:.1f}%) | SCOP_tot={scop_tot:.2f}')
