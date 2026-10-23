import json
import math
import os

with open('sim_data/weather_10_winters.json', 'r', encoding='utf-8') as f:
    weather = json.load(f)

# Referenční RD parameters from documentation
H_loss = 5.8 / 32.0  # 0.18125 kW/K (5.8 kW at -12°C, 20°C inside)
C_room = 9.5         # kWh/K (air + internal partition walls)
C_floor = 6.0        # kWh/K (21.2 tons concrete screed 50mm)
U_floor_room = 1.68  # kW/K (heat transfer floor to room)
U_pipe_floor = 2.50  # kW/K (heat transfer water pipes to floor slab)
delta_T_water = 4.0  # specified 4°C temperature drop in underfloor heating
PRICE_PER_KWH = 5.00 # CZK / kWh D57d

# --- Model 1: Gawliczek 8,9 kW R290 (HIGHLY/Hitachi kompresor) ---
def cop_89kw(te, tf, rh=70.0):
    if te >= 7.0: c = 5.08 + (te - 7.0) * 0.08
    elif te >= 2.0: c = 4.20 + (te - 2.0) * (5.08 - 4.20) / 5.0
    elif te >= -7.0: c = 3.12 + (te + 7.0) * (4.20 - 3.12) / 9.0
    elif te >= -15.0: c = 2.48 + (te + 15.0) * (3.12 - 2.48) / 8.0
    else: c = max(1.8, 2.08 + (te + 20.0) * (2.48 - 2.08) / 5.0)
    c *= (1.0 + 0.022 * (35.0 - tf))
    if -3.5 <= te <= 3.5 and rh > 75.0:
        c *= (1.0 - 0.08 * (rh / 100.0))
    return max(1.2, c)

def cap_89kw(te):
    if te >= 7.0: return 8.9
    if te >= 2.0: return 7.8 + (te - 2.0) * (8.9 - 7.8) / 5.0
    if te >= -7.0: return 6.5 + (te + 7.0) * (7.8 - 6.5) / 9.0
    if te >= -15.0: return 5.3 + (te + 15.0) * (6.5 - 5.3) / 8.0
    return max(3.8, 4.5 + (te + 20.0) * (5.3 - 4.5) / 5.0)

# --- Model 2: Gawliczek 8,1 kW R290 Ultra tiché (Panasonic kompresor) ---
def cop_81kw(te, tf, rh=70.0):
    if te >= 7.0: c = 5.30 + (te - 7.0) * 0.08
    elif te >= 2.0: c = 4.45 + (te - 2.0) * (5.30 - 4.45) / 5.0
    elif te >= -7.0: c = 3.35 + (te + 7.0) * (4.45 - 3.35) / 9.0
    elif te >= -15.0: c = 2.65 + (te + 15.0) * (3.35 - 2.65) / 8.0
    else: c = max(1.8, 2.20 + (te + 20.0) * (2.65 - 2.20) / 5.0)
    c *= (1.0 + 0.022 * (35.0 - tf))
    if -3.5 <= te <= 3.5 and rh > 75.0:
        c *= (1.0 - 0.07 * (rh / 100.0))
    return max(1.2, c)

def cap_81kw(te):
    if te >= 7.0: return 8.1
    if te >= 2.0: return 7.5 + (te - 2.0) * (8.1 - 7.5) / 5.0
    if te >= -7.0: return 6.3 + (te + 7.0) * (7.5 - 6.3) / 9.0
    if te >= -15.0: return 5.2 + (te + 15.0) * (6.3 - 5.2) / 8.0
    return max(3.5, 4.3 + (te + 20.0) * (5.2 - 4.3) / 5.0)

full_output = {
    'parameters': {
        'building': 'Rodinný dům (novostavba)',
        'heat_loss_design_kw': 5.80,
        't_ext_design': -12.0,
        't_in_design': 20.0,
        'h_loss_w_per_k': round(H_loss * 1000, 1),
        'floor_screed_thickness_mm': 50,
        'floor_area_m2': 180,
        'concrete_volume_m3': 9.0,
        'concrete_mass_tons': 21.2,
        'c_floor_kwh_per_k': C_floor,
        'c_room_kwh_per_k': C_room,
        'c_total_kwh_per_k': round(C_floor + C_room, 1),
        'temp_drop_c': delta_T_water,
        'room_allowed_fluctuation_c': 1.0,
        'storage_capacity_kwh': round((C_floor + C_room) * 2.0, 1),
        'electricity_price_czk': PRICE_PER_KWH,
        'models': {
            '89kw': {
                'id': '89kw',
                'name': 'Gawliczek 8,9 kW R290 Invertor',
                'url': 'https://www.gawliczek.cz/product-page/8-9kwy-r290-pln%C4%9B-invertorov%C3%A9-tepeln%C3%A9-%C4%8Derpadlo-full-inverter-heat-pump',
                'code': 'PW030-R290',
                'min_kw': 2.5,
                'max_kw': 8.9,
                'price_czk': 58630, # bez DPH
                'cop_a7w35': 5.08,
                'noise': '48-52 dB(A)',
                'compressor': 'HIGHLY / Hitachi twin-rotary'
            },
            '81kw': {
                'id': '81kw',
                'name': 'Gawliczek 8,1 kW R290 Ultra tiché',
                'url': 'https://www.gawliczek.cz/product-page/8-1kw-r290-ultra-tich%C3%A9-pln%C4%9B-invertorov%C3%A9-tepeln%C3%A9-%C4%8Derpadlo',
                'code': 'WH-08-R290',
                'min_kw': 2.5,
                'max_kw': 8.1,
                'price_czk': 69950, # bez DPH
                'cop_a7w35': 5.30,
                'noise': '35-38 dB(A)',
                'compressor': 'Panasonic Inverter twin-rotary'
            }
        }
    },
    'winters': {}
}

for season, data in weather.items():
    times = data['time']
    temps = data['temp']
    rhs = data['rh']
    dnis = data['dni']
    diffs = data['diffuse']
    N = len(temps)
    
    avg_te = sum(temps) / N
    min_te = min(temps)
    max_te = max(temps)
    frost_hrs = sum(1 for t in temps if t < 0)
    deep_frost_hrs = sum(1 for t in temps if t < -10)
    hdd = sum(max(0.0, 21.0 - t) for t in temps) / 24.0

    # 1. 8.9 kW Standard
    el_89_std = 0.0; th_89_std = 0.0; starts_89_std = 0
    # 2. 8.9 kW Optimized
    el_89_opt = 0.0; th_89_opt = 0.0; starts_89_opt = 0
    # 3. 8.1 kW Standard
    el_81_std = 0.0; th_81_std = 0.0; starts_81_std = 0
    # 4. 8.1 kW Optimized
    el_81_opt = 0.0; th_81_opt = 0.0; starts_81_opt = 0

    hourly_records = []
    days_data = {}

    Tr_89_opt = 21.0; Tf_89_opt = 22.5
    Tr_81_opt = 21.0; Tf_81_opt = 22.5

    for i in range(N):
        dt_str = times[i]
        date_str = dt_str[:10]
        hour = int(dt_str[11:13])
        te = temps[i]
        rh = rhs[i]
        q_sol = min(1.2, (0.6 * dnis[i] + 0.3 * diffs[i]) * 0.0035)
        q_gain = q_sol + 0.3

        t_flow_std = min(36.0, max(24.0, 23.0 + (15.0 - te) * 10.0 / 27.0))
        t_ret_std = t_flow_std - delta_T_water

        q_loss_std = H_loss * (21.0 - te)
        q_need_std = max(0.0, q_loss_std - q_gain)

        # --- A) 8.9 kW Standard ---
        cop89_std = cop_89kw(te, t_flow_std, rh)
        if q_need_std <= 0:
            q_hp_89_std = 0.0; p_el_89_std = 0.0
        elif q_need_std < 2.5:
            duty = q_need_std / 2.5
            p_el_89_std = q_need_std / (cop89_std * (0.88 + 0.12 * duty))
            q_hp_89_std = q_need_std
            starts_89_std += 1
        else:
            cap89 = cap_89kw(te)
            q_hp = min(q_need_std, cap89)
            q_bk = q_need_std - q_hp
            p_el_89_std = q_hp / cop89_std + q_bk / 1.0
            q_hp_89_std = q_need_std
            starts_89_std += 1
        el_89_std += p_el_89_std; th_89_std += q_hp_89_std

        # --- B) 8.1 kW Standard ---
        cop81_std = cop_81kw(te, t_flow_std, rh)
        if q_need_std <= 0:
            q_hp_81_std = 0.0; p_el_81_std = 0.0
        elif q_need_std < 2.5:
            duty = q_need_std / 2.5
            p_el_81_std = q_need_std / (cop81_std * (0.90 + 0.10 * duty))
            q_hp_81_std = q_need_std
            starts_81_std += 1
        else:
            cap81 = cap_81kw(te)
            q_hp = min(q_need_std, cap81)
            q_bk = q_need_std - q_hp
            p_el_81_std = q_hp / cop81_std + q_bk / 1.0
            q_hp_81_std = q_need_std
            starts_81_std += 1
        el_81_std += p_el_81_std; th_81_std += q_hp_81_std

        # Lookahead for optimized
        win = temps[max(0, i-6):min(N, i+18)]
        avg_win = sum(win) / len(win)
        is_charge = (10 <= hour <= 16) or (te > avg_win + 0.8)
        is_discharge = (hour >= 22 or hour <= 6) and (te < avg_win)
        target_tr = 21.9 if is_charge else (20.1 if is_discharge else 20.8)

        # --- C) 8.9 kW Optimized ---
        q_fl_89 = U_floor_room * (Tf_89_opt - Tr_89_opt)
        q_loss_89 = H_loss * (Tr_89_opt - te)
        Tr_cand_89 = Tr_89_opt + (q_fl_89 + q_gain - q_loss_89) / C_room
        cap89 = cap_89kw(te)
        if Tr_cand_89 < target_tr:
            defic = max(0.0, (target_tr - Tr_cand_89)*C_room + (target_tr + 1.8 - Tf_89_opt)*C_floor)
            if defic < 1.3 and not is_charge and Tr_89_opt > 20.3:
                q_hp_89 = 0.0
            else:
                q_hp_89 = max(2.5, min(cap89, defic))
        else:
            q_hp_89 = 0.0
        q_bk_89 = max(0.0, q_hp_89 - cap89)
        q_hp_89 = min(q_hp_89, cap89)
        Tf_89_opt += (q_hp_89 + q_bk_89 - q_fl_89) / C_floor
        Tr_89_opt += (U_floor_room * (Tf_89_opt - Tr_89_opt) + q_gain - q_loss_89) / C_room
        if Tr_89_opt < 20.0: Tr_89_opt = 20.0
        if q_hp_89 > 0:
            tm89 = Tf_89_opt + (q_hp_89 / U_pipe_floor)
            tfl89 = min(36.0, max(24.0, tm89 + delta_T_water / 2.0))
            p_el_89_opt = q_hp_89 / cop_89kw(te, tfl89, rh) + q_bk_89 / 1.0
            starts_89_opt += 1
        else:
            p_el_89_opt = 0.0
        el_89_opt += p_el_89_opt; th_89_opt += (q_hp_89 + q_bk_89)

        # --- D) 8.1 kW Optimized ---
        q_fl_81 = U_floor_room * (Tf_81_opt - Tr_81_opt)
        q_loss_81 = H_loss * (Tr_81_opt - te)
        Tr_cand_81 = Tr_81_opt + (q_fl_81 + q_gain - q_loss_81) / C_room
        cap81 = cap_81kw(te)
        if Tr_cand_81 < target_tr:
            defic = max(0.0, (target_tr - Tr_cand_81)*C_room + (target_tr + 1.8 - Tf_81_opt)*C_floor)
            if defic < 1.2 and not is_charge and Tr_81_opt > 20.3:
                q_hp_81 = 0.0
            else:
                q_hp_81 = max(2.5, min(cap81, defic))
        else:
            q_hp_81 = 0.0
        q_bk_81 = max(0.0, q_hp_81 - cap81)
        q_hp_81 = min(q_hp_81, cap81)
        Tf_81_opt += (q_hp_81 + q_bk_81 - q_fl_81) / C_floor
        Tr_81_opt += (U_floor_room * (Tf_81_opt - Tr_81_opt) + q_gain - q_loss_81) / C_room
        if Tr_81_opt < 20.0: Tr_81_opt = 20.0
        if q_hp_81 > 0:
            tm81 = Tf_81_opt + (q_hp_81 / U_pipe_floor)
            tfl81 = min(36.0, max(24.0, tm81 + delta_T_water / 2.0))
            tret81 = tfl81 - delta_T_water
            cop81_eff = cop_81kw(te, tfl81, rh)
            p_el_81_opt = q_hp_81 / cop81_eff + q_bk_81 / 1.0
            starts_81_opt += 1
        else:
            tfl81 = Tf_81_opt
            tret81 = Tf_81_opt
            cop81_eff = cop_81kw(te, tfl81, rh)
            p_el_81_opt = 0.0
        el_81_opt += p_el_81_opt; th_81_opt += (q_hp_81 + q_bk_81)

        # Day aggregation
        if date_str not in days_data:
            days_data[date_str] = {
                'date': date_str,
                'te_vals': [],
                'el_89_std': 0.0, 'el_89_opt': 0.0,
                'el_81_std': 0.0, 'el_81_opt': 0.0,
                'th_81_opt': 0.0, 'tr_81_vals': []
            }
        days_data[date_str]['te_vals'].append(te)
        days_data[date_str]['el_89_std'] += p_el_89_std
        days_data[date_str]['el_89_opt'] += p_el_89_opt
        days_data[date_str]['el_81_std'] += p_el_81_std
        days_data[date_str]['el_81_opt'] += p_el_81_opt
        days_data[date_str]['th_81_opt'] += (q_hp_81 + q_bk_81)
        days_data[date_str]['tr_81_vals'].append(Tr_81_opt)

        # Hourly sample for Jan 6 - 14 freeze
        dt_m = dt_str[5:7]
        dt_d = int(dt_str[8:10])
        if (dt_m == '01' and 6 <= dt_d <= 14):
            hourly_records.append({
                'time': dt_str,
                'te': round(te, 1),
                'rh': round(rh, 0),
                'tr_81_opt': round(Tr_81_opt, 2),
                'tf_81_opt': round(Tf_81_opt, 2),
                'tfl_81_opt': round(tfl81, 1),
                'tret_81_opt': round(tret81, 1),
                'pel_89_opt': round(p_el_89_opt, 2),
                'pel_81_opt': round(p_el_81_opt, 2),
                'cop_81_opt': round(cop81_eff, 2)
            })

    daily_list = []
    for d_k, d_v in days_data.items():
        te_list = d_v['te_vals']
        daily_list.append({
            'date': d_k,
            'te_avg': round(sum(te_list)/len(te_list), 1),
            'te_min': round(min(te_list), 1),
            'te_max': round(max(te_list), 1),
            'el_89_std': round(d_v['el_89_std'], 1),
            'el_89_opt': round(d_v['el_89_opt'], 1),
            'el_81_std': round(d_v['el_81_std'], 1),
            'el_81_opt': round(d_v['el_81_opt'], 1),
            'th_81_opt': round(d_v['th_81_opt'], 1),
            'scop_81_opt': round(d_v['th_81_opt'] / d_v['el_81_opt'], 2) if d_v['el_81_opt'] > 0 else 0,
            'tr_min': round(min(d_v['tr_81_vals']), 1),
            'tr_max': round(max(d_v['tr_81_vals']), 1)
        })

    monthly_data = {}
    for d in daily_list:
        m_k = d['date'][:7]
        if m_k not in monthly_data:
            monthly_data[m_k] = {
                'month': m_k,
                'te_sum': 0.0, 'cnt': 0,
                'th_81': 0.0,
                'el_89_std': 0.0, 'el_89_opt': 0.0,
                'el_81_std': 0.0, 'el_81_opt': 0.0,
            }
        monthly_data[m_k]['te_sum'] += d['te_avg']
        monthly_data[m_k]['cnt'] += 1
        monthly_data[m_k]['th_81'] += d['th_81_opt']
        monthly_data[m_k]['el_89_std'] += d['el_89_std']
        monthly_data[m_k]['el_89_opt'] += d['el_89_opt']
        monthly_data[m_k]['el_81_std'] += d['el_81_std']
        monthly_data[m_k]['el_81_opt'] += d['el_81_opt']

    monthly_list = []
    for m_k in sorted(monthly_data.keys()):
        mv = monthly_data[m_k]
        c = mv['cnt']
        monthly_list.append({
            'month': m_k,
            'te_avg': round(mv['te_sum'] / c, 1),
            'th_81': round(mv['th_81'], 1),
            'el_89_std': round(mv['el_89_std'], 1),
            'el_89_opt': round(mv['el_89_opt'], 1),
            'el_81_std': round(mv['el_81_std'], 1),
            'el_81_opt': round(mv['el_81_opt'], 1),
            'scop_89_opt': round(mv['th_81'] / mv['el_89_opt'], 2) if mv['el_89_opt'] > 0 else 0,
            'scop_81_opt': round(mv['th_81'] / mv['el_81_opt'], 2) if mv['el_81_opt'] > 0 else 0,
            'savings_vs_89_std_czk': round((mv['el_89_std'] - mv['el_81_opt']) * PRICE_PER_KWH, 0)
        })

    scop_89_std = round(th_89_std / el_89_std, 2)
    scop_89_opt = round(th_89_opt / el_89_opt, 2)
    scop_81_std = round(th_81_std / el_81_std, 2)
    scop_81_opt = round(th_81_opt / el_81_opt, 2)

    savings_81opt_vs_89std_kwh = round(el_89_std - el_81_opt, 1)
    savings_81opt_vs_89std_pct = round((savings_81opt_vs_89std_kwh / el_89_std) * 100.0, 1)
    savings_81opt_vs_89opt_kwh = round(el_89_opt - el_81_opt, 1)
    savings_81opt_vs_89opt_pct = round((savings_81opt_vs_89opt_kwh / el_89_opt) * 100.0, 1)

    full_output['winters'][season] = {
        'season': season,
        'weather_stats': {
            'avg_temp': round(avg_te, 1),
            'min_temp': round(min_te, 1),
            'max_temp': round(max_te, 1),
            'frost_hours': frost_hrs,
            'deep_frost_hours': deep_frost_hrs,
            'hdd_21': round(hdd, 0)
        },
        'results': {
            # 8.9 kW Gawliczek
            'el_89_std_kwh': round(el_89_std, 1),
            'el_89_opt_kwh': round(el_89_opt, 1),
            'scop_89_std': scop_89_std,
            'scop_89_opt': scop_89_opt,
            'cost_89_std_czk': round(el_89_std * PRICE_PER_KWH, 0),
            'cost_89_opt_czk': round(el_89_opt * PRICE_PER_KWH, 0),
            'starts_89_std': starts_89_std,
            'starts_89_opt': starts_89_opt,
            # 8.1 kW Gawliczek Ultra tiché
            'el_81_std_kwh': round(el_81_std, 1),
            'el_81_opt_kwh': round(el_81_opt, 1),
            'scop_81_std': scop_81_std,
            'scop_81_opt': scop_81_opt,
            'cost_81_std_czk': round(el_81_std * PRICE_PER_KWH, 0),
            'cost_81_opt_czk': round(el_81_opt * PRICE_PER_KWH, 0),
            'starts_81_std': starts_81_std,
            'starts_81_opt': starts_81_opt,
            'th_kwh': round(th_81_opt, 1),
            # Comparison metrics
            'savings_81opt_vs_89std_kwh': savings_81opt_vs_89std_kwh,
            'savings_81opt_vs_89std_pct': savings_81opt_vs_89std_pct,
            'savings_81opt_vs_89std_czk': round(savings_81opt_vs_89std_kwh * PRICE_PER_KWH, 0),
            'savings_81opt_vs_89opt_kwh': savings_81opt_vs_89opt_kwh,
            'savings_81opt_vs_89opt_pct': savings_81opt_vs_89opt_pct,
            'savings_81opt_vs_89opt_czk': round(savings_81opt_vs_89opt_kwh * PRICE_PER_KWH, 0),
        },
        'monthly': monthly_list,
        'daily': daily_list,
        'hourly_sample': hourly_records
    }

os.makedirs('sim_data', exist_ok=True)
with open('sim_data/full_simulation_results.json', 'w', encoding='utf-8') as f:
    json.dump(full_output, f, indent=2)

print('Updated simulation with 8.9 kW and 8.1 kW Ultra tiché generated successfully!')
