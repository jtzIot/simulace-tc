import json

with open('sim_data/full_simulation_results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fmt = "{:<10} | {:>7} | {:>10} | {:>10} | {:>10} | {:>9} | {:>9} | {:>10} | {:>10}"
print(fmt.format("Zima", "T_prum", "8.9kW Běž", "8.9kW Opt", "8.1kW Opt", "SCOP 8.9", "SCOP 8.1", "Úspora kWh", "Úspora Kč"))
print("-" * 105)
for zima, info in d['winters'].items():
    ws = info['weather_stats']
    r = info['results']
    print(fmt.format(
        zima,
        f"{ws['avg_temp']:.1f} °C",
        f"{r['el_89_std_kwh']:.0f} kWh",
        f"{r['el_89_opt_kwh']:.0f} kWh",
        f"{r['el_81_opt_kwh']:.0f} kWh",
        f"{r['scop_89_opt']:.2f}",
        f"{r['scop_81_opt']:.2f}",
        f"-{r['savings_81opt_vs_89std_kwh']:.0f} kWh",
        f"-{r['savings_81opt_vs_89std_czk']:.0f} Kč"
    ))
