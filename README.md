# Simulace vytápění TČ a plynem — v3

Interaktivní simulace rodinného domu na deseti historických topných sezónách (říjen–duben, 2014/15–2023/24). Grafy a ekonomické přehledy zobrazují vybrané pětileté okno.

## Spuštění a sestavení

Otevřete `index.html` nebo původní `Spustit_simulaci.cmd`. Data počasí, model i aplikační JavaScript jsou vloženy v HTML; místní Tailwind a ikony zůstávají součástí projektu. Vyhledávání obcí, nové počasí a externí odkazy vyžadují internet.

```powershell
python scripts/build_full_interactive_app.py
node scripts/test_model_v3.cjs
```

Generátor zapisuje pouze `index.html` v tomto projektu. Už automaticky nepřepisuje kopie v nadřazeném projektu ani v adresáři jiného asistenta.

- `scripts/build_full_interactive_app.py`: HTML/CSS, původní grafy a meteorologický vstup.
- `scripts/model-v3.js`: společný fyzikální model a ekonomika.
- `scripts/review-ui-v3.js`: komfort, citlivost, ekonomický přehled, scénáře A/B, export/import a sdílení.
- `scripts/test_model_v3.cjs`: regresní testy bez dalších npm závislostí.

Moduly se při sestavení vloží do výsledného HTML. Upravujte zdrojové moduly nebo šablonu, nikoli pouze vygenerovaný HTML soubor.

## Změny v3

- Všechny čtyři regulátory používají stejnou energetickou bilanci se dvěma teplotními uzly a krokem 10 minut. Zmizelo umělé zvýšení teploty místnosti bez dodané energie.
- Karty řízení skutečně simulují každou variantu a uvádějí stejnou vybranou sezónu jako hlavní karty. Souhrny jasně označují pětiletý průměr.
- Sepnutí jsou přechody vypnuto → zapnuto při časovém rozlišení modelu. Provozní hodina se již nevydává za jeden start.
- Komfort uvádí průměr, minimum, maximum, hodiny a stupňohodiny mimo pásmo; zobrazují se dodané teplo, patrona, změna uložené energie a chyba energetické bilance.
- TUV má přednost ve výkonové kapacitě; společná patrona je omezena na 3 kW. Případná nedodaná TUV je výslovně vykázána. Volba standardního/poledního ohřevu se respektuje.
- Noční klid a popis akumulace odpovídají vybranému dni. Interval 22–06 h obsahuje osm hodin, součet dvou úseků téhož kalendářního dne.
- Sezónní ekonomika poměrně krátí roční paušály a servis. Celoroční režim doplňuje odhad letní TUV a plné paušály; mimo říjen–duben nesimuluje vytápění.
- ETS 2 je vypnutý volitelný cenový scénář. Výsledek uvádí i úsporu bez něj. Lze zadat rozdíl elektrického paušálu, plynový paušál a zachování přípojky.
- Citlivost ukazuje devět kombinací cen ±30 %, hraniční cenu elektřiny a mírnou/prostřední/studenou sezónu.
- Scénáře A/B uchovávají parametry a souhrn výsledků. JSON obsahuje i vlastní archiv počasí; odkaz přenáší scénář s výchozím archivem. Uložení v prohlížeči může být omezeno jeho kapacitou.
- Posuvníky mají přesné číselné vstupy, detailní sekce se otevírají podle potřeby a stránka umožňuje přiblížení na mobilu.
- Nová verze cache service workeru; čištění omezené na cache této aplikace.

## Interpretace výsledků

Nejde o certifikovaný návrhový software ani validaci konkrétního výrobku. Prediktivní režim je pravidlový regulátor s ideální znalostí budoucí historické teploty, nikoli optimalizační MPC nebo test reálné předpovědi. SG Ready neobsahuje energetickou simulaci FVE.

COP se odvozuje z dosavadního katalogu a modelových korekcí. Certifikáty a hlukové údaje nebyly při této úpravě znovu ověřeny; zdrojové odkazy a omezení jsou přímo v aplikaci. Radiátory předávají teplo do uzlu místnosti bez akumulace v podlaze. Model neřeší detailní hydrauliku, povrchovou teplotu krytiny, odběrové špičky TUV, investice ani budoucí vývoj cen.

Výchozí sezóna 2022/23 v modelu v3: přibližně 3 046 kWh u prediktivního režimu proti 3 160 kWh u referenčního řízení; rozdíl 114 kWh, 3,6 %, při 6 Kč/kWh přibližně 684 Kč. Čísla se změnila opravou modelu; nejsou kalibrována na původní marketingové procento. Současně vždy porovnávejte komfort a dodané teplo.

## Ověření

Testy kontrolují syntaxi sestaveného JavaScriptu, všech deset sezón, zachování energie, součet denních spotřeb, nulový rozdíl při volbě reference, oddělený ETS 2, roční TUV, vypnutou i standardní TUV, nedostatečný výkon za mrazu a radiátorovou bilanci. V prohlížeči byly ověřeny přepínače ekonomiky, uložení/obnova A/B, shoda přehledu plynu a denní detail mrazu.

Nasazení na GitHub Pages je samostatný krok; místní sestavení nic nepublikuje.
