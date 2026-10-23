import json
import math
import os
from datetime import datetime

with open('sim_data/weather_10_winters.json', 'r', encoding='utf-8') as f:
    weather = json.load(f)

# Referenční RD parameters from documentation
H_loss = 5.8 / 32.0  # 0.18125 kW/K (5.8 kW at -12°C, 20°C inside)
C_room = 9.5         # kWh/K (air + internal partition walls)
C_floor = 6.0        # kWh/K (21.2 tons concrete screed 50mm)
U_floor_room = 1.68  # kW/K (heat transfer floor to room)
U_pipe_floor = 2.50  # kW/K (heat transfer water pipes to floor slab)
delta_T_water = 4.0  # specified 4°C temperature drop in underfloor heating

def get_cop(t_ext, t_flow, rh=70.0):
    if t_ext >= 7.0:
        cop_nom = 5.15 + (t_ext - 7.0) * 0.08
    elif t_ext >= 2.0:
        cop_nom = 4.25 + (t_ext - 2.0) * (5.15 - 4.25) / 5.0
    elif t_ext >= -7.0:
        cop_nom = 3.15 + (t_ext - (-7.0)) * (4.25 - 3.15) / 9.0
    elif t_ext >= -15.0:
        cop_nom = 2.50 + (t_ext - (-15.0)) * (3.15 - 2.50) / 8.0
    else:
        cop_nom = max(1.8, 2.10 + (t_ext - (-20.0)) * (2.50 - 2.10) / 5.0)
    
    # Low temperature floor heating correction (nominal test is W35)
    # With 4°C drop, average water temperature is very low!
    flow_corr = 1.0 + 0.022 * (35.0 - t_flow)
    cop = cop_nom * flow_corr
    
    # Defrost penalty: high humidity around freezing point
    if -3.5 <= t_ext <= 3.5 and rh > 75.0:
        defrost_loss = 0.08 * (rh / 100.0)
        cop *= (1.0 - defrost_loss)
        
    return max(1.2, cop)

def max_hp_capacity(t_ext):
    if t_ext >= 7.0: return 11.4
    if t_ext >= 2.0: return 10.0 + (t_ext - 2.0) * (11.4 - 10.0) / 5.0
    if t_ext >= -7.0: return 8.2 + (t_ext - (-7.0)) * (10.0 - 8.2) / 9.0
    if t_ext >= -15.0: return 6.4 + (t_ext - (-15.0)) * (8.2 - 6.4) / 8.0
    return max(4.5, 5.3 + (t_ext - (-20.0)) * (6.4 - 5.3) / 5.0)

PRICE_PER_KWH = 5.00 # CZK / kWh D57d

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
        'hp_model': 'Gawliczek Invertor GW040-DKZLRS-E (R290)',
        'hp_max_power_kw': 11.4,
        'hp_min_power_kw': 4.5,
        'hp_tank': 'Kombinovaná nerezová nádrž PDWT-300L (200l TUV + 100l topná vyrovnávací)',
        'electricity_price_czk': PRICE_PER_KWH
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
    
    # Stats
    avg_te = sum(temps) / N
    min_te = min(temps)
    max_te = max(temps)
    frost_hrs = sum(1 for t in temps if t < 0)
    deep_frost_hrs = sum(1 for t in temps if t < -10)
    hdd = sum(max(0.0, 21.0 - t) for t in temps) / 24.0
    
    # Hourly records
    hourly_records = []
    
    # State tracking
    # Standard
    T_room_std = 21.0
    std_el_tot = 0.0
    std_th_tot = 0.0
    std_starts = 0
    std_backup_tot = 0.0
    std_flow_sum = 0.0
    std_flow_cnt = 0
    
    # Optimized
    T_room_opt = 21.0
    T_floor_opt = 22.5
    opt_el_tot = 0.0
    opt_th_tot = 0.0
    opt_starts = 0
    opt_backup_tot = 0.0
    opt_flow_sum = 0.0
    opt_flow_cnt = 0
    
    # Day grouping
    days_data = {}
    
    for i in range(N):
        dt_str = times[i]
        date_str = dt_str[:10]
        hour = int(dt_str[11:13])
        te = temps[i]
        rh = rhs[i]
        
        q_sol = min(1.2, (0.6 * dnis[i] + 0.3 * diffs[i]) * 0.0035)
        q_gain = q_sol + 0.3
        
        # 1. Standard Step
        q_loss_std = H_loss * (T_room_std - te)
        q_need_std = max(0.0, q_loss_std - q_gain)
        
        # Equithermal water supply curve with Delta T = 4°C
        # At -12°C: 33°C, at +15°C: 23°C
        t_flow_std = 23.0 + (15.0 - te) * (33.0 - 23.0) / 27.0
        t_flow_std = min(36.0, max(24.0, t_flow_std))
        t_ret_std = t_flow_std - delta_T_water
        
        cop_std_raw = get_cop(te, t_flow_std, rh)
        
        if q_need_std <= 0:
            q_hp_std = 0.0
            p_el_std = 0.0
            cop_std_eff = cop_std_raw
            q_backup_std = 0.0
        elif q_need_std < 4.5:
            # Cycling duty cycle
            duty = q_need_std / 4.5
            cop_std_eff = cop_std_raw * (0.86 + 0.14 * duty)
            q_hp_std = q_need_std
            p_el_std = q_hp_std / cop_std_eff
            q_backup_std = 0.0
            std_starts += 2
        else:
            cap = max_hp_capacity(te)
            q_hp_std = min(q_need_std, cap)
            q_backup_std = q_need_std - q_hp_std
            cop_std_eff = cop_std_raw
            p_el_std = q_hp_std / cop_std_eff + q_backup_std / 1.0
            std_starts += 1
            
        std_el_tot += p_el_std
        std_th_tot += (q_hp_std + q_backup_std)
        std_backup_tot += q_backup_std
        if q_hp_std > 0:
            std_flow_sum += t_flow_std
            std_flow_cnt += 1
            
        # 2. Optimized Step
        # 24h rolling lookahead
        window = temps[max(0, i-6):min(N, i+18)]
        avg_win = sum(window) / len(window)
        
        is_charge = (10 <= hour <= 16) or (te > avg_win + 0.8)
        is_discharge = (hour >= 22 or hour <= 6) and (te < avg_win)
        
        if is_charge:
            target_tr = 21.9
        elif is_discharge:
            target_tr = 20.1
        else:
            target_tr = 20.8
            
        q_floor_to_room = U_floor_room * (T_floor_opt - T_room_opt)
        q_loss_opt = H_loss * (T_room_opt - te)
        dT_room = (q_floor_to_room + q_gain - q_loss_opt) / C_room
        T_room_cand = T_room_opt + dT_room
        
        cap = max_hp_capacity(te)
        
        if T_room_cand < target_tr:
            deficit = (target_tr - T_room_cand) * C_room + (target_tr + 1.8 - T_floor_opt) * C_floor
            deficit = max(0.0, deficit)
            if deficit < 2.0 and not is_charge and T_room_opt > 20.3:
                q_hp_opt = 0.0
            else:
                q_hp_opt = max(4.5, min(cap, deficit))
        else:
            q_hp_opt = 0.0
            
        q_backup_opt = 0.0
        if q_hp_opt > cap:
            q_backup_opt = q_hp_opt - cap
            q_hp_opt = cap
            
        dT_floor = (q_hp_opt + q_backup_opt - q_floor_to_room) / C_floor
        T_floor_opt += dT_floor
        T_room_opt += (U_floor_room * (T_floor_opt - T_room_opt) + q_gain - q_loss_opt) / C_room
        
        if T_room_opt < 20.0:
            boost = (20.0 - T_room_opt) * C_room
            q_hp_opt = min(cap, q_hp_opt + boost)
            T_room_opt = 20.0
            
        if q_hp_opt > 0:
            t_mean = T_floor_opt + (q_hp_opt / U_pipe_floor)
            t_flow_opt = min(36.0, max(24.0, t_mean + (delta_T_water / 2.0)))
            t_ret_opt = t_flow_opt - delta_T_water
            cop_opt_eff = get_cop(te, t_flow_opt, rh)
            p_el_opt = q_hp_opt / cop_opt_eff + q_backup_opt / 1.0
            opt_starts += 1
            opt_flow_sum += t_flow_opt
            opt_flow_cnt += 1
        else:
            t_flow_opt = T_floor_opt
            t_ret_opt = T_floor_opt
            cop_opt_eff = get_cop(te, t_flow_opt, rh)
            p_el_opt = 0.0
            
        opt_el_tot += p_el_opt
        opt_th_tot += (q_hp_opt + q_backup_opt)
        opt_backup_tot += q_backup_opt
        
        slab_stored_kwh = max(0.0, (T_floor_opt - 20.0) * C_floor)
        
        # Save sample hourly if it is in January (Jan 6 - 15) or first 3 days of months
        dt_m = dt_str[5:7]
        dt_d = int(dt_str[8:10])
        if (dt_m == '01' and 6 <= dt_d <= 14):
            hourly_records.append({
                'time': dt_str,
                'te': round(te, 1),
                'rh': round(rh, 0),
                'tr_std': round(T_room_std, 2),
                'tr_opt': round(T_room_opt, 2),
                'tf_opt': round(T_floor_opt, 2),
                't_flow_opt': round(t_flow_opt, 1),
                't_ret_opt': round(t_ret_opt, 1),
                'q_hp_std': round(q_hp_std + q_backup_std, 2),
                'q_hp_opt': round(q_hp_opt + q_backup_opt, 2),
                'pel_std': round(p_el_std, 2),
                'pel_opt': round(p_el_opt, 2),
                'cop_std': round(cop_std_eff, 2),
                'cop_opt': round(cop_opt_eff, 2),
                'slab_stored_kwh': round(slab_stored_kwh, 2)
            })
            
        if date_str not in days_data:
            days_data[date_str] = {
                'date': date_str,
                'te_vals': [],
                'th_std': 0.0, 'el_std': 0.0,
                'th_opt': 0.0, 'el_opt': 0.0,
                'tr_opt_vals': []
            }
        days_data[date_str]['te_vals'].append(te)
        days_data[date_str]['th_std'] += (q_hp_std + q_backup_std)
        days_data[date_str]['el_std'] += p_el_std
        days_data[date_str]['th_opt'] += (q_hp_opt + q_backup_opt)
        days_data[date_str]['el_opt'] += p_el_opt
        days_data[date_str]['tr_opt_vals'].append(T_room_opt)

    daily_list = []
    for d_k, d_v in days_data.items():
        te_list = d_v['te_vals']
        daily_list.append({
            'date': d_k,
            'te_avg': round(sum(te_list)/len(te_list), 1),
            'te_min': round(min(te_list), 1),
            'te_max': round(max(te_list), 1),
            'th_std': round(d_v['th_std'], 1),
            'el_std': round(d_v['el_std'], 1),
            'th_opt': round(d_v['th_opt'], 1),
            'el_opt': round(d_v['el_opt'], 1),
            'scop_std': round(d_v['th_std'] / d_v['el_std'], 2) if d_v['el_std'] > 0 else 0,
            'scop_opt': round(d_v['th_opt'] / d_v['el_opt'], 2) if d_v['el_opt'] > 0 else 0,
            'tr_min': round(min(d_v['tr_opt_vals']), 1),
            'tr_max': round(max(d_v['tr_opt_vals']), 1)
        })
        
    monthly_data = {}
    for d in daily_list:
        m_k = d['date'][:7]
        if m_k not in monthly_data:
            monthly_data[m_k] = {
                'month': m_k,
                'te_sum': 0.0, 'cnt': 0,
                'th_std': 0.0, 'el_std': 0.0,
                'th_opt': 0.0, 'el_opt': 0.0,
            }
        monthly_data[m_k]['te_sum'] += d['te_avg']
        monthly_data[m_k]['cnt'] += 1
        monthly_data[m_k]['th_std'] += d['th_std']
        monthly_data[m_k]['el_std'] += d['el_std']
        monthly_data[m_k]['th_opt'] += d['th_opt']
        monthly_data[m_k]['el_opt'] += d['el_opt']
        
    monthly_list = []
    for m_k in sorted(monthly_data.keys()):
        mv = monthly_data[m_k]
        c = mv['cnt']
        monthly_list.append({
            'month': m_k,
            'te_avg': round(mv['te_sum'] / c, 1),
            'th_std': round(mv['th_std'], 1),
            'el_std': round(mv['el_std'], 1),
            'th_opt': round(mv['th_opt'], 1),
            'el_opt': round(mv['el_opt'], 1),
            'scop_std': round(mv['th_std'] / mv['el_std'], 2) if mv['el_std'] > 0 else 0,
            'scop_opt': round(mv['th_opt'] / mv['el_opt'], 2) if mv['el_opt'] > 0 else 0,
            'savings_kwh': round(mv['el_std'] - mv['el_opt'], 1),
            'savings_czk': round((mv['el_std'] - mv['el_opt']) * PRICE_PER_KWH, 0)
        })

    scop_std = round(std_th_tot / std_el_tot, 2) if std_el_tot > 0 else 0
    scop_opt = round(opt_th_tot / opt_el_tot, 2) if opt_el_tot > 0 else 0
    sav_kwh = round(std_el_tot - opt_el_tot, 1)
    sav_pct = round((sav_kwh / std_el_tot) * 100.0, 1)
    
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
            'th_std_kwh': round(std_th_tot, 1),
            'el_std_kwh': round(std_el_tot, 1),
            'scop_std': scop_std,
            'cost_std_czk': round(std_el_tot * PRICE_PER_KWH, 0),
            'starts_std': std_starts,
            'avg_t_flow_std': round(std_flow_sum / max(1, std_flow_cnt), 1),
            'th_opt_kwh': round(opt_th_tot, 1),
            'el_opt_kwh': round(opt_el_tot, 1),
            'scop_opt': scop_opt,
            'cost_opt_czk': round(opt_el_tot * PRICE_PER_KWH, 0),
            'starts_opt': opt_starts,
            'avg_t_flow_opt': round(opt_flow_sum / max(1, opt_flow_cnt), 1),
            'savings_kwh': sav_kwh,
            'savings_pct': sav_pct,
            'savings_czk': round(sav_kwh * PRICE_PER_KWH, 0),
            'cycle_reduction_pct': round((1.0 - opt_starts / std_starts) * 100.0, 1)
        },
        'monthly': monthly_list,
        'daily': daily_list,
        'hourly_sample': hourly_records
    }

os.makedirs('sim_data', exist_ok=True)
with open('sim_data/full_simulation_results.json', 'w', encoding='utf-8') as f:
    json.dump(full_output, f, indent=2)

print('Full simulation data generated successfully!')
