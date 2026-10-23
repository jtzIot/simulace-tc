import json

with open('sim_data/full_simulation_results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fmt = "{:<11} | {:>8} | {:>8} | {:>10} | {:>10} | {:>10} | {:>8} | {:>8} | {:>8} | {:>10} | {:>10} | {:>10}"
print(fmt.format("Zima", "T_prum", "T_min", "Teplo_kWh", "Std_el_kWh", "Opt_el_kWh", "Std_SCOP", "Opt_SCOP", "Uspora_%", "Uspora_Kc", "Starty_Std", "Starty_Opt"))
print("-" * 140)
for zima, info in d['winters'].items():
    ws = info['weather_stats']
    r = info['results']
    print(fmt.format(
        zima,
        f"{ws['avg_temp']:.1f} °C",
        f"{ws['min_temp']:.1f} °C",
        f"{r['th_std_kwh']:.0f}",
        f"{r['el_std_kwh']:.0f}",
        f"{r['el_opt_kwh']:.0f}",
        f"{r['scop_std']:.2f}",
        f"{r['scop_opt']:.2f}",
        f"{r['savings_pct']:.1f} %",
        f"{r['savings_czk']:.0f} Kč",
        str(r['starts_std']),
        str(r['starts_opt'])
    ))
