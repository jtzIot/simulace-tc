import json

with open(r'.\sim_data\weather_10_winters.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

w = raw['2016-2017']
temps = w['temp']
rhs = w['rh']
sols = [round(min(1.5, (0.6 * w['dni'][i] + 0.3 * w['diffuse'][i]) * 0.0035), 2) for i in range(len(temps))]

hp = {'pDesign': 8.1, 'minMod': 2.5, 'copA7W35': 5.30, 'copA2W35': 4.45, 'copAm7W35': 3.35, 'copAm15W35': 2.65}
def getCop(te, tf, rh):
    if te >= 7.0: c = hp['copA7W35'] + (te - 7.0) * 0.08
    elif te >= 2.0: c = hp['copA2W35'] + (te - 2.0) * (hp['copA7W35'] - hp['copA2W35']) / 5.0
    elif te >= -7.0: c = hp['copAm7W35'] + (te + 7.0) * (hp['copA2W35'] - hp['copAm7W35']) / 9.0
    elif te >= -15.0: c = hp['copAm15W35'] + (te + 15.0) * (hp['copAm7W35'] - hp['copAm15W35']) / 8.0
    else: c = max(1.8, hp['copAm15W35'] - 0.45 + (te + 20.0) * 0.45 / 5.0)
    c *= (1.0 + 0.022 * (35.0 - tf))
    if te >= -3.5 and te <= 3.5 and rh > 75.0: c *= (1.0 - 0.07 * (rh / 100.0))
    return max(1.2, c)

def getCap(te):
    p = hp['pDesign']
    if te >= 7.0: return p
    if te >= 2.0: return p * 0.92 + (te - 2.0) * (p - p * 0.92) / 5.0
    if te >= -7.0: return p * 0.78 + (te + 7.0) * (p * 0.92 - p * 0.78) / 9.0
    if te >= -15.0: return p * 0.65 + (te + 15.0) * (p * 0.78 - p * 0.65) / 8.0
    return max(3.0, p * 0.54 + (te + 20.0) * (p * 0.65 - p * 0.54) / 5.0)

tInTarget = 22.0
tTolerance = 1.0
tExtDesign = -12.0
qLossDesign = 5.80
tFlowDesign = 28.0
area = 170.0
areaRatio = area / 180.0
H_loss = qLossDesign / (tInTarget - tExtDesign)
u_pipe = 2.50 * areaRatio
C_floor = (area * 0.05 * 2350 * 1020) / 3600000.0
C_room = 9.5 * areaRatio
U_floor_room = 1.68 * areaRatio

q_dhw_net_day = (120.0 * 4.186 * 45.0) / 3600.0
q_dhw_total_day = q_dhw_net_day + 1.2
tFlowDhw = 58.0

T_r_opt = tInTarget
T_f_opt = tInTarget + 1.5

N = len(temps)
hourly_log = []

for i in range(N):
    te = temps[i]; rh = rhs[i]; q_gain = sols[i] + 0.3; hour = i % 24
    dayIdx = i // 24

    # Std
    q_need_std = max(0.0, H_loss * (tInTarget - te) - q_gain)
    loadFactor = max(0.0, min(1.0, (tInTarget - te) / (tInTarget - tExtDesign)))
    t_flow_std = min(45.0, max(24.0, tInTarget + (tFlowDesign - tInTarget) * (loadFactor**0.9) + 1.0 * loadFactor))
    cop_std = getCop(te, t_flow_std, rh)
    p_el_std = (q_need_std / cop_std) if q_need_std >= 2.5 else (q_need_std / (cop_std * (0.88 + 0.12 * (q_need_std/2.5)))) if q_need_std > 0 else 0

    # Opt
    winStart = max(0, i - 6); winEnd = min(N, i + 18)
    avgWin = sum(temps[winStart:winEnd]) / (winEnd - winStart)
    isCharge = (hour >= 10 and hour <= 16) or (te > avgWin + 0.8)
    isDischarge = (hour >= 22 or hour <= 6) and (te < avgWin)
    target_tr = (tInTarget + tTolerance * 0.9) if isCharge else ((tInTarget - tTolerance * 0.9) if isDischarge else tInTarget)

    q_fl_rm = U_floor_room * (T_f_opt - T_r_opt)
    q_loss_opt = H_loss * (T_r_opt - te)
    Tr_cand = T_r_opt + (q_fl_rm + q_gain - q_loss_opt) / C_room
    maxCap = getCap(te)
    q_hp_opt = 0.0
    if Tr_cand < target_tr:
        defic = max(0.0, (target_tr - Tr_cand) * C_room + (target_tr + 1.8 - T_f_opt) * C_floor)
        if defic < 1.2 and not isCharge and T_r_opt > (tInTarget - tTolerance * 0.6): q_hp_opt = 0.0
        else: q_hp_opt = max(2.5, min(maxCap, defic))
    actual_q_hp = min(q_hp_opt, maxCap); q_bk_opt = max(0.0, q_hp_opt - maxCap)
    T_f_opt += (actual_q_hp + q_bk_opt - q_fl_rm) / C_floor
    T_r_opt += (U_floor_room * (T_f_opt - T_r_opt) + q_gain - q_loss_opt) / C_room
    if T_r_opt < (tInTarget - tTolerance): T_r_opt = tInTarget - tTolerance

    t_flow_ekv = tInTarget + (tFlowDesign - tInTarget) * (loadFactor**0.85) + 1.0 * loadFactor
    chargeLift = max(0.0, (actual_q_hp - q_loss_opt) / (u_pipe * 2.5))
    tfl = min(52.0, max(22.0, t_flow_ekv + chargeLift)) if actual_q_hp > 0 else 0
    cop_opt = getCop(te, tfl, rh) if actual_q_hp > 0 else 0
    p_el_opt = (actual_q_hp / cop_opt + q_bk_opt) if actual_q_hp > 0 else 0

    p_el_opt_dhw = 0.0; q_th_opt_dhw = 0.0
    if hour == 13 or hour == 14:
        q_slot = q_dhw_total_day / 2.0
        cop_dhw = getCop(te, tFlowDhw, rh)
        p_el_opt_dhw = q_slot / cop_dhw
        q_th_opt_dhw = q_slot

    if dayIdx == 105:
        hourly_log.append({
            'h': hour, 'te': te, 'tr': round(T_r_opt, 2), 'tf': round(T_f_opt, 2),
            'tfl': round(tfl, 1), 'q_hp': round(actual_q_hp, 2), 'q_dhw': round(q_th_opt_dhw, 2),
            'p_el': round(p_el_opt, 2), 'p_dhw': round(p_el_opt_dhw, 2), 'cop': round(cop_opt, 2),
            'q_std': round(q_need_std, 2), 'p_std': round(p_el_std, 2)
        })

print(f"{'Hod':>3} | {'Te(°C)':>6} | {'Tr(°C)':>6} | {'Tpodl':>6} | {'Výkon kW':>8} | {'TUV kW':>7} | {'P_el opt':>8} | {'P_el std':>8} | {'COP':>4} | Stav")
print("-" * 85)
for r in hourly_log:
    state_str = 'VYPNUTO (vybíjení aku)' if r['q_hp'] == 0 and r['q_dhw'] == 0 else ('NABÍJENÍ PODLAHY + TUV' if r['q_dhw'] > 0 else 'NABÍJENÍ PODLAHY')
    print(f"{r['h']:02d}:00 | {r['te']:6.1f} | {r['tr']:6.2f} | {r['tf']:6.2f} | {r['q_hp']:8.2f} | {r['q_dhw']:7.2f} | {r['p_el']+r['p_dhw']:8.2f} | {r['p_std']:8.2f} | {r['cop']:4.2f} | {state_str}")
