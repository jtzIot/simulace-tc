# Kontrola výpočtů – 25. 10. 2026

Kontrolována lokální aplikace, nikoli shoda s měřením konkrétního domu.

- Nezávislé kontrolní vzorce nákladů souhlasí pro všech 10 sezón: elektřina × variabilní cena + paušály a servis; plyn z dodaného tepla, účinnosti a ceny + paušály a servis.
- SCOP je poměr dodaného tepla a odebrané elektřiny, nikoli aritmetický průměr hodinových COP. Hodinové a denní součty souhlasí.
- Maximální odchylka energetické bilance při výchozím nastavení je 1,11 × 10⁻¹⁰ kWh (numerické zaokrouhlení).
- Ověřeny přestupné roky, sezónní krácení paušálů, letní TUV v ročním režimu, vypnutí jističe, zachování plynové přípojky, VT/NT a nepřičítání paušálů dvakrát.
- Ověřen převod scénáře ETS 2: 30 €/t × 25 Kč/€ × 0,00018 t/kWh × 1,21. Kurz a emisní faktor jsou modelové předpoklady, nikoli aktuální tržní údaje.
- Opraven starý popis kapacity akumulace: používá skutečně nastavenou jednostrannou toleranci místo pevných 2 °C.

## Praktické meze výsledků

Plynová varianta dodává stejné teplo jako simulované TČ. Účinnost vytápění je nastavitelná (výchozí 94 %), účinnost přípravy TUV plynem je pevný předpoklad 86 %. Sezónní náklady obsahují jen poměrnou část ročních plateb; nejde o celou roční fakturu. COP vychází z katalogových bodů a modelových korekcí, nebyl ověřen provozním měřením. Denní optimalizace není matematická záruka maximálního COP ani dodržení teplotního pásma při každém počasí. Setrvačnost a solární zisky mohou způsobit překročení cíle. Investice nejsou zahrnuté.

## Anonymizace a zobrazení

Ve výsledném index.html nejsou žádné osobní identifikátory, souřadnice ani lokální cesty. Dům je označen jako modelový a výchozí archiv počasí Open-Meteo ERA5 je nastaven na modelovou lokalitu Ostrava (211 m n. m., 1960–2026, výchozích nejnovějších 10 sezón 2016–2026). Technické parametry modelového domu, veřejné ceníky a odkazy ČEZ / GasNet / HP KEYMARK zůstaly zachované.

Úvodní přehled byl ověřen v prohlížeči: průměr pěti vybraných sezón při výchozím nastavení TČ 19 019 Kč, plyn 24 783 Kč, rozdíl 5 764 Kč za topnou sezónu, ETS vypnuto.

Testy: `node scripts/test_audit.cjs`, `node scripts/test_energy_prices.cjs`, `node scripts/test_model_v3.cjs` – všechny prošly.
